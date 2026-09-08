import customtkinter as ctk
from tkinter import filedialog
import threading
from core.ftp_service import test_connection
from core.path_utils import sanitize_remote_path
from ui.components.ftp_browser_dialog import FTPBrowserDialog
from ui.components.date_picker import DatePickerPopup, validate_date_range
from ui.components.modal_utils import setup_modal_dialog

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
        header_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        header_frame.grid_columnconfigure(5, weight=0, minsize=140)
        
        headers = ["Line Name", "Host:Port", "Username", "Configured Machines", "Date Filter", "Actions"]
        for col, text in enumerate(headers):
            anchor = "e" if col == 5 else "w"
            ctk.CTkLabel(header_frame, text=text, font=ctk.CTkFont(weight="bold")).grid(row=0, column=col, padx=10, pady=5, sticky=anchor)
            
        sep = ctk.CTkFrame(self.plc_list_frame, height=2, fg_color=("gray70", "gray30"))
        sep.pack(fill="x", padx=5, pady=(0, 5))
        
        plcs = self.config_manager.get().get("plcs", [])
        for i, plc in enumerate(plcs):
            frame = ctk.CTkFrame(self.plc_list_frame)
            frame.pack(fill="x", padx=5, pady=2)
            frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
            frame.grid_columnconfigure(5, weight=0, minsize=140)
            
            ctk.CTkLabel(frame, text=plc.get('name', ''), font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
            ctk.CTkLabel(frame, text=f"{plc.get('host', '')}:{plc.get('port', 21)}").grid(row=0, column=1, padx=10, pady=10, sticky="w")
            ctk.CTkLabel(frame, text=plc.get('username', '')).grid(row=0, column=2, padx=10, pady=10, sticky="w")
            
            machines = plc.get('machines', [])
            if machines:
                m_names = [m.get('name', 'MC') for m in machines]
                m_summary = f"{len(machines)} MC: " + ", ".join(m_names)
            else:
                m_summary = "1 MC: (Default)"
                
            if len(m_summary) > 28:
                m_summary = m_summary[:25] + "..."
            ctk.CTkLabel(frame, text=m_summary).grid(row=0, column=3, padx=10, pady=10, sticky="w")
            
            # Date filter summary
            df = plc.get("date_filter", {})
            if df.get("mode") == "range" and df.get("start_date") and df.get("end_date"):
                df_label = f"📅 {df['start_date']} - {df['end_date']}"
            else:
                df_label = "📅 All Files"
            ctk.CTkLabel(frame, text=df_label, text_color=("#4A148C", "#CE93D8"), font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=4, padx=10, pady=10, sticky="w")

            btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame.grid(row=0, column=5, padx=10, pady=5, sticky="e")
            
            edit_btn = ctk.CTkButton(btn_frame, text="Edit", width=60, command=lambda idx=i: self.open_plc_dialog(idx))
            edit_btn.pack(side="left", padx=(0, 5))
            
            del_btn = ctk.CTkButton(btn_frame, text="Delete", fg_color="#d32f2f", hover_color="#b71c1c", width=60, command=lambda idx=i: self.delete_plc(idx))
            del_btn.pack(side="left")

    def delete_plc(self, index):
        plcs = self.config_manager.get().get("plcs", [])
        plc_name = plcs[index].get("name", f"PLC {index+1}") if index < len(plcs) else f"PLC {index+1}"

        confirm = ctk.CTkToplevel(self)
        confirm.title("Confirm Delete")
        setup_modal_dialog(confirm, self, target_width=440, target_height=200, resizable=False)

        ctk.CTkLabel(
            confirm,
            text="⚠️  ยืนยันการลบ (Confirm Delete)",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 8))

        ctk.CTkLabel(
            confirm,
            text=f"ต้องการลบ '{plc_name}' ออกจากรายการหรือไม่?\nการกระทำนี้ไม่สามารถย้อนกลับได้",
            font=ctk.CTkFont(size=13)
        ).pack(pady=(0, 16))

        btn_row = ctk.CTkFrame(confirm, fg_color="transparent")
        btn_row.pack(pady=(0, 10))

        def do_delete():
            confirm.destroy()
            self.config_manager.delete_plc(index)
            self.refresh_list()
            if self.on_plc_list_updated:
                self.on_plc_list_updated()

        ctk.CTkButton(
            btn_row, text="❌ Delete", width=100, height=34,
            fg_color="#d32f2f", hover_color="#b71c1c",
            font=ctk.CTkFont(weight="bold"), command=do_delete
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_row, text="Cancel", width=100, height=34,
            fg_color="gray", hover_color="#555",
            font=ctk.CTkFont(weight="bold"), command=confirm.destroy
        ).pack(side="left", padx=8)

    def open_plc_dialog(self, edit_index=None):
        dialog = ctk.CTkToplevel(self)
        is_edit = edit_index is not None
        dialog.title("Edit Line / PLC" if is_edit else "Add New Line / PLC")
        setup_modal_dialog(dialog, self, target_width=720, target_height=780, resizable=True, min_width=580, min_height=480)

        # Scrollable content wrapper so everything fits even on small screens
        scroll_wrapper = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll_wrapper.pack(fill="both", expand=True, padx=4, pady=4)
        
        plcs = self.config_manager.get().get("plcs", [])
        plc_data = plcs[edit_index] if is_edit and edit_index < len(plcs) else {}
        
        # Top Grid: Connection Settings
        conn_frame = ctk.CTkFrame(scroll_wrapper, fg_color="transparent")
        conn_frame.pack(fill="x", padx=16, pady=(10, 5))
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
        
        mode_val_map = {
            "Auto (Auto Fallback)": "auto",
            "Active (PORT - แนะนำสำหรับ PLC)": "active",
            "Passive (PASV)": "passive",
        }
        mode_inv_map = {
            "auto": "Auto (Auto Fallback)",
            "active": "Active (PORT - แนะนำสำหรับ PLC)",
            "passive": "Passive (PASV)",
        }
        cur_ftp_mode = plc_data.get("ftp_mode", "auto")
        ftp_mode_var = ctk.StringVar(value=mode_inv_map.get(cur_ftp_mode, "Auto (Auto Fallback)"))

        ctk.CTkLabel(conn_frame, text="FTP Password:").grid(row=4, column=0, sticky="w", pady=(0, 2))
        pass_entry = ctk.CTkEntry(conn_frame, width=260, show="*")
        pass_entry.insert(0, plc_data.get("password", ""))
        pass_entry.grid(row=5, column=0, sticky="ew", padx=(0, 10), pady=(0, 8))
        
        ctk.CTkLabel(conn_frame, text="FTP Mode:").grid(row=4, column=1, sticky="w", pady=(0, 2))
        ftp_mode_menu = ctk.CTkOptionMenu(conn_frame, values=list(mode_val_map.keys()), variable=ftp_mode_var)
        ftp_mode_menu.grid(row=5, column=1, sticky="ew", pady=(0, 8))

        # Test Connection button
        test_status_lbl = ctk.CTkLabel(scroll_wrapper, text="", font=ctk.CTkFont(size=11))
        
        def do_test():
            h = host_entry.get().strip()
            p = int(port_entry.get() if port_entry.get().isdigit() else 21)
            u = user_entry.get().strip()
            pw = pass_entry.get().strip()
            m = mode_val_map.get(ftp_mode_var.get(), "auto")
            test_status_lbl.configure(text="Testing connection...", text_color="gray")
            def run():
                ok, msg = test_connection(h, p, u, pw, ftp_mode=m)
                if ok:
                    dialog.after(0, lambda: test_status_lbl.configure(text="✓ Connection Successful!", text_color="#00E676"))
                else:
                    dialog.after(0, lambda: test_status_lbl.configure(text=f"✗ {msg}", text_color="#FF5252"))
            threading.Thread(target=run, daemon=True).start()

        btn_test = ctk.CTkButton(conn_frame, text="🔌 Test Connection", command=do_test)
        btn_test.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(4, 8))
        test_status_lbl.pack(padx=20, pady=(0, 5))

        # Machines Section
        m_section_header = ctk.CTkFrame(scroll_wrapper, fg_color="transparent")
        m_section_header.pack(fill="x", padx=20, pady=(5, 2))
        
        ctk.CTkLabel(m_section_header, text="🏭 Machines / Stations in this Line:", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        
        machines_container = ctk.CTkScrollableFrame(scroll_wrapper, height=220, label_text="Machine Name & Remote FTP Directory")
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
                m = mode_val_map.get(ftp_mode_var.get(), "auto")
                init_d = dir_ent.get().strip() or "/"
                if h:
                    def on_dir_selected(sel):
                        dir_ent.delete(0, "end")
                        dir_ent.insert(0, sel)
                    FTPBrowserDialog(dialog, h, p, u, pw, initial_dir=init_d, on_select_callback=on_dir_selected, ftp_mode=m)
                else:
                    dir_name = filedialog.askdirectory(title=f"Select Directory for {name_ent.get() or 'Machine'}")
                    if dir_name:
                        cleaned = sanitize_remote_path(dir_name)
                        dir_ent.delete(0, "end")
                        dir_ent.insert(0, cleaned)

            btn_browse_m = ctk.CTkButton(row_frame, text="Browse", width=75, command=browse_for_this_row)
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

        # Populate initial machines (Default to 1 machine)
        init_machines = plc_data.get("machines", [])
        if init_machines:
            for m in init_machines:
                add_machine_row(m.get("name", ""), m.get("remote_dir", ""))
        else:
            add_machine_row("MC1", "/0_CARD/log0/")

        # Add Machine button
        btn_add_m = ctk.CTkButton(scroll_wrapper, text="➕ Add Another Machine", width=180, command=lambda: add_machine_row())
        btn_add_m.pack(pady=5)

        # Date Filter Section
        df_frame = ctk.CTkFrame(scroll_wrapper, fg_color=("gray85", "gray17"), corner_radius=8)
        df_frame.pack(fill="x", padx=20, pady=(5, 10))
        
        ctk.CTkLabel(df_frame, text="📅 Download Date Filter (การเลือกไฟล์ดาวน์โหลด):", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=12, pady=(8, 4))
        
        plc_df = plc_data.get("date_filter", {})
        filter_mode_var = ctk.StringVar(value=plc_df.get("mode", "all"))
        
        radio_row = ctk.CTkFrame(df_frame, fg_color="transparent")
        radio_row.pack(fill="x", padx=12, pady=(0, 6))
        
        date_inputs_row = ctk.CTkFrame(df_frame, fg_color="transparent")
        
        def toggle_date_mode():
            if filter_mode_var.get() == "range":
                date_inputs_row.pack(fill="x", padx=12, pady=(0, 8))
            else:
                date_inputs_row.pack_forget()

        rb_all = ctk.CTkRadioButton(radio_row, text="All Files (ดาวน์โหลดไฟล์ทั้งหมด)", variable=filter_mode_var, value="all", command=toggle_date_mode)
        rb_all.pack(side="left", padx=(0, 20))
        
        rb_range = ctk.CTkRadioButton(radio_row, text="Date Range (เลือกช่วงวันที่)", variable=filter_mode_var, value="range", command=toggle_date_mode)
        rb_range.pack(side="left")
        
        def pick_start():
            def on_sel(d_str):
                start_date_ent.delete(0, "end")
                start_date_ent.insert(0, d_str)
            DatePickerPopup(dialog, initial_date=start_date_ent.get(), on_select=on_sel)

        def pick_end():
            def on_sel(d_str):
                end_date_ent.delete(0, "end")
                end_date_ent.insert(0, d_str)
            DatePickerPopup(dialog, initial_date=end_date_ent.get(), on_select=on_sel)

        ctk.CTkLabel(date_inputs_row, text="Start:").pack(side="left", padx=(0, 4))
        start_date_ent = ctk.CTkEntry(date_inputs_row, width=95, placeholder_text="DD/MM/YYYY")
        start_date_ent.insert(0, plc_df.get("start_date", ""))
        start_date_ent.pack(side="left", padx=(0, 2))
        btn_start_cal = ctk.CTkButton(date_inputs_row, text="📅", width=28, height=28, command=pick_start)
        btn_start_cal.pack(side="left", padx=(0, 12))
        
        ctk.CTkLabel(date_inputs_row, text="End:").pack(side="left", padx=(0, 4))
        end_date_ent = ctk.CTkEntry(date_inputs_row, width=95, placeholder_text="DD/MM/YYYY")
        end_date_ent.insert(0, plc_df.get("end_date", ""))
        end_date_ent.pack(side="left", padx=(0, 2))
        btn_end_cal = ctk.CTkButton(date_inputs_row, text="📅", width=28, height=28, command=pick_end)
        btn_end_cal.pack(side="left", padx=(0, 8))
        
        ctk.CTkLabel(date_inputs_row, text="(e.g. 01/05/2025)", font=ctk.CTkFont(size=11), text_color="gray").pack(side="left")

        toggle_date_mode()

        # Bottom Save / Cancel
        bottom_bar = ctk.CTkFrame(scroll_wrapper, fg_color="transparent")
        bottom_bar.pack(fill="x", padx=20, pady=(5, 15))
        
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
                    collected_machines.append({"name": m_n, "remote_dir": sanitize_remote_path(m_d)})
                    
            if not collected_machines:
                collected_machines.append({"name": "MC1", "remote_dir": "/"})

            df_mode = filter_mode_var.get()
            s_date = start_date_ent.get().strip()
            e_date = end_date_ent.get().strip()
            if df_mode == "range":
                ok, err, _, _ = validate_date_range(s_date, e_date)
                if not ok:
                    test_status_lbl.configure(text=err, text_color="#FF5252")
                    return

            new_data = {
                "name": line_name,
                "host": host,
                "port": int(port_entry.get() if port_entry.get().isdigit() else 21),
                "username": user_entry.get().strip(),
                "password": pass_entry.get().strip(),
                "ftp_mode": mode_val_map.get(ftp_mode_var.get(), "auto"),
                "machines": collected_machines,
                "date_filter": {
                    "mode": df_mode,
                    "start_date": s_date,
                    "end_date": e_date
                }
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
