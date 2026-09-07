import customtkinter as ctk
from tkinter import filedialog

class SettingsView(ctk.CTkFrame):
    def __init__(self, master, config_manager, target_dir_var=None, on_settings_changed=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.config_manager = config_manager
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

        # Main Cards Container
        cards_container = ctk.CTkFrame(self, fg_color="transparent")
        cards_container.pack(fill="both", expand=True, padx=20, pady=0)

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
        self.target_dir_entry.bind("<FocusOut>", lambda e: self.config_manager.update_global_settings({"target_directory": self.target_dir_var.get().strip()}))
        
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
        # CARD 3: Auto Pull Interval
        # ==========================================
        card_sched = ctk.CTkFrame(cards_container, corner_radius=10)
        card_sched.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(card_sched, text="⏱️ Auto Pull Interval (รอบเวลาดึงข้อมูลอัตโนมัติ)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=18, pady=(14, 2))
        ctk.CTkLabel(card_sched, text="Time in minutes between automatic background downloads. Set to 0 to disable.",
                     font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=18, pady=(0, 10))
        
        interval_row = ctk.CTkFrame(card_sched, fg_color="transparent")
        interval_row.pack(fill="x", padx=18, pady=(0, 16))
        
        curr_int = self.config["global_settings"].get("auto_pull_interval_minutes", 60)
        self.interval_var = ctk.StringVar(value=str(curr_int))
        self.interval_entry = ctk.CTkEntry(interval_row, textvariable=self.interval_var, width=90, height=34, font=ctk.CTkFont(size=13, weight="bold"))
        self.interval_entry.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(interval_row, text="Minutes (นาที)  —  [ 0 = ปิดการดึงอัตโนมัติ ]", font=ctk.CTkFont(size=12), text_color="gray").pack(side="left")

        # ==========================================
        # Bottom Save Bar
        # ==========================================
        save_bar = ctk.CTkFrame(self, fg_color="transparent")
        save_bar.pack(fill="x", padx=20, pady=(0, 15))
        
        btn_save = ctk.CTkButton(save_bar, text="💾 Save Settings", font=ctk.CTkFont(size=13, weight="bold"), height=38, width=150, command=self.save_settings)
        btn_save.pack(side="left")
        
        self.saved_feedback = ctk.CTkLabel(save_bar, text="", font=ctk.CTkFont(size=13, weight="bold"))
        self.saved_feedback.pack(side="left", padx=15)

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
        val = self.custom_ext_entry.get().strip().lower()
        if val:
            if not val.startswith("."):
                val = "." + val
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
        dir_name = filedialog.askdirectory(title="Select Target Save Directory")
        if dir_name:
            self.target_dir_var.set(dir_name)
            self.config_manager.update_global_settings({"target_directory": dir_name})

    def save_settings(self):
        exts = self.get_selected_extensions()
        val = self.interval_var.get().strip()
        interval = int(val) if val.isdigit() else 0
            
        settings = {
            "target_directory": self.target_dir_var.get().strip(),
            "file_extensions": exts,
            "separate_by_date": False,
            "auto_pull_interval_minutes": interval
        }
        self.config_manager.update_global_settings(settings)
        if self.on_settings_changed:
            self.on_settings_changed()
            
        self.saved_feedback.configure(text="✓ Settings Saved Successfully!", text_color="#00E676")
        self.after(3000, lambda: self.saved_feedback.configure(text=""))
