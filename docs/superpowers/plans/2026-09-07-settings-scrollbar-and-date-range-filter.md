# Settings Scrollbar, PLC Date Range Filter & Batch Folder Structure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement scrollable Settings layout, PLC line date range filter (All vs Range), filename date decoding (`020425.txt`), and batch folder generation (`Target / Line / MC / (DateRange) / files`).

**Architecture:** Extend `core/path_utils.py` with filename date parsing and batch folder formatting. Update `core/config_service.py` with `date_filter` on PLCs. Enhance `core/ftp_service.py` to filter remote files by date and save to batch directories. Update `ui/views/settings_view.py` with `CTkScrollableFrame` and pinned save bar. Update `ui/views/plc_manager_view.py` with date range radio/entries in Edit dialog. Update `ui/views/dashboard_view.py` with filter badges.

**Tech Stack:** Python 3.12, CustomTkinter, ftplib, pytest/unittest, Nuitka.

## Global Constraints
- Do not introduce comma-separated inputs anywhere in the UI.
- All temporary Nuitka build folders (`main.build/`, `main.dist/`, `main.onefile-build/`) must be removed after build.
- Preserve backward-compatibility shims.
- Date input format in UI: `DD/MM/YYYY`.
- Filename date format: `DDMMYY` prefix (e.g. `020425.txt` -> 02/04/2025).

---

### Task 1: Core Date Utilities and Batch Folder Formatting

**Files:**
- Modify: `core/path_utils.py`
- Test: `tests/test_path_utils.py`

**Interfaces:**
- Produces:
  - `parse_date_from_filename(filename: str) -> datetime.date | None`
  - `format_batch_save_dir(base_dir: str, plc_name: str, machine_name: str, batch_folder_name: str) -> Path`

- [ ] **Step 1: Write failing unit test in `tests/test_path_utils.py`**

```python
def test_parse_date_from_filename():
    from core.path_utils import parse_date_from_filename
    import datetime
    assert parse_date_from_filename("020425.txt") == datetime.date(2025, 4, 2)
    assert parse_date_from_filename("311224.csv") == datetime.date(2024, 12, 31)
    assert parse_date_from_filename("invalid.txt") is None
    assert parse_date_from_filename("999999.txt") is None

def test_format_batch_save_dir(tmp_path):
    from core.path_utils import format_batch_save_dir
    p = format_batch_save_dir(str(tmp_path), "LINE 1", "MC1", "(01-04-2025 - 15-04-2025)")
    assert p == tmp_path / "LINE 1" / "MC1" / "(01-04-2025 - 15-04-2025)"
    assert p.exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\venv\Scripts\python.exe tests/test_path_utils.py`
Expected: FAIL (ImportError / AttributeError `parse_date_from_filename`)

- [ ] **Step 3: Implement functions in `core/path_utils.py`**

```python
def parse_date_from_filename(filename: str) -> datetime.date | None:
    """
    Parse date from filename with DDMMYY format (e.g. 020425.txt -> 2025-04-02).
    """
    m = re.match(r'^(\d{2})(\d{2})(\d{2})', Path(filename).name)
    if not m:
        return None
    dd, mm, yy = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        year = 2000 + yy
        return datetime.date(year, mm, dd)
    except ValueError:
        return None

def format_batch_save_dir(base_dir: str, plc_name: str, machine_name: str, batch_folder_name: str) -> Path:
    """
    Format local batch save directory: base_dir / plc_name / machine_name / batch_folder_name
    """
    target = Path(base_dir) / plc_name / machine_name / batch_folder_name
    target.mkdir(parents=True, exist_ok=True)
    return target
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\venv\Scripts\python.exe tests/test_path_utils.py`
Expected: `ALL TESTS PASSED!`

- [ ] **Step 5: Commit**

```bash
git add core/path_utils.py tests/test_path_utils.py
git commit -m "feat: add parse_date_from_filename and format_batch_save_dir"
```

---

### Task 2: Config Service PLC Date Filter Schema

