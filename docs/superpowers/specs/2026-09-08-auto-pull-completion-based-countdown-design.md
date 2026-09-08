# Design Spec: Auto Pull Completion-Based Countdown

**Date:** 2026-09-08  
**Status:** Approved by User  
**Scope:** DEV mode only (`python main.py`, Python 3.12)

---

## 1. Objectives & Requirements
1. **Completion-Based Countdown Timing**:
   - The countdown timer for Auto Pull must NOT run while downloads are actively in progress.
   - The countdown for the next auto pull cycle must start **only after all selected production lines have completely finished downloading and converting files**.
2. **Prevent Overlapping Pulls (Overlap Protection)**:
   - If an Auto Pull cycle is currently in progress, any subsequent timer or trigger must not launch duplicate concurrent downloads.
   - Introduce `is_auto_pulling` lock/flag in `FTPControlApp`.
3. **Clear UI Status Indication**:
   - While downloading: Cooldown label displays `"Auto Pull: In Progress (กำลังดึงข้อมูล...)"`.
   - After all lines complete: Cooldown label starts countdown from the full configured interval (e.g., `Next Auto Pull in: 01:00`).

---

## 2. Architecture & Components

### 2.1 `ui/views/dashboard_view.py`
- Update `download_single(..., on_finish_callback=None)`:
  - In `run()` thread's `finally:` block, invoke `on_finish_callback()` via `self.after(0, ...)`.
- Update `download_selected_lines(target_line_names=None, on_complete=None)`:
  - Track active lines count using `threading.Lock` and counter `finished_count`.
  - When all selected lines finish execution, invoke `on_complete()`.
- Update `download_all(on_complete=None)`:
  - Supports `on_complete` callback similarly when all lines finish.

### 2.2 `ui/app.py`
- Add attribute `self.is_auto_pulling = False`.
- In `trigger_auto_pull()`:
  - If `self.is_auto_pulling`: Log warning and do not trigger.
  - Set `self.is_auto_pulling = True`.
  - Set `self.next_pull_time = 0` (stops countdown while downloading).
  - Define `on_all_finished()`:
    - Sets `self.is_auto_pulling = False`.
    - Logs completion notice.
    - Calls `self.start_auto_pull_timer()`.
  - Call `self.dashboard_view.download_selected_lines(target_lines, on_complete=on_all_finished)`.
- In `update_cooldown_ui()`:
  - If `self.is_auto_pulling`: display `"Auto Pull: In Progress (กำลังดาวน์โหลด...)"`.
  - If enabled and `self.next_pull_time > 0`: display remaining time as `Next Auto Pull in: MM:SS`.

---

## 3. Verification Plan
1. **Syntax and Unit Tests**:
   - `python -m py_compile main.py ui/app.py ui/views/dashboard_view.py`
   - `python -m unittest discover -s tests`
2. **Integration Verification**:
   - Simulate multi-line download completion flow.
   - Verify that countdown resets and starts only after `on_all_finished` is called.
