# CustomTkinter Date Picker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a native CustomTkinter calendar popup widget and integrate it into PLC Manager (Add/Edit dialog) and Dashboard (Overview) for one-click date filter modification in DEV mode.

**Architecture:** A lightweight `DatePickerPopup` modal class inside `ui/components/date_picker.py` using Python's built-in `calendar` and `datetime` libraries, styled to match CustomTkinter dark/light theme. A companion `QuickDateFilterDialog` modal for editing line date filters directly from Dashboard.

**Tech Stack:** Python 3.12, CustomTkinter 6.0.0, standard `calendar` and `datetime` libraries.

## Global Constraints
- Pure CustomTkinter (zero extra external packages like tkcalendar or babel).
- No Quick Presets buttons (explicitly excluded by user).
- DEV mode only: verify with python `main.py`, DO NOT run Nuitka build.
- Exact date string format: `DD/MM/YYYY`.

---

### Task 1: DatePickerPopup Component (`ui/components/date_picker.py`)

**Files:**
- Create: `ui/components/date_picker.py`
- Create: `tests/test_date_picker.py`

**Interfaces:**
- Produces: `DatePickerPopup(parent, initial_date=None, on_select=None)`
  - `initial_date`: `str` ("DD/MM/YYYY") or `None`
  - `on_select`: Callable `callback(date_str: str)` receiving `"DD/MM/YYYY"`

- [ ] **Step 1: Write test for date helper logic**
Create `tests/test_date_picker.py` testing calendar day matrix generation and date string formatting.

- [ ] **Step 2: Run test to verify it fails**
Run: `.\venv\Scripts\python.exe tests/test_date_picker.py`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement DatePickerPopup in `ui/components/date_picker.py`**
Implement modal `DatePickerPopup(ctk.CTkToplevel)` with navigation buttons (`◀`, `▶`), month/year label, day header row (จ., อ., พ., พฤ., ศ., ส., อา.), and day grid.

- [ ] **Step 4: Run tests to verify they pass**
Run: `.\venv\Scripts\python.exe tests/test_date_picker.py`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add ui/components/date_picker.py tests/test_date_picker.py
git commit -m "feat: implement DatePickerPopup component in CustomTkinter"
```

---

### Task 2: QuickDateFilterDialog Component (`ui/components/date_picker.py`)

**Files:**
- Modify: `ui/components/date_picker.py`
- Modify: `tests/test_date_picker.py`

**Interfaces:**
- Produces: `QuickDateFilterDialog(parent, plc_name: str, current_filter: dict, on_save: callable)`
  - `current_filter`: `{"mode": "all"|"range", "start_date": "DD/MM/YYYY", "end_date": "DD/MM/YYYY"}`
  - `on_save`: `callback(updated_filter: dict)`

- [ ] **Step 1: Write test for filter validation helper**
Add validation test for date range in `tests/test_date_picker.py`.

- [ ] **Step 2: Implement QuickDateFilterDialog in `ui/components/date_picker.py`**
Build modal dialog with Mode radio buttons (`All Files` / `Date Range`), Start/End entry with `📅` button opening `DatePickerPopup`, Save and Cancel buttons.

- [ ] **Step 3: Run test to verify it passes**
Run: `.\venv\Scripts\python.exe tests/test_date_picker.py`
Expected: PASS

- [ ] **Step 4: Commit**
```bash
git add ui/components/date_picker.py tests/test_date_picker.py
git commit -m "feat: implement QuickDateFilterDialog modal"
```

---

### Task 3: Integrate Date Picker into PLC Manager Dialog (`ui/views/plc_manager_view.py`)

**Files:**
- Modify: `ui/views/plc_manager_view.py`

**Interfaces:**
- Consumes: `DatePickerPopup` from `ui.components.date_picker`

- [ ] **Step 1: Update Add/Edit Line dialog in `plc_manager_view.py`**
In `open_plc_dialog()`, wrap `start_entry` and `end_entry` with horizontal sub-frames and add a `📅` button next to each entry that opens `DatePickerPopup`.

- [ ] **Step 2: Verify syntax and behavior**
Run: `.\venv\Scripts\python.exe -c "import ui.views.plc_manager_view; print('PLC Manager View OK')"`
Expected: `PLC Manager View OK`

- [ ] **Step 3: Commit**
```bash
git add ui/views/plc_manager_view.py
git commit -m "feat: add date picker popup button in PLC Manager dialog"
```

---

### Task 4: Integrate Quick Date Filter into Dashboard View (`ui/views/dashboard_view.py`)

**Files:**
- Modify: `ui/views/dashboard_view.py`

**Interfaces:**
- Consumes: `QuickDateFilterDialog` from `ui.components.date_picker`

- [ ] **Step 1: Make Date Filter badge clickable or add `📅` button in Dashboard row**
In `ui/views/dashboard_view.py`, update `_render_plc_cards` to make the date badge an interactive button or attach a `📅` icon button that opens `QuickDateFilterDialog`. On save, update `self.config["plcs"]`, invoke `config_service.save_config`, and refresh the row's badge and downloader filter.

- [ ] **Step 2: Verify syntax and behavior**
Run: `.\venv\Scripts\python.exe -c "import ui.views.dashboard_view; print('Dashboard View OK')"`
Expected: `Dashboard View OK`

- [ ] **Step 3: Commit**
```bash
git add ui/views/dashboard_view.py
git commit -m "feat: enable direct date filter modification from Dashboard"
```

---

### Task 5: Comprehensive DEV Mode Verification

**Files:**
- Test all components and integration in DEV mode.

- [ ] **Step 1: Run full test suite**
Run: `.\venv\Scripts\python.exe tests/test_path_utils.py; .\venv\Scripts\python.exe tests/test_config_and_logger.py; .\venv\Scripts\python.exe tests/test_ftp_service.py; .\venv\Scripts\python.exe tests/test_date_picker.py`
Expected: ALL TESTS PASSED

- [ ] **Step 2: Launch application in DEV mode for smoke test**
Run: `powershell -Command "Start-Process .\venv\Scripts\python.exe -ArgumentList 'main.py'"`
Verify UI opens and runs cleanly.
