import customtkinter as ctk
import threading
from pathlib import Path
from tkinter import filedialog
from core.ftp_service import test_connection, FTPDownloader
from core.logger import logger
from ui.components.tooltip import ToolTip
from ui.components.log_console import LogConsole
from ui.components.date_picker import QuickDateFilterDialog

class DashboardView(ctk.CTkFrame):
    def __init__(self, master, config_manager, target_dir_var=None, request_timer_reset_cb=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.config_manager = config_manager
        self.target_dir_var = target_dir_var
        self.request_timer_reset_cb = request_timer_reset_cb
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        header = ctk.CTkLabel(self, text="Download Overview", font=ctk.CTkFont(size=24, weight="bold"))
        header.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # Target Save Directory Bar (Shared identical with Settings)
        dest_card = ctk.CTkFrame(self, corner_radius=8)
        dest_card.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        ctk.CTkLabel(dest_card, text="📁 Target Save Directory (โฟลเดอร์ปลายทาง):", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(12, 8), pady=8)
        
        if self.target_dir_var is None:
            init_target = self.config_manager.get().get("global_settings", {}).get("target_directory", "")
            if not init_target:
                init_target = str(Path.home() / "Desktop" / "PLC_Downloads").replace("\\", "/")
                self.config_manager.update_global_settings({"target_directory": init_target})
            self.target_dir_var = ctk.StringVar(value=init_target)
            
        self.target_dir_entry = ctk.CTkEntry(dest_card, textvariable=self.target_dir_var, height=30, placeholder_text="e.g. C:/PLC_Logs or D:/Production_Data")
        self.target_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=8)
        self.target_dir_entry.bind("<FocusOut>", lambda e: self.config_manager.update_global_settings({"target_directory": self.target_dir_var.get().strip()}))
        
        btn_browse_dest = ctk.CTkButton(dest_card, text="Browse...", width=80, height=30, font=ctk.CTkFont(weight="bold"), command=self.browse_dest_dir)
        btn_browse_dest.pack(side="right", padx=(0, 12), pady=8)
        
        self.scrollable_plc_frame = ctk.CTkScrollableFrame(self, label_text="Connected PLCs")
        self.scrollable_plc_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        
        # Log Console Component
        self.log_console = LogConsole(self, height=150)
        self.log_console.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        logger.register_callback(self.log_console.append_message)
        
        # Bottom controls
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=4, column=0, padx=10, pady=10, sticky="ew")
        
        self.btn_download_all = ctk.CTkButton(btn_frame, text="Download All", font=ctk.CTkFont(weight="bold"), text_color="white", command=self.download_all)
        self.btn_download_all.pack(side="left", padx=5)
        
        self.cooldown_label = ctk.CTkLabel(btn_frame, text="", text_color="gray", font=ctk.CTkFont(weight="bold"))
        self.cooldown_label.pack(side="left", padx=10)
        
        self.refresh_plcs()

    def browse_dest_dir(self):
        folder = filedialog.askdirectory(title="Select Target Save Directory")
        if folder:
            self.target_dir_var.set(folder)
            self.config_manager.update_global_settings({"target_directory": folder})
            logger.info(f"Target save directory updated to: {folder}")

    def refresh_plcs(self):
        for w in self.scrollable_plc_frame.winfo_children():
            w.destroy()
            
        plcs = self.config_manager.get().get("plcs", [])
        for idx, plc in enumerate(plcs):
            frame = ctk.CTkFrame(self.scrollable_plc_frame)
            frame.pack(fill="x", padx=5, pady=5)
            
            lbl = ctk.CTkLabel(frame, text=f"{plc['name']} ({plc['host']})", font=ctk.CTkFont(weight="bold"))
            lbl.pack(side="left", padx=10, pady=10)
            
            small_btn = ctk.CTkButton(frame, text="🔌", width=30, height=30)
            small_btn.pack(side="left", padx=5, pady=10)
            ToolTip(small_btn, "Test Connection")
            
            # Interactive Date filter badge
            df = plc.get("date_filter", {})
            if df.get("mode") == "range" and df.get("start_date") and df.get("end_date"):
                df_badge = f"📅 {df['start_date']} - {df['end_date']}"
            else:
                df_badge = "📅 All Files"

            def edit_filter_for_plc(target_plc=plc, target_idx=idx):
                def on_filter_saved(new_filter):
                    cur_plcs = self.config_manager.get().get("plcs", [])
                    if target_idx < len(cur_plcs):
                        cur_plcs[target_idx]["date_filter"] = new_filter
                        self.config_manager.update_plc(target_idx, cur_plcs[target_idx])
                        self.refresh_plcs()
                QuickDateFilterDialog(
                    self,
                    plc_name=target_plc["name"],
                    current_filter=target_plc.get("date_filter"),
                    on_save=on_filter_saved,
                )

            date_btn = ctk.CTkButton(
                frame,
                text=df_badge,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=("#E1BEE7", "#4A148C"),
                hover_color=("#CE93D8", "#6A1B9A"),
                text_color=("#311B92", "#F3E5F5"),
                height=26,
                corner_radius=6,
                command=lambda p=plc, i=idx: edit_filter_for_plc(p, i)
            )
            date_btn.pack(side="left", padx=8, pady=10)
            ToolTip(date_btn, "คลิกเพื่อแก้ไขช่วงวันที่ดาวน์โหลด (Click to edit date filter)")

            pb = ctk.CTkProgressBar(frame, width=130)
            pb.set(0)
            pb.pack(side="left", padx=15, pady=10)
            
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
        target_dir = self.target_dir_var.get().strip() or g_settings.get("target_directory", "").strip()
        if not target_dir:
            target_dir = str(Path.home() / "Desktop" / "PLC_Downloads").replace("\\", "/")
            self.target_dir_var.set(target_dir)
            self.config_manager.update_global_settings({"target_directory": target_dir})
            logger.info(f"Target save directory defaulted to: {target_dir}")

        machines = plc_data.get('machines')
        if not machines:
            r_dirs_raw = plc_data.get('remote_directory', '')
            remote_dirs = [d.strip() for d in r_dirs_raw.split(',') if d.strip()]
            machines = [{"name": f"MC{i+1}", "remote_dir": d} for i, d in enumerate(remote_dirs)]

        downloader = FTPDownloader(
            host=plc_data['host'],
            port=plc_data.get('port', 21),
            username=plc_data['username'],
            password=plc_data['password'],
            machines=machines,
            local_target_dir=target_dir,
            file_extensions=g_settings.get("file_extensions", [".csv", ".txt"]),
            separate_by_date=g_settings.get("separate_by_date", True),
            plc_name=plc_data['name'],
            date_filter=plc_data.get("date_filter")
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
