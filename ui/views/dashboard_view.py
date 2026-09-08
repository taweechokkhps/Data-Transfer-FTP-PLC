import customtkinter as ctk
import threading
import time
import os
import subprocess
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
        self.plc_download_callbacks = []
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # 1. Header Frame
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=16, pady=(12, 8), sticky="ew")
        
        header_title = ctk.CTkLabel(
            header_frame, 
            text="Download Overview", 
            font=ctk.CTkFont(size=22, weight="bold")
        )
        header_title.pack(side="left")
        
        self.summary_badge = ctk.CTkLabel(
            header_frame, 
            text="", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="gray"
        )
        self.summary_badge.pack(side="right")
        
        # 2. Target Save Directory Bar
        dest_card = ctk.CTkFrame(self, corner_radius=10)
        dest_card.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="ew")
        
        ctk.CTkLabel(
            dest_card, 
            text="📁 Target Directory:", 
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(14, 8), pady=10)
        
        if self.target_dir_var is None:
            init_target = self.config_manager.get().get("global_settings", {}).get("target_directory", "")
            if not init_target:
                init_target = str(Path.home() / "Desktop" / "PLC_Downloads").replace("\\", "/")
                self.config_manager.update_global_settings({"target_directory": init_target})
            self.target_dir_var = ctk.StringVar(value=init_target)
            
        self.target_dir_entry = ctk.CTkEntry(
            dest_card, 
            textvariable=self.target_dir_var, 
            height=32, 
            font=ctk.CTkFont(size=12),
            placeholder_text="e.g. C:/PLC_Logs or D:/Production_Data"
        )
        self.target_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=10)
        self.target_dir_entry.bind(
            "<FocusOut>", 
            lambda e: self.config_manager.update_global_settings({"target_directory": self.target_dir_var.get().strip()})
        )
        
        btn_open = ctk.CTkButton(
            dest_card, 
            text="📂 Open Folder", 
            width=105, 
            height=32, 
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#E0E0E0", "#333333"),
            hover_color=("#D5D5D5", "#444444"),
            text_color=("#212121", "#FFFFFF"),
            command=self.open_target_folder
        )
        btn_open.pack(side="right", padx=(0, 14), pady=10)
        ToolTip(btn_open, "เปิดโฟลเดอร์ปลายทางใน Windows Explorer")

        btn_browse_dest = ctk.CTkButton(
            dest_card, 
            text="🔍 Browse...", 
            width=90, 
            height=32, 
            font=ctk.CTkFont(size=12, weight="bold"), 
            command=self.browse_dest_dir
        )
        btn_browse_dest.pack(side="right", padx=(0, 8), pady=10)
        ToolTip(btn_browse_dest, "เลือกโฟลเดอร์สำหรับบันทึกไฟล์")
        
        # 3. Scrollable Connected PLCs Frame
        self.scrollable_plc_frame = ctk.CTkScrollableFrame(self, label_text="Connected PLCs", corner_radius=10)
        self.scrollable_plc_frame.grid(row=2, column=0, padx=16, pady=5, sticky="nsew")
        
        # 4. Action Controls Toolbar (Above Log Console)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, padx=16, pady=(8, 8), sticky="ew")
        
        self.btn_download_all = ctk.CTkButton(
            btn_frame, 
            text="⬇  Download All PLCs", 
            font=ctk.CTkFont(size=13, weight="bold"), 
            text_color="white", 
            height=36,
            command=self.download_all
        )
        self.btn_download_all.pack(side="left", padx=(0, 12))
        
        self.cooldown_label = ctk.CTkLabel(
            btn_frame, 
            text="", 
            text_color="gray", 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.cooldown_label.pack(side="left", padx=5)
        
        # 5. Log Console Component
        self.log_console = LogConsole(self, height=180)
        self.log_console.grid(row=4, column=0, padx=16, pady=(0, 12), sticky="ew")
        logger.register_callback(self.log_console.append_message)
        
        self.refresh_plcs()

    def open_target_folder(self):
        target_dir = self.target_dir_var.get().strip()
        if not target_dir:
            return
        p = Path(target_dir)
        try:
            if not p.exists():
                p.mkdir(parents=True, exist_ok=True)
            if hasattr(os, "startfile"):
                os.startfile(str(p))
            else:
                subprocess.Popen(["explorer", str(p)])
        except Exception as e:
            logger.error(f"Cannot open folder '{target_dir}': {e}")

    def browse_dest_dir(self):
        folder = filedialog.askdirectory(title="Select Target Save Directory")
        if folder:
            self.target_dir_var.set(folder)
            self.config_manager.update_global_settings({"target_directory": folder})
            logger.info(f"Target save directory updated to: {folder}")

    def refresh_plcs(self):
        self.plc_download_callbacks.clear()
        for w in self.scrollable_plc_frame.winfo_children():
            w.destroy()
            
        plcs = self.config_manager.get().get("plcs", [])
        self.summary_badge.configure(text=f"Total: {len(plcs)} PLC(s) configured")
        
        if not plcs:
            empty_frame = ctk.CTkFrame(self.scrollable_plc_frame, fg_color="transparent")
            empty_frame.pack(fill="x", pady=40)
            ctk.CTkLabel(
                empty_frame, 
                text="ยังไม่มีข้อมูล PLC (No PLCs added yet)\nไปที่เมนู 'PLC Manager' ด้านซ้ายเพื่อเพิ่มเครื่อง", 
                font=ctk.CTkFont(size=14),
                text_color="gray"
            ).pack()
            return

        for idx, plc in enumerate(plcs):
            # Elevated modern card
            card = ctk.CTkFrame(self.scrollable_plc_frame, corner_radius=10, fg_color=("#F5F5F5", "#212121"))
            card.pack(fill="x", padx=4, pady=5)
            
            card.grid_columnconfigure(0, weight=3)  # PLC info
            card.grid_columnconfigure(1, weight=2)  # Date filter
            card.grid_columnconfigure(2, weight=3)  # Status & Progress
            card.grid_columnconfigure(3, weight=0)  # Action buttons
            
            # --- Column 0: PLC Information ---
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.grid(row=0, column=0, padx=(16, 10), pady=12, sticky="w")
            
            title_lbl = ctk.CTkLabel(
                info_frame, 
                text=plc.get("name", f"PLC {idx+1}"), 
                font=ctk.CTkFont(size=15, weight="bold")
            )
            title_lbl.pack(anchor="w")
            
            machines = plc.get("machines", [])
            if not machines:
                r_dirs_raw = plc.get("remote_directory", "")
                m_list = [d.strip() for d in r_dirs_raw.split(",") if d.strip()]
                mc_str = f"{len(m_list)} MC(s)" if m_list else "No MC"
            else:
                mc_names = [m.get("name", f"MC{i+1}") for i, m in enumerate(machines)]
                if len(mc_names) <= 2:
                    mc_str = ", ".join(mc_names)
                else:
                    mc_str = f"{len(machines)} MCs ({mc_names[0]}, {mc_names[1]}...)"
            
            mode_str = plc.get("ftp_mode", "auto").upper()
            sub_text = f"{plc.get('host', '')}:{plc.get('port', 21)}  •  {mc_str}  •  {mode_str}"
            sub_lbl = ctk.CTkLabel(
                info_frame, 
                text=sub_text, 
                font=ctk.CTkFont(size=12), 
                text_color=("#666666", "#9E9E9E")
            )
            sub_lbl.pack(anchor="w", pady=(2, 0))

            # --- Column 1: Date Filter Chip Badge ---
            date_frame = ctk.CTkFrame(card, fg_color="transparent")
            date_frame.grid(row=0, column=1, padx=8, pady=12, sticky="ew")
            
            df = plc.get("date_filter", {})
            if df.get("mode") == "range" and df.get("start_date") and df.get("end_date"):
                df_badge = f"📅 {df['start_date']}  ➔  {df['end_date']}"
                badge_fg = ("#EDE7F6", "#311B92")
                badge_hover = ("#D1C4E9", "#4A148C")
                badge_text = ("#311B92", "#EDE7F6")
            else:
                df_badge = "📅 All Files (ทั้งหมด)"
                badge_fg = ("#E0E0E0", "#2D2D2D")
                badge_hover = ("#D5D5D5", "#3D3D3D")
                badge_text = ("#424242", "#BDBDBD")

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
                date_frame,
                text=df_badge,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=badge_fg,
                hover_color=badge_hover,
                text_color=badge_text,
                height=32,
                corner_radius=8,
                command=lambda p=plc, i=idx: edit_filter_for_plc(p, i)
            )
            date_btn.pack(fill="x")
            ToolTip(date_btn, "คลิกเพื่อแก้ไขช่วงวันที่ดาวน์โหลด (Click to edit date filter)")

            # --- Column 2: Status, Stopwatch & Progress Bar ---
            prog_frame = ctk.CTkFrame(card, fg_color="transparent")
            prog_frame.grid(row=0, column=2, padx=12, pady=12, sticky="ew")
            
            status_top_row = ctk.CTkFrame(prog_frame, fg_color="transparent")
            status_top_row.pack(fill="x", pady=(0, 4))
            
            status_badge = ctk.CTkLabel(
                status_top_row, 
                text="● Ready", 
                font=ctk.CTkFont(size=12, weight="bold"), 
                text_color="#9E9E9E"
            )
            status_badge.pack(side="left")
            
            timer_lbl = ctk.CTkLabel(
                status_top_row, 
                text="", 
                font=ctk.CTkFont(size=12, weight="bold"), 
                text_color="#3B8ED0"
            )
            timer_lbl.pack(side="right")
            
            pb = ctk.CTkProgressBar(prog_frame, height=8, corner_radius=4)
            pb.set(0)
            pb.pack(fill="x")
            
            counter_lbl = ctk.CTkLabel(
                prog_frame, 
                text="พร้อมดาวน์โหลด", 
                font=ctk.CTkFont(size=11), 
                text_color=("#888888", "#757575")
            )
            counter_lbl.pack(anchor="e", pady=(2, 0))

            # --- Column 3: Action Buttons ---
            action_frame = ctk.CTkFrame(card, fg_color="transparent")
            action_frame.grid(row=0, column=3, padx=(10, 16), pady=12, sticky="e")
            
            btn_test = ctk.CTkButton(
                action_frame, 
                text="🔌 Test", 
                width=65, 
                height=32, 
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=("#E0E0E0", "#333333"),
                hover_color=("#D5D5D5", "#444444"),
                text_color=("#212121", "#FFFFFF")
            )
            btn_test.pack(side="left", padx=(0, 8))
            ToolTip(btn_test, "ทดสอบการเชื่อมต่อ FTP กับเครื่องนี้")
            btn_test.configure(command=lambda p=plc, stat=status_badge, c_lbl=counter_lbl: self.test_single_connection(p, stat, c_lbl))
            
            btn_dl = ctk.CTkButton(
                action_frame, 
                text="⬇ Download", 
                width=105, 
                height=32, 
                font=ctk.CTkFont(size=12, weight="bold"), 
                text_color="white"
            )
            btn_dl.pack(side="left")
            
            def make_dl_trigger(p=plc, progress=pb, stat=status_badge, t_lbl=timer_lbl, c_lbl=counter_lbl, b=btn_dl):
                return lambda: self.download_single(p, progress, stat, t_lbl, c_lbl, b)
            
            dl_trigger = make_dl_trigger()
            btn_dl.configure(command=dl_trigger)
            self.plc_download_callbacks.append(dl_trigger)

    def test_single_connection(self, plc_data, status_label, counter_label=None):
        def run():
            status_label.configure(text="● Testing...", text_color="#FFA726")
            if counter_label:
                counter_label.configure(text="Checking FTP connection...")
            ok, msg = test_connection(
                plc_data['host'],
                int(plc_data.get('port', 21)),
                plc_data['username'],
                plc_data['password'],
                ftp_mode=plc_data.get('ftp_mode', 'auto')
            )
            if ok:
                status_label.configure(text="● Conn OK", text_color="#00E676")
                if counter_label:
                    counter_label.configure(text="เชื่อมต่อสำเร็จ (Connection Success)")
                logger.success(f"[{plc_data['name']}] Connection Test: Success")
            else:
                status_label.configure(text="● Conn Fail", text_color="#FF5252")
                if counter_label:
                    counter_label.configure(text="เชื่อมต่อล้มเหลว (Connection Failed)")
                logger.error(f"[{plc_data['name']}] Connection Test: Failed ({msg})")
        threading.Thread(target=run, daemon=True).start()

    def download_single(self, plc_data, progress_bar, status_label, timer_label=None, counter_label=None, action_button=None):
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
            date_filter=plc_data.get("date_filter"),
            ftp_mode=plc_data.get("ftp_mode", "auto")
        )

        start_time = time.time()
        is_running = [True]

        def update_timer_ui():
            if is_running[0] and timer_label:
                elapsed = int(time.time() - start_time)
                mins, secs = divmod(elapsed, 60)
                timer_label.configure(text=f"⏱ {mins:02d}:{secs:02d}", text_color="#3B8ED0")
                self.after(500, update_timer_ui)

        if timer_label:
            timer_label.configure(text="⏱ 00:00", text_color="#3B8ED0")
            self.after(500, update_timer_ui)

        if action_button:
            action_button.configure(state="disabled")

        def update_progress(current, total):
            prog = current / total if total > 0 else 0
            self.after(0, lambda: progress_bar.set(prog))
            pct = int(prog * 100)
            if counter_label:
                self.after(0, lambda: counter_label.configure(text=f"{current} / {total} files ({pct}%)"))

        def log_cb(msg):
            self.after(0, lambda: logger.info(msg))

        def run():
            self.after(0, lambda: status_label.configure(text="● Connecting...", text_color="#FFA726"))
            if counter_label:
                self.after(0, lambda: counter_label.configure(text="Connecting to FTP..."))
            self.after(0, lambda: progress_bar.set(0))
            logger.info(f"Starting download for {plc_data['name']}...")
            try:
                downloader.download_files(progress_callback=update_progress, log_callback=log_cb)
            finally:
                is_running[0] = False
                elapsed = time.time() - start_time
                mins, secs = divmod(int(elapsed), 60)
                time_str = f"{mins:02d}:{secs:02d}" if mins > 0 else f"{elapsed:.2f}s"
                self.after(0, lambda: status_label.configure(text="● Finished", text_color="#00E676"))
                if counter_label:
                    self.after(0, lambda: counter_label.configure(text=f"Completed in {time_str}"))
                if timer_label:
                    self.after(0, lambda: timer_label.configure(text=f"⏱ {time_str}", text_color="#00E676"))
                if action_button:
                    self.after(0, lambda: action_button.configure(state="normal"))

        threading.Thread(target=run, daemon=True).start()

    def download_all(self):
        for trigger in self.plc_download_callbacks:
            trigger()
        if self.request_timer_reset_cb:
            self.request_timer_reset_cb()
