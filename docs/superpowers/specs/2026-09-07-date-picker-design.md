# Design Spec: CustomTkinter Date Picker (No Quick Presets)

**Date:** 2026-09-07  
**Status:** Approved by User  
**Scope:** DEV mode only (no Nuitka build)

---

## 1. Objectives & Requirements
1. **Interactive Date Picker Widget (`ui/components/date_picker.py`)**:
   - Clean, lightweight modal calendar popup built purely with CustomTkinter (`CTkToplevel`).
   - Month/Year navigation: `◀` (Previous Month), `▶` (Next Month), Month Name, Year.
   - 7x6 calendar day grid (Monday through Sunday) for selecting a single date.
   - When a user clicks a day button, it automatically formats the date to `DD/MM/YYYY`, sets it to the target field/variable, and closes the popup.
   - Matches the dark/light theme of the application.
   - Pure Python / CustomTkinter with standard `datetime` and `calendar` modules (no third-party packages, 100% clean for later Nuitka build).
2. **Explicitly Excluded**:
   - NO Quick Presets (no "วันนี้", "7 วัน", "30 วัน" shortcut buttons per user request).
3. **Integration Points**:
   - **PLC Manager View (`ui/views/plc_manager_view.py`)**:
     - Inside `open_plc_dialog`, beside `start_entry` and `end_entry`, add a `📅` button.
     - Clicking `📅` opens `DatePickerPopup`.
     - Selecting a date fills the respective entry (`DD/MM/YYYY`).
   - **Dashboard View (`ui/views/dashboard_view.py`)**:
     - On each PLC row/card, allow modifying the date filter without going to PLC Manager.
     - Clicking the date badge or a small `📅` button opens a quick modal dialog to change the date filter (`All Files` vs `Date Range` with Start/End date pickers).
     - Saves to config and immediately refreshes the active badge and downloader filter.
4. **Dev Workflow**:
   - Develop and verify in DEV mode (`python main.py`).
   - Do NOT run Nuitka standalone build.

---

## 2. Architecture & Components

### 2.1 `ui/components/date_picker.py`
- `DatePickerPopup(ctk.CTkToplevel)`:
  - Constructor: `DatePickerPopup(parent, initial_date=None, on_select=None)`
  - Window properties:
    - Title: "เลือกวันที่"
    - `transient(parent)`
    - `grab_set()` (modal)
    - Resizable: False
    - Geometry: ~300x320 px, centered relative to parent.
  - UI Elements:
    - Header frame:
      - `btn_prev = ctk.CTkButton(..., text="◀", width=32)`
      - `lbl_month_year = ctk.CTkLabel(..., text="กันยายน 2026", font=...)`
      - `btn_next = ctk.CTkButton(..., text="▶", width=32)`
    - Day names header:
      - Mon, Tue, Wed, Thu, Fri, Sat, Sun (or จ., อ., พ., พฤ., ศ., ส., อา.)
    - Day buttons grid:
      - Calculated using Python's standard `calendar.Calendar().monthdayscalendar(year, month)`.
      - Click on day: `on_select(f"{day:02d}/{month:02d}/{year:04d}")` and `destroy()`.
      - Today button at the bottom (optional convenient "วันนี้" jump inside the calendar, or just standard calendar days).

- `QuickDateFilterDialog(ctk.CTkToplevel)`:
  - Takes `parent`, `plc_name`, `current_filter`, `on_save_callback`.
  - Radio buttons: `All Files` vs `Date Range`.
  - Start Date Entry + `📅` button, End Date Entry + `📅` button.
  - Save button: Validates format and range (`start <= end`), calls `on_save_callback(new_filter)`, closes dialog.

### 2.2 Integration in `ui/views/plc_manager_view.py`
- In `open_plc_dialog`, layout `start_entry` and `end_entry` inside a sub-frame with a `📅` button next to each entry.
- Clicking the button opens `DatePickerPopup(dialog, initial_date=..., on_select=lambda d: ...)`.

### 2.3 Integration in `ui/views/dashboard_view.py`
- In `_render_plc_cards`, add a click action to the date filter badge or an adjacent `📅` button.
- Clicking opens `QuickDateFilterDialog`.
- On save, updates the PLC's `date_filter` in `self.config["plcs"]`, saves via `config_service.save_config`, updates badge text and download parameters.

---

## 3. Verification Plan
- Verify `DatePickerPopup` standalone rendering and date selection.
- Verify `QuickDateFilterDialog` saves and propagates to `config.json`.
- Run application in dev mode via `.\venv\Scripts\python.exe main.py`.
