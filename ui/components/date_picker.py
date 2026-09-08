"""Date picker popup and quick date filter dialog using CustomTkinter."""

import calendar
from datetime import date, datetime
import tkinter as tk
from typing import Callable, Dict, Optional, Tuple
import customtkinter as ctk
from ui.components.modal_utils import setup_modal_dialog

MONTH_NAMES_TH = [
    "",
    "มกราคม",
    "กุมภาพันธ์",
    "มีนาคม",
    "เมษายน",
    "พฤษภาคม",
    "มิถุนายน",
    "กรกฎาคม",
    "สิงหาคม",
    "กันยายน",
    "ตุลาคม",
    "พฤศจิกายน",
    "ธันวาคม",
]

MONTH_NAMES_EN = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

DAY_NAMES_TH = ["จ.", "อ.", "พ.", "พฤ.", "ศ.", "ส.", "อา."]


def parse_display_date(date_str: str) -> Optional[date]:
    """Parses a date string in DD/MM/YYYY format into a datetime.date object."""
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        return datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


def format_display_date(date_obj: date) -> str:
    """Formats a datetime.date object into DD/MM/YYYY format."""
    return date_obj.strftime("%d/%m/%Y")


def get_month_matrix(year: int, month: int):
    """Returns a list of weeks (Monday to Sunday) for the specified year and month."""
    cal = calendar.Calendar(firstweekday=0)
    return cal.monthdayscalendar(year, month)


def validate_date_range(
    start_str: str, end_str: str
) -> Tuple[bool, str, Optional[date], Optional[date]]:
    """Validates start and end date strings.

    Returns (is_valid, error_message, start_date_obj, end_date_obj).
    """
    s_date = parse_display_date(start_str)
    if not s_date:
        return (
            False,
            "Invalid Start Date. Format must be DD/MM/YYYY (e.g. 01/05/2025)",
            None,
            None,
        )

    e_date = parse_display_date(end_str)
    if not e_date:
        return (
            False,
            "Invalid End Date. Format must be DD/MM/YYYY (e.g. 31/05/2025)",
            None,
            None,
        )

    if s_date > e_date:
        return (
            False,
            "Start date cannot be after end date (วันที่เริ่มต้นต้องไม่มากกว่าวันสิ้นสุด)",
            None,
            None,
        )

    return True, "", s_date, e_date


