# Duplicate IP Prevention & Per-Host Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent socket connection collisions on PLC devices by strictly prohibiting duplicate IP addresses in the PLC configuration form, and providing a per-host lock queue at runtime so that downloads to the same host run sequentially without connection clash.

**Architecture:** Form validation in `PLCManagerController` rejects duplicate `(host, port)` and `name`. Runtime concurrency in `DashboardController` utilizes a per-host `threading.Lock` registry: lines with different IPs download concurrently (parallel), while lines sharing an IP wait in queue with clear UI status ("● In Queue").

**Tech Stack:** Python 3.12, standard library (`threading`, `unittest`).

## Global Constraints
- Zero visual regression; keep all existing layout geometry, fonts, and colors intact.
- Thread-safe UI updates via `safe_after`.
- Standard library and existing dependencies only (offline environment).

---

### Task 1: Strict Form Validation for Duplicate IP & Line Name in `PLCManagerController`

**Files:**
- Modify: `ui/controllers/plc_manager_controller.py`
- Modify: `ui/components/plc_modal_dialog.py`
- Test: `tests/test_controllers.py`

**Interfaces:**
- Produces: `PLCManagerController.validate_plc(data: Dict[str, Any], edit_index: Optional[int] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]`
- Produces: `PLCManagerController.add_plc(plc_data: Dict[str, Any]) -> Tuple[bool, str]`
- Produces: `PLCManagerController.update_plc(index: int, plc_data: Dict[str, Any]) -> Tuple[bool, str]`

- [ ] **Step 1: Write failing tests in `tests/test_controllers.py`**

Add tests to `TestPLCManagerController`:
- `test_validate_plc_duplicate_ip`: Rejects adding a new PLC with an existing host and port.
- `test_validate_plc_duplicate_name`: Rejects adding a new PLC with an existing line name.
- `test_validate_plc_edit_self_allowed`: Allows saving when `edit_index` matches the existing PLC (editing self).

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_controllers.TestPLCManagerController`
Expected: FAIL (duplicate checks not implemented yet)

- [ ] **Step 3: Implement duplicate checks in `PLCManagerController` and `PLCModalDialog`**

In `ui/controllers/plc_manager_controller.py`:
- Update `validate_plc(self, data, edit_index=None)`:
  - Retrieve existing PLCs from `self.get_plcs()`.
  - Check if any other PLC (`i != edit_index`) has matching `name.lower()` -> return `(False, "Line / PLC Name '{line_name}' is already used by another Line.", None)`.
  - Check if any other PLC (`i != edit_index`) has matching `(host.lower(), port)` -> return `(False, "IP Address '{host}:{port}' is already used by '{other_name}'. Duplicate IP is not allowed to prevent connection collisions.", None)`.
- Update `add_plc`: calls `self.validate_plc(plc_data, edit_index=None)`.
- Update `update_plc`: calls `self.validate_plc(plc_data, edit_index=index)`.

In `ui/components/plc_modal_dialog.py`:
- Ensure `self.edit_index` is passed to `controller.update_plc(self.edit_index, new_data)` or `controller.add_plc(new_data)`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_controllers.TestPLCManagerController`
Expected: ALL PASS

- [ ] **Step 5: Commit Task 1**

```bash
git add ui/controllers/plc_manager_controller.py ui/components/plc_modal_dialog.py tests/test_controllers.py
git commit -m "feat(plc-manager): prevent duplicate IP and line name in form validation"
```

---

### Task 2: Implement Per-Host Concurrency Lock & Queue in `DashboardController`

**Files:**
- Modify: `ui/controllers/dashboard_controller.py`
- Modify: `ui/views/dashboard_view.py`
- Test: `tests/test_controllers.py`

**Interfaces:**
- Produces: `DashboardController.get_host_lock(host: str) -> threading.Lock`
- Produces: `DashboardController.download_single(...)` with `on_queue` callback for queue status.

- [ ] **Step 1: Write unit tests in `tests/test_controllers.py`**

Add tests to `TestDashboardController`:
- `test_get_host_lock_singleton`: Verifies that calling `get_host_lock` with the same host returns the identical `threading.Lock` instance.
- `test_same_host_downloads_run_sequentially`: Two downloads to the same host execute one after another without concurrent execution.
- `test_different_host_downloads_run_concurrently`: Two downloads to different hosts execute concurrently.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_controllers.TestDashboardController`
Expected: FAIL (host lock methods not found)

- [ ] **Step 3: Implement Per-Host Lock in `DashboardController` & UI wiring in `DashboardView`**

In `ui/controllers/dashboard_controller.py`:
- Initialize `self._host_locks: Dict[str, threading.Lock] = {}` and `self._host_locks_mutex = threading.Lock()`.
- Add method `get_host_lock(self, host: str) -> threading.Lock`.
- In `download_single(self, plc_data, ...)`:
  - Extract `host = plc_data.get("host", "").strip()`.
  - Before entering download work in background thread:
    - Get `host_lock = self.get_host_lock(host)`.
    - If `host_lock.locked()`: call `on_queue(host)`.
    - `with host_lock:`
      - Proceed with `downloader.download_files(...)`.

In `ui/views/dashboard_view.py`:
- Wire `on_queue` callback in `download_single`:
  - Update `status_label.configure(text="● In Queue", text_color="#FFA726")`
  - Update `counter_label.configure(text=f"Waiting for PLC ({host}) to be free...")`

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_controllers.TestDashboardController`
Expected: ALL PASS

- [ ] **Step 5: Commit Task 2**

```bash
git add ui/controllers/dashboard_controller.py ui/views/dashboard_view.py tests/test_controllers.py
git commit -m "feat(download): add per-host lock queue to eliminate connection collisions"
```

---

### Task 3: Full Regression & Integration Verification

- [ ] **Step 1: Run complete test suite**

Run: `python -m unittest discover -s tests`
Expected: ALL PASS

- [ ] **Step 2: Verify git status and diff**

Ensure all changes are clean and committed.

- [ ] **Step 3: Update documentation and artifacts**

Update `task.md` with features and verification status.
