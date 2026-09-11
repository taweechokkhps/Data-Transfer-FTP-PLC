import customtkinter as ctk
import threading
from ui.components.tooltip import ToolTip
from ui.components.ftp_browser_dialog import FTPBrowserDialog
from ui.components.date_picker import DatePickerPopup
from ui.components.modal_utils import setup_modal_dialog
from ui.controllers.plc_manager_controller import PLCManagerController

class PLCModalDialog(ctk.CTkToplevel):
    """Modal dialog for adding or editing a PLC configuration with multiple machines."""
    def __init__(self, parent, config_manager, edit_index=None, on_save_callback=None, controller=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.controller = controller or PLCManagerController(config_manager)
        self.edit_index = edit_index
        self.on_save_callback = on_save_callback
        self.is_edit = edit_index is not None

        self.title("Edit Line / PLC" if self.is_edit else "Add New Line / PLC")
        setup_modal_dialog(self, parent, target_width=720, target_height=780, resizable=True, min_width=580, min_height=480)

        # Scrollable content wrapper
        scroll_wrapper = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_wrapper.pack(fill="both", expand=True, padx=4, pady=4)

        plcs = self.config_manager.get().get("plcs", [])
        plc_data = plcs[edit_index] if self.is_edit and edit_index < len(plcs) else {}

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
                ok, msg = self.controller.test_connection(h, p, u, pw, ftp_mode=m)
                try:
                    if not self.winfo_exists():
                        return
                    if ok:
                        self.after(0, lambda: test_status_lbl.winfo_exists() and test_status_lbl.configure(text="✓ Connection Successful!", text_color="#00E676"))
                    else:
                        self.after(0, lambda: test_status_lbl.winfo_exists() and test_status_lbl.configure(text=f"✗ {msg}", text_color="#FF5252"))
                except Exception:
                    pass
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

        machine_rows = []

        def add_machine_row(name="", remote_dir=""):
            row_idx = len(machine_rows) + 1
            row_frame = ctk.CTkFrame(machines_container, corner_radius=8, fg_color=("#F5F5F5", "#242424"))
            row_frame.pack(fill="x", padx=4, pady=4)

            badge_lbl = ctk.CTkLabel(
                row_frame,
                text=f"#{row_idx}",
                width=32,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=("#E0E0E0", "#333333"),
                corner_radius=6
            )
            badge_lbl.pack(side="left", padx=(8, 6), pady=6)

            name_ent = ctk.CTkEntry(row_frame, width=170, placeholder_text="Station / MC Name")
            name_ent.insert(0, name if name else f"MC{row_idx}")
            name_ent.pack(side="left", padx=(0, 6), pady=6)

            dir_ent = ctk.CTkEntry(row_frame, placeholder_text="Remote FTP Directory (e.g. /0_CARD/log0/)")
            dir_ent.insert(0, remote_dir if remote_dir else "/")
            dir_ent.pack(side="left", fill="x", expand=True, padx=(0, 6), pady=6)

            def browse_for_this_row():
                h = host_entry.get().strip()
                p = int(port_entry.get() if port_entry.get().isdigit() else 21)
                u = user_entry.get().strip()
                pw = pass_entry.get().strip()
                m = mode_val_map.get(ftp_mode_var.get(), "auto")
                init_d = dir_ent.get().strip() or "/"
                if h:
                    def on_dir_selected(sel):
                        try:
                            if dir_ent.winfo_exists():
                                dir_ent.delete(0, "end")
                                dir_ent.insert(0, sel)
                        except Exception:
                            pass
                    FTPBrowserDialog(self, h, p, u, pw, initial_dir=init_d, on_select_callback=on_dir_selected, ftp_mode=m)
                else:
                    test_status_lbl.configure(text="⚠️ กรุณาระบุ IP Address ก่อนเปิดดูโฟลเดอร์บน PLC", text_color="#FFA726")

            btn_browse_m = ctk.CTkButton(
                row_frame,
                text="🌐 Browse PLC",
                width=105,
                height=30,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=("#673AB7", "#5E35B1"),
                hover_color=("#512DA8", "#4527A0"),
                text_color="white",
                command=browse_for_this_row
            )
            btn_browse_m.pack(side="left", padx=(0, 6), pady=6)
            ToolTip(btn_browse_m, "เชื่อมต่อไปยัง PLC เพื่อเลือกโฟลเดอร์ปลายทางโดยตรง (ไม่ต้องเปิด WinSCP)")

            def delete_this_row():
                if len(machine_rows) > 1:
                    row_frame.destroy()
                    machine_rows.remove(row_data)
                    for idx, r in enumerate(machine_rows):
                        r["badge_lbl"].configure(text=f"#{idx+1}")

            btn_del_m = ctk.CTkButton(
                row_frame,
                text="✕",
                width=30,
                height=30,
                fg_color="#D32F2F",
                hover_color="#B71C1C",
                command=delete_this_row
            )
            btn_del_m.pack(side="left", padx=(0, 8), pady=6)

            row_data = {"frame": row_frame, "name_entry": name_ent, "dir_entry": dir_ent, "badge_lbl": badge_lbl}
            machine_rows.append(row_data)

        # Populate initial machines
        init_machines = plc_data.get("machines", [])
        if init_machines:
            for m in init_machines:
                add_machine_row(m.get("name", ""), m.get("remote_dir", ""))
        else:
            add_machine_row("MC1", "/0_CARD/log0/")

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
            DatePickerPopup(self, initial_date=start_date_ent.get(), on_select=on_sel)

        def pick_end():
            def on_sel(d_str):
                end_date_ent.delete(0, "end")
                end_date_ent.insert(0, d_str)
            DatePickerPopup(self, initial_date=end_date_ent.get(), on_select=on_sel)

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
            collected_machines = []
            for r in machine_rows:
                m_n = r["name_entry"].get().strip()
                m_d = r["dir_entry"].get().strip()
                if m_n and m_d:
                    collected_machines.append({"name": m_n, "remote_dir": m_d})

            new_data = {
                "name": name_entry.get().strip(),
                "host": host_entry.get().strip(),
                "port": port_entry.get().strip(),
                "username": user_entry.get().strip(),
                "password": pass_entry.get().strip(),
                "ftp_mode": mode_val_map.get(ftp_mode_var.get(), "auto"),
                "machines": collected_machines,
                "date_filter": {
                    "mode": filter_mode_var.get(),
                    "start_date": start_date_ent.get().strip(),
                    "end_date": end_date_ent.get().strip()
                }
            }
            if self.is_edit:
                ok, msg = self.controller.update_plc(self.edit_index, new_data)
            else:
                ok, msg = self.controller.add_plc(new_data)

            if not ok:
                test_status_lbl.configure(text=msg, text_color="#FF5252")
                return

            if self.on_save_callback:
                self.on_save_callback()
            self.destroy()

        btn_save = ctk.CTkButton(bottom_bar, text="💾 Save Line & Machines", font=ctk.CTkFont(weight="bold"), height=35, command=save)
        btn_save.pack(side="right", padx=5)

        btn_cancel = ctk.CTkButton(bottom_bar, text="Cancel", width=80, height=35, fg_color="gray", hover_color="#555", command=self.destroy)
        btn_cancel.pack(side="right", padx=5)
