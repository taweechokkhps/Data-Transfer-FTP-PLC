import customtkinter as ctk
from tkinter import filedialog

class SettingsView(ctk.CTkFrame):
    def __init__(self, master, config_manager, on_settings_changed=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.config_manager = config_manager
        self.on_settings_changed = on_settings_changed
        self.config = self.config_manager.get()
        self.build_view()

    def build_view(self):
        # Header
        header = ctk.CTkLabel(self, text="Settings", font=ctk.CTkFont(size=24, weight="bold"))
        header.grid(row=0, column=0, padx=10, pady=(10, 25), sticky="w")
        
        # 1. Target Directory
        ctk.CTkLabel(self, text="Target Save Directory:").grid(row=1, column=0, padx=10, pady=(5, 2), sticky="w")
        
        target_row = ctk.CTkFrame(self, fg_color="transparent")
        target_row.grid(row=2, column=0, padx=10, pady=(0, 15), sticky="w")
        
        self.target_dir_var = ctk.StringVar(value=self.config["global_settings"].get("target_directory", ""))
        self.target_dir_entry = ctk.CTkEntry(target_row, textvariable=self.target_dir_var, width=340)
        self.target_dir_entry.pack(side="left", padx=(0, 10))
        
        btn_browse = ctk.CTkButton(target_row, text="Browse", width=80, command=self.browse_target_dir)
        btn_browse.pack(side="left")
        
        # 2. File Extensions (Default: .txt, .csv)
        ctk.CTkLabel(self, text="File Extensions to Download:").grid(row=3, column=0, padx=10, pady=(5, 2), sticky="w")
        
        ext_frame = ctk.CTkFrame(self, fg_color="transparent")
        ext_frame.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="w")
        
        saved_exts = [e.lower() for e in self.config["global_settings"].get("file_extensions", [".txt", ".csv"])]
        if not saved_exts:
            saved_exts = [".txt", ".csv"]
            
        self.std_ext_vars = {
            ".txt": ctk.BooleanVar(value=".txt" in saved_exts),
            ".csv": ctk.BooleanVar(value=".csv" in saved_exts),
        }
        for ext, var in self.std_ext_vars.items():
            cb = ctk.CTkCheckBox(ext_frame, text=ext, variable=var)
            cb.pack(side="left", padx=(0, 20))
            
        self.custom_ext_entry = ctk.CTkEntry(ext_frame, width=70, placeholder_text=".log")
        self.custom_ext_entry.pack(side="left", padx=(5, 5))
        btn_add = ctk.CTkButton(ext_frame, text="+ Add", width=55, command=self.add_custom_ext)
        btn_add.pack(side="left")
        
        self.custom_chips_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.custom_chips_frame.grid(row=5, column=0, padx=10, pady=(0, 10), sticky="w")
        self.custom_ext_list = [e for e in saved_exts if e not in self.std_ext_vars]
        self.render_custom_chips()
        
        # 3. Auto Pull Interval (Minutes) [0 = Disable]
        ctk.CTkLabel(self, text="Auto Pull Interval (Minutes) [0 = Disable]:").grid(row=6, column=0, padx=10, pady=(10, 2), sticky="w")
        self.interval_var = ctk.StringVar(value=str(self.config["global_settings"].get("auto_pull_interval_minutes", 60)))
        self.interval_entry = ctk.CTkEntry(self, textvariable=self.interval_var, width=120)
        self.interval_entry.grid(row=7, column=0, padx=10, pady=(0, 25), sticky="w")
        
        # 4. Save Button
        save_frame = ctk.CTkFrame(self, fg_color="transparent")
        save_frame.grid(row=8, column=0, padx=10, pady=10, sticky="w")
        
        btn_save_settings = ctk.CTkButton(save_frame, text="Save Settings", font=ctk.CTkFont(weight="bold"), command=self.save_settings)
        btn_save_settings.pack(side="left")
        
        self.saved_feedback = ctk.CTkLabel(save_frame, text="", font=ctk.CTkFont(size=12, weight="bold"))
        self.saved_feedback.pack(side="left", padx=15)

    def render_custom_chips(self):
        for w in self.custom_chips_frame.winfo_children():
            w.destroy()
        for ext in self.custom_ext_list:
            chip = ctk.CTkFrame(self.custom_chips_frame, fg_color=("#E0E0E0", "#333333"), corner_radius=10)
            chip.pack(side="left", padx=(0, 6), pady=2)
            ctk.CTkLabel(chip, text=ext, font=ctk.CTkFont(size=11)).pack(side="left", padx=(6, 2), pady=1)
            del_b = ctk.CTkButton(chip, text="✕", width=16, height=16, fg_color="transparent", hover_color="#d32f2f",
                                  text_color="gray", command=lambda e=ext: self.remove_custom_ext(e))
            del_b.pack(side="left", padx=(0, 4), pady=1)

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
        dir_name = filedialog.askdirectory()
        if dir_name:
            self.target_dir_var.set(dir_name)

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
