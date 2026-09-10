# Design Spec: Download ETA & Remaining Files Display (Format B-2)

## 1. Overview
Provide an accurate, compact, and responsive real-time indicator of remaining files and estimated time remaining (ETA) on the PLC card during FTP downloads, using the compact "Format B-2".

Format: `{current}/{total} ({pct}%) • เหลือ {remaining} ({eta_str})`
Example: `150/430 (35%) • เหลือ 280 (~3m)`

---

## 2. Calculation Logic (`core/ftp_service.py`)

### 2.1 Accounting for Skipped / Duplicate Files
- Files previously downloaded are skipped near-instantaneously (within ~0.05s).
- Counting skipped files into download speed calculations would severely distort ETA (predicting 0s remaining for real downloads).
- Therefore, ETA is calculated **strictly from actual file transfer times** over the FTP network:
  - `actual_durations: list[float] = []`: Appends the duration (seconds) of each file downloaded over FTP.
  - `remaining = total_files - current_index`: Files still remaining in the queue.

### 2.2 ETA Estimator Algorithm
- **Warm-up Phase (`len(actual_durations) < 2`):**
  - Displays `คำนวณ...` to avoid jumpy or misleading numbers while the first file or two is downloading.
- **Stable Phase (`len(actual_durations) >= 2`):**
  - Uses the sliding average of the last 10 downloaded files:
    `avg_sec = sum(actual_durations[-10:]) / len(actual_durations[-10:])`
  - `eta_sec = remaining * avg_sec`
  - If `eta_sec >= 60`:
    `mins = max(1, round(eta_sec / 60))`
    `eta_str = f"~{mins}m"`
  - If `eta_sec < 60`:
    `secs = max(1, int(eta_sec))`
    `eta_str = f"~{secs}s"`

### 2.3 Progress Callback Signature
- To maintain backwards compatibility while passing rich progress metadata:
  ```python
  def _emit_progress(cb, current, total, remaining=0, eta_str=""):
      if not cb:
          return
      try:
          cb(current, total, remaining=remaining, eta_str=eta_str)
      except TypeError:
          try:
              cb(current, total)
          except Exception:
              pass
  ```

---

## 3. UI Implementation (`ui/views/dashboard_view.py`)

### 3.1 Counter Label Layout
- Location: Row 1, Column 2 of `mid_row` (between Progress Bar and Timer).
- `counter_lbl`:
  - Set `width=200` (or `width=210`) with `anchor="e"`.
  - Column 1 (`pb`) has `weight=1`, allowing the progress bar to absorb any extra card width flexibly.

### 3.2 State-Driven Text Formatting
1. **Initial / Connecting:** `Connecting to FTP...`
2. **Skipping duplicates only (0 actual files to download):** `Files up to date` / finished.
3. **Downloading (Warm-up):**
   `{current}/{total} ({pct}%) • เหลือ {remaining} (คำนวณ...)`
4. **Downloading (Active ETA):**
   `{current}/{total} ({pct}%) • เหลือ {remaining} ({eta_str})`
   e.g. `150/430 (35%) • เหลือ 280 (~3m)`
5. **Completed:**
   `Completed in {time_str}`
6. **Stopped / Cancelled:**
   `Cancelled`

---

## 4. Verification & Testing
1. Unit tests in `tests/`:
   - Verify ETA calculation helper with various inputs (0 files, 1 file, 10 files, >= 60s, < 60s).
   - Verify `_emit_progress` handles both 2-arg and 4-arg callbacks cleanly without errors.
2. Regression testing:
   - Run `python -m unittest discover -s tests` to ensure all existing 27 tests continue to pass.
