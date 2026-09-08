# Auto Pull Completion-Based Countdown Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure the Auto Pull countdown starts only AFTER all selected production lines finish downloading and converting, preventing overlap and ensuring accurate cooldown timing.

**Architecture:** Add `on_finish_callback` to `download_single` and batch counter completion to `download_selected_lines` in `ui/views/dashboard_view.py`. Update `ui/app.py` to track `is_auto_pulling` and start the timer only on completion.

**Tech Stack:** Python 3.12, CustomTkinter, threading.

## Global Constraints
- Run in DEV mode only (`python main.py`).
- No changes to FTP connection logic or file formats.
- Cooldown label shows `"Auto Pull: In Progress (กำลังดึงข้อมูล...)"` while downloading.
- Next cycle timer starts only when `on_complete` fires.

---

### Task 1: Add Completion Tracking to `dashboard_view.py`

**Files:**
- Modify: `ui/views/dashboard_view.py`

**Interfaces:**
- `download_single(..., on_finish_callback=None)`
- `download_selected_lines(target_line_names=None, on_complete=None)`
- `download_all(on_complete=None)`

- [ ] **Step 1: Update `download_single` to accept and invoke `on_finish_callback`**

In `ui/views/dashboard_view.py`:
- In `download_single(self, plc_data, progress_bar, status_label, timer_label=None, counter_label=None, action_button=None, on_finish_callback=None)`:
  - In `run()` thread's `finally:` block, invoke `if on_finish_callback: self.after(0, on_finish_callback)`.

- [ ] **Step 2: Update `download_selected_lines` to track batch completion**

In `ui/views/dashboard_view.py`:
- In `download_selected_lines(self, target_line_names=None, on_complete=None)`:
  - Determine list of target triggers.
  - If no triggers: invoke `if on_complete: on_complete()` immediately.
  - Track `remaining = [len(active_triggers)]` with a lock or thread-safe counter.
  - When each line finishes:
    - Decrement remaining count.
    - When remaining reaches 0: invoke `if on_complete: self.after(0, on_complete)`.

- [ ] **Step 3: Verify syntax**

Run: `python -m py_compile ui/views/dashboard_view.py`
Expected: exit code 0

- [ ] **Step 4: Commit Task 1**

```bash
git add ui/views/dashboard_view.py
git commit -m "feat(dashboard): add completion callback tracking to line downloads"
```

---

### Task 2: Implement Completion-Based Auto Pull in `ui/app.py`

**Files:**
- Modify: `ui/app.py`

**Interfaces:**
- `trigger_auto_pull()` passes `on_complete` to `download_selected_lines`.
- `update_cooldown_ui()` displays in-progress status when `is_auto_pulling=True`.

- [ ] **Step 1: Update `trigger_auto_pull` and `update_cooldown_ui` in `ui/app.py`**

In `ui/app.py`:
- Initialize `self.is_auto_pulling = False` in `__init__`.
- In `trigger_auto_pull()`:
  - If `self.is_auto_pulling`:
    - `logger.warning("[Auto Pull] Skipped: Previous pull cycle is still in progress.")`
    - return
  - Set `self.is_auto_pulling = True`
  - Stop countdown while downloading: `self.next_pull_time = 0`
  - Define `on_all_finished()`:
    - `self.is_auto_pulling = False`
    - `logger.info("[Auto Pull] All lines completed. Starting countdown for next cycle.")`
    - `self.start_auto_pull_timer()`
  - Call `self.dashboard_view.download_selected_lines(target_lines, on_complete=on_all_finished)`
- In `update_cooldown_ui()`:
  - If `self.is_auto_pulling`:
    - Set label text: `"Auto Pull: In Progress (กำลังดึงข้อมูล...)"` with color `#FFA726` (orange).

- [ ] **Step 2: Verify syntax and existing tests**

Run:
```bash
python -m py_compile ui/app.py
python -m unittest discover -s tests
```
Expected: All pass.

- [ ] **Step 3: Commit Task 2**

```bash
git add ui/app.py
git commit -m "feat(app): trigger countdown only after auto pull downloads complete"
```

---

### Task 3: Integration Verification

- [ ] **Step 1: Test simulated batch download with completion callback**
- [ ] **Step 2: Run full test suite and verify clean working tree**
