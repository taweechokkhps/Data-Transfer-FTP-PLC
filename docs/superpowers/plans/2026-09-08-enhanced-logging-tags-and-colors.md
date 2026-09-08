# Enhanced Logging Tags & Colors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement distinct log prefixes (`[INFO]`, `[SUCCESS]`, `[ERROR]`, `[WARNING]`, `[SWITCH MODE]`) with dynamic color highlighting across the UI Log Console and file logging.

**Architecture:** Extend `core/logger.py` to support canonical level tags and smart keyword fallback detection. Update `ui/components/log_console.py` with CTkTextbox tags for distinct hex colors. Update `core/ftp_service.py` and `ui/views/dashboard_view.py` to emit level-aware events.

**Tech Stack:** Python 3.12, CustomTkinter (CTkTextbox color tagging), standard `logging`.

## Global Constraints
- Run in DEV mode only (`python main.py`, Python 3.12).
- File logging path: `logs/app.log`.
- All log lines formatted as: `[{timestamp}] [{TAG}] {message}`.
- Colors:
  - `[INFO]`: `#64B5F6`
  - `[SUCCESS]`: `#00E676`
  - `[ERROR]`: `#FF5252`
  - `[WARNING]`: `#FFB74D`
  - `[SWITCH MODE]`: `#E040FB`

---

### Task 1: Extend Logger with Canonical Tags and `switch_mode` (TDD)

**Files:**
- Modify: `tests/test_config_and_logger.py`
- Modify: `core/logger.py`

**Interfaces:**
- Produces: `logger.switch_mode(msg)`, `logger.log(msg, level)`, formatted UI lines `[{timestamp}] [{TAG}] {msg}`.

- [ ] **Step 1: Write failing unit test for canonical log tags and `switch_mode`**

In `tests/test_config_and_logger.py`, add tests for `logger.switch_mode` and formatted tag output:

```python
def test_logger_tags_and_switch_mode():
    logs = []
    def cb(formatted_ui, level):
        logs.append((formatted_ui, level))

    logger.register_callback(cb)
    logger.info("Normal info message")
    logger.success("Operation succeeded")
    logger.error("Operation failed")
    logger.warning("Caution advised")
    logger.switch_mode("Switched from PASV to PORT")
    logger.unregister_callback(cb)

    assert len(logs) == 5
    assert "[INFO]" in logs[0][0] and logs[0][1] == "info"
    assert "[SUCCESS]" in logs[1][0] and logs[1][1] == "success"
    assert "[ERROR]" in logs[2][0] and logs[2][1] == "error"
    assert "[WARNING]" in logs[3][0] and logs[3][1] == "warning"
    assert "[SWITCH MODE]" in logs[4][0] and logs[4][1] == "switch_mode"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_config_and_logger.py`
Expected: FAIL (missing `logger.switch_mode` or missing `[TAG]` in formatted string)

- [ ] **Step 3: Implement canonical tagging in `core/logger.py`**

In `core/logger.py`:
- Add `switch_mode(self, message: str)`
- Normalize level into canonical tag:
  - `"info"` -> `"INFO"`
  - `"success"` -> `"SUCCESS"`
  - `"error"` -> `"ERROR"`
  - `"warning"` -> `"WARNING"`
  - `"switch_mode"` / `"switch mode"` -> `"SWITCH MODE"`
- Smart keyword fallback if `level` is `"info"` or None:
  - If `"error"` or `"failed"` in message.lower() -> tag = `"ERROR"`, level = `"error"`
  - If `"502"` in message or `"switching to active"` in message.lower() -> tag = `"SWITCH MODE"`, level = `"switch_mode"`
  - If `"downloaded"` in message.lower() or `"converted"` in message.lower() or `"success"` in message.lower() -> tag = `"SUCCESS"`, level = `"success"`
