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
        
        header = ctk.CTkLabel(self, text="Production Line & PLC Manager", font=ctk.CTkFont(size=24, weight="bold"))
        header.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.plc_list_frame = ctk.CTkScrollableFrame(self)
        self.plc_list_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        add_btn = ctk.CTkButton(self, text="➕ Add New Line / PLC", font=ctk.CTkFont(weight="bold"), command=self.open_plc_dialog)
        add_btn.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        
        self.refresh_list()

    def refresh_list(self):
        for w in self.plc_list_frame.winfo_children():
            w.destroy()
            
        header_frame = ctk.CTkFrame(self.plc_list_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=5, pady=(5, 0))
        header_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        header_frame.grid_columnconfigure(4, weight=0, minsize=140)
        
        headers = ["Line Name", "Host:Port", "Username", "Configured Machines", "Actions"]
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
            
            ctk.CTkLabel(frame, text=plc.get('name', ''), font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
            ctk.CTkLabel(frame, text=f"{plc.get('host', '')}:{plc.get('port', 21)}").grid(row=0, column=1, padx=10, pady=10, sticky="w")
            ctk.CTkLabel(frame, text=plc.get('username', '')).grid(row=0, column=2, padx=10, pady=10, sticky="w")
            
            machines = plc.get('machines', [])
            if machines:
                m_names = [m.get('name', 'MC') for m in machines]
                m_summary = f"{len(machines)} MC: " + ", ".join(m_names)
            else:
                m_summary = "1 MC: (Default)"
                
            if len(m_summary) > 35:
                m_summary = m_summary[:32] + "..."
            ctk.CTkLabel(frame, text=m_summary).grid(row=0, column=3, padx=10, pady=10, sticky="w")
            
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
        dialog.title("Edit Line / PLC" if is_edit else "Add New Line / PLC")
        dialog.geometry("620x680")
        dialog.minsize(580, 550)
        dialog.grab_set()
        
        plcs = self.config_manager.get().get("plcs", [])
        plc_data = plcs[edit_index] if is_edit and edit_index < len(plcs) else {}
        
        # Top Grid: Connection Settings
        conn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        conn_frame.pack(fill="x", padx=20, pady=(15, 5))
        conn_frame.grid_columnconfigure((0, 1), weight=1)
        
        ctk.CTkLabel(conn_frame, text="Line / PLC Name:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 2))
        name_entry = ctk.CTkEntry(conn_frame, width=260)
        name_entry.insert(0, plc_data.get("name", "LINE 1"))
        name_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 8))
        
        ctk.CTkLabel(conn_frame, text="IP Address (Host):", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky="w", pady=(0, 2))
        host_entry = ctk.CTkEntry(conn_frame, width=260)
        host_entry.insert(0, plc_data.get("host", ""))
        host_entry.grid(row=1, column=1, sticky="ew", pady=(0, 8))
        
        ctk.CTkLabel(conn_frame, text="FTP Port:").grid(row=2, column=0, sticky="w", pady=(0, 2))
        port_entry = ctk.CTkEntry(conn_frame, width=260)
        port_entry.insert(0, str(plc_data.get("port", 21)))
        port_entry.grid(row=3, column=0, sticky="ew", padx=(0, 10), pady=(0, 8))
        
        ctk.CTkLabel(conn_frame, text="FTP Username:").grid(row=2, column=1, sticky="w", pady=(0, 2))
        user_entry = ctk.CTkEntry(conn_frame, width=260)
        user_entry.insert(0, plc_data.get("username", "ftp"))
        user_entry.grid(row=3, column=1, sticky="ew", pady=(0, 8))
        
        ctk.CTkLabel(conn_frame, text="FTP Password:").grid(row=4, column=0, sticky="w", pady=(0, 2))
        pass_entry = ctk.CTkEntry(conn_frame, width=260, show="*")
        pass_entry.insert(0, plc_data.get("password", ""))
        pass_entry.grid(row=5, column=0, sticky="ew", padx=(0, 10), pady=(0, 8))
        
        # Test Connection button
        test_btn_frame = ctk.CTkFrame(conn_frame, fg_color="transparent")
        test_btn_frame.grid(row=5, column=1, sticky="ew")
        
        test_status_lbl = ctk.CTkLabel(dialog, text="", font=ctk.CTkFont(size=11))
        
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

        btn_test = ctk.CTkButton(test_btn_frame, text="🔌 Test Connection", command=do_test)
        btn_test.pack(side="left", fill="x", expand=True)
        test_status_lbl.pack(padx=20, pady=(0, 5))

        # Machines Section
        m_section_header = ctk.CTkFrame(dialog, fg_color="transparent")
        m_section_header.pack(fill="x", padx=20, pady=(5, 2))
        
        ctk.CTkLabel(m_section_header, text="🏭 Machines / Stations in this Line:", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        
        machines_container = ctk.CTkScrollableFrame(dialog, height=220, label_text="Machine Name & Remote FTP Directory")
        machines_container.pack(fill="both", expand=True, padx=20, pady=5)
        
        # Rows list
        machine_rows = []

        def add_machine_row(name="", remote_dir=""):
            row_frame = ctk.CTkFrame(machines_container)
            row_frame.pack(fill="x", padx=5, pady=4)
            
            # Machine name entry
            name_ent = ctk.CTkEntry(row_frame, width=180, placeholder_text="e.g. MC1 Leak Test")
            name_ent.insert(0, name if name else f"MC{len(machine_rows)+1}")
            name_ent.pack(side="left", padx=(5, 5), pady=5)
            
            # Remote dir entry
            dir_ent = ctk.CTkEntry(row_frame, width=220, placeholder_text="/0_CARD/log0/")
            dir_ent.insert(0, remote_dir if remote_dir else "/")
            dir_ent.pack(side="left", fill="x", expand=True, padx=5, pady=5)
            
            # Browse button for this specific machine
            def browse_for_this_row():
                h = host_entry.get().strip()
                p = int(port_entry.get() if port_entry.get().isdigit() else 21)
                u = user_entry.get().strip()
                pw = pass_entry.get().strip()
                if not h:
                    test_status_lbl.configure(text="Please enter Host/IP first.", text_color="#FF5252")
                    return
                
                def on_selected(chosen_dir):
                    dir_ent.delete(0, "end")
                    dir_ent.insert(0, chosen_dir)
                
                init_d = dir_ent.get().strip() or "/"
                FTPBrowserDialog(dialog, h, p, u, pw, initial_dir=init_d, on_select_callback=on_selected)

            btn_browse_m = ctk.CTkButton(row_frame, text="📁 Browse", width=75, command=browse_for_this_row)
            btn_browse_m.pack(side="left", padx=5, pady=5)
            
            # Delete button
            def delete_this_row():
                if len(machine_rows) > 1:
                    row_frame.destroy()
                    machine_rows.remove(row_data)
                    
            btn_del_m = ctk.CTkButton(row_frame, text="✕", width=30, fg_color="#d32f2f", hover_color="#b71c1c", command=delete_this_row)
            btn_del_m.pack(side="left", padx=(0, 5), pady=5)
            
            row_data = {"frame": row_frame, "name_entry": name_ent, "dir_entry": dir_ent}
            machine_rows.append(row_data)

        # Populate initial machines
        init_machines = plc_data.get("machines", [])
        if init_machines:
            for m in init_machines:
                add_machine_row(m.get("name", ""), m.get("remote_dir", ""))
        else:
            # Default to 3 machines for new or migrated line
            add_machine_row("MC1 Connector Leak", "/0_CARD/log0/")
            add_machine_row("MC2 Final And Resistance", "/0_CARD/log1/")
            add_machine_row("MC3 Auto Appearance", "/0_CARD/log2/")

        # Add Machine button
        btn_add_m = ctk.CTkButton(dialog, text="➕ Add Another Machine", width=180, command=lambda: add_machine_row())
        btn_add_m.pack(pady=5)

        # Bottom Save / Cancel
        bottom_bar = ctk.CTkFrame(dialog, fg_color="transparent")
        bottom_bar.pack(fill="x", padx=20, pady=(10, 15))
        
        def save():
            line_name = name_entry.get().strip()
            host = host_entry.get().strip()
            if not line_name or not host:
                test_status_lbl.configure(text="Please fill Line Name and IP Address.", text_color="#FF5252")
                return
                
            collected_machines = []
            for r in machine_rows:
                m_n = r["name_entry"].get().strip()
                m_d = r["dir_entry"].get().strip()
                if m_n and m_d:
                    collected_machines.append({"name": m_n, "remote_dir": m_d})
                    
            if not collected_machines:
                collected_machines.append({"name": "MC1", "remote_dir": "/"})

            new_data = {
                "name": line_name,
                "host": host,
                "port": int(port_entry.get() if port_entry.get().isdigit() else 21),
                "username": user_entry.get().strip(),
                "password": pass_entry.get().strip(),
                "machines": collected_machines
            }
            if is_edit:
                self.config_manager.update_plc(edit_index, new_data)
            else:
                self.config_manager.add_plc(new_data)
            self.refresh_list()
            if self.on_plc_list_updated:
                self.on_plc_list_updated()
            dialog.destroy()

        btn_save = ctk.CTkButton(bottom_bar, text="💾 Save Line & Machines", font=ctk.CTkFont(weight="bold"), height=35, command=save)
        btn_save.pack(side="right", padx=5)
        
        btn_cancel = ctk.CTkButton(bottom_bar, text="Cancel", width=80, height=35, fg_color="gray", hover_color="#555", command=dialog.destroy)
        btn_cancel.pack(side="right", padx=5)
