import customtkinter as ctk
from core.logger import logger
from ui.components.tooltip import ToolTip
from ui.components.plc_modal_dialog import PLCModalDialog
from ui.components.modal_utils import setup_modal_dialog
from ui.controllers.plc_manager_controller import PLCManagerController

class PLCManagerView(ctk.CTkFrame):
    def __init__(self, master, config_manager, on_plc_list_updated=None, controller=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.config_manager = config_manager
        self.controller = controller or PLCManagerController(self.config_manager)
        self.on_plc_list_updated = on_plc_list_updated
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # 1. Top Header Toolbar
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=16, pady=(12, 8), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")
        
        header_title = ctk.CTkLabel(
            title_box, 
            text="Production Line & PLC Manager", 
            font=ctk.CTkFont(size=22, weight="bold")
        )
        header_title.pack(anchor="w")

        self.summary_badge = ctk.CTkLabel(
            title_box, 
            text="", 
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.summary_badge.pack(anchor="w", pady=(2, 0))

        add_btn = ctk.CTkButton(
            header_frame, 
            text="➕ Add New Line / PLC", 
            font=ctk.CTkFont(size=13, weight="bold"), 
            height=36,
            command=self.open_plc_dialog
        )
        add_btn.grid(row=0, column=1, sticky="e")
        
        # 2. Scrollable List Frame
        self.plc_list_frame = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.plc_list_frame.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="nsew")
        
        self.refresh_list()

    def refresh_list(self):
        for w in self.plc_list_frame.winfo_children():
            w.destroy()

        plcs = self.controller.get_plcs()
        self.summary_badge.configure(text=f"จัดการข้อมูลสายการผลิตและตู้ PLC ({len(plcs)} Line(s) configured)")

        if not plcs:
            empty_frame = ctk.CTkFrame(self.plc_list_frame, fg_color="transparent")
            empty_frame.pack(fill="x", pady=60)
            ctk.CTkLabel(
                empty_frame,
                text="ยังไม่มีสายการผลิต / ตู้ PLC ในระบบ (No Lines Added)\nคลิกปุ่ม '➕ Add New Line / PLC' ด้านบนเพื่อเพิ่มเครื่องแรก",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            ).pack()
            return

        for i, plc in enumerate(plcs):
            # Card Container
            card = ctk.CTkFrame(self.plc_list_frame, corner_radius=10, fg_color=("#F5F5F5", "#212121"))
            card.pack(fill="x", padx=4, pady=6)
            card.grid_columnconfigure(0, weight=1)

            # TOP ROW: Line Name, IP info, Date Badge, Action Buttons
            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="ew")
            top_row.grid_columnconfigure(0, weight=1)

            # Left: Name & Connection info
            info_frame = ctk.CTkFrame(top_row, fg_color="transparent")
            info_frame.grid(row=0, column=0, sticky="w")

            line_title = ctk.CTkLabel(
                info_frame,
                text=plc.get("name", f"LINE {i+1}"),
                font=ctk.CTkFont(size=16, weight="bold")
            )
            line_title.pack(anchor="w")

            conn_sub = f"🌐 {plc.get('host', '')}:{plc.get('port', 21)}  •  User: {plc.get('username', 'ftp')}  •  Mode: {plc.get('ftp_mode', 'auto').upper()}"
            ctk.CTkLabel(
                info_frame,
                text=conn_sub,
                font=ctk.CTkFont(size=11),
                text_color=("#666666", "#9E9E9E")
            ).pack(anchor="w", pady=(2, 0))

            # Right: Edit/Delete action buttons
            actions_frame = ctk.CTkFrame(top_row, fg_color="transparent")
            actions_frame.grid(row=0, column=1, sticky="e")

            edit_btn = ctk.CTkButton(
                actions_frame,
                text="✏️ Edit",
                width=65,
                height=30,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=("#E0E0E0", "#333333"),
                hover_color=("#D5D5D5", "#444444"),
                text_color=("#212121", "#FFFFFF"),
                command=lambda idx=i: self.open_plc_dialog(idx)
            )
            edit_btn.pack(side="left", padx=(0, 6))

            del_btn = ctk.CTkButton(
                actions_frame,
                text="🗑️ Delete",
                width=70,
                height=30,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#D32F2F",
                hover_color="#B71C1C",
                text_color="white",
                command=lambda idx=i: self.delete_plc(idx)
            )
            del_btn.pack(side="left")

            # DIVIDER
            divider = ctk.CTkFrame(card, height=1, fg_color=("#E0E0E0", "#333333"))
            divider.grid(row=1, column=0, padx=16, pady=4, sticky="ew")

            # BOTTOM ROW: Machines Container (Neat Chips / Badges Grid)
            machines = plc.get("machines", [])
            if not machines:
                r_dirs_raw = plc.get("remote_directory", "")
                m_list = [d.strip() for d in r_dirs_raw.split(",") if d.strip()]
                if m_list:
                    machines = [{"name": f"MC{idx+1}", "remote_dir": d} for idx, d in enumerate(m_list)]
                else:
                    machines = [{"name": "MC1 (Default)", "remote_dir": "/"}]

            mc_section = ctk.CTkFrame(card, fg_color="transparent")
            mc_section.grid(row=2, column=0, padx=16, pady=(4, 12), sticky="ew")

            mc_header = ctk.CTkLabel(
                mc_section,
                text=f"🏭 Configured Machines ({len(machines)}):",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=("#666666", "#9E9E9E")
            )
            mc_header.pack(anchor="w", pady=(0, 4))

            mc_list = ctk.CTkFrame(mc_section, fg_color="transparent")
            mc_list.pack(fill="x")

            # Render each machine on its own row (full-width)
            for mc_idx, mc in enumerate(machines):
                row_frame = ctk.CTkFrame(mc_list, corner_radius=6, fg_color=("#EAEAEA", "#2A2A2A"))
                row_frame.pack(fill="x", pady=2)

                mc_name_lbl = ctk.CTkLabel(
                    row_frame,
                    text=f"🖥️ {mc.get('name', f'MC{mc_idx+1}')}",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=("#1565C0", "#64B5F6")
                )
                mc_name_lbl.pack(side="left", padx=(10, 8), pady=4)

                path_text = mc.get('remote_dir', '/')
                mc_path_lbl = ctk.CTkLabel(
                    row_frame,
                    text=f"📂 {path_text}",
                    font=ctk.CTkFont(size=11),
                    text_color=("#555555", "#AAAAAA"),
                    anchor="w"
                )
                mc_path_lbl.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=4)

            # Date Filter info (informative label at the bottom, not looking like a button)
            df = plc.get("date_filter", {})
            if df.get("mode") == "range" and df.get("start_date") and df.get("end_date"):
                df_str = f"📅 Date Filter: {df['start_date']} ➔ {df['end_date']}"
                df_color = ("#5E35B1", "#B39DDB")
            else:
                df_str = "📅 Date Filter: All Files (ดาวน์โหลดไฟล์ทั้งหมด)"
                df_color = ("#757575", "#9E9E9E")

            df_lbl = ctk.CTkLabel(
                mc_section,
                text=df_str,
                font=ctk.CTkFont(size=11),
                text_color=df_color
            )
            df_lbl.pack(anchor="w", pady=(8, 0))

    def delete_plc(self, index):
        plcs = self.controller.get_plcs()
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
            self.controller.delete_plc(index)
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
        PLCModalDialog(
            self,
            config_manager=self.config_manager,
            edit_index=edit_index,
            on_save_callback=self._on_dialog_saved,
            controller=self.controller
        )

    def _on_dialog_saved(self):
        self.refresh_list()
        if self.on_plc_list_updated:
            self.on_plc_list_updated()
