import customtkinter as ctk
import threading
from core.ftp_service import list_remote_directories
from core.path_utils import sanitize_remote_path

class FTPBrowserDialog(ctk.CTkToplevel):
    def __init__(self, parent, host, port, username, password, initial_dir="/", on_select_callback=None, ftp_mode="auto"):
        super().__init__(parent)
        self.title("📁 Browse Remote FTP Directories")
        self.geometry("520x480")
        self.minsize(450, 350)
        self.grab_set()

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ftp_mode = ftp_mode
        self.current_dir = sanitize_remote_path(initial_dir)
        self.on_select_callback = on_select_callback

        # Top Address Bar
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=15, pady=(15, 5))

        btn_up = ctk.CTkButton(nav_frame, text="⬆ Up", width=60, command=self.go_up)
        btn_up.pack(side="left", padx=(0, 5))

        self.path_entry = ctk.CTkEntry(nav_frame)
        self.path_entry.insert(0, self.current_dir)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=5)

        btn_go = ctk.CTkButton(nav_frame, text="Go", width=50, command=self.go_manual)
        btn_go.pack(side="right", padx=(5, 0))

        # Status indicator
        self.status_label = ctk.CTkLabel(self, text="Connecting...", text_color="gray")
        self.status_label.pack(anchor="w", padx=20, pady=2)

        # Folder List Frame
        self.folder_frame = ctk.CTkScrollableFrame(self, label_text="Folders")
        self.folder_frame.pack(fill="both", expand=True, padx=15, pady=5)

        # Bottom Action Buttons
        bot_frame = ctk.CTkFrame(self, fg_color="transparent")
        bot_frame.pack(fill="x", padx=15, pady=(5, 15))

        btn_cancel = ctk.CTkButton(bot_frame, text="Cancel", width=80, fg_color="gray", hover_color="#555", command=self.destroy)
        btn_cancel.pack(side="right", padx=5)

        btn_select = ctk.CTkButton(bot_frame, text="Select This Directory", width=160, command=self.select_current)
        btn_select.pack(side="right", padx=5)

        self.load_directory(self.current_dir)

    def load_directory(self, target_dir):
        self.status_label.configure(text=f"Loading {target_dir}...", text_color="gray")
        for w in self.folder_frame.winfo_children():
            w.destroy()

        def worker():
            ok, res = list_remote_directories(self.host, self.port, self.username, self.password, target_dir, ftp_mode=self.ftp_mode)
            if ok:
                self.after(0, lambda: self._on_load_success(target_dir, res))
            else:
                self.after(0, lambda: self._on_load_fail(str(res)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_load_success(self, target_dir, folders):
        self.current_dir = target_dir
        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, self.current_dir)
        self.status_label.configure(text=f"Found {len(folders)} folder(s)", text_color="#00E676")

        if not folders:
            ctk.CTkLabel(self.folder_frame, text="(No subdirectories found)", text_color="gray").pack(pady=20)
            return

        for name in folders:
            btn = ctk.CTkButton(
                self.folder_frame,
                text=f"📁 {name}",
                anchor="w",
                fg_color="transparent",
                hover_color=("#3E2723", "#333333"),
                text_color=("black", "white"),
                command=lambda n=name: self.navigate_into(n)
            )
            btn.pack(fill="x", padx=5, pady=2)

    def _on_load_fail(self, err_msg):
        self.status_label.configure(text=f"Error: {err_msg}", text_color="#FF5252")
        ctk.CTkLabel(self.folder_frame, text=f"Failed to access directory:\n{err_msg}", text_color="#FF5252").pack(pady=20)

    def navigate_into(self, folder_name):
        new_path = sanitize_remote_path(f"{self.current_dir.rstrip('/')}/{folder_name}")
        self.load_directory(new_path)

    def go_up(self):
        if self.current_dir in ["/", ""]:
            return
        parts = self.current_dir.rstrip("/").split("/")[:-1]
        parent = sanitize_remote_path("/".join(parts)) if parts else "/"
        self.load_directory(parent)

    def go_manual(self):
        entered = sanitize_remote_path(self.path_entry.get())
        self.load_directory(entered)

    def select_current(self):
        if self.on_select_callback:
            self.on_select_callback(self.current_dir)
        self.destroy()
