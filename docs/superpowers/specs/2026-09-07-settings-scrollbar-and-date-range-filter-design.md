# Design Specification: Settings Scrollbar, PLC Date Range Filter & Batch Folder Structure

- **Date:** 2026-09-07
- **Version:** v1.2.0
- **Status:** Approved by User

---

## 1. Overview & Goals
The objective of this design is to resolve UI overflow in Settings and provide high-performance date-targeted downloads from Keyence PLCs / FTP servers:
1. **Settings View Scrollbar:** Convert settings cards container into a scrollable frame with a pinned bottom save bar, preventing overflow on small displays.
2. **PLC Manager Date Range Filter:** Allow users to configure download date ranges (`All Files` vs `Date Range: DD/MM/YYYY - DD/MM/YYYY`) per PLC line inside the Add/Edit Line dialog.
3. **Filename Date Parsing & Filtering:** Decode date from standard PLC log filenames (e.g. `020425.txt` -> 02/04/2025) to avoid downloading unnecessary historical logs when thousands of files exist.
4. **Structured Batch Folders:** Organize downloaded files into clear date range subdirectories:
   - Date range mode: `Target / <PLC_Name> / <Machine_Name> / (<start_date> - <end_date>) / <filename>`
   - All files mode: `Target / <PLC_Name> / <Machine_Name> / (<min_date> - <max_date>) ALL / <filename>`
5. **Overview (Dashboard) Visibility:** Display active date filter badges on each PLC card before downloading.

---

## 2. Architecture & Components

### 2.1 Core Layer

#### `core/path_utils.py`
- Add `parse_date_from_filename(filename: str) -> datetime.date | None`:
  - Matches 6-digit prefix pattern: `^(\d{2})(\d{2})(\d{2})\.` (DDMMYY)
  - Computes year `2000 + int(yy)`, month `int(mm)`, day `int(dd)`
  - Returns `datetime.date` or `None` if invalid/not matching.
- Add `format_batch_save_dir(base_dir: str, plc_name: str, machine_name: str, batch_folder_name: str) -> Path`:
  - Builds path: `Path(base_dir) / plc_name / machine_name / batch_folder_name`
  - Ensures directory exists.

#### `core/config_service.py`
- Update PLC data schema to support `date_filter`:
  ```json
  {
      "name": "LINE 1",
      "host": "192.168.1.169",
      "port": 21,
      "username": "user",
      "password": "...",
      "machines": [...],
      "date_filter": {
          "mode": "all",
          "start_date": "",
          "end_date": ""
      }
  }
  ```
- Default for `date_filter`: `{"mode": "all", "start_date": "", "end_date": ""}`.

#### `core/ftp_service.py`
- In `FTPDownloader`:
  - Accept `date_filter: dict = None`.
  - In `download_files()`:
    1. Filter target files based on `date_filter`:
       - If `mode == "range"`: parse `start_date` and `end_date` (`DD/MM/YYYY`). Only include files where `parse_date_from_filename(f)` falls within `[start_date, end_date]`.
       - If `mode == "all"`: include all files matching target file extensions.
    2. Determine batch folder name:
       - If `mode == "range"`: `f"({start_date.strftime('%d-%m-%Y')} - {end_date.strftime('%d-%m-%Y')})"`
       - If `mode == "all"`: find min and max date among matching files:
         - If dates exist: `f"({min_date.strftime('%d-%m-%Y')} - {max_date.strftime('%d-%m-%Y')}) ALL"`
         - Fallback if no dates parsed: `"(ALL_FILES)"`
    3. Save files to `format_batch_save_dir(self.local_target_dir, self.plc_name, m_name, batch_folder_name)`.

---

### 2.2 UI Layer

#### `ui/views/settings_view.py`
- Change `cards_container` from `ctk.CTkFrame` to `ctk.CTkScrollableFrame` with transparent background.
- Keep `save_bar` pinned at the bottom of `self`, outside the scrollable frame, ensuring the Save button is always accessible without scrolling.

#### `ui/views/plc_manager_view.py`
- In `open_plc_dialog`:
  - Add **📅 Download Date Filter** section:
    - Radio buttons: `All Files (ดาวน์โหลดทั้งหมด)` vs `Date Range (เลือกช่วงวันที่)`
    - If `Date Range` selected: show `Start Date (DD/MM/YYYY)` and `End Date (DD/MM/YYYY)` text entries.
    - Validate date string format before saving.
  - Save `date_filter` into PLC object.
  - In `refresh_list`: display summary of date filter in PLC summary row.

#### `ui/views/dashboard_view.py`
- In `refresh_plcs()`:
  - Add a visible badge on each PLC row displaying its active date filter:
    - e.g. `[ 📅 01/04/2025 - 15/04/2025 ]` or `[ 📅 All Files ]`.
  - Pass `plc.get("date_filter")` to `FTPDownloader`.
- Log console shows the applied date filter and matching file count.

---

## 3. Error Handling & Edge Cases
1. **Invalid Date Format in Input:** Validate `DD/MM/YYYY` using `datetime.strptime(s, "%d/%m/%Y")`. If invalid, show alert and prevent saving invalid ranges.
2. **Start Date > End Date:** Automatically swap or show warning if start date is after end date.
3. **Files without Date in Name:** In "range" mode, files without valid dates are skipped so only intended dates are pulled. In "all" mode, all files are downloaded into `(ALL_FILES)`.
4. **Zero Matching Files:** Log clear message: `No files found matching the date range <start> to <end>` without failing or throwing exceptions.

---

## 4. Verification Plan
1. Unit tests in `tests/test_path_utils.py` for `parse_date_from_filename()` and `format_batch_save_dir()`.
2. Integration test in `tests/test_ftp_service.py` downloading files with Date Range filter and All Files filter.
3. Verify Settings view scrollbar in CTk UI.
4. Verify standalone binary compilation (`FTP_Control.exe`) with cleanup of build directories.
