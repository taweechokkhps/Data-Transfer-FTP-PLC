import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog
from core.logger import logger
from ui.components.tooltip import ToolTip
from ui.components.log_console import LogConsole
from ui.components.quick_date_filter_dialog import QuickDateFilterDialog
from ui.controllers.dashboard_controller import DashboardController

class DashboardView(ctk.CTkFrame):
    """View rendering the Download Overview dashboard, PLC status cards, and live logs."""

    def __init__(self, master, config_manager, target_dir_var=None, request_timer_reset_cb=None, controller=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.config_manager = config_manager
        self.controller = controller or DashboardController(self.config_manager)
        self.target_dir_var = target_dir_var
        self.request_timer_reset_cb = request_timer_reset_cb

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

    @property
    def plc_download_callbacks(self):
        return self.controller.plc_download_callbacks

    @property
    def plc_download_by_name(self):
        return self.controller.plc_download_by_name

    @property
    def active_downloaders(self):
        return self.controller.active_downloaders

    def safe_after(self, delay, cb):
        """Thread-safe after invocation on main loop."""
        try:
            if self.winfo_exists():
                return self.after(delay, cb)
        except Exception:
            pass
        return None

    def has_active_downloads(self) -> bool:
        return self.controller.has_active_downloads()

    def stop_all_downloads(self):
        self.controller.stop_all_downloads()

    def open_target_folder(self):
        self.controller.open_target_folder(self.target_dir_var.get())

    def browse_dest_dir(self):
        initial = self.target_dir_var.get() if self.target_dir_var else ""
        folder = filedialog.askdirectory(title="Select Target Save Directory", initialdir=initial)
        if folder:
            self.target_dir_var.set(folder)
            self.config_manager.update_global_settings({"target_directory": folder})
            logger.info(f"Target save directory updated to: {folder}")

    def refresh_plcs(self):
        """Rebuild PLC cards from config."""
        if self.has_active_downloads():
            logger.warning("Cannot refresh PLC cards while downloads are actively running.")
            return

        self.controller.clear_triggers()
        for w in self.scrollable_plc_frame.winfo_children():
            w.destroy()

        plcs = self.config_manager.get().get("plcs", [])
        g_settings = self.config_manager.get().get("global_settings", {})
        is_auto_on = g_settings.get("auto_pull_enabled", True)
        auto_lines = g_settings.get("auto_pull_lines", [])
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
            card = ctk.CTkFrame(self.scrollable_plc_frame, corner_radius=10, fg_color=("#F5F5F5", "#212121"))
            card.pack(fill="x", padx=4, pady=5)
            card.grid_columnconfigure(0, weight=1)

            # Row 0: Info + Actions
            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.grid(row=0, column=0, padx=14, pady=(10, 4), sticky="ew")
            top_row.grid_columnconfigure(0, weight=1)

            info_frame = ctk.CTkFrame(top_row, fg_color="transparent")
            info_frame.grid(row=0, column=0, sticky="w")

            title_box = ctk.CTkFrame(info_frame, fg_color="transparent")
            title_box.pack(anchor="w")

            title_lbl = ctk.CTkLabel(
                title_box,
                text=plc.get("name", f"PLC {idx+1}"),
                font=ctk.CTkFont(size=14, weight="bold")
            )
            title_lbl.pack(side="left")

            if is_auto_on and plc.get("name") in auto_lines:
                auto_badge = ctk.CTkLabel(
                    title_box,
                    text="⏱ Auto",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color="#10B981",
                    fg_color=("#E8F5E9", "#133E2B"),
                    corner_radius=4,
                    padx=6,
                    pady=1
                )
                auto_badge.pack(side="left", padx=(8, 0))

            machines = plc.get("machines", [])
            if not machines:
                r_dirs_raw = plc.get("remote_directory", "")
                m_list = [d.strip() for d in r_dirs_raw.split(",") if d.strip()]
                mc_str = f"{len(m_list)} MC(s)" if m_list else "No MC"
            else:
                mc_names = [m.get("name", f"MC{i+1}") for i, m in enumerate(machines)]
                mc_str = ", ".join(mc_names[:3])
                if len(mc_names) > 3:
                    mc_str += f" +{len(mc_names)-3}"

            mode_str = plc.get("ftp_mode", "auto").upper()
            sub_text = f"{plc.get('host', '')}:{plc.get('port', 21)} • {mc_str} • {mode_str}"
            sub_lbl = ctk.CTkLabel(
                info_frame,
                text=sub_text,
                font=ctk.CTkFont(size=11),
                text_color=("#666666", "#9E9E9E")
            )
            sub_lbl.pack(anchor="w")

            action_frame = ctk.CTkFrame(top_row, fg_color="transparent")
            action_frame.grid(row=0, column=1, sticky="e")

            btn_test = ctk.CTkButton(
                action_frame,
                text="🔌 Test",
                width=65,
                height=30,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=("#E0E0E0", "#333333"),
                hover_color=("#D5D5D5", "#444444"),
                text_color=("#212121", "#FFFFFF")
            )
            btn_test.pack(side="left", padx=(0, 6))

            # Date Filter Badge
            df = plc.get("date_filter", {})
            if df.get("mode") == "range" and df.get("start_date") and df.get("end_date"):
                df_badge = f"📅 {df['start_date']} ➔ {df['end_date']}"
                badge_fg = ("#EDE7F6", "#311B92")
                badge_hover = ("#D1C4E9", "#4A148C")
                badge_text = ("#311B92", "#EDE7F6")
            else:
                df_badge = "📅 All Files"
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
                action_frame,
                text=df_badge,
                width=220,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=badge_fg,
                hover_color=badge_hover,
                text_color=badge_text,
                height=30,
                corner_radius=8,
                command=lambda p=plc, i=idx: edit_filter_for_plc(p, i)
            )
            date_btn.pack(side="left", padx=(0, 6))

            btn_dl = ctk.CTkButton(
                action_frame,
                text="⬇ Download",
                width=100,
                height=30,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="white"
            )
            btn_dl.pack(side="left")

            # Row 1: Status + Progress bar + Timer
            mid_row = ctk.CTkFrame(card, fg_color="transparent")
            mid_row.grid(row=1, column=0, padx=14, pady=(0, 10), sticky="ew")
            mid_row.grid_columnconfigure(1, weight=1)

            status_badge = ctk.CTkLabel(
                mid_row,
                text="● Ready",
                width=100,
                anchor="w",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#9E9E9E"
            )
            status_badge.grid(row=0, column=0, sticky="w", padx=(0, 8))

            pb = ctk.CTkProgressBar(mid_row, height=8, corner_radius=4)
            pb.set(0)
            pb.grid(row=0, column=1, sticky="ew", padx=4)

            counter_lbl = ctk.CTkLabel(
                mid_row,
                text="พร้อมดาวน์โหลด",
                width=260,
                anchor="e",
                font=ctk.CTkFont(size=11),
                text_color=("#888888", "#757575")
            )
            counter_lbl.grid(row=0, column=2, sticky="e", padx=(8, 4))

            timer_lbl = ctk.CTkLabel(
                mid_row,
                text="",
                width=70,
                anchor="e",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#3B8ED0"
            )
            timer_lbl.grid(row=0, column=3, sticky="e")

            # Wire up button commands
            btn_test.configure(
                command=lambda p=plc, stat=status_badge, c_lbl=counter_lbl: self.test_single_connection(p, stat, c_lbl)
            )

            def make_dl_trigger(p=plc, progress=pb, stat=status_badge, t_lbl=timer_lbl, c_lbl=counter_lbl, b=btn_dl):
                return lambda on_finish=None: self.download_single(
                    p, progress, stat, t_lbl, c_lbl, b, on_finish_callback=on_finish
                )

            dl_trigger = make_dl_trigger()
            btn_dl.configure(command=dl_trigger)
            self.controller.register_download_trigger(plc.get("name"), dl_trigger)

    def test_single_connection(self, plc_data, status_label, counter_label=None):
        """Delegate connection testing to DashboardController and update widgets."""
        def on_status(status_text, color, msg_text=""):
            def _up():
                try:
                    if status_label and status_label.winfo_exists():
                        status_label.configure(text=status_text, text_color=color)
                    if counter_label and counter_label.winfo_exists() and msg_text:
                        counter_label.configure(text=msg_text)
                except Exception:
                    pass
            self.safe_after(0, _up)

        self.controller.test_single_connection(plc_data, on_status=on_status)

    def download_single(
        self,
        plc_data,
        progress_bar,
        status_label,
        timer_label=None,
        counter_label=None,
        action_button=None,
        on_finish_callback=None
    ):
        """Delegate single line download execution to DashboardController and wire UI feedbacks."""
        target_dir = self.target_dir_var.get().strip()

        def on_queue(host_ip, stop_callback=None):
            try:
                if status_label and status_label.winfo_exists():
                    status_label.configure(text="● In Queue", text_color="#FFA726")
                if counter_label and counter_label.winfo_exists():
                    counter_label.configure(text=f"รอตู้ PLC ({host_ip}) ว่าง...")
                if action_button and action_button.winfo_exists():
                    cmd = (lambda: [action_button.configure(text="Stopping...", state="disabled"), stop_callback()]) if stop_callback else None
                    action_button.configure(
                        text="🛑 Stop",
                        fg_color=("#D32F2F", "#C62828"),
                        hover_color=("#B71C1C", "#B71C1C"),
                        state="normal",
                        command=cmd
                    )
            except Exception:
                pass

        def on_init(stop_callback):
            try:
                if action_button and action_button.winfo_exists():
                    action_button.configure(
                        text="🛑 Stop",
                        fg_color=("#D32F2F", "#C62828"),
                        hover_color=("#B71C1C", "#B71C1C"),
                        state="normal",
                        command=lambda: [action_button.configure(text="Stopping...", state="disabled"), stop_callback()]
                    )
                if status_label and status_label.winfo_exists():
                    status_label.configure(text="● Connecting...", text_color="#FFA726")
                if counter_label and counter_label.winfo_exists():
                    counter_label.configure(text="Connecting to FTP...")
                if progress_bar and progress_bar.winfo_exists():
                    progress_bar.set(0)
                if timer_label and timer_label.winfo_exists():
                    timer_label.configure(text="⏱ 00:00", text_color="#3B8ED0")
            except Exception:
                pass

        def on_progress(prog, pct, c_text):
            try:
                if progress_bar and progress_bar.winfo_exists():
                    progress_bar.set(prog)
                if counter_label and counter_label.winfo_exists():
                    counter_label.configure(text=c_text)
            except Exception:
                pass

        def on_timer(time_str, color):
            try:
                if timer_label and timer_label.winfo_exists():
                    timer_label.configure(text=time_str, text_color=color)
            except Exception:
                pass

        def on_finish_ui(was_cancelled, time_str):
            try:
                if status_label and status_label.winfo_exists():
                    status_label.configure(
                        text="● Stopped" if was_cancelled else "● Finished",
                        text_color="#FFA726" if was_cancelled else "#00E676"
                    )
                if counter_label and counter_label.winfo_exists():
                    counter_label.configure(text="Cancelled" if was_cancelled else f"Completed in {time_str}")
                if timer_label and timer_label.winfo_exists():
                    timer_label.configure(
                        text=f"⏱ {time_str}",
                        text_color="#FFA726" if was_cancelled else "#00E676"
                    )
                if action_button and action_button.winfo_exists():
                    dl_trigger = self.controller.plc_download_by_name.get(plc_data.get("name"))
                    action_button.configure(
                        text="⬇ Download",
                        fg_color=("#3B8ED0", "#1F6AA5"),
                        hover_color=("#36719F", "#144870"),
                        state="normal",
                        command=dl_trigger
                    )
            except Exception:
                pass

        self.controller.download_single(
            plc_data,
            target_dir=target_dir,
            on_init=on_init,
            on_progress=on_progress,
            on_timer=on_timer,
            on_finish_ui=on_finish_ui,
            on_finish_callback=on_finish_callback,
            on_queue=on_queue,
            safe_after=self.safe_after
        )

    def download_all(self, on_complete=None):
        """Trigger or stop all line downloads via DashboardController."""
        def on_btn_state(is_running):
            try:
                if hasattr(self, "btn_download_all") and self.btn_download_all.winfo_exists():
                    if is_running:
                        self.btn_download_all.configure(
                            text="🛑 Stop All",
                            fg_color=("#D32F2F", "#C62828"),
                            hover_color=("#B71C1C", "#B71C1C")
                        )
                    else:
                        self.btn_download_all.configure(
                            text="⬇  Download All PLCs",
                            fg_color=("#1976D2", "#0D47A1"),
                            hover_color=("#1565C0", "#0A3880")
                        )
            except Exception:
                pass

        self.controller.download_all(
            on_complete=on_complete,
            on_button_state=on_btn_state,
            request_timer_reset_cb=self.request_timer_reset_cb,
            safe_after=self.safe_after
        )

    def download_selected_lines(self, target_line_names=None, on_complete=None):
        """Trigger download for specific lines via DashboardController."""
        self.controller.download_selected_lines(
            target_line_names=target_line_names,
            on_complete=on_complete,
            request_timer_reset_cb=self.request_timer_reset_cb,
            safe_after=self.safe_after
        )