**Files:**
- Modify: `core/config_service.py`
- Test: `tests/test_config_and_logger.py`

**Interfaces:**
- Consumes: PLC dictionary in `config.json`
- Produces: `plc.get("date_filter", {"mode": "all", "start_date": "", "end_date": ""})`

- [ ] **Step 1: Write test for PLC date_filter migration and retrieval**

```python
def test_plc_date_filter_default():
    cm = ConfigManager()
    plcs = cm.get().get("plcs", [])
    if plcs:
        assert "date_filter" in plcs[0]
```

- [ ] **Step 2: Run test to verify current state**

Run: `.\venv\Scripts\python.exe tests/test_config_and_logger.py`

- [ ] **Step 3: Update `core/config_service.py` `load_config`**

Ensure every PLC in `data["plcs"]` has a valid `date_filter`:
```python
if "date_filter" not in plc:
    plc["date_filter"] = {"mode": "all", "start_date": "", "end_date": ""}
    needs_save = True
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\venv\Scripts\python.exe tests/test_config_and_logger.py`
Expected: `CONFIG AND LOGGER TESTS PASSED!`

- [ ] **Step 5: Commit**

```bash
git add core/config_service.py tests/test_config_and_logger.py
git commit -m "feat: add date_filter default to PLC configuration"
```

---

### Task 3: FTP Service Date Range Filter & Batch Directory Support

**Files:**
- Modify: `core/ftp_service.py`
- Test: `tests/test_ftp_service.py`

**Interfaces:**
- Consumes: `date_filter: dict` passed to `FTPDownloader`
- Produces: Filtered file download into `(start - end)` or `(min - max) ALL` batch directory.

- [ ] **Step 1: Write test in `tests/test_ftp_service.py` testing date filtering logic**

Test filtering with mock filenames `010525.txt`, `020525.txt`, `150525.txt` with range `01/05/2025` - `05/05/2025`.

- [ ] **Step 2: Run test to verify it fails**

Run: `.\venv\Scripts\python.exe tests/test_ftp_service.py`

- [ ] **Step 3: Update `FTPDownloader` in `core/ftp_service.py`**

1. Accept `date_filter: dict = None` in `__init__`.
2. In `download_files`:
   - Parse `date_filter`: `mode = self.date_filter.get("mode", "all")`.
   - If `mode == "range"`:
     Parse `start_date` and `end_date` using `datetime.strptime(s, "%d/%m/%Y").date()`.
     Filter `t_files`: only keep `f` if `parse_date_from_filename(f)` is between `start_date` and `end_date`.
     Compute batch folder name: `f"({start_date.strftime('%d-%m-%Y')} - {end_date.strftime('%d-%m-%Y')})"`.
   - If `mode == "all"`:
     Keep all `t_files`.
     Find min and max date among `t_files` using `parse_date_from_filename(f)`.
     If found: `f"({min_d.strftime('%d-%m-%Y')} - {max_d.strftime('%d-%m-%Y')}) ALL"`.
     Else: `"(ALL_FILES)"`.
   - Use `save_dir = format_batch_save_dir(self.local_target_dir, self.plc_name, m_name, batch_folder_name)` to save files.

- [ ] **Step 4: Run test to verify it passes**

Run: `.\venv\Scripts\python.exe tests/test_ftp_service.py`
Expected: `FTP SERVICE TESTS PASSED!`

- [ ] **Step 5: Commit**

```bash
git add core/ftp_service.py tests/test_ftp_service.py
git commit -m "feat: implement date range file filtering and batch folder creation in FTPDownloader"
```

---

### Task 4: Settings View Scrollbar & Layout Optimization

**Files:**
- Modify: `ui/views/settings_view.py`

**Interfaces:**
- Produces: Non-overflowing scrollable settings interface with pinned bottom save bar.

- [ ] **Step 1: Update `build_view()` in `ui/views/settings_view.py`**

