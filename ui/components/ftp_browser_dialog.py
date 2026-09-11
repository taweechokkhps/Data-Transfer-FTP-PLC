import customtkinter as ctk
import threading
import tkinter as tk
from core.ftp_service import list_remote_items
from core.path_utils import sanitize_remote_path
from ui.components.modal_utils import setup_modal_dialog

def _format_size(bytes_val: int) -> str:
    """Format bytes to human readable B / KB / MB string."""
    if bytes_val <= 0:
        return "0 B"
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    else:
        return f"{bytes_val / (1024 * 1024):.2f} MB"

class FTPBrowserDialog(ctk.CTkToplevel):
    def __init__(self, parent, host, port, username, password, initial_dir="/", on_select_callback=None, ftp_mode="auto"):
        super().__init__(parent)
        self.parent_dialog = parent
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ftp_mode = ftp_mode
        self.current_dir = sanitize_remote_path(initial_dir) or "/"
        self.on_select_callback = on_select_callback
        self.is_loading = False
        self.btn_select = None

        self.title(f"📁 Remote PLC Browser — {self.host}:{self.port}")
        setup_modal_dialog(self, parent, target_width=720, target_height=600, resizable=True, min_width=620, min_height=480)

        # 1. Top Navigation & Address Bar
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=16, pady=(14, 4))

        self.btn_up = ctk.CTkButton(nav_frame, text="⬆ Up", width=55, height=32, font=ctk.CTkFont(weight="bold"), command=self.go_up)
        self.btn_up.pack(side="left", padx=(0, 4))

        self.btn_root = ctk.CTkButton(nav_frame, text="🏠 Root", width=60, height=32, font=ctk.CTkFont(weight="bold"), command=self.go_root)
        self.btn_root.pack(side="left", padx=(0, 6))

        self.path_entry = ctk.CTkEntry(nav_frame, height=32, font=ctk.CTkFont(size=12))
        self.path_entry.insert(0, self.current_dir)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=4)
        self.path_entry.bind("<Return>", lambda e: self.go_manual())

        self.btn_go = ctk.CTkButton(nav_frame, text="Go", width=45, height=32, font=ctk.CTkFont(weight="bold"), command=self.go_manual)
        self.btn_go.pack(side="left", padx=(4, 4))

        self.btn_refresh = ctk.CTkButton(nav_frame, text="🔄", width=36, height=32, font=ctk.CTkFont(size=13), command=lambda: self.load_directory(self.current_dir))
        self.btn_refresh.pack(side="left")

        # 2. Connection & Status info bar
        status_bar = ctk.CTkFrame(self, fg_color="transparent")
        status_bar.pack(fill="x", padx=16, pady=(2, 6))
        status_bar.grid_columnconfigure(0, weight=1)

        self.conn_info_lbl = ctk.CTkLabel(
            status_bar,
            text=f"🌐 Server: {self.host}:{self.port}  •  Mode: {self.ftp_mode.upper()}",
            font=ctk.CTkFont(size=11),
            text_color=("#666666", "#9E9E9E")
        )
        self.conn_info_lbl.grid(row=0, column=0, sticky="w")

        self.status_label = ctk.CTkLabel(
            status_bar,
            text="Connecting...",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#FFA726"
        )
        self.status_label.grid(row=0, column=1, sticky="e")

        # 3. Main Remote Item Explorer Frame (Scrollable)
        self.content_frame = ctk.CTkScrollableFrame(self, label_text="PLC Files & Folders")
        self.content_frame.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        # 4. Bottom Action Area (Two-row layout: Row 1 = Selected Path box, Row 2 = Buttons)
        bot_container = ctk.CTkFrame(self, fg_color="transparent")
        bot_container.pack(fill="x", padx=16, pady=(0, 14))

        # Row 1: Selected path preview box
        path_box = ctk.CTkFrame(bot_container, fg_color=("gray92", "gray17"), corner_radius=6)
        path_box.pack(fill="x", pady=(0, 10))

        lbl_cur = ctk.CTkLabel(
            path_box,
            text="Selected Path:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#555555", "#AAAAAA")
        )
        lbl_cur.pack(side="left", padx=(10, 4), pady=6)

        self.sel_preview_lbl = ctk.CTkLabel(
            path_box,
            text=self.current_dir,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#1976D2", "#64B5F6"),
            anchor="w",
            wraplength=560
        )
        self.sel_preview_lbl.pack(side="left", padx=(0, 10), pady=6, fill="x", expand=True)

        # Row 2: Action buttons row
        btn_bar = ctk.CTkFrame(bot_container, fg_color="transparent")
        btn_bar.pack(fill="x")

        self.btn_copy = ctk.CTkButton(
            btn_bar,
            text="📋 Copy Path",
            width=100,
            height=34,
            fg_color=("#E0E0E0", "#333333"),
            hover_color=("#D5D5D5", "#444444"),
            text_color=("#212121", "#FFFFFF"),
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.copy_path_to_clipboard
        )
        self.btn_copy.pack(side="left")

        # Right buttons (Pack right side first to guarantee visibility)
        if self.on_select_callback:
            self.btn_select = ctk.CTkButton(
                btn_bar,
                text="✓ Select This Directory",
                width=175,
                height=34,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=("#2E7D32", "#1B5E20"),
                hover_color=("#1B5E20", "#0D3311"),
                text_color="white",
                command=self.select_current
            )
            self.btn_select.pack(side="right", padx=(8, 0))

        btn_cancel = ctk.CTkButton(
            btn_bar,
            text="Cancel",
            width=80,
            height=34,
            fg_color="gray",
            hover_color="#555",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.destroy
        )
        btn_cancel.pack(side="right", padx=(4, 0))

        # Load initial target directory
        self.load_directory(self.current_dir)

    def _reset_scroll_to_top(self):
        """Reset the scrollable content frame's vertical scroll position to top (0.0)."""
        try:
            if hasattr(self, "content_frame") and hasattr(self.content_frame, "_parent_canvas"):
                self.content_frame._parent_canvas.yview_moveto(0.0)
        except Exception:
            pass

    def _set_controls_loading_state(self, is_loading: bool):
        """Manage enable/disable state of navigation and selection controls during loading."""
        self.is_loading = is_loading
        try:
            nav_state = "disabled" if is_loading else "normal"
            for attr in ["btn_up", "btn_root", "btn_go", "btn_refresh"]:
                if hasattr(self, attr):
                    btn = getattr(self, attr)
                    if btn and hasattr(btn, "winfo_exists") and btn.winfo_exists():
                        btn.configure(state=nav_state)
            if hasattr(self, "path_entry") and self.path_entry and self.path_entry.winfo_exists():
                self.path_entry.configure(state=nav_state)
            if hasattr(self, "btn_select") and self.btn_select and self.btn_select.winfo_exists():
                if is_loading:
                    self.btn_select.configure(state="disabled", text="⏳ Loading...")
                else:
                    self.btn_select.configure(state="normal", text="✓ Select This Directory")
        except Exception:
            pass

    def load_directory(self, target_dir):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        self._set_controls_loading_state(True)
        self._reset_scroll_to_top()

        try:
            self.status_label.configure(text=f"Loading...", text_color="#FFA726")
            for w in self.content_frame.winfo_children():
                w.destroy()

            loading_lbl = ctk.CTkLabel(
                self.content_frame,
                text="⏳ Fetching directory listing from PLC...",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            loading_lbl.pack(pady=30)
        except Exception:
            return

        def worker():
            ok, res = list_remote_items(
                self.host, self.port, self.username, self.password, target_dir, ftp_mode=self.ftp_mode
            )
            try:
                if not self.winfo_exists():
                    return
            except Exception:
                return

            if ok:
                try:
                    self.after(0, lambda: self._on_load_success(res))
                except Exception:
                    pass
            else:
                try:
                    self.after(0, lambda: self._on_load_fail(str(res), target_dir))
                except Exception:
                    pass

        threading.Thread(target=worker, daemon=True).start()

    def _on_load_success(self, data):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        self._set_controls_loading_state(False)
        self._reset_scroll_to_top()

        try:
            self.current_dir = data.get("current_dir", "/")
            folders = data.get("folders", [])
            files = data.get("files", [])

            if hasattr(self, "path_entry") and self.path_entry.winfo_exists():
                self.path_entry.delete(0, "end")
                self.path_entry.insert(0, self.current_dir)
            if hasattr(self, "sel_preview_lbl") and self.sel_preview_lbl.winfo_exists():
                self.sel_preview_lbl.configure(text=self.current_dir)

            total_cnt = len(folders) + len(files)
            if hasattr(self, "status_label") and self.status_label.winfo_exists():
                self.status_label.configure(
                    text=f"Found {len(folders)} folder(s), {len(files)} file(s)",
                    text_color="#00E676"
                )

            if hasattr(self, "content_frame") and self.content_frame.winfo_exists():
                for w in self.content_frame.winfo_children():
                    w.destroy()

                if not folders and not files:
                    ctk.CTkLabel(
                        self.content_frame,
                        text="📂 (Directory is empty / โฟลเดอร์ว่าง)",
                        font=ctk.CTkFont(size=13),
                        text_color="gray"
                    ).pack(pady=35)
                    return

                # --- A. FOLDERS SECTION ---
                if folders:
                    f_hdr = ctk.CTkLabel(
                        self.content_frame,
                        text=f"📁 Folders ({len(folders)}):",
                        font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=("#666666", "#9E9E9E")
                    )
                    f_hdr.pack(anchor="w", padx=6, pady=(4, 2))

                    for name in folders:
                        row = ctk.CTkFrame(self.content_frame, fg_color="transparent")
                        row.pack(fill="x", padx=4, pady=2)

                        btn = ctk.CTkButton(
                            row,
                            text=f"📁 {name}/",
                            anchor="w",
                            height=32,
                            fg_color=("gray95", "gray20"),
                            hover_color=("#E0E0E0", "#383838"),
                            text_color=("#1565C0", "#64B5F6"),
                            font=ctk.CTkFont(size=12, weight="bold"),
                            command=lambda n=name: self.navigate_into(n)
                        )
                        btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

                        if self.on_select_callback:
                            sub_path = sanitize_remote_path(f"{self.current_dir.rstrip('/')}/{name}")
                            btn_select_this = ctk.CTkButton(
                                row,
                                text="Choose ➔",
                                width=80,
                                height=30,
                                font=ctk.CTkFont(size=11, weight="bold"),
                                fg_color=("#E8F5E9", "#1B5E20"),
                                hover_color=("#C8E6C9", "#2E7D32"),
                                text_color=("#2E7D32", "#A5D6A7"),
                                command=lambda p=sub_path: self.select_path(p)
                            )
                            btn_select_this.pack(side="right")

                # --- B. FILES SECTION ---
                if files:
                    file_hdr = ctk.CTkLabel(
                        self.content_frame,
                        text=f"📄 Files ({len(files)}):",
                        font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=("#666666", "#9E9E9E")
                    )
                    file_hdr.pack(anchor="w", padx=6, pady=(10 if folders else 4, 2))

                    for item in files:
                        f_name = item.get("name", "")
                        f_size = item.get("size", 0)
                        size_str = _format_size(f_size)

                        row = ctk.CTkFrame(self.content_frame, fg_color=("white", "gray17"), corner_radius=4, height=28)
                        row.pack(fill="x", padx=4, pady=1)

                        ctk.CTkLabel(
                            row,
                            text=f"📄 {f_name}",
                            font=ctk.CTkFont(size=11),
                            text_color=("#212121", "#E0E0E0")
                        ).pack(side="left", padx=(8, 4), pady=3)

                        ctk.CTkLabel(
                            row,
                            text=size_str,
                            font=ctk.CTkFont(size=10),
                            text_color="gray"
                        ).pack(side="right", padx=(4, 10), pady=3)
        except Exception:
            pass

        self._reset_scroll_to_top()
        try:
            self.after(20, self._reset_scroll_to_top)
        except Exception:
            pass

    def _on_load_fail(self, err_msg, failed_dir=None):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        self._set_controls_loading_state(False)
        # Keep select button disabled on failure because directory could not be read
        if hasattr(self, "btn_select") and self.btn_select and self.btn_select.winfo_exists():
            self.btn_select.configure(state="disabled", text="✓ Select This Directory")

        try:
            if hasattr(self, "status_label") and self.status_label.winfo_exists():
                self.status_label.configure(text="Connection Error", text_color="#FF5252")
            if hasattr(self, "content_frame") and self.content_frame.winfo_exists():
                for w in self.content_frame.winfo_children():
                    w.destroy()

                err_box = ctk.CTkFrame(self.content_frame, fg_color=("#FFEBEE", "#3E2723"), corner_radius=8)
                err_box.pack(fill="x", padx=10, pady=20)

                ctk.CTkLabel(
                    err_box,
                    text=f"⚠️ Failed to browse PLC directory:\n{err_msg}",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color="#D32F2F",
                    wraplength=480
                ).pack(padx=14, pady=12)

                btn_row = ctk.CTkFrame(self.content_frame, fg_color="transparent")
                btn_row.pack(pady=6)

                retry_target = failed_dir or self.current_dir
                ctk.CTkButton(
                    btn_row,
                    text="🔄 Retry",
                    width=90,
                    command=lambda: self.load_directory(retry_target)
                ).pack(side="left", padx=4)

                if failed_dir and failed_dir != self.current_dir:
                    ctk.CTkButton(
                        btn_row,
                        text="⬅ Stay on Current",
                        width=130,
                        command=lambda: self.load_directory(self.current_dir)
                    ).pack(side="left", padx=4)

                ctk.CTkButton(
                    btn_row,
                    text="🏠 Root",
                    width=80,
                    command=self.go_root
                ).pack(side="left", padx=4)
        except Exception:
            pass

    def navigate_into(self, folder_name):
        if self.is_loading:
            return
        new_path = sanitize_remote_path(f"{self.current_dir.rstrip('/')}/{folder_name}")
        self.load_directory(new_path)

    def go_up(self):
        if self.is_loading or self.current_dir in ["/", ""]:
            return
        parts = self.current_dir.rstrip("/").split("/")[:-1]
        parent = sanitize_remote_path("/".join(parts)) if parts else "/"
        self.load_directory(parent)

    def go_root(self):
        if self.is_loading:
            return
        self.load_directory("/")

    def go_manual(self):
        if self.is_loading:
            return
        entered = sanitize_remote_path(self.path_entry.get().strip())
        self.load_directory(entered)

    def copy_path_to_clipboard(self):
        try:
            self.clipboard_clear()
            self.clipboard_append(self.current_dir)
            if hasattr(self, "btn_copy") and self.btn_copy.winfo_exists():
                self.btn_copy.configure(text="✓ Copied!", fg_color="#2E7D32")
            def reset_btn():
                try:
                    if self.winfo_exists() and hasattr(self, "btn_copy") and self.btn_copy.winfo_exists():
                        self.btn_copy.configure(text="📋 Copy Path", fg_color=("#E0E0E0", "#333333"))
                except Exception:
                    pass
            self.after(2000, reset_btn)
        except Exception:
            pass

    def select_path(self, path):
        if self.is_loading:
            return
        if self.on_select_callback:
            self.on_select_callback(path)
        self.destroy()

    def select_current(self):
        if self.is_loading:
            return
        self.select_path(self.current_dir)

    def destroy(self):
        try:
            if self.parent_dialog and hasattr(self.parent_dialog, "grab_set") and self.parent_dialog.winfo_exists():
                self.parent_dialog.grab_set()
        except Exception:
            pass
        super().destroy()
