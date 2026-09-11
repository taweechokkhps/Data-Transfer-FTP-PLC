# Clean Views & MVC Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the UI layer (`ui/`) into a clean Model-View-Controller (MVC) architecture by separating business logic/threads into `ui/controllers/`, extracting popup dialogs to `ui/components/`, and keeping `ui/views/` purely as presentation layouts.

**Architecture:** Popup dialogs (`QuickDateFilterDialog`, `PLCModalDialog`) move to `ui/components/`. Action handling, validation, threading, and state orchestration move to dedicated controllers in `ui/controllers/` (`DashboardController`, `PLCManagerController`, `SettingsController`). The view classes (`DashboardView`, `PLCManagerView`, `SettingsView`) become lightweight UI builders that delegate user actions to their respective controllers.

**Tech Stack:** Python 3.12, CustomTkinter, standard library (`threading`, `queue`).

## Global Constraints
- Zero visual and behavioral regression (identical UI layout, fonts, colors, and workflows).
- Thread-safety preserved: all UI updates from background threads must use `safe_after` on the main thread.
- Python standard library and existing dependencies only (offline environment).

---

### Task 1: Extract Dialog Components to `ui/components/`

**Files:**
- Create: `ui/components/quick_date_filter_dialog.py`
- Create: `ui/components/plc_modal_dialog.py`
- Modify: `ui/components/__init__.py`
- Modify: `ui/views/dashboard_view.py`
- Modify: `ui/views/plc_manager_view.py`

**Interfaces:**
- Produces: `QuickDateFilterDialog(parent, plc_name, current_filter, on_save_callback)`
- Produces: `PLCModalDialog(parent, config_manager, plc_data=None, index=None, on_save_callback=None)`

- [x] **Step 1: Create `ui/components/quick_date_filter_dialog.py`**

Extract `QuickDateFilterDialog` from `ui/views/dashboard_view.py` (lines 35-180) into standalone component file with its imports.

- [x] **Step 2: Create `ui/components/plc_modal_dialog.py`**

Extract `PLCModalDialog` from `ui/views/plc_manager_view.py` (lines 270-550) into standalone component file with its imports.

- [x] **Step 3: Update `ui/components/__init__.py`**

Export `QuickDateFilterDialog` and `PLCModalDialog` from `ui/components`.

- [x] **Step 4: Update imports in `dashboard_view.py` and `plc_manager_view.py`**

Import `QuickDateFilterDialog` in `dashboard_view.py` and `PLCModalDialog` in `plc_manager_view.py`.

- [x] **Step 5: Run unit tests to verify no import regressions**

Run: `python -m unittest discover -s tests`
Expected: ALL PASS

- [x] **Step 6: Commit Task 1**

```bash
git add ui/components/ ui/views/
git commit -m "refactor(components): extract QuickDateFilterDialog and PLCModalDialog to ui/components"
```

---

### Task 2: Implement Settings & PLC Manager Controllers

**Files:**
- Create: `ui/controllers/__init__.py`
- Create: `ui/controllers/settings_controller.py`
- Create: `ui/controllers/plc_manager_controller.py`
- Create: `tests/test_controllers.py`
- Modify: `ui/views/settings_view.py`
- Modify: `ui/views/plc_manager_view.py`

**Interfaces:**
- Produces: `SettingsController(config_manager, logger)` with `save_settings(data)`, `reset_defaults()`, `browse_target_dir()`
- Produces: `PLCManagerController(config_manager, logger)` with `validate_plc(data)`, `delete_plc(index)`, `test_connection(host, port, user, pwd, timeout, mode)`

- [x] **Step 1: Write unit tests for `SettingsController` and `PLCManagerController`**

In `tests/test_controllers.py`:
- Test settings validation and save logic
- Test PLC validation (validating host, port, machine names)
- Test PLC delete logic

- [x] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests/test_controllers.py`
Expected: FAIL (modules not found)

- [x] **Step 3: Implement `SettingsController` and `PLCManagerController`**

Create `ui/controllers/settings_controller.py` and `ui/controllers/plc_manager_controller.py`.

- [x] **Step 4: Refactor `settings_view.py` and `plc_manager_view.py` to use controllers**

Delegate action events in `SettingsView` and `PLCManagerView` to their respective controllers.

- [x] **Step 5: Run tests to verify they pass**

Run: `python -m unittest discover -s tests`
Expected: ALL PASS

- [x] **Step 6: Commit Task 2**

```bash
git add ui/controllers/ ui/views/ tests/test_controllers.py
git commit -m "refactor(controllers): implement SettingsController and PLCManagerController"
```

---

### Task 3: Implement Dashboard Controller & Refactor `dashboard_view.py`

**Files:**
- Create: `ui/controllers/dashboard_controller.py`
- Modify: `ui/controllers/__init__.py`
- Modify: `tests/test_controllers.py`
- Modify: `ui/views/dashboard_view.py`

**Interfaces:**
- Produces: `DashboardController(config_manager, logger)` with `download_single(...)`, `download_all(...)`, `stop_all(...)`, `test_connection(...)`

- [x] **Step 1: Add unit tests for `DashboardController` in `tests/test_controllers.py`**

Test single download coordination, state tracking, and stop handling.

- [x] **Step 2: Implement `DashboardController` in `ui/controllers/dashboard_controller.py`**

Move `download_single`, `download_all`, `download_selected_lines`, `test_single_connection`, and timer tracking from `dashboard_view.py` into `DashboardController`.

- [x] **Step 3: Refactor `dashboard_view.py`**

Clean up `dashboard_view.py` to focus solely on building the card layouts, progress bars, and wiring buttons to `self.controller`.

- [x] **Step 4: Run full unit test suite**

Run: `python -m unittest discover -s tests`
Expected: ALL PASS

- [x] **Step 5: Commit Task 3**

```bash
git add ui/controllers/ ui/views/dashboard_view.py tests/test_controllers.py
git commit -m "refactor(controllers): implement DashboardController and decouple dashboard_view"
```

---

### Task 4: Full Regression & Integration Verification

- [x] **Step 1: Run complete test suite**

Run: `python -m unittest discover -s tests`
Expected: ALL PASS

- [x] **Step 2: Verify git status and diff**

Ensure all new and modified files are committed and clean.

- [x] **Step 3: Update documentation and artifacts**

Update `task.md` with refactoring summary and architectural metrics.