class DatePickerPopup(ctk.CTkToplevel):
    """A clean, modal calendar popup built with CustomTkinter."""

    def __init__(
        self,
        parent,
        initial_date: Optional[str] = None,
        on_select: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(parent)
        self.on_select = on_select
        self.title("เลือกวันที่")
        self.resizable(False, False)

        # Determine starting year & month
        parsed = parse_display_date(initial_date) if initial_date else None
        today = date.today()
        if parsed:
            self.current_year = parsed.year
            self.current_month = parsed.month
            self.selected_date = parsed
        else:
            self.current_year = today.year
            self.current_month = today.month
            self.selected_date = today

        self.today = today

        # Build UI
        self._build_ui()
        self._render_calendar()

        setup_modal_dialog(self, parent, target_width=340, target_height=420, resizable=False)

    def _build_ui(self):
        # Header navigation frame
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=12, pady=(12, 6))

        # Year navigation
        self.btn_prev_year = ctk.CTkButton(
            self.header_frame,
            text="«",
            width=28,
            height=28,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._prev_year,
        )
        self.btn_prev_year.pack(side="left", padx=2)

        # Month navigation
        self.btn_prev_month = ctk.CTkButton(
            self.header_frame,
            text="‹",
            width=28,
            height=28,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._prev_month,
        )
        self.btn_prev_month.pack(side="left", padx=2)

        self.lbl_month_year = ctk.CTkLabel(
            self.header_frame,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.lbl_month_year.pack(side="left", expand=True)

        self.btn_next_month = ctk.CTkButton(
            self.header_frame,
            text="›",
            width=28,
            height=28,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._next_month,
        )
        self.btn_next_month.pack(side="right", padx=2)

        self.btn_next_year = ctk.CTkButton(
            self.header_frame,
            text="»",
            width=28,
            height=28,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._next_year,
        )
        self.btn_next_year.pack(side="right", padx=2)

        # Day of week header
        self.days_header = ctk.CTkFrame(self, fg_color="transparent")
        self.days_header.pack(fill="x", padx=12, pady=(4, 4))
        for i, day_name in enumerate(DAY_NAMES_TH):
            color = "#E06666" if i >= 5 else "gray70"
            lbl = ctk.CTkLabel(
                self.days_header,
                text=day_name,
                width=36,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=color,
            )
            lbl.grid(row=0, column=i, padx=2)

        # Calendar grid frame
        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(padx=12, pady=4)

        # Footer actions
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.pack(fill="x", padx=12, pady=(6, 12))

        self.btn_today = ctk.CTkButton(
            self.footer_frame,
            text="วันนี้ (Today)",
            height=28,
            font=ctk.CTkFont(size=11),
            command=self._select_today,
        )
        self.btn_today.pack(side="left", padx=4)

        self.btn_cancel = ctk.CTkButton(
            self.footer_frame,
            text="ยกเลิก",
            fg_color="transparent",
            border_width=1,
            height=28,
            font=ctk.CTkFont(size=11),
            command=self.destroy,
        )
        self.btn_cancel.pack(side="right", padx=4)

    def _prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self._render_calendar()

    def _next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self._render_calendar()

    def _prev_year(self):
        self.current_year -= 1
        self._render_calendar()

    def _next_year(self):
        self.current_year += 1
        self._render_calendar()

    def _render_calendar(self):
        # Update header label
        th_month = MONTH_NAMES_TH[self.current_month]
        self.lbl_month_year.configure(
            text=f"{th_month} {self.current_year}"
        )

        # Clear existing buttons in grid
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        weeks = get_month_matrix(self.current_year, self.current_month)

        for row_idx, week in enumerate(weeks):
            for col_idx, day in enumerate(week):
                if day == 0:
                    # Placeholder label for empty days
                    lbl = ctk.CTkLabel(
                        self.grid_frame,
                        text="",
                        width=36,
                        height=30,
                    )
                    lbl.grid(row=row_idx, column=col_idx, padx=2, pady=2)
                else:
                    is_selected = (
                        self.selected_date
                        and self.selected_date.year == self.current_year
                        and self.selected_date.month == self.current_month
                        and self.selected_date.day == day
                    )
                    is_today = (
                        self.today.year == self.current_year
                        and self.today.month == self.current_month
                        and self.today.day == day
                    )

                    btn_kwargs = {
                        "text": str(day),
                        "width": 36,
                        "height": 30,
                        "font": ctk.CTkFont(size=12),
                        "command": lambda d=day: self._on_date_clicked(d),
                    }

                    if is_selected:
                        btn_kwargs["fg_color"] = "#1f538d"
                        btn_kwargs["font"] = ctk.CTkFont(size=12, weight="bold")
                    elif is_today:
                        btn_kwargs["border_width"] = 1
                        btn_kwargs["border_color"] = "#3B8ED0"

                    # Weekend text color
                    if col_idx >= 5 and not is_selected:
                        btn_kwargs["text_color"] = "#FF8080"

                    btn = ctk.CTkButton(self.grid_frame, **btn_kwargs)
                    btn.grid(row=row_idx, column=col_idx, padx=2, pady=2)

    def _on_date_clicked(self, day: int):
        selected = date(self.current_year, self.current_month, day)
        date_str = format_display_date(selected)
        if self.on_select:
            self.on_select(date_str)
        self.destroy()

    def _select_today(self):
        date_str = format_display_date(self.today)
        if self.on_select:
            self.on_select(date_str)
        self.destroy()


class QuickDateFilterDialog(ctk.CTkToplevel):
    """Modal dialog for quickly changing a PLC's date filter settings."""

    def __init__(
        self,
        parent,
        plc_name: str,
        current_filter: Optional[Dict] = None,
        on_save: Optional[Callable[[Dict], None]] = None,
    ):
        super().__init__(parent)
        self.plc_name = plc_name
        self.on_save = on_save
        self.title(f"ตั้งค่าช่วงวันที่ - {plc_name}")
        self.resizable(False, False)

        cur = current_filter or {}
        self.mode_var = tk.StringVar(value=cur.get("mode", "all"))
        self.start_date_var = tk.StringVar(value=cur.get("start_date", ""))
        self.end_date_var = tk.StringVar(value=cur.get("end_date", ""))

        self._build_ui()
        setup_modal_dialog(self, parent, target_width=440, target_height=260, resizable=False)

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=16)

        title_lbl = ctk.CTkLabel(
            container,
            text=f"📅 กำหนดช่วงเวลาดาวน์โหลด ({self.plc_name})",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        title_lbl.pack(anchor="w", pady=(0, 10))

        # Mode Radio Buttons
        mode_frame = ctk.CTkFrame(container, fg_color="transparent")
        mode_frame.pack(fill="x", pady=5)

        self.radio_all = ctk.CTkRadioButton(
            mode_frame,
            text="All Files (ดาวน์โหลดไฟล์ทั้งหมด)",
            variable=self.mode_var,
            value="all",
            command=self._on_mode_change,
        )
        self.radio_all.pack(anchor="w", pady=4)

        self.radio_range = ctk.CTkRadioButton(
            mode_frame,
            text="Date Range (กำหนดช่วงวันที่เริ่มต้น - สิ้นสุด)",
            variable=self.mode_var,
            value="range",
            command=self._on_mode_change,
        )
        self.radio_range.pack(anchor="w", pady=4)

        # Date entries frame
        self.range_inputs_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.range_inputs_frame.pack(fill="x", pady=8)

        # Start Date
        start_row = ctk.CTkFrame(self.range_inputs_frame, fg_color="transparent")
        start_row.pack(fill="x", pady=4)
        ctk.CTkLabel(
            start_row,
            text="วันที่เริ่มต้น (Start):",
            width=130,
            anchor="w",
            font=ctk.CTkFont(size=12),
        ).pack(side="left")
        self.start_entry = ctk.CTkEntry(
            start_row,
            textvariable=self.start_date_var,
            placeholder_text="DD/MM/YYYY",
            width=130,
        )
        self.start_entry.pack(side="left", padx=(0, 6))
        self.btn_start_cal = ctk.CTkButton(
            start_row,
            text="📅",
            width=32,
            height=28,
            command=self._pick_start_date,
        )
        self.btn_start_cal.pack(side="left")

        # End Date
        end_row = ctk.CTkFrame(self.range_inputs_frame, fg_color="transparent")
        end_row.pack(fill="x", pady=4)
        ctk.CTkLabel(
            end_row,
            text="วันที่สิ้นสุด (End):",
            width=130,
            anchor="w",
            font=ctk.CTkFont(size=12),
        ).pack(side="left")
        self.end_entry = ctk.CTkEntry(
            end_row,
            textvariable=self.end_date_var,
            placeholder_text="DD/MM/YYYY",
            width=130,
        )
        self.end_entry.pack(side="left", padx=(0, 6))
        self.btn_end_cal = ctk.CTkButton(
            end_row,
            text="📅",
            width=32,
            height=28,
            command=self._pick_end_date,
        )
        self.btn_end_cal.pack(side="left")

        # Error label
        self.lbl_error = ctk.CTkLabel(
            container,
            text="",
            text_color="#FF6B6B",
            font=ctk.CTkFont(size=11),
            wraplength=340,
            justify="left",
        )
        self.lbl_error.pack(fill="x", pady=4)

        # Action buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))

        self.btn_save = ctk.CTkButton(
            btn_frame,
            text="บันทึก (Save)",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._save,
        )
        self.btn_save.pack(side="right", padx=4)

        self.btn_cancel = ctk.CTkButton(
            btn_frame,
            text="ยกเลิก",
            fg_color="transparent",
            border_width=1,
            command=self.destroy,
        )
        self.btn_cancel.pack(side="right", padx=4)

        self._on_mode_change()

    def _on_mode_change(self):
        is_range = self.mode_var.get() == "range"
        state = "normal" if is_range else "disabled"
        self.start_entry.configure(state=state)
        self.end_entry.configure(state=state)
        self.btn_start_cal.configure(state=state)
        self.btn_end_cal.configure(state=state)
        if not is_range:
            self.lbl_error.configure(text="")

    def _pick_start_date(self):
        def on_selected(d_str):
            self.start_date_var.set(d_str)

        DatePickerPopup(self, initial_date=self.start_date_var.get(), on_select=on_selected)

    def _pick_end_date(self):
        def on_selected(d_str):
            self.end_date_var.set(d_str)

        DatePickerPopup(self, initial_date=self.end_date_var.get(), on_select=on_selected)

    def _save(self):
        mode = self.mode_var.get()
        start = self.start_date_var.get().strip()
        end = self.end_date_var.get().strip()

        if mode == "range":
            ok, err, _, _ = validate_date_range(start, end)
            if not ok:
                self.lbl_error.configure(text=err)
                return

        new_filter = {
            "mode": mode,
            "start_date": start,
            "end_date": end,
        }

        if self.on_save:
            self.on_save(new_filter)
        self.destroy()
