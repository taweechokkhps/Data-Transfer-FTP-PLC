# Design Spec: FTP Browser Loading Guard & Auto-Scroll to Top

## Overview
Improve the Remote PLC FTP Browser Dialog (`ui/components/ftp_browser_dialog.py`) used in the PLC Manager view when browsing remote directories. Specifically:
1. Prevent premature directory selection by disabling the Select / OK button and navigation buttons while fetching directory contents.
2. Automatically reset the scrollbar position to the very top whenever navigating into a new directory or loading directory contents.

---

## 1. Problem Statement
1. **Premature Selection Issue:**
   When clicking "Browse" or navigating into directories on a remote PLC, network round-trips over FTP take time (especially on industrial fieldbuses or remote networks). During this loading period, the "✓ Select This Directory" button remained enabled. If clicked while loading or in an error state, an empty or unverified directory path could be returned to the PLC form, causing invalid configurations.
2. **Scroll Position Retention Issue:**
   When a directory has many folders or files, the user scrolls down to find a folder and clicks it. In Tkinter/CustomTkinter `CTkScrollableFrame`, the underlying canvas does not reset its vertical scroll view (`yview`) when child widgets are replaced. As a result, when the new directory loads, the view remains stuck scrolled down in the middle or bottom, forcing the user to manually scroll back up to see the top folders.

---

## 2. Proposed Architecture & Solution

### A. Loading Guard & Button State Management
In `FTPBrowserDialog`:
- Maintain a state variable `self.is_loading: bool = False`.
- Reference navigation controls: `self.btn_up`, `self.btn_root`, `self.btn_go`, `self.btn_refresh`, `self.path_entry`, and `self.btn_select`.
- **When `load_directory(target_dir)` starts:**
  - Set `self.is_loading = True`.
  - Update `self.status_label` to `"Loading..."` (`#FFA726`).
  - Disable `self.btn_select`: `configure(state="disabled", text="⏳ Loading...")`.
  - Disable navigation buttons: `self.btn_up`, `self.btn_root`, `self.btn_go`, `self.btn_refresh`, and disable `self.path_entry`.
  - Trigger `self._reset_scroll_to_top()`.
- **When loading succeeds (`_on_load_success`):**
  - Set `self.is_loading = False`.
  - Re-enable `self.btn_select`: `configure(state="normal", text="✓ Select This Directory")`.
  - Re-enable navigation buttons: `btn_up` (enabled only if not at root), `btn_root`, `btn_go`, `btn_refresh`, and `path_entry`.
  - Update `self.status_label` to show count.
  - Trigger `self._reset_scroll_to_top()` both immediately and after a short 20ms Tkinter geometry layout pass (`self.after(20, self._reset_scroll_to_top)`).
- **When loading fails (`_on_load_fail`):**
  - Set `self.is_loading = False`.
  - Keep `self.btn_select` disabled: `configure(state="disabled", text="✓ Select This Directory")`.
  - Re-enable navigation buttons so the user can go up, go to root, or retry.
- **In `select_current()` / `select_path(path)`:**
  - Guard: If `self.is_loading`, return early and do not trigger `self.on_select_callback`.

### B. Auto-Scroll to Top (`_reset_scroll_to_top`)
In `FTPBrowserDialog`:
- Implement a helper method `_reset_scroll_to_top(self)`:
  ```python
  def _reset_scroll_to_top(self):
      try:
          if hasattr(self, "content_frame") and hasattr(self.content_frame, "_parent_canvas"):
              self.content_frame._parent_canvas.yview_moveto(0.0)
      except Exception:
          pass
  ```
- Called in `load_directory` when clearing previous children and showing the loading label.
- Called in `_on_load_success` immediately after packing folder and file rows.
- Scheduled with `self.after(20, self._reset_scroll_to_top)` to ensure after Tkinter layout geometry update, the scrollbar sits reliably at `0.0`.

---

## 3. Testing & Verification
1. **Unit tests:**
   - Verify `FTPBrowserDialog` disables `btn_select` and navigation controls when loading starts.
   - Verify `FTPBrowserDialog` re-enables `btn_select` upon `_on_load_success`.
   - Verify `FTPBrowserDialog` keeps `btn_select` disabled upon `_on_load_fail`.
   - Verify `_reset_scroll_to_top` calls `yview_moveto(0.0)`.
   - Verify `select_current` does not trigger callback while `is_loading` is `True`.
2. **Regression testing:**
   - Run `python -m unittest discover -s tests` to ensure 100% pass across all 47 existing tests.
