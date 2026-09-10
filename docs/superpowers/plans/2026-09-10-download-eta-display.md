# Download ETA & Remaining Files Display (Format B-2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add real-time estimated remaining time (ETA) and remaining files counter formatted as Format B-2 (`150/430 (35%) • เหลือ 280 (~3m)`) on the PLC card during download.

**Architecture:** A lightweight helper function `calculate_download_eta(remaining, actual_durations)` in `core/ftp_service.py` computes ETA using a sliding average of the last 10 actual network transfer durations (excluding skipped files). The `_emit_progress` utility communicates this safely to `ui/views/dashboard_view.py`, where `counter_lbl` formats the text cleanly without overflowing.

**Tech Stack:** Python 3.12, CustomTkinter, unittest

## Global Constraints
- Format: `{current}/{total} ({pct}%) • เหลือ {remaining} ({eta_str})` (e.g. `150/430 (35%) • เหลือ 280 (~3m)`)
- Do not count skipped/duplicate files into transfer duration calculations.
- Warm-up period: Show `คำนวณ...` for the first 1-2 files until duration average stabilizes.
- Preserve backward compatibility with any 2-argument `progress_callback(current, total)`.
- All UI widget calls must remain thread-safe (`winfo_exists()`, `try...except`, `safe_after`).

---

### Task 1: ETA Calculation Helper & Rich Progress Callback

**Files:**
- Modify: `core/ftp_service.py`
- Test: `tests/test_ftp_service.py`

**Interfaces:**
- Produces: `calculate_download_eta(remaining: int, actual_durations: list[float]) -> str`
- Produces: `_emit_progress(cb, current: int, total: int, remaining: int = 0, eta_str: str = "")`

- [ ] **Step 1: Write unit tests for `calculate_download_eta` and `_emit_progress`**

Add tests to `tests/test_ftp_service.py`:
```python
def test_calculate_download_eta_warmup(self):
    from core.ftp_service import calculate_download_eta
    # 0 or 1 file downloaded -> warm-up
    self.assertEqual(calculate_download_eta(remaining=10, actual_durations=[]), "คำนวณ...")
    self.assertEqual(calculate_download_eta(remaining=10, actual_durations=[1.0]), "คำนวณ...")

def test_calculate_download_eta_minutes_and_seconds(self):
    from core.ftp_service import calculate_download_eta
    # 20 files remaining, average 10s per file -> 200s -> ~3m
    self.assertEqual(calculate_download_eta(remaining=20, actual_durations=[10.0, 10.0]), "~3m")
    # 2 files remaining, average 15s per file -> 30s -> ~30s
    self.assertEqual(calculate_download_eta(remaining=2, actual_durations=[15.0, 15.0]), "~30s")
    # 0 files remaining -> empty
    self.assertEqual(calculate_download_eta(remaining=0, actual_durations=[1.0, 1.0]), "")

def test_emit_progress_backwards_compatible(self):
    from core.ftp_service import _emit_progress
    # 2-arg callback
    called_2 = []
    _emit_progress(lambda c, t: called_2.append((c, t)), 10, 20, 10, "~1m")
    self.assertEqual(called_2, [(10, 20)])

    # 4-arg keyword callback
    called_4 = []
    def rich_cb(c, t, remaining=0, eta_str=""):
        called_4.append((c, t, remaining, eta_str))
    _emit_progress(rich_cb, 10, 20, 10, "~1m")
    self.assertEqual(called_4, [(10, 20, 10, "~1m")])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_ftp_service.py`
Expected: FAIL with `ImportError: cannot import name 'calculate_download_eta'`

- [ ] **Step 3: Implement `calculate_download_eta`, `_emit_progress`, and integrate in `core/ftp_service.py`**

