import customtkinter as ctk
from tkinter import filedialog
import datetime
from pathlib import Path

class SettingsView(ctk.CTkFrame):
    def __init__(self, master, config_manager, on_settings_changed=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.config_manager = config_manager
        self.on_settings_changed = on_settings_changed
        self.config = self.config_manager.get()
        self.build_view()

    def build_view(self):
        # Header
        header = ctk.CTkLabel(self, text="Global Settings", font=ctk.CTkFont(size=24, weight="bold"))
        header.pack(anchor="w", padx=15, pady=(10, 15))

        # Main scrollable settings container
        content = ctk.CTkScrollableFrame(self)
        content.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # --- Section 1: Target Save Directory ---
        sec1 = ctk.CTkFrame(content, fg_color="transparent")
        sec1.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(sec1, text="1. Target Save Directory (โฟลเดอร์ปลายทางในเครื่อง):", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))
        
        dir_row = ctk.CTkFrame(sec1, fg_color="transparent")
        dir_row.pack(fill="x")
        
        self.target_dir_var = ctk.StringVar(value=self.config["global_settings"].get("target_directory", ""))
        self.target_dir_var.trace_add("write", lambda *args: self.update_preview())
        
        self.target_dir_entry = ctk.CTkEntry(dir_row, textvariable=self.target_dir_var, width=380, placeholder_text="e.g. D:/PLC_Logs")
        self.target_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        btn_browse = ctk.CTkButton(dir_row, text="📁 Browse", width=90, command=self.browse_target_dir)
        btn_browse.pack(side="left")

        # --- Section 2: File Types (No commas!) ---
        sec2 = ctk.CTkFrame(content, fg_color="transparent")
        sec2.pack(fill="x", padx=10, pady=15)
        
        ctk.CTkLabel(sec2, text="2. File Types to Download (เลือกชนิดไฟล์ที่ต้องการดึง):", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))
        
        saved_exts = [e.lower() for e in self.config["global_settings"].get("file_extensions", [".csv", ".txt"])]
        
        # Standard checkboxes row
        cb_row = ctk.CTkFrame(sec2, fg_color="transparent")
        cb_row.pack(fill="x", pady=5)
        
        self.std_ext_vars = {
            ".csv": ctk.BooleanVar(value=".csv" in saved_exts),
            ".txt": ctk.BooleanVar(value=".txt" in saved_exts),
            ".log": ctk.BooleanVar(value=".log" in saved_exts),
            ".dat": ctk.BooleanVar(value=".dat" in saved_exts),
        }
        
        for ext, var in self.std_ext_vars.items():
            cb = ctk.CTkCheckBox(cb_row, text=ext, variable=var, command=self.update_preview)
            cb.pack(side="left", padx=(0, 20))

        # Custom extensions row
        custom_row = ctk.CTkFrame(sec2, fg_color="transparent")
        custom_row.pack(fill="x", pady=(8, 5))
        
        ctk.CTkLabel(custom_row, text="Add Custom Extension:").pack(side="left", padx=(0, 10))
        self.custom_ext_entry = ctk.CTkEntry(custom_row, width=100, placeholder_text=".tsv")
        self.custom_ext_entry.pack(side="left", padx=(0, 10))
        
        btn_add_ext = ctk.CTkButton(custom_row, text="+ Add", width=65, command=self.add_custom_ext)
        btn_add_ext.pack(side="left")
        
        # Chips container for other extensions
        self.custom_chips_frame = ctk.CTkFrame(sec2, fg_color="transparent")
        self.custom_chips_frame.pack(fill="x", pady=5)
        
        self.custom_ext_list = [e for e in saved_exts if e not in self.std_ext_vars]
        self.render_custom_chips()

        # --- Section 3: Folder Structure & Live Preview ---
        sec3 = ctk.CTkFrame(content, fg_color="transparent")
        sec3.pack(fill="x", padx=10, pady=15)
        
        ctk.CTkLabel(sec3, text="3. Folder Organization (การจัดโครงสร้างโฟลเดอร์):", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))
        
        self.date_var = ctk.BooleanVar(value=self.config["global_settings"].get("separate_by_date", True))
        self.date_check = ctk.CTkCheckBox(sec3, text="Automatically create date folders (สร้างโฟลเดอร์แยกตามวันที่ DD-MM-YYYY)",
                                          variable=self.date_var, command=self.update_preview)
        self.date_check.pack(anchor="w", pady=5)
        
        # Live Preview Box
        preview_box = ctk.CTkFrame(sec3, fg_color=("#F0F0F0", "#1E1E1E"), corner_radius=6)
        preview_box.pack(fill="x", pady=(8, 5))
        
        ctk.CTkLabel(preview_box, text="🔍 Folder Structure Preview:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#7B1FA2").pack(anchor="w", padx=10, pady=(6, 2))
        self.preview_lbl = ctk.CTkLabel(preview_box, text="", font=ctk.CTkFont(size=12), text_color="gray", justify="left")
        self.preview_lbl.pack(anchor="w", padx=10, pady=(0, 8))
        self.update_preview()

        # --- Section 4: Auto Pull Schedule ---
        sec4 = ctk.CTkFrame(content, fg_color="transparent")
        sec4.pack(fill="x", padx=10, pady=15)
        
        ctk.CTkLabel(sec4, text="4. Auto Pull Schedule (รอบเวลาดึงข้อมูลอัตโนมัติ):", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))
        
        curr_interval = self.config["global_settings"].get("auto_pull_interval_minutes", 60)
        self.sched_mode_var = ctk.StringVar(value="auto" if curr_interval > 0 else "manual")
        
        mode_frame = ctk.CTkFrame(sec4, fg_color="transparent")
        mode_frame.pack(fill="x", pady=5)
        
        r_manual = ctk.CTkRadioButton(mode_frame, text="Manual (ดึงด้วยตนเองเท่านั้น ไม่ตั้งเวลา)", variable=self.sched_mode_var, value="manual", command=self.toggle_sched_input)
        r_manual.pack(anchor="w", pady=3)
        
        r_auto_row = ctk.CTkFrame(mode_frame, fg_color="transparent")
        r_auto_row.pack(fill="x", pady=3)
        
        r_auto = ctk.CTkRadioButton(r_auto_row, text="Automatic (ดึงอัตโนมัติทุกๆ):", variable=self.sched_mode_var, value="auto", command=self.toggle_sched_input)
        r_auto.pack(side="left", padx=(0, 10))
        
        self.interval_var = ctk.StringVar(value=str(curr_interval if curr_interval > 0 else 60))
        self.interval_entry = ctk.CTkEntry(r_auto_row, textvariable=self.interval_var, width=70)
        self.interval_entry.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(r_auto_row, text="Minutes (นาที)").pack(side="left")
        self.toggle_sched_input()

        # --- Bottom Save Bar ---
        bot_bar = ctk.CTkFrame(self, fg_color="transparent")
        bot_bar.pack(fill="x", padx=15, pady=(5, 15))
        
        btn_save = ctk.CTkButton(bot_bar, text="💾 Save Settings", font=ctk.CTkFont(weight="bold"), height=36, command=self.save_settings)
        btn_save.pack(side="left", padx=5)
        
        self.saved_feedback = ctk.CTkLabel(bot_bar, text="", font=ctk.CTkFont(size=12, weight="bold"))
        self.saved_feedback.pack(side="left", padx=15)

    def toggle_sched_input(self):
        if self.sched_mode_var.get() == "auto":
            self.interval_entry.configure(state="normal")
        else:
            self.interval_entry.configure(state="disabled")

    def render_custom_chips(self):
        for w in self.custom_chips_frame.winfo_children():
            w.destroy()
            
        for ext in self.custom_ext_list:
            chip = ctk.CTkFrame(self.custom_chips_frame, fg_color=("#E0E0E0", "#333333"), corner_radius=12)
            chip.pack(side="left", padx=(0, 8), pady=2)
            
            ctk.CTkLabel(chip, text=ext, font=ctk.CTkFont(size=12)).pack(side="left", padx=(8, 4), pady=2)
            del_b = ctk.CTkButton(chip, text="✕", width=18, height=18, fg_color="transparent", hover_color="#d32f2f",
                                  text_color="gray", command=lambda e=ext: self.remove_custom_ext(e))
            del_b.pack(side="left", padx=(0, 6), pady=2)

    def add_custom_ext(self):
        val = self.custom_ext_entry.get().strip().lower()
        if val:
            if not val.startswith("."):
                val = "." + val
            if val not in self.std_ext_vars and val not in self.custom_ext_list:
                self.custom_ext_list.append(val)
                self.render_custom_chips()
                self.update_preview()
            self.custom_ext_entry.delete(0, "end")

    def remove_custom_ext(self, ext):
        if ext in self.custom_ext_list:
            self.custom_ext_list.remove(ext)
            self.render_custom_chips()
            self.update_preview()

    def get_selected_extensions(self):
        exts = [ext for ext, var in self.std_ext_vars.items() if var.get()]
        exts.extend(self.custom_ext_list)
        return exts if exts else [".csv"]

    def update_preview(self):
        base = self.target_dir_var.get().strip() or "C:/TargetFolder"
        today = datetime.datetime.now().strftime("%d-%m-%Y")
        exts = self.get_selected_extensions()
        sample_ext = exts[0] if exts else ".csv"
        
        if self.date_var.get():
            preview_path = f"{base}/LINE 1/MC1 Leak Test/{today}/DATA001{sample_ext}"
        else:
            preview_path = f"{base}/LINE 1/MC1 Leak Test/DATA001{sample_ext}"
            
        self.preview_lbl.configure(text=preview_path)

    def browse_target_dir(self):
        dir_name = filedialog.askdirectory()
        if dir_name:
            self.target_dir_var.set(dir_name)

    def save_settings(self):
        exts = self.get_selected_extensions()
        interval = 0
        if self.sched_mode_var.get() == "auto":
            val = self.interval_var.get().strip()
            interval = int(val) if val.isdigit() and int(val) > 0 else 60
            
        settings = {
            "target_directory": self.target_dir_var.get().strip(),
            "file_extensions": exts,
            "separate_by_date": self.date_var.get(),
            "auto_pull_interval_minutes": interval
        }
        self.config_manager.update_global_settings(settings)
        if self.on_settings_changed:
            self.on_settings_changed()
            
        self.saved_feedback.configure(text="✓ Settings Saved Successfully!", text_color="#00E676")
        self.after(3000, lambda: self.saved_feedback.configure(text=""))
