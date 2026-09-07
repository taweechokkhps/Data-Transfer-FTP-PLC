import customtkinter as ctk
from tkinter import filedialog
import threading
import time
import tkinter as tk
from config_manager import ConfigManager
from ftp_client import FTPDownloader

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tw = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 20
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#333333", foreground="white", relief='solid', borderwidth=1,
                       font=("Arial", "10", "normal"))
        label.pack(ipadx=4, ipady=2)

    def leave(self, event=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None

# Set appearance and theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Overwrite theme colors to Purple tone
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
        self.geometry("900x600")
        self.minsize(800, 500)
        
        import os
        import sys
        def resource_path(relative_path):
            try:
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(os.path.dirname(__file__))
            return os.path.join(base_path, relative_path)
            
        icon_path = resource_path("app_icon.png")
        if os.path.exists(icon_path):
            self.icon_img = tk.PhotoImage(file=icon_path)
            self.after(200, lambda: self.iconphoto(False, self.icon_img))
        
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get()
        
        # Configure grid layout (1x2)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # --- Sidebar ---
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
        


        # --- Main Frames ---
        self.dashboard_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.plc_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.settings_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        
        self.active_downloaders = []
        
        # Build Frames
        self.build_dashboard()
        self.build_plc_manager()
        self.build_settings()
        
        # Show default
        self.show_dashboard()
        
        # Setup auto pull timer
        self.next_pull_time = 0
        self.auto_pull_job = None
        self.cooldown_update_job = None
        self.start_auto_pull_timer()
        self.update_cooldown_ui()

        # Version Label at bottom right
        self.version_label = ctk.CTkLabel(self, text="v1.0.0", text_color="gray", font=ctk.CTkFont(size=12))
        self.version_label.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-10)
        self.version_label.lift()

    def start_auto_pull_timer(self):
        if self.auto_pull_job is not None:
            self.after_cancel(self.auto_pull_job)
            self.auto_pull_job = None
            
        interval_mins = self.config["global_settings"].get("auto_pull_interval_minutes", 60)
        if interval_mins > 0:
            interval_ms = interval_mins * 60 * 1000
            self.next_pull_time = time.time() + (interval_ms / 1000.0)
            self.auto_pull_job = self.after(interval_ms, self.trigger_auto_pull)
        else:
            self.next_pull_time = 0
            if hasattr(self, 'cooldown_label'):
                self.cooldown_label.configure(text="Auto Pull: Disabled")
                
    def update_cooldown_ui(self):
        if self.next_pull_time > 0 and hasattr(self, 'cooldown_label'):
            remaining = int(self.next_pull_time - time.time())
            if remaining > 0:
                mins, secs = divmod(remaining, 60)
                self.cooldown_label.configure(text=f"Next Auto Pull in: {mins:02d}:{secs:02d}")
            else:
                self.cooldown_label.configure(text="Pulling...")
        
        self.cooldown_update_job = self.after(1000, self.update_cooldown_ui)
            
    def trigger_auto_pull(self):
        self.log_message(f"--- Triggering Automatic Background Pull ---")
        self.download_all()
        self.start_auto_pull_timer()


    def select_frame_by_name(self, name):
        self.dashboard_frame.grid_forget()
        self.plc_frame.grid_forget()
        self.settings_frame.grid_forget()
        
        if name == "dashboard":
            self.dashboard_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
            self.refresh_dashboard_plcs()
        elif name == "plcs":
            self.plc_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
            self.refresh_plc_list()
        elif name == "settings":
            self.settings_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def show_dashboard(self): self.select_frame_by_name("dashboard")
    def show_plc_manager(self): self.select_frame_by_name("plcs")
    def show_settings(self): self.select_frame_by_name("settings")

    # --- Dashboard View ---
    def build_dashboard(self):
        self.dashboard_frame.grid_columnconfigure(0, weight=1)
        self.dashboard_frame.grid_rowconfigure(1, weight=1)
        
        header = ctk.CTkLabel(self.dashboard_frame, text="Download Overview", font=ctk.CTkFont(size=24, weight="bold"))
        header.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.scrollable_plc_frame = ctk.CTkScrollableFrame(self.dashboard_frame, label_text="Connected PLCs")
        self.scrollable_plc_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        log_label = ctk.CTkLabel(self.dashboard_frame, text="Log Console", font=ctk.CTkFont(weight="bold"))
        log_label.grid(row=2, column=0, padx=10, pady=(10, 0), sticky="w")
        
        self.log_textbox = ctk.CTkTextbox(self.dashboard_frame, height=150)
        self.log_textbox.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.log_textbox.tag_config("error", foreground="red")
        self.log_textbox.tag_config("success", foreground="#00FF00")
        self.log_textbox.tag_config("warning", foreground="orange")
        
        btn_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        btn_frame.grid(row=4, column=0, padx=10, pady=10, sticky="ew")
        
        self.btn_download_all = ctk.CTkButton(btn_frame, text="Download All", font=ctk.CTkFont(weight="bold"), text_color="white", command=self.download_all)
        self.btn_download_all.pack(side="left", padx=5)
        
        self.cooldown_label = ctk.CTkLabel(btn_frame, text="", text_color="gray", font=ctk.CTkFont(weight="bold"))
        self.cooldown_label.pack(side="left", padx=10)

    def log_message(self, message):
        timestamp = time.strftime("%H:%M:%S")
        
        tag = None
        lower_msg = message.lower()
        if "error" in lower_msg or "fail" in lower_msg:
            tag = "error"
        elif "warning" in lower_msg:
            tag = "warning"
        elif "success" in lower_msg or "ok" in lower_msg or "completed" in lower_msg or "finished" in lower_msg:
            tag = "success"
            
        text_to_insert = f"[{timestamp}] {message}\n"
        if tag:
            self.log_textbox.insert("end", text_to_insert, tag)
        else:
            self.log_textbox.insert("end", text_to_insert)
            
        self.log_textbox.see("end")

    def refresh_dashboard_plcs(self):
        for widget in self.scrollable_plc_frame.winfo_children():
            widget.destroy()
            
        for i, plc in enumerate(self.config["plcs"]):
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
            
            small_btn.configure(command=lambda p=plc, stat=status: self.test_ftp_connection(p, stat))
            
            btn = ctk.CTkButton(frame, text="Download", font=ctk.CTkFont(weight="bold"), text_color="white", command=lambda p=plc, progress=pb, stat=status: self.download_single(p, progress, stat))
            btn.pack(side="right", padx=10, pady=10)

    def test_ftp_connection(self, plc_data, status_label):
        def run_test():
            status_label.configure(text="Testing...")
            try:
                from ftplib import FTP
                ftp = FTP()
                ftp.connect(plc_data['host'], int(plc_data.get('port', 21)), timeout=5)
                ftp.login(plc_data['username'], plc_data['password'])
                ftp.quit()
                status_label.configure(text="Conn OK")
                self.log_message(f"[{plc_data['name']}] Connection Test: Success")
            except Exception as e:
                status_label.configure(text="Conn Fail")
                self.log_message(f"[{plc_data['name']}] Connection Test: Failed ({e})")
        
        threading.Thread(target=run_test, daemon=True).start()

    def download_single(self, plc_data, progress_bar, status_label):
        g_settings = self.config["global_settings"]
        target_dir = g_settings.get("target_directory", "")
        if not target_dir:
            self.log_message(f"[{plc_data['name']}] Error: Target directory not set in Global Settings.")
            return

        # Handle multiple directories separated by comma
        r_dirs_raw = plc_data.get('remote_directory', '')
        remote_dirs = [d.strip() for d in r_dirs_raw.split(',') if d.strip()]
        
        downloader = FTPDownloader(
            host=plc_data['host'],
            port=int(plc_data.get('port', 21)),
            username=plc_data['username'],
            password=plc_data['password'],
            remote_dirs=remote_dirs,
            local_target_dir=target_dir,
            file_extensions=g_settings.get("file_extensions", [".csv"]),
            separate_by_date=g_settings.get("separate_by_date", True),
            plc_name=plc_data['name']
        )
        
        def update_progress(current, total):
            progress = current / total
            progress_bar.set(progress)
            status_label.configure(text=f"{current}/{total}")
            
        def log_cb(msg):
            self.after(0, self.log_message, msg)
            
        def run_download():
            status_label.configure(text="Connecting...")
            progress_bar.set(0)
            self.log_message(f"Starting download for {plc_data['name']}...")
            downloader.download_files(progress_callback=update_progress, log_callback=log_cb)
            status_label.configure(text="Finished")
            
        threading.Thread(target=run_download, daemon=True).start()

    def download_all(self):
        # Trigger download on all buttons in the list (for simplicity in UI)
        for widget in self.scrollable_plc_frame.winfo_children():
            btn = [w for w in widget.winfo_children() if isinstance(w, ctk.CTkButton)][0]
            btn.invoke()
        
        # Reset timer so it doesn't auto-pull right after a manual download
        self.start_auto_pull_timer()

    # --- PLC Manager View ---
    def build_plc_manager(self):
        self.plc_frame.grid_columnconfigure(0, weight=1)
        self.plc_frame.grid_rowconfigure(1, weight=1)
        
        header = ctk.CTkLabel(self.plc_frame, text="PLC Manager", font=ctk.CTkFont(size=24, weight="bold"))
        header.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.plc_list_frame = ctk.CTkScrollableFrame(self.plc_frame)
        self.plc_list_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        add_btn = ctk.CTkButton(self.plc_frame, text="Add New PLC", command=self.open_plc_dialog)
        add_btn.grid(row=2, column=0, padx=10, pady=10, sticky="w")

    def refresh_plc_list(self):
        for widget in self.plc_list_frame.winfo_children():
            widget.destroy()
            
        # Header Row
        header_frame = ctk.CTkFrame(self.plc_list_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=5, pady=(5, 0))
        
        header_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        header_frame.grid_columnconfigure(4, weight=0, minsize=140)
        
        headers = ["Name", "Host:Port", "Username", "Remote Directories", "Actions"]
        for col, text in enumerate(headers):
            anchor = "e" if col == 4 else "w"
            ctk.CTkLabel(header_frame, text=text, font=ctk.CTkFont(weight="bold")).grid(row=0, column=col, padx=10, pady=5, sticky=anchor)
                
        # Separator line
        sep = ctk.CTkFrame(self.plc_list_frame, height=2, fg_color=("gray70", "gray30"))
        sep.pack(fill="x", padx=5, pady=(0, 5))
            
        for i, plc in enumerate(self.config["plcs"]):
            frame = ctk.CTkFrame(self.plc_list_frame)
            frame.pack(fill="x", padx=5, pady=2)
            
            frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
            frame.grid_columnconfigure(4, weight=0, minsize=140)
            
            ctk.CTkLabel(frame, text=plc.get('name', '')).grid(row=0, column=0, padx=10, pady=10, sticky="w")
            ctk.CTkLabel(frame, text=f"{plc.get('host', '')}:{plc.get('port', 21)}").grid(row=0, column=1, padx=10, pady=10, sticky="w")
            ctk.CTkLabel(frame, text=plc.get('username', '')).grid(row=0, column=2, padx=10, pady=10, sticky="w")
            
            # Truncate long directory strings for UI
            r_dir = plc.get('remote_directory', '')
            if len(r_dir) > 30: r_dir = r_dir[:27] + "..."
            ctk.CTkLabel(frame, text=r_dir).grid(row=0, column=3, padx=10, pady=10, sticky="w")
            
            btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame.grid(row=0, column=4, padx=10, pady=5, sticky="e")
            
            edit_btn = ctk.CTkButton(btn_frame, text="Edit", width=60, command=lambda idx=i: self.open_plc_dialog(idx))
            edit_btn.pack(side="left", padx=(0, 5))
            
            del_btn = ctk.CTkButton(btn_frame, text="Delete", fg_color="#d32f2f", hover_color="#b71c1c", width=60, command=lambda idx=i: self.delete_plc(idx))
            del_btn.pack(side="left")

    def delete_plc(self, index):
        self.config_manager.delete_plc(index)
        self.refresh_plc_list()

    def open_plc_dialog(self, edit_index=None):
        dialog = ctk.CTkToplevel(self)
        is_edit = edit_index is not None
        dialog.title("Edit PLC" if is_edit else "Add PLC")
        dialog.geometry("400x480")
        dialog.grab_set() # Modal
        
        plc_data = self.config["plcs"][edit_index] if is_edit else {}
        
        ctk.CTkLabel(dialog, text="PLC Name:").pack(pady=(15,0))
        name_entry = ctk.CTkEntry(dialog, width=200)
        name_entry.insert(0, plc_data.get("name", ""))
        name_entry.pack()
        
        ctk.CTkLabel(dialog, text="IP Address (Host):").pack(pady=(5,0))
        host_entry = ctk.CTkEntry(dialog, width=200)
        host_entry.insert(0, plc_data.get("host", ""))
        host_entry.pack()
        
        ctk.CTkLabel(dialog, text="Port:").pack(pady=(5,0))
        port_entry = ctk.CTkEntry(dialog, width=200)
        port_entry.insert(0, str(plc_data.get("port", 21)))
        port_entry.pack()
        
        ctk.CTkLabel(dialog, text="Username:").pack(pady=(5,0))
        user_entry = ctk.CTkEntry(dialog, width=200)
        user_entry.insert(0, plc_data.get("username", "ftp"))
        user_entry.pack()
        
        ctk.CTkLabel(dialog, text="Password:").pack(pady=(5,0))
        pass_entry = ctk.CTkEntry(dialog, width=200, show="*")
        pass_entry.insert(0, plc_data.get("password", ""))
        pass_entry.pack()
        
        ctk.CTkLabel(dialog, text="Remote Dirs (comma separated):").pack(pady=(5,0))
        dir_entry = ctk.CTkEntry(dialog, width=300)
        dir_entry.insert(0, plc_data.get("remote_directory", "/0_CARD/log0/,/0_CARD/log1/,/0_CARD/log2/"))
        dir_entry.pack()
        
        def save():
            new_data = {
                "name": name_entry.get(),
                "host": host_entry.get(),
                "port": int(port_entry.get() if port_entry.get().isdigit() else 21),
                "username": user_entry.get(),
                "password": pass_entry.get(),
                "remote_directory": dir_entry.get()
            }
            if new_data["name"] and new_data["host"]:
                if is_edit:
                    self.config_manager.update_plc(edit_index, new_data)
                else:
                    self.config_manager.add_plc(new_data)
                self.refresh_plc_list()
                dialog.destroy()
                
        ctk.CTkButton(dialog, text="Save", command=save).pack(pady=20)

    # --- Settings View ---
    def build_settings(self):
        header = ctk.CTkLabel(self.settings_frame, text="Settings", font=ctk.CTkFont(size=24, weight="bold"))
        header.grid(row=0, column=0, padx=10, pady=(10, 30), sticky="w")
        
        # Target Directory
        ctk.CTkLabel(self.settings_frame, text="Target Save Directory:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.target_dir_var = ctk.StringVar(value=self.config["global_settings"].get("target_directory", ""))
        self.target_dir_entry = ctk.CTkEntry(self.settings_frame, textvariable=self.target_dir_var, width=300)
        self.target_dir_entry.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        btn_browse = ctk.CTkButton(self.settings_frame, text="Browse", command=self.browse_target_dir)
        btn_browse.grid(row=2, column=1, padx=10, pady=5)
        
        # File Extensions
        ctk.CTkLabel(self.settings_frame, text="File Extensions (comma separated, e.g. .csv,.txt):").grid(row=3, column=0, padx=10, pady=(20,5), sticky="w")
        exts = self.config["global_settings"].get("file_extensions", [])
        self.ext_var = ctk.StringVar(value=",".join(exts))
        self.ext_entry = ctk.CTkEntry(self.settings_frame, textvariable=self.ext_var, width=300)
        self.ext_entry.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        
        # Separate by Date
        self.date_var = ctk.BooleanVar(value=self.config["global_settings"].get("separate_by_date", True))
        self.date_check = ctk.CTkCheckBox(self.settings_frame, text="Automatically create folders by Date (e.g. 2026-08-18)", variable=self.date_var)
        self.date_check.grid(row=5, column=0, padx=10, pady=(20, 5), sticky="w")
        
        # Auto Pull Interval
        ctk.CTkLabel(self.settings_frame, text="Auto Pull Interval (Minutes) [0 = Disable]:").grid(row=6, column=0, padx=10, pady=(20, 5), sticky="w")
        self.interval_var = ctk.StringVar(value=str(self.config["global_settings"].get("auto_pull_interval_minutes", 60)))
        self.interval_entry = ctk.CTkEntry(self.settings_frame, textvariable=self.interval_var, width=100)
        self.interval_entry.grid(row=7, column=0, padx=10, pady=5, sticky="w")
        
        # Save Button
        btn_save_settings = ctk.CTkButton(self.settings_frame, text="Save Settings", command=self.save_settings)
        btn_save_settings.grid(row=8, column=0, padx=10, pady=30, sticky="w")

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
        
        # Update timer
        self.config = self.config_manager.get()
        self.start_auto_pull_timer()
        
        # show saved visual feedback
        saved_lbl = ctk.CTkLabel(self.settings_frame, text="Settings Saved Successfully!", text_color="green")
        saved_lbl.grid(row=8, column=1, padx=10, pady=30, sticky="w")
        self.after(3000, saved_lbl.destroy)
