import customtkinter as ctk
import threading
from core.ftp_service import test_connection
from ui.components.ftp_browser_dialog import FTPBrowserDialog

class PLCManagerView(ctk.CTkFrame):
    def __init__(self, master, config_manager, on_plc_list_updated=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.config_manager = config_manager
        self.on_plc_list_updated = on_plc_list_updated
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        header = ctk.CTkLabel(self, text="PLC Manager", font=ctk.CTkFont(size=24, weight="bold"))
        header.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.plc_list_frame = ctk.CTkScrollableFrame(self)
        self.plc_list_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        add_btn = ctk.CTkButton(self, text="Add New PLC", font=ctk.CTkFont(weight="bold"), command=self.open_plc_dialog)
        add_btn.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        
        self.refresh_list()

    def refresh_list(self):
        for w in self.plc_list_frame.winfo_children():
            w.destroy()
            
        header_frame = ctk.CTkFrame(self.plc_list_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=5, pady=(5, 0))
        header_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        header_frame.grid_columnconfigure(4, weight=0, minsize=140)
        
        headers = ["Name", "Host:Port", "Username", "Remote Directories", "Actions"]
        for col, text in enumerate(headers):
            anchor = "e" if col == 4 else "w"
            ctk.CTkLabel(header_frame, text=text, font=ctk.CTkFont(weight="bold")).grid(row=0, column=col, padx=10, pady=5, sticky=anchor)
            
        sep = ctk.CTkFrame(self.plc_list_frame, height=2, fg_color=("gray70", "gray30"))
        sep.pack(fill="x", padx=5, pady=(0, 5))
        
        plcs = self.config_manager.get().get("plcs", [])
        for i, plc in enumerate(plcs):
            frame = ctk.CTkFrame(self.plc_list_frame)
            frame.pack(fill="x", padx=5, pady=2)
            frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
            frame.grid_columnconfigure(4, weight=0, minsize=140)
            
            ctk.CTkLabel(frame, text=plc.get('name', '')).grid(row=0, column=0, padx=10, pady=10, sticky="w")
            ctk.CTkLabel(frame, text=f"{plc.get('host', '')}:{plc.get('port', 21)}").grid(row=0, column=1, padx=10, pady=10, sticky="w")
            ctk.CTkLabel(frame, text=plc.get('username', '')).grid(row=0, column=2, padx=10, pady=10, sticky="w")
            
            r_dir = plc.get('remote_directory', '')
            display_rdir = r_dir if len(r_dir) <= 30 else r_dir[:27] + "..."
            ctk.CTkLabel(frame, text=display_rdir).grid(row=0, column=3, padx=10, pady=10, sticky="w")
            
            btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame.grid(row=0, column=4, padx=10, pady=5, sticky="e")
            
            edit_btn = ctk.CTkButton(btn_frame, text="Edit", width=60, command=lambda idx=i: self.open_plc_dialog(idx))
            edit_btn.pack(side="left", padx=(0, 5))
            
            del_btn = ctk.CTkButton(btn_frame, text="Delete", fg_color="#d32f2f", hover_color="#b71c1c", width=60, command=lambda idx=i: self.delete_plc(idx))
            del_btn.pack(side="left")

    def delete_plc(self, index):
        self.config_manager.delete_plc(index)
        self.refresh_list()
        if self.on_plc_list_updated:
            self.on_plc_list_updated()

    def open_plc_dialog(self, edit_index=None):
        dialog = ctk.CTkToplevel(self)
        is_edit = edit_index is not None
        dialog.title("Edit PLC" if is_edit else "Add PLC")
        dialog.geometry("450x540")
        dialog.grab_set()
        
        plcs = self.config_manager.get().get("plcs", [])
        plc_data = plcs[edit_index] if is_edit and edit_index < len(plcs) else {}
        
        ctk.CTkLabel(dialog, text="PLC Name:").pack(pady=(12, 0))
        name_entry = ctk.CTkEntry(dialog, width=280)
        name_entry.insert(0, plc_data.get("name", ""))
        name_entry.pack()
        
        ctk.CTkLabel(dialog, text="IP Address (Host):").pack(pady=(5, 0))
        host_entry = ctk.CTkEntry(dialog, width=280)
        host_entry.insert(0, plc_data.get("host", ""))
        host_entry.pack()
        
        ctk.CTkLabel(dialog, text="Port:").pack(pady=(5, 0))
        port_entry = ctk.CTkEntry(dialog, width=280)
        port_entry.insert(0, str(plc_data.get("port", 21)))
        port_entry.pack()
        
        ctk.CTkLabel(dialog, text="Username:").pack(pady=(5, 0))
        user_entry = ctk.CTkEntry(dialog, width=280)
        user_entry.insert(0, plc_data.get("username", "ftp"))
        user_entry.pack()
        
        ctk.CTkLabel(dialog, text="Password:").pack(pady=(5, 0))
        pass_entry = ctk.CTkEntry(dialog, width=280, show="*")
        pass_entry.insert(0, plc_data.get("password", ""))
        pass_entry.pack()
        
        ctk.CTkLabel(dialog, text="Remote Dirs (comma separated):").pack(pady=(5, 0))
        dir_entry = ctk.CTkEntry(dialog, width=280)
        dir_entry.insert(0, plc_data.get("remote_directory", "/0_CARD/log0/,/0_CARD/log1/,/0_CARD/log2/"))
        dir_entry.pack()

        tools_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        tools_frame.pack(pady=8)
        
        test_status_lbl = ctk.CTkLabel(dialog, text="", font=ctk.CTkFont(size=11))
        test_status_lbl.pack()

        def do_test():
            h = host_entry.get().strip()
            p = int(port_entry.get() if port_entry.get().isdigit() else 21)
            u = user_entry.get().strip()
            pw = pass_entry.get().strip()
            test_status_lbl.configure(text="Testing connection...", text_color="gray")
            
            def run():
                ok, msg = test_connection(h, p, u, pw)
                if ok:
                    dialog.after(0, lambda: test_status_lbl.configure(text="✓ Connection Successful!", text_color="#00E676"))
                else:
                    dialog.after(0, lambda: test_status_lbl.configure(text=f"✗ {msg}", text_color="#FF5252"))
            threading.Thread(target=run, daemon=True).start()

        def open_ftp_browser():
            h = host_entry.get().strip()
            p = int(port_entry.get() if port_entry.get().isdigit() else 21)
            u = user_entry.get().strip()
            pw = pass_entry.get().strip()
            if not h:
                test_status_lbl.configure(text="Please enter Host/IP first.", text_color="#FF5252")
                return
            
            def on_dir_selected(chosen_dir):
                current_text = dir_entry.get().strip()
                if not current_text or current_text.startswith("/0_CARD/"):
                    dir_entry.delete(0, "end")
                    dir_entry.insert(0, chosen_dir)
                else:
                    dir_entry.delete(0, "end")
                    dir_entry.insert(0, chosen_dir)
            
            init_d = dir_entry.get().split(",")[0].strip() if dir_entry.get().strip() else "/"
            FTPBrowserDialog(dialog, h, p, u, pw, initial_dir=init_d, on_select_callback=on_dir_selected)

        btn_test = ctk.CTkButton(tools_frame, text="🔌 Test Connection", width=130, command=do_test)
        btn_test.pack(side="left", padx=5)

        btn_browse_ftp = ctk.CTkButton(tools_frame, text="📁 Browse FTP...", width=130, command=open_ftp_browser)
        btn_browse_ftp.pack(side="left", padx=5)

        def save():
            new_data = {
                "name": name_entry.get().strip(),
                "host": host_entry.get().strip(),
                "port": int(port_entry.get() if port_entry.get().isdigit() else 21),
                "username": user_entry.get().strip(),
                "password": pass_entry.get().strip(),
                "remote_directory": dir_entry.get().strip()
            }
            if new_data["name"] and new_data["host"]:
                if is_edit:
                    self.config_manager.update_plc(edit_index, new_data)
                else:
                    self.config_manager.add_plc(new_data)
                self.refresh_list()
                if self.on_plc_list_updated:
                    self.on_plc_list_updated()
                dialog.destroy()

        ctk.CTkButton(dialog, text="Save PLC", font=ctk.CTkFont(weight="bold"), command=save).pack(pady=(15, 20))
