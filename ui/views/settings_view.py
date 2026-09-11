import customtkinter as ctk
from ui.controllers.settings_controller import SettingsController

class SettingsView(ctk.CTkFrame):
    def __init__(self, master, config_manager, target_dir_var=None, on_settings_changed=None, controller=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.config_manager = config_manager
        self.controller = controller or SettingsController(self.config_manager)
        self.target_dir_var = target_dir_var
        self.on_settings_changed = on_settings_changed
        self.config = self.config_manager.get()
        self.build_view()

    def build_view(self):
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 20))
        
        ctk.CTkLabel(header_frame, text="Settings", font=ctk.CTkFont(size=26, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="Configure local storage, target file types, and automatic download schedules",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w", pady=(2, 0))

        # Main Cards Container (Scrollable)
        cards_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        cards_container.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # ==========================================
        # CARD 1: Target Save Directory
        # ==========================================
        card_dir = ctk.CTkFrame(cards_container, corner_radius=10)
        card_dir.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(card_dir, text="📁 Target Save Directory (โฟลเดอร์ปลายทาง)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=18, pady=(14, 2))
        ctk.CTkLabel(card_dir, text="Local folder on your computer where downloaded machine files will be organized.",
                     font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=18, pady=(0, 8))
        
        dir_input_row = ctk.CTkFrame(card_dir, fg_color="transparent")
        dir_input_row.pack(fill="x", padx=18, pady=(0, 16))
        
        if self.target_dir_var is None:
            self.target_dir_var = ctk.StringVar(value=self.config["global_settings"].get("target_directory", ""))
        self.target_dir_entry = ctk.CTkEntry(dir_input_row, textvariable=self.target_dir_var, height=34, placeholder_text="e.g. C:/PLC_Logs or D:/Production_Data")
        self.target_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.target_dir_entry.bind("<FocusOut>", lambda e: self.save_settings(show_feedback=False))
        
        btn_browse = ctk.CTkButton(dir_input_row, text="Browse...", width=95, height=34, font=ctk.CTkFont(weight="bold"), command=self.browse_target_dir)
        btn_browse.pack(side="right")

        # ==========================================
        # CARD 2: File Extensions
        # ==========================================
        card_ext = ctk.CTkFrame(cards_container, corner_radius=10)
        card_ext.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(card_ext, text="📄 File Extensions to Download (นามสกุลไฟล์)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=18, pady=(14, 2))
        ctk.CTkLabel(card_ext, text="Select file formats to retrieve from machines. Add custom extensions if needed.",
                     font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=18, pady=(0, 10))
        
        ext_ctrl_row = ctk.CTkFrame(card_ext, fg_color="transparent")
        ext_ctrl_row.pack(fill="x", padx=18, pady=(0, 10))
        
        saved_exts = [e.lower() for e in self.config["global_settings"].get("file_extensions", [".txt", ".csv"])]
        if not saved_exts:
            saved_exts = [".txt", ".csv"]
            
        self.std_ext_vars = {
            ".txt": ctk.BooleanVar(value=".txt" in saved_exts),
            ".csv": ctk.BooleanVar(value=".csv" in saved_exts),
        }
        for ext, var in self.std_ext_vars.items():
            cb = ctk.CTkCheckBox(ext_ctrl_row, text=ext, variable=var, font=ctk.CTkFont(size=13, weight="bold"))
            cb.pack(side="left", padx=(0, 24))
            
        # Custom extension input
        sep_label = ctk.CTkLabel(ext_ctrl_row, text="|   Add other:", font=ctk.CTkFont(size=12), text_color="gray")
        sep_label.pack(side="left", padx=(0, 10))
        
        self.custom_ext_entry = ctk.CTkEntry(ext_ctrl_row, width=80, height=30, placeholder_text=".log")
        self.custom_ext_entry.pack(side="left", padx=(0, 8))
        
        btn_add = ctk.CTkButton(ext_ctrl_row, text="+ Add", width=60, height=30, command=self.add_custom_ext)
        btn_add.pack(side="left")
        
        # Chips container for extra extensions
        self.custom_chips_frame = ctk.CTkFrame(card_ext, fg_color="transparent")
        self.custom_chips_frame.pack(fill="x", padx=18, pady=(0, 14))
        self.custom_ext_list = [e for e in saved_exts if e not in self.std_ext_vars]
        self.render_custom_chips()

        # ==========================================
        # CARD 3: Auto Pull Automation & Line Selection
        # ==========================================
        card_sched = ctk.CTkFrame(cards_container, corner_radius=10)
        card_sched.pack(fill="x", pady=(0, 20))
        
        # Header with Master Switch
        sched_top = ctk.CTkFrame(card_sched, fg_color="transparent")
        sched_top.pack(fill="x", padx=18, pady=(14, 2))
        sched_top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            sched_top, 
            text="⏱️ Auto Pull & Download Automation (ระบบดึงข้อมูลอัตโนมัติ)", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        curr_enabled = self.config["global_settings"].get("auto_pull_enabled", True)
        self.auto_pull_enabled_var = ctk.BooleanVar(value=curr_enabled)
        
        self.auto_pull_switch = ctk.CTkSwitch(
            sched_top,
            text="เปิดใช้งาน (Active)" if curr_enabled else "ปิดใช้งาน (Disabled)",
            variable=self.auto_pull_enabled_var,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.toggle_auto_pull_switch
        )
        self.auto_pull_switch.grid(row=0, column=1, sticky="e")

        ctk.CTkLabel(
            card_sched, 
            text="ตั้งเวลารอบดาวน์โหลดอัตโนมัติในพื้นหลัง และเลือกเฉพาะ Line การผลิตที่ต้องการให้ทำงาน",
            font=ctk.CTkFont(size=11), 
            text_color="gray"
        ).pack(anchor="w", padx=18, pady=(0, 10))

        # Body Container (Holds interval and line selector)
        self.sched_body = ctk.CTkFrame(card_sched, fg_color="transparent")
        if curr_enabled:
            self.sched_body.pack(fill="x", padx=18, pady=(0, 16))

        # 1. Interval row
        interval_row = ctk.CTkFrame(self.sched_body, fg_color="transparent")
        interval_row.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(interval_row, text="รอบเวลาดึงข้อมูล (Interval):", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 10))

        curr_int = self.config["global_settings"].get("auto_pull_interval_minutes", 60)
        self.interval_var = ctk.StringVar(value=str(curr_int))
        self.interval_entry = ctk.CTkEntry(interval_row, textvariable=self.interval_var, width=80, height=32, font=ctk.CTkFont(size=13, weight="bold"))
        self.interval_entry.pack(side="left", padx=(0, 8))
        self.interval_entry.bind("<FocusOut>", lambda e: self.save_settings(show_feedback=False))
        self.interval_entry.bind("<Return>", lambda e: self.save_settings(show_feedback=False))

        ctk.CTkLabel(interval_row, text="นาที (Minutes)  [ค่าเริ่มต้น 60 นาที]", font=ctk.CTkFont(size=12), text_color="gray").pack(side="left")

        # 2. Line Selector Frame
        lines_header = ctk.CTkFrame(self.sched_body, fg_color="transparent")
        lines_header.pack(fill="x", pady=(6, 4))
        lines_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            lines_header, 
            text="🏭 เลือก Line การผลิตที่เข้าร่วม Auto Pull (Select Lines):", 
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        btn_box = ctk.CTkFrame(lines_header, fg_color="transparent")
        btn_box.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(
            btn_box, text="เลือกทั้งหมด", width=75, height=24, font=ctk.CTkFont(size=11),
            fg_color=("gray80", "gray25"), hover_color=("gray70", "gray35"), text_color=("black", "white"),
            command=self.select_all_auto_lines
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            btn_box, text="ยกเลิกทั้งหมด", width=80, height=24, font=ctk.CTkFont(size=11),
            fg_color=("gray80", "gray25"), hover_color=("gray70", "gray35"), text_color=("black", "white"),
            command=self.deselect_all_auto_lines
        ).pack(side="left")

        # Checkboxes container for lines
        self.lines_checkboxes_frame = ctk.CTkFrame(self.sched_body, fg_color=("gray90", "gray18"), corner_radius=8)
        self.lines_checkboxes_frame.pack(fill="x", pady=(4, 6))

        self.line_vars = {}
        self.render_lines_checkboxes()

        # ==========================================
        # Bottom Save Bar
        # ==========================================
        save_bar = ctk.CTkFrame(self, fg_color="transparent")
        save_bar.pack(fill="x", padx=20, pady=(0, 15))
        
        btn_save = ctk.CTkButton(save_bar, text="💾 Save Settings", font=ctk.CTkFont(size=13, weight="bold"), height=38, width=150, command=lambda: self.save_settings(show_feedback=True))
        btn_save.pack(side="left")
        
        self.saved_feedback = ctk.CTkLabel(save_bar, text="", font=ctk.CTkFont(size=13, weight="bold"))
        self.saved_feedback.pack(side="left", padx=15)

    def toggle_auto_pull_switch(self):
        is_on = self.auto_pull_enabled_var.get()
        if is_on:
            self.auto_pull_switch.configure(text="เปิดใช้งาน (Active)")
            self.sched_body.pack(fill="x", padx=18, pady=(0, 16))
        else:
            self.auto_pull_switch.configure(text="ปิดใช้งาน (Disabled)")
            self.sched_body.pack_forget()
        self.save_settings(show_feedback=False)

    def on_line_toggled(self):
        self.save_settings(show_feedback=False)

    def select_all_auto_lines(self):
        for var in self.line_vars.values():
            var.set(True)
        self.save_settings(show_feedback=False)

    def deselect_all_auto_lines(self):
        for var in self.line_vars.values():
            var.set(False)
        self.save_settings(show_feedback=False)

    def sync_from_config(self):
        g = self.config_manager.get()["global_settings"]
        is_on = g.get("auto_pull_enabled", True)
        self.auto_pull_enabled_var.set(is_on)
        self.auto_pull_switch.configure(text="เปิดใช้งาน (Active)" if is_on else "ปิดใช้งาน (Disabled)")
        self.interval_var.set(str(g.get("auto_pull_interval_minutes", 60)))
        if is_on:
            self.sched_body.pack(fill="x", padx=18, pady=(0, 16))
        else:
            self.sched_body.pack_forget()
        self.render_lines_checkboxes()

    def render_lines_checkboxes(self):
        for w in self.lines_checkboxes_frame.winfo_children():
            w.destroy()

        plcs = self.config_manager.get().get("plcs", [])
        if not plcs:
            ctk.CTkLabel(
                self.lines_checkboxes_frame,
                text="ยังไม่มีรายการ Line ในระบบ (สามารถเพิ่มได้ที่แท็บ PLC Manager)",
                font=ctk.CTkFont(size=11),
                text_color="gray"
            ).pack(padx=14, pady=10)
            return

        saved_selected = self.config_manager.get()["global_settings"].get("auto_pull_lines", None)
        self.line_vars = {}
        for p in plcs:
            name = p.get("name", "Unnamed Line")
            is_checked = True if saved_selected is None else (name in saved_selected)
            var = ctk.BooleanVar(value=is_checked)
            self.line_vars[name] = var

            machines = p.get("machines", [])
            mc_cnt = len(machines) if machines else 1
            mc_str = f"{mc_cnt} MC{'s' if mc_cnt > 1 else ''}"

            row_item = ctk.CTkFrame(self.lines_checkboxes_frame, fg_color=("white", "#262626"), corner_radius=6)
            row_item.pack(fill="x", padx=8, pady=4)

            cb = ctk.CTkCheckBox(
                row_item,
                text=name,
                variable=var,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=self.on_line_toggled
            )
            cb.pack(side="left", padx=(10, 6), pady=8)

            ctk.CTkLabel(
                row_item,
                text=f"🌐 {p.get('host', '')}:{p.get('port', 21)}  •  {mc_str}",
                font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray70")
            ).pack(side="left", padx=4)

    def render_custom_chips(self):
        for w in self.custom_chips_frame.winfo_children():
            w.destroy()
        if not self.custom_ext_list:
            return
        for ext in self.custom_ext_list:
            chip = ctk.CTkFrame(self.custom_chips_frame, fg_color=("#D1C4E9", "#3A2A4D"), corner_radius=12)
            chip.pack(side="left", padx=(0, 8), pady=2)
            ctk.CTkLabel(chip, text=ext, font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(10, 4), pady=3)
            del_b = ctk.CTkButton(chip, text="✕", width=18, height=18, fg_color="transparent", hover_color="#d32f2f",
                                  text_color="gray", command=lambda e=ext: self.remove_custom_ext(e))
            del_b.pack(side="left", padx=(0, 6), pady=3)

    def add_custom_ext(self):
        raw = self.custom_ext_entry.get()
        val = self.controller.format_extension(raw)
        if val:
            if val not in self.std_ext_vars and val not in self.custom_ext_list:
                self.custom_ext_list.append(val)
                self.render_custom_chips()
            self.custom_ext_entry.delete(0, "end")

    def remove_custom_ext(self, ext):
        if ext in self.custom_ext_list:
            self.custom_ext_list.remove(ext)
            self.render_custom_chips()

    def get_selected_extensions(self):
        exts = [ext for ext, var in self.std_ext_vars.items() if var.get()]
        exts.extend(self.custom_ext_list)
        return exts if exts else [".txt", ".csv"]

    def browse_target_dir(self):
        initial = self.target_dir_var.get() if self.target_dir_var else ""
        chosen = self.controller.browse_target_dir(initial_dir=initial)
        if chosen:
            self.target_dir_var.set(chosen)
            self.save_settings(show_feedback=False)

    def save_settings(self, show_feedback=True):
        exts = self.get_selected_extensions()
        val = self.interval_var.get().strip()
        interval = int(val) if val.isdigit() else 0
        is_enabled = self.auto_pull_enabled_var.get()
        selected_lines = [name for name, var in self.line_vars.items() if var.get()]

        settings = {
            "target_directory": self.target_dir_var.get().strip(),
            "file_extensions": exts,
            "separate_by_date": False,
            "auto_pull_enabled": is_enabled,
            "auto_pull_interval_minutes": interval,
            "auto_pull_lines": selected_lines
        }
        ok, msg = self.controller.save_settings(settings)
        if ok and self.on_settings_changed:
            self.on_settings_changed()
            
        if show_feedback:
            if ok:
                self.saved_feedback.configure(text="✓ บันทึกการตั้งค่าสำเร็จ! (Settings Saved)", text_color="#00E676")
            else:
                self.saved_feedback.configure(text=f"✗ {msg}", text_color="#FF5252")
            self.after(3000, lambda: self.saved_feedback.configure(text=""))