In `core/ftp_service.py`:
```python
def calculate_download_eta(remaining: int, actual_durations: list[float]) -> str:
    """Calculates compact ETA string using sliding average of recent actual download times."""
    if remaining <= 0:
        return ""
    if len(actual_durations) < 2:
        return "คำนวณ..."
    # Sliding average of up to 10 most recent downloaded files
    recent = actual_durations[-10:]
    avg_sec = sum(recent) / len(recent)
    eta_sec = remaining * avg_sec
    if eta_sec >= 60:
        mins = max(1, round(eta_sec / 60))
        return f"~{mins}m"
    secs = max(1, int(eta_sec))
    return f"~{secs}s"

def _emit_progress(cb, current: int, total: int, remaining: int = 0, eta_str: str = ""):
    if not cb:
        return
    try:
        cb(current, total, remaining=remaining, eta_str=eta_str)
    except TypeError:
        try:
            cb(current, total, remaining, eta_str)
        except TypeError:
            try:
                cb(current, total)
            except Exception:
                pass
```

In `FTPDownloader.download_files()`:
- Initialize `actual_durations = []`
- When duplicate files are skipped:
  `remaining_files = max(0, total_files - current_index)`
  `_emit_progress(progress_callback, current_index, total_files, remaining_files, calculate_download_eta(remaining_files, actual_durations))`
- When a file finishes downloading:
  `actual_durations.append(f_dur_ms / 1000.0)`
  `remaining_files = max(0, total_files - current_index)`
  `_emit_progress(progress_callback, current_index, total_files, remaining_files, calculate_download_eta(remaining_files, actual_durations))`

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_ftp_service.py`
Expected: PASS (all tests in test_ftp_service pass)

- [ ] **Step 5: Commit changes**

```bash
git add core/ftp_service.py tests/test_ftp_service.py
git commit -m "feat(ftp): add calculate_download_eta and rich progress callback"
```

---

### Task 2: Dashboard UI Counter Label Format B-2

**Files:**
- Modify: `ui/views/dashboard_view.py`

**Interfaces:**
- Consumes: `update_progress(current, total, remaining=0, eta_str="")`
- Produces: Formatted UI text in `counter_lbl`:
  `{current}/{total} ({pct}%) • เหลือ {remaining} ({eta_str})`

- [ ] **Step 1: Update `counter_lbl` layout and `update_progress` in `ui/views/dashboard_view.py`**

In `ui/views/dashboard_view.py`:
1. In `refresh_plcs`:
   Change `counter_lbl` width from `140` to `210` (or `220`) with `anchor="e"` so B-2 format has sufficient room:
   ```python
   counter_lbl = ctk.CTkLabel(
       mid_row,
       text="พร้อมดาวน์โหลด",
       width=210,
       anchor="e",
       font=ctk.CTkFont(size=11),
       text_color=("#888888", "#757575")
   )
   ```
2. In `download_single`:
   Update `update_progress` callback signature:
   ```python
   def update_progress(current, total, remaining=0, eta_str=""):
       prog = current / total if total > 0 else 0
       pct = int(prog * 100)
       def _up():
           try:
               if progress_bar and progress_bar.winfo_exists():
                   progress_bar.set(prog)
               if counter_label and counter_label.winfo_exists():
                   if remaining > 0 and eta_str:
                       counter_label.configure(text=f"{current}/{total} ({pct}%) • เหลือ {remaining} ({eta_str})")
                   else:
                       counter_label.configure(text=f"{current} / {total} files ({pct}%)")
           except Exception:
               pass
       self.safe_after(0, _up)
   ```

- [ ] **Step 2: Run full unit test suite**

Run: `python -m unittest discover -s tests`
Expected: ALL PASS

- [ ] **Step 3: Commit changes**

```bash
git add ui/views/dashboard_view.py
git commit -m "feat(ui): display remaining files and ETA in counter label (Format B-2)"
```

---

### Task 3: Full Verification & Live Test

**Files:**
- Test all components with automated test suite

- [ ] **Step 1: Run complete test suite**

Run: `python -m unittest discover -s tests`
Expected: Ran 30 tests, ALL PASS.

- [ ] **Step 2: Verify git status and clean working tree**

Run: `git status`
Expected: Clean working tree on branch main.
