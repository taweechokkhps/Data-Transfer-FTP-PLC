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
        header = ctk.CTkLabel(self, text="Settings", font=ctk.CTkFont(size=24, weight="bold"))
        header.grid(row=0, column=0, padx=10, pady=(10, 30), sticky="w")
        
        # Target Directory
        ctk.CTkLabel(self, text="Target Save Directory:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.target_dir_var = ctk.StringVar(value=self.config["global_settings"].get("target_directory", ""))
        self.target_dir_entry = ctk.CTkEntry(self, textvariable=self.target_dir_var, width=320)
        self.target_dir_entry.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        btn_browse = ctk.CTkButton(self, text="Browse", width=80, command=self.browse_target_dir)
        btn_browse.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        # File Extensions
        ctk.CTkLabel(self, text="File Extensions (comma separated, e.g. .csv,.txt):").grid(row=3, column=0, padx=10, pady=(20, 5), sticky="w")
        exts = self.config["global_settings"].get("file_extensions", [])
        self.ext_var = ctk.StringVar(value=",".join(exts))
        self.ext_entry = ctk.CTkEntry(self, textvariable=self.ext_var, width=320)
        self.ext_entry.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        
        # Separate by Date
        self.date_var = ctk.BooleanVar(value=self.config["global_settings"].get("separate_by_date", True))
        self.date_check = ctk.CTkCheckBox(self, text="Automatically create folders by Date (e.g. 07-09-2026)", variable=self.date_var)
        self.date_check.grid(row=5, column=0, padx=10, pady=(20, 5), sticky="w")
        
        # Auto Pull Interval
        ctk.CTkLabel(self, text="Auto Pull Interval (Minutes) [0 = Disable]:").grid(row=6, column=0, padx=10, pady=(20, 5), sticky="w")
        self.interval_var = ctk.StringVar(value=str(self.config["global_settings"].get("auto_pull_interval_minutes", 60)))
        self.interval_entry = ctk.CTkEntry(self, textvariable=self.interval_var, width=100)
        self.interval_entry.grid(row=7, column=0, padx=10, pady=5, sticky="w")
        
        # Save Button
        btn_save = ctk.CTkButton(self, text="Save Settings", font=ctk.CTkFont(weight="bold"), command=self.save_settings)
        btn_save.grid(row=8, column=0, padx=10, pady=30, sticky="w")

    def browse_target_dir(self):
        dir_name = filedialog.askdirectory()
        if dir_name:
            self.target_dir_var.set(dir_name)

    def save_settings(self):
        exts = [e.strip() for e in self.ext_var.get().split(",") if e.strip()]
        settings = {
            "target_directory": self.target_dir_var.get(),
            "file_extensions": exts,
            "separate_by_date": self.date_var.get(),
            "auto_pull_interval_minutes": int(self.interval_var.get() if self.interval_var.get().isdigit() else 0)
        }
        self.config_manager.update_global_settings(settings)
        if self.on_settings_changed:
            self.on_settings_changed()
            
        saved_lbl = ctk.CTkLabel(self, text="Settings Saved Successfully!", text_color="#00E676")
        saved_lbl.grid(row=8, column=1, padx=10, pady=30, sticky="w")
        self.after(3000, saved_lbl.destroy)
