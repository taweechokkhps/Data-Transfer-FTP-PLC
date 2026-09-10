import customtkinter as ctk
import tkinter as tk
import time
import os
import sys
from core.config_service import ConfigManager
from core.logger import logger
from ui.views.dashboard_view import DashboardView
from ui.views.plc_manager_view import PLCManagerView
from ui.views.settings_view import SettingsView

# Apply Purple Theme overrides
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
if "CTkButton" in ctk.ThemeManager.theme:
    ctk.ThemeManager.theme["CTkButton"]["fg_color"] = ["#7B1FA2", "#7B1FA2"]
    ctk.ThemeManager.theme["CTkButton"]["hover_color"] = ["#4A148C", "#4A148C"]
if "CTkProgressBar" in ctk.ThemeManager.theme:
    ctk.ThemeManager.theme["CTkProgressBar"]["progress_color"] = ["#7B1FA2", "#7B1FA2"]
if "CTkOptionMenu" in ctk.ThemeManager.theme:
    ctk.ThemeManager.theme["CTkOptionMenu"]["fg_color"] = ["#7B1FA2", "#7B1FA2"]
    ctk.ThemeManager.theme["CTkOptionMenu"]["button_color"] = ["#4A148C", "#4A148C"]
    ctk.ThemeManager.theme["CTkOptionMenu"]["button_hover_color"] = ["#311B92", "#311B92"]

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FTP Get Data Record Process Critical Control")
        self.geometry("920x620")
        self.minsize(820, 520)
        
        # Schedule window maximization after CustomTkinter initialization/deiconify
        self.after(200, self._maximize_window)
        self.after(400, self._maximize_window)

        def resource_path(relative_path):
            try:
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
            return os.path.join(base_path, relative_path)

        icon_path = resource_path("app_icon.png")
        if os.path.exists(icon_path):
            try:
                self.icon_img = tk.PhotoImage(file=icon_path)
                self.after(200, lambda: self.iconphoto(False, self.icon_img))
            except Exception:
                pass

        self.config_manager = ConfigManager()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="FTP Control", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text="Overview", command=self.show_dashboard)
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10)

        self.btn_plcs = ctk.CTkButton(self.sidebar_frame, text="PLC Manager", command=self.show_plc_manager)
        self.btn_plcs.grid(row=2, column=0, padx=20, pady=10)

        self.btn_settings = ctk.CTkButton(self.sidebar_frame, text="Settings", command=self.show_settings)
        self.btn_settings.grid(row=3, column=0, padx=20, pady=10)

        # Shared target directory variable across Overview and Settings
        from pathlib import Path
        init_target = self.config_manager.get().get("global_settings", {}).get("target_directory", "")
        if not init_target:
            init_target = str(Path.home() / "Desktop" / "PLC_Downloads").replace("\\", "/")
            self.config_manager.update_global_settings({"target_directory": init_target})
        self.target_dir_var = ctk.StringVar(value=init_target)

        # Views
        self.dashboard_view = DashboardView(self, self.config_manager, target_dir_var=self.target_dir_var, request_timer_reset_cb=self.start_auto_pull_timer)
        self.plc_manager_view = PLCManagerView(self, self.config_manager, on_plc_list_updated=self.dashboard_view.refresh_plcs)
        self.settings_view = SettingsView(self, self.config_manager, target_dir_var=self.target_dir_var, on_settings_changed=self.on_settings_saved)

        self.show_dashboard()

        # Auto pull timer
        self.next_pull_time = 0
        self.auto_pull_job = None
        self.next_pull_time = 0
        self.is_auto_pulling = False
        self.start_auto_pull_timer()
        self.update_cooldown_ui()

        # Version
        self.version_label = ctk.CTkLabel(self, text="v1.2.1", text_color="gray", font=ctk.CTkFont(size=12))
        self.version_label.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-10)
        self.version_label.lift()

        # Graceful exit handler
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _maximize_window(self):
        try:
            self.state("zoomed")
        except Exception:
            try:
                self.attributes("-zoomed", True)
            except Exception:
                pass

    def on_closing(self):
        """Cleanly terminates any active downloads, releases PLC sockets, and closes the app."""
        try:
            if self.auto_pull_job is not None:
                self.after_cancel(self.auto_pull_job)
                self.auto_pull_job = None
        except Exception:
            pass

        if hasattr(self, "dashboard_view") and self.dashboard_view.has_active_downloads():
            logger.warning("[App] Closing application during active downloads. Gracefully disconnecting from PLCs...")
            try:
                self.dashboard_view.stop_all_downloads()
            except Exception as e:
                logger.error(f"[App] Error terminating downloads: {e}")
            # Give background socket teardown 250ms to dispatch TCP FIN packets to PLCs
            time.sleep(0.25)

        try:
            self.destroy()
        except Exception:
            pass
        sys.exit(0)

    def select_view(self, view):
        self.dashboard_view.grid_forget()
        self.plc_manager_view.grid_forget()
        self.settings_view.grid_forget()
        view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def show_dashboard(self):
        self.select_view(self.dashboard_view)
        curr = self.config_manager.get()["global_settings"].get("target_directory", "")
        if curr and self.target_dir_var.get() != curr:
            self.target_dir_var.set(curr)
        if not self.dashboard_view.has_active_downloads():
            self.dashboard_view.refresh_plcs()

    def show_plc_manager(self):
        self.select_view(self.plc_manager_view)
        self.plc_manager_view.refresh_list()

    def show_settings(self):
        self.select_view(self.settings_view)
        curr = self.config_manager.get()["global_settings"].get("target_directory", "")
        if curr and self.target_dir_var.get() != curr:
            self.target_dir_var.set(curr)
        self.settings_view.sync_from_config()

    def on_settings_saved(self):
        self.start_auto_pull_timer()
        curr = self.config_manager.get()["global_settings"].get("target_directory", "")
        if curr:
            self.target_dir_var.set(curr)
        if not self.dashboard_view.has_active_downloads():
            self.dashboard_view.refresh_plcs()

    def start_auto_pull_timer(self):
        if self.auto_pull_job is not None:
            self.after_cancel(self.auto_pull_job)
            self.auto_pull_job = None

        g_settings = self.config_manager.get()["global_settings"]
        is_enabled = g_settings.get("auto_pull_enabled", True)
        interval_mins = g_settings.get("auto_pull_interval_minutes", 60)

        if is_enabled and interval_mins > 0:
            interval_ms = interval_mins * 60 * 1000
            self.next_pull_time = time.time() + (interval_ms / 1000.0)
            self.auto_pull_job = self.after(interval_ms, self.trigger_auto_pull)
        else:
            self.next_pull_time = 0
            if hasattr(self, "dashboard_view") and hasattr(self.dashboard_view, "cooldown_label"):
                self.dashboard_view.cooldown_label.configure(text="Auto Pull: Disabled (ปิด)")

    def safe_after(self, delay, cb):
        try:
            if self.winfo_exists():
                return self.after(delay, cb)
        except Exception:
            pass
        return None

    def update_cooldown_ui(self):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        try:
            g_settings = self.config_manager.get().get("global_settings", {})
            is_enabled = g_settings.get("auto_pull_enabled", True)
            interval_mins = g_settings.get("auto_pull_interval_minutes", 60)

            c_label = getattr(self.dashboard_view, "cooldown_label", None)
            has_label = c_label is not None and c_label.winfo_exists()

            if not is_enabled or interval_mins <= 0:
                if has_label:
                    c_label.configure(text="Auto Pull: Disabled (ปิด)", text_color="gray")
            elif self.is_auto_pulling:
                lines = g_settings.get("auto_pull_lines", [])
                lines_str = f" ({len(lines)} Line{'s' if len(lines) != 1 else ''})"
                if has_label:
                    c_label.configure(text=f"🔄 Auto Pull: In Progress{lines_str}...", text_color="#FFA726")
            elif self.next_pull_time > 0:
                remaining = int(self.next_pull_time - time.time())
                lines = g_settings.get("auto_pull_lines", [])
                if not lines:
                    if has_label:
                        c_label.configure(text="Auto Pull: No Lines Selected (ยังไม่เลือก Line)", text_color="#FFA726")
                elif remaining > 0:
                    mins, secs = divmod(remaining, 60)
                    lines_str = f" ({len(lines)} Line{'s' if len(lines) != 1 else ''})"
                    if has_label:
                        c_label.configure(text=f"Next Auto Pull{lines_str} in: {mins:02d}:{secs:02d}", text_color="#3B8ED0")
                else:
                    lines_str = f" ({len(lines)} Line{'s' if len(lines) != 1 else ''})"
                    if has_label:
                        c_label.configure(text=f"🔄 Pulling{lines_str}...", text_color="#FFA726")
        except Exception:
            pass
        self.safe_after(1000, self.update_cooldown_ui)

    def trigger_auto_pull(self):
        g_settings = self.config_manager.get().get("global_settings", {})
        is_enabled = g_settings.get("auto_pull_enabled", True)
        if not is_enabled:
            return

        if self.is_auto_pulling:
            logger.warning("[Auto Pull] Skipped: Previous pull cycle is still in progress.")
            return

        target_lines = g_settings.get("auto_pull_lines", [])
        if not target_lines:
            logger.warning("[Auto Pull] Skipped: No production lines selected in Settings.")
            self.start_auto_pull_timer()
            return

        self.is_auto_pulling = True
        self.next_pull_time = 0
        logger.info(f"[Auto Pull] Triggering download for selected lines: {target_lines}")

        def on_all_finished():
            self.is_auto_pulling = False
            logger.success("[Auto Pull] All selected lines finished downloading. Starting countdown for next cycle.")
            self.start_auto_pull_timer()

        self.dashboard_view.download_selected_lines(target_lines, on_complete=on_all_finished)