- Format UI message as: `f"[{timestamp}] [{tag}] {clean_msg}"`

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_config_and_logger.py`
Expected: PASS

- [ ] **Step 5: Commit Task 1**

```bash
git add tests/test_config_and_logger.py core/logger.py
git commit -m "feat(logger): add canonical log tags and switch_mode method"
```

---

### Task 2: Update `LogConsole` Color Highlighting

**Files:**
- Modify: `ui/components/log_console.py`

**Interfaces:**
- Consumes: `cb(formatted_ui, level)` from `logger`
- Displays: Colorized tags in CTkTextbox.

- [ ] **Step 1: Configure tag styles and parsing in `ui/components/log_console.py`**

In `ui/components/log_console.py`:
- Add tag configurations:
  ```python
  self.textbox.tag_config("info", foreground="#64B5F6")
  self.textbox.tag_config("success", foreground="#00E676")
  self.textbox.tag_config("error", foreground="#FF5252")
  self.textbox.tag_config("warning", foreground="#FFB74D")
  self.textbox.tag_config("switch_mode", foreground="#E040FB")
  ```
- In `append_message(message: str, level: str = None)`:
  - Normalize level: if level is None, extract tag from `message` (e.g. `[SUCCESS]` -> `"success"`, `[SWITCH MODE]` -> `"switch_mode"`, `[ERROR]` -> `"error"`).
  - Insert with matching tag style.

- [ ] **Step 2: Verify syntax**

Run: `python -m py_compile ui/components/log_console.py`
Expected: exit code 0

- [ ] **Step 3: Commit Task 2**

```bash
git add ui/components/log_console.py
git commit -m "feat(ui): add color highlighting for all log tags in LogConsole"
```

---

### Task 3: Emit Level-Aware Logs in FTP Service and Dashboard View

**Files:**
- Modify: `core/ftp_service.py`
- Modify: `ui/views/dashboard_view.py`

**Interfaces:**
- Calls: `log_callback(msg, level)` and `logger.switch_mode`, `logger.success`, `logger.error`.

- [ ] **Step 1: Update `core/ftp_service.py` to emit level-aware logs**

In `core/ftp_service.py`:
- When switching to Active mode on 502:
  ```python
  if log_callback:
      log_callback(f"[{self.plc_name}] Notice: 502 PASV not implemented. Switching to Active (PORT) mode.", "switch_mode")
  logger.switch_mode(f"[{self.plc_name}] Switching to Active (PORT) mode due to 502 PASV error.")
  ```
- When downloaded file:
  ```python
  log_callback(f"[{self.plc_name}][{m_name}] Downloaded {pure_filename} ({f_size_kb:.1f} KB) in {f_dur_ms:.1f} ms", "success")
  ```
- When converted to CSV:
  ```python
  log_callback(f"[{self.plc_name}][{m_name}] Converted to csv/{csv_filename} ({row_count} rows) in {conv_ms:.1f} ms", "success")
  ```
- When batch completed:
  ```python
  log_callback(f"[{self.plc_name}] Download process completed in {dur_str} ({current_index}/{total_files} files).", "success")
  ```
- When download / directory error occurs:
  ```python
  log_callback(f"[{self.plc_name}][{m_name}] Error downloading {filename}: {e}", "error")
  ```

- [ ] **Step 2: Update `log_cb` in `ui/views/dashboard_view.py`**

In `ui/views/dashboard_view.py`:
```python
def log_cb(msg, level=None):
    self.after(0, lambda: logger.log(msg, level=level))
```

- [ ] **Step 3: Verify all test cases pass**

Run: `python -m unittest discover -s tests`
Expected: 0 failures, exit code 0

- [ ] **Step 4: Commit Task 3**

```bash
git add core/ftp_service.py ui/views/dashboard_view.py
git commit -m "feat(ftp): emit level-aware log events for downloads, conversions, and mode switches"
```

---

### Task 4: Final Integration Verification

- [ ] **Step 1: Run comprehensive tests and syntax verification**

Run:
```bash
python -m py_compile main.py core/logger.py core/ftp_service.py ui/components/log_console.py ui/views/dashboard_view.py
python -m unittest discover -s tests
```
Expected: All pass.

- [ ] **Step 2: Commit plan completion**
