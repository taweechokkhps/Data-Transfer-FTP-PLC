import customtkinter as ctk
import threading
from core.ftp_service import test_connection, FTPDownloader
from core.logger import logger
from ui.components.tooltip import ToolTip
from ui.components.log_console import LogConsole

class DashboardView(ctk.CTkFrame):
    def __init__(self, master, config_manager, request_timer_reset_cb=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.config_manager = config_manager
        self.request_timer_reset_cb = request_timer_reset_cb
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        header = ctk.CTkLabel(self, text="Download Overview", font=ctk.CTkFont(size=24, weight="bold"))
        header.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.scrollable_plc_frame = ctk.CTkScrollableFrame(self, label_text="Connected PLCs")
        self.scrollable_plc_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Log Console Component
        self.log_console = LogConsole(self, height=150)
        self.log_console.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        logger.register_callback(self.log_console.append_message)
        
        # Bottom controls
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        
        self.btn_download_all = ctk.CTkButton(btn_frame, text="Download All", font=ctk.CTkFont(weight="bold"), text_color="white", command=self.download_all)
        self.btn_download_all.pack(side="left", padx=5)
        
        self.cooldown_label = ctk.CTkLabel(btn_frame, text="", text_color="gray", font=ctk.CTkFont(weight="bold"))
        self.cooldown_label.pack(side="left", padx=10)
        
        self.refresh_plcs()

    def refresh_plcs(self):
        for w in self.scrollable_plc_frame.winfo_children():
            w.destroy()
            
        plcs = self.config_manager.get().get("plcs", [])
        for plc in plcs:
            frame = ctk.CTkFrame(self.scrollable_plc_frame)
            frame.pack(fill="x", padx=5, pady=5)
            
            lbl = ctk.CTkLabel(frame, text=f"{plc['name']} ({plc['host']})", font=ctk.CTkFont(weight="bold"))
            lbl.pack(side="left", padx=10, pady=10)
            
            small_btn = ctk.CTkButton(frame, text="🔌", width=30, height=30)
            small_btn.pack(side="left", padx=5, pady=10)
            ToolTip(small_btn, "Test Connection")
            
            pb = ctk.CTkProgressBar(frame, width=150)
            pb.set(0)
            pb.pack(side="left", padx=20, pady=10)
            
            status = ctk.CTkLabel(frame, text="Ready")
            status.pack(side="left", padx=10, pady=10)
            
            small_btn.configure(command=lambda p=plc, stat=status: self.test_single_connection(p, stat))
            
            btn = ctk.CTkButton(frame, text="Download", font=ctk.CTkFont(weight="bold"), text_color="white",
                                command=lambda p=plc, progress=pb, stat=status: self.download_single(p, progress, stat))
            btn.pack(side="right", padx=10, pady=10)

    def test_single_connection(self, plc_data, status_label):
        def run():
            status_label.configure(text="Testing...")
            ok, msg = test_connection(plc_data['host'], int(plc_data.get('port', 21)), plc_data['username'], plc_data['password'])
            if ok:
                status_label.configure(text="Conn OK")
                logger.success(f"[{plc_data['name']}] Connection Test: Success")
            else:
                status_label.configure(text="Conn Fail")
                logger.error(f"[{plc_data['name']}] Connection Test: Failed ({msg})")
        threading.Thread(target=run, daemon=True).start()

    def download_single(self, plc_data, progress_bar, status_label):
        g_settings = self.config_manager.get()["global_settings"]
        target_dir = g_settings.get("target_directory", "")
        if not target_dir:
            logger.error(f"[{plc_data['name']}] Target directory not configured in Settings.")
            return

        r_dirs_raw = plc_data.get('remote_directory', '')
        remote_dirs = [d.strip() for d in r_dirs_raw.split(',') if d.strip()]
        
        downloader = FTPDownloader(
            host=plc_data['host'],
            port=plc_data.get('port', 21),
            username=plc_data['username'],
            password=plc_data['password'],
            remote_dirs=remote_dirs,
            local_target_dir=target_dir,
            file_extensions=g_settings.get("file_extensions", [".csv", ".txt"]),
            separate_by_date=g_settings.get("separate_by_date", True),
            plc_name=plc_data['name']
        )

        def update_progress(current, total):
            prog = current / total if total > 0 else 0
            self.after(0, lambda: progress_bar.set(prog))
            self.after(0, lambda: status_label.configure(text=f"{current}/{total}"))

        def log_cb(msg):
            self.after(0, lambda: logger.info(msg))

        def run():
            self.after(0, lambda: status_label.configure(text="Connecting..."))
            self.after(0, lambda: progress_bar.set(0))
            logger.info(f"Starting download for {plc_data['name']}...")
            downloader.download_files(progress_callback=update_progress, log_callback=log_cb)
            self.after(0, lambda: status_label.configure(text="Finished"))

        threading.Thread(target=run, daemon=True).start()

    def download_all(self):
        for widget in self.scrollable_plc_frame.winfo_children():
            btn = [w for w in widget.winfo_children() if isinstance(w, ctk.CTkButton) and w.cget("text") == "Download"]
            if btn:
                btn[0].invoke()
        if self.request_timer_reset_cb:
            self.request_timer_reset_cb()