1. Change `cards_container` from `ctk.CTkFrame` to `ctk.CTkScrollableFrame(self, fg_color="transparent")`.
2. Pack `cards_container` with `pack(fill="both", expand=True, padx=20, pady=(0, 10))`.
3. Keep `save_bar` packed at bottom outside the scrollable frame so it never scrolls out of view.

- [ ] **Step 2: Test rendering SettingsView**

Run: `.\venv\Scripts\python.exe -c "from ui.views.settings_view import SettingsView; print('SettingsView loaded')"`

- [ ] **Step 3: Commit**

```bash
git add ui/views/settings_view.py
git commit -m "feat: add scrollbar and pinned save bar to Settings view"
```

---

### Task 5: PLC Manager Date Range Configuration in Dialog

**Files:**
- Modify: `ui/views/plc_manager_view.py`

**Interfaces:**
- Produces: Date range selection (`All Files` vs `Date Range`) in Add/Edit PLC dialog, and badge summary in PLC list.

- [ ] **Step 1: Add Date Filter Section to `open_plc_dialog`**

1. Add a new card/section: **📅 Download Filter (การเลือกไฟล์ดาวน์โหลด)**.
2. Radio buttons for mode: `All Files (ดาวน์โหลดทั้งหมด)` vs `Date Range (เลือกช่วงวันที่)`.
3. When `Date Range` selected, enable start date (`DD/MM/YYYY`) and end date (`DD/MM/YYYY`) entries.
4. Validate date inputs upon `save()`.
5. Save `date_filter` into PLC object.

- [ ] **Step 2: Display Date Filter in `refresh_list()` summary**

In the PLC table, display `All Files` or `01/04/2025 - 15/04/2025`.

- [ ] **Step 3: Test PLC dialog import and rendering**

Run: `.\venv\Scripts\python.exe -c "from ui.views.plc_manager_view import PLCManagerView; print('PLCManagerView loaded')"`

- [ ] **Step 4: Commit**

```bash
git add ui/views/plc_manager_view.py
git commit -m "feat: add date filter configuration to PLC Manager dialog"
```

---

### Task 6: Overview (Dashboard) Date Filter Badge & Download Execution

**Files:**
- Modify: `ui/views/dashboard_view.py`

**Interfaces:**
- Consumes: `plc["date_filter"]`
- Produces: Visual date badge on each PLC row and passing `date_filter` to `FTPDownloader`.

- [ ] **Step 1: Update `refresh_plcs()` in `ui/views/dashboard_view.py`**

1. For each PLC row, display a date filter badge:
   - If `mode == "range"`: `f"📅 {df.get('start_date')} - {df.get('end_date')}"`
   - Else: `📅 All Files`
2. In `download_single()`: pass `date_filter=plc_data.get("date_filter")` to `FTPDownloader`.

- [ ] **Step 2: Test live download with date range**

Run test script with date range filter on live FTP server (`192.168.1.169`).

- [ ] **Step 3: Commit**

```bash
git add ui/views/dashboard_view.py
git commit -m "feat: display date filter badge in dashboard and pass to downloader"
```

---

### Task 7: Full Verification & Standalone Binary Compilation

**Files:**
- Rebuild: `FTP_Control.exe`
- Clean: `main.build/`, `main.dist/`, `main.onefile-build/`

- [ ] **Step 1: Run all unit and integration test suites**

Run: `.\venv\Scripts\python.exe tests/test_path_utils.py; .\venv\Scripts\python.exe tests/test_config_and_logger.py; .\venv\Scripts\python.exe tests/test_ftp_service.py`
Expected: 100% PASS.

- [ ] **Step 2: Compile with Nuitka**

Run: `.\venv\Scripts\python.exe -m nuitka --onefile --output-filename=FTP_Control.exe ... main.py`

- [ ] **Step 3: Clean temporary build directories**

Run: `Remove-Item -Recurse -Force main.build, main.dist, main.onefile-build`

- [ ] **Step 4: Commit and finalize**

```bash
git add FTP_Control.exe config.json
git commit -m "build: compile FTP_Control.exe with date range filter and scrollable settings"
```
