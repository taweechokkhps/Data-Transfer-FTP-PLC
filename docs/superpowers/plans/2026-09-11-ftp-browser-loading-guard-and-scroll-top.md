# FTP Browser Loading Guard & Auto-Scroll to Top Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enhance `FTPBrowserDialog` to disable directory selection and navigation while loading from PLC, and automatically scroll to the top whenever entering or loading a directory.

**Architecture:** Add state tracking (`is_loading`) in `FTPBrowserDialog` to govern button states (`btn_select`, navigation buttons), and implement `_reset_scroll_to_top()` targeting the underlying canvas of `content_frame`.

**Tech Stack:** Python 3.12, CustomTkinter, standard library (`unittest`).

## Global Constraints
- Zero visual regression; maintain existing colors, padding, and layout geometry.
- Offline environment: use only existing standard library and installed dependencies.
- Thread-safe GUI updates via `self.after(0, ...)`.

---

### Task 1: Implement Loading Guard, Control States, and Auto-Scroll to Top in `FTPBrowserDialog`

**Files:**
- Modify: `ui/components/ftp_browser_dialog.py`
- Test: `tests/test_ftp_browser_dialog.py`

**Interfaces:**
- Produces: `FTPBrowserDialog.is_loading: bool`
- Produces: `FTPBrowserDialog._reset_scroll_to_top() -> None`
- Produces: `FTPBrowserDialog._set_nav_state(enabled: bool) -> None`

- [ ] **Step 1: Write tests in `tests/test_ftp_browser_dialog.py`**

Test cases:
- `test_dialog_loading_state_disables_select_button`: Verifies that while loading, `btn_select` is disabled and text is `"⏳ Loading..."`.
- `test_dialog_load_success_enables_select_button`: Verifies that `_on_load_success` re-enables `btn_select` and resets scroll to top.
- `test_dialog_load_fail_keeps_select_button_disabled`: Verifies that `_on_load_fail` keeps `btn_select` disabled.
- `test_dialog_select_current_blocked_while_loading`: Verifies calling `select_current()` while `is_loading` is True does NOT trigger `on_select_callback`.
- `test_reset_scroll_to_top`: Verifies `_reset_scroll_to_top` calls `yview_moveto(0.0)`.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_ftp_browser_dialog`
Expected: FAIL (methods / attributes not implemented yet)

- [ ] **Step 3: Implement Loading Guard & Auto-Scroll in `FTPBrowserDialog`**

In `ui/components/ftp_browser_dialog.py`:
- In `__init__`:
  - Store button references: `self.btn_up`, `self.btn_root`, `self.btn_go`, `self.btn_refresh`.
  - Initialize `self.is_loading = False`.
- Add helper `_reset_scroll_to_top(self)`:
  ```python
  def _reset_scroll_to_top(self):
      try:
          if hasattr(self, "content_frame") and hasattr(self.content_frame, "_parent_canvas"):
              self.content_frame._parent_canvas.yview_moveto(0.0)
      except Exception:
          pass
  ```
- Add helper `_set_controls_loading_state(self, is_loading: bool)`:
  - Updates `self.is_loading = is_loading`
  - When `is_loading`:
    - `btn_select` -> `state="disabled"`, `text="⏳ Loading..."`
    - `btn_up`, `btn_root`, `btn_go`, `btn_refresh`, `path_entry` -> `state="disabled"`
  - When not `is_loading`:
    - `btn_up`, `btn_root`, `btn_go`, `btn_refresh`, `path_entry` -> `state="normal"`
- In `load_directory(self, target_dir)`:
  - Set loading state: `self._set_controls_loading_state(True)`
  - Call `self._reset_scroll_to_top()`
- In `_on_load_success(self, data)`:
  - Set loading state: `self._set_controls_loading_state(False)`
  - Configure `self.btn_select`: `state="normal"`, `text="✓ Select This Directory"`
  - Call `self._reset_scroll_to_top()` and `self.after(20, self._reset_scroll_to_top)`
- In `_on_load_fail(self, err_msg, failed_dir=None)`:
  - Set loading state: `self._set_controls_loading_state(False)`
  - Keep `self.btn_select`: `state="disabled"`, `text="✓ Select This Directory"`
- In `select_path` and `select_current`:
  - Guard check: `if self.is_loading: return`

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_ftp_browser_dialog`
Expected: ALL PASS

- [ ] **Step 5: Commit Task 1**

```bash
git add ui/components/ftp_browser_dialog.py tests/test_ftp_browser_dialog.py
git commit -m "feat(ui): add loading guard and auto-scroll top to FTP browser dialog"
```

---

### Task 2: Full Regression & Integration Verification

- [ ] **Step 1: Run complete test suite**

Run: `python -m unittest discover -s tests`
Expected: ALL PASS (all 47+ tests)

- [ ] **Step 2: Verify git status and diff**

Ensure clean working directory.
