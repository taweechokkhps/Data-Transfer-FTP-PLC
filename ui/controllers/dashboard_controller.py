import threading
import time
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Callable, Optional, Any
from core.ftp_service import test_connection, FTPDownloader
from core.logger import logger

class DashboardController:
    """Controller orchestrating downloads, connection testing, and background workers for the Dashboard."""

    def __init__(self, config_manager, app_logger=None):
        self.config_manager = config_manager
        self.logger = app_logger or logger
        self.active_downloaders: Dict[str, FTPDownloader] = {}
        self.plc_download_callbacks: List[Callable] = []
        self.plc_download_by_name: Dict[str, Callable] = {}

    def register_download_trigger(self, name: str, trigger: Callable):
        """Register a download trigger callback for a specific PLC line."""
        self.plc_download_callbacks.append(trigger)
        if name:
            self.plc_download_by_name[name] = trigger

    def clear_triggers(self):
        """Clear all registered download triggers."""
        self.plc_download_callbacks.clear()
        self.plc_download_by_name.clear()

    def has_active_downloads(self) -> bool:
        """Return True if there are any active download tasks running."""
        return len(self.active_downloaders) > 0

    def stop_all_downloads(self):
        """Cancel and stop all active downloads."""
        for name, dl in list(self.active_downloaders.items()):
            try:
                dl.is_running = False
                dl.cancel()
            except Exception:
                pass
        self.active_downloaders.clear()

    def stop_download(self, line_name: str):
        """Cancel a specific download task by line name."""
        dl = self.active_downloaders.get(line_name)
        if dl:
            dl.is_running = False
            threading.Thread(target=dl.cancel, daemon=True).start()

    def open_target_folder(self, target_dir: str):
        """Open the target directory in Windows Explorer or system file manager."""
        target = target_dir.strip() if target_dir else ""
        if not target:
            return
        p = Path(target)
        try:
            if not p.exists():
                p.mkdir(parents=True, exist_ok=True)
            if hasattr(os, "startfile"):
                os.startfile(str(p))
            else:
                subprocess.Popen(["explorer", str(p)])
        except Exception as e:
            self.logger.error(f"Cannot open folder '{target}': {e}")

    def test_single_connection(self, plc_data: Dict[str, Any], on_status: Optional[Callable] = None, on_finish: Optional[Callable] = None):
        """
        Run connection test in a background thread.
        on_status(status_text: str, color: str, msg_text: str)
        on_finish(ok: bool, msg: str)
        """
        def run():
            if on_status:
                on_status("● Testing...", "#FFA726", "Checking FTP connection...")
            ok, msg = test_connection(
                plc_data.get("host", ""),
                int(plc_data.get("port", 21)),
                plc_data.get("username", "ftp"),
                plc_data.get("password", ""),
                ftp_mode=plc_data.get("ftp_mode", "auto")
            )
            name = plc_data.get("name", "PLC")
            if ok:
                if on_status:
                    on_status("● Conn OK", "#00E676", "เชื่อมต่อสำเร็จ (Connection Success)")
                self.logger.success(f"[{name}] Connection Test: Success")
            else:
                if on_status:
                    on_status("● Conn Fail", "#FF5252", "เชื่อมต่อล้มเหลว (Connection Failed)")
                self.logger.error(f"[{name}] Connection Test: Failed ({msg})")
            if on_finish:
                on_finish(ok, msg)

        threading.Thread(target=run, daemon=True).start()

    def download_single(
        self,
        plc_data: Dict[str, Any],
        target_dir: Optional[str] = None,
        on_init: Optional[Callable] = None,
        on_progress: Optional[Callable] = None,
        on_timer: Optional[Callable] = None,
        on_finish_ui: Optional[Callable] = None,
        on_finish_callback: Optional[Callable] = None,
        safe_after: Optional[Callable] = None
    ):
        """
        Execute file download for a single PLC line in a background thread.
        """
        g_settings = self.config_manager.get().get("global_settings", {})
        target = (target_dir or g_settings.get("target_directory", "")).strip()
        if not target:
            target = str(Path.home() / "Desktop" / "PLC_Downloads").replace("\\", "/")
            self.config_manager.update_global_settings({"target_directory": target})
            self.logger.info(f"Target save directory defaulted to: {target}")

        machines = plc_data.get("machines")
        if not machines:
            r_dirs_raw = plc_data.get("remote_directory", "")
            remote_dirs = [d.strip() for d in r_dirs_raw.split(",") if d.strip()]
            machines = [{"name": f"MC{i+1}", "remote_dir": d} for i, d in enumerate(remote_dirs)]

        downloader = FTPDownloader(
            host=plc_data.get("host", ""),
            port=plc_data.get("port", 21),
            username=plc_data.get("username", "ftp"),
            password=plc_data.get("password", ""),
            machines=machines,
            local_target_dir=target,
            file_extensions=g_settings.get("file_extensions", [".csv", ".txt"]),
            separate_by_date=g_settings.get("separate_by_date", True),
            plc_name=plc_data.get("name", "PLC"),
            date_filter=plc_data.get("date_filter"),
            ftp_mode=plc_data.get("ftp_mode", "auto")
        )

        plc_name = plc_data.get("name", "PLC")
        self.active_downloaders[plc_name] = downloader
        start_time = time.time()
        is_running = [True]

        def call_safe(fn, delay=0):
            if safe_after:
                safe_after(delay, fn)
            elif delay == 0:
                fn()

        def stop_this():
            self.stop_download(plc_name)

        if on_init:
            call_safe(lambda: on_init(stop_callback=stop_this))

        def update_timer_ui():
            if is_running[0]:
                elapsed = int(time.time() - start_time)
                mins, secs = divmod(elapsed, 60)
                t_str = f"⏱ {mins:02d}:{secs:02d}"
                if on_timer:
                    on_timer(t_str, "#3B8ED0")
                call_safe(update_timer_ui, 500)

        if on_timer:
            on_timer("⏱ 00:00", "#3B8ED0")
            call_safe(update_timer_ui, 500)

        def progress_cb(current, total, remaining=0, eta_str="", speed_str=""):
            prog = current / total if total > 0 else 0
            pct = int(prog * 100)
            if remaining > 0 and eta_str:
                if speed_str:
                    c_text = f"{current}/{total} ({pct}%) • ({eta_str}) • {speed_str}"
                else:
                    c_text = f"{current}/{total} ({pct}%) • ({eta_str})"
            else:
                c_text = f"{current} / {total} files ({pct}%)"
            if on_progress:
                call_safe(lambda: on_progress(prog, pct, c_text))

        def log_cb(msg, level=None):
            call_safe(lambda: self.logger.log(msg, level=level))

        def run():
            self.logger.info(f"Starting download for {plc_name}...")
            try:
                downloader.download_files(progress_callback=progress_cb, log_callback=log_cb)
            finally:
                self.active_downloaders.pop(plc_name, None)
                is_running[0] = False
                elapsed = time.time() - start_time
                mins, secs = divmod(int(elapsed), 60)
                time_str = f"{mins:02d}:{secs:02d}" if mins > 0 else f"{elapsed:.2f}s"
                was_cancelled = not downloader.is_running

                if on_finish_ui:
                    call_safe(lambda: on_finish_ui(was_cancelled=was_cancelled, time_str=time_str))
                if on_finish_callback:
                    call_safe(on_finish_callback)

        threading.Thread(target=run, daemon=True).start()

    def download_all(
        self,
        on_complete: Optional[Callable] = None,
        on_button_state: Optional[Callable] = None,
        request_timer_reset_cb: Optional[Callable] = None,
        safe_after: Optional[Callable] = None
    ):
        """Download from all registered PLC lines or stop if already running."""
        def call_safe(fn):
            if safe_after:
                safe_after(0, fn)
            else:
                fn()

        if self.has_active_downloads():
            self.logger.warning("[Download All] Stopping all ongoing downloads...")
            for dl in list(self.active_downloaders.values()):
                dl.is_running = False
            threading.Thread(target=self.stop_all_downloads, daemon=True).start()
            if on_button_state:
                call_safe(lambda: on_button_state(is_running=False))
            return

        if on_button_state:
            call_safe(lambda: on_button_state(is_running=True))

        def _on_all_done():
            if on_button_state:
                call_safe(lambda: on_button_state(is_running=False))
            if on_complete:
                call_safe(on_complete)

        self.download_selected_lines(None, on_complete=_on_all_done, request_timer_reset_cb=request_timer_reset_cb, safe_after=safe_after)

    def download_selected_lines(
        self,
        target_line_names: Optional[List[str]] = None,
        on_complete: Optional[Callable] = None,
        request_timer_reset_cb: Optional[Callable] = None,
        safe_after: Optional[Callable] = None
    ):
        """Execute download triggers for specified lines (or all lines if None)."""
        def call_safe(fn):
            if safe_after:
                safe_after(0, fn)
            else:
                fn()

        if target_line_names is None:
            triggers = list(self.plc_download_callbacks)
        else:
            triggers = [self.plc_download_by_name[name] for name in target_line_names if name in self.plc_download_by_name]

        if not triggers:
            if on_complete:
                call_safe(on_complete)
            return

        remaining = [len(triggers)]
        lock = threading.Lock()

        def on_line_finished():
            with lock:
                remaining[0] -= 1
                if remaining[0] <= 0:
                    if on_complete:
                        call_safe(on_complete)

        for trigger in triggers:
            trigger(on_finish=on_line_finished)

        if request_timer_reset_cb and not on_complete:
            request_timer_reset_cb()
