# Design Spec: Enhanced Logging Tags & Color Highlights

**Date:** 2026-09-08  
**Status:** Approved by User  
**Scope:** DEV mode only (`python main.py`, Python 3.12)

---

## 1. Objectives & Requirements
1. **Log Tag Prefixes**:
   - Provide distinct standardized prefixes in all log lines:
     - `[INFO]` — General operational events, app startup, setting updates, directory selection.
     - `[SUCCESS]` — File downloaded, CSV converted, connection test passed, download batch completed.
     - `[ERROR]` — Connection failure, download failure, directory access denied, conversion error.
     - `[WARNING]` — Skipped operations, empty directory warnings, unselected lines in Auto Pull.
     - `[SWITCH MODE]` — FTP connection automatically switching from Passive (PASV) to Active (PORT) mode upon receiving error `502`.
2. **Log Formatting Consistency**:
   - UI format: `[{timestamp}] [{TAG}] {message}`
   - File log format (`logs/app.log`): `[{asctime}] [{LEVEL}] {message}`
3. **UI Log Console Color Highlighting (`ui/components/log_console.py`)**:
   - `[INFO]`: Sky Blue (`#64B5F6`)
   - `[SUCCESS]`: Bright Green (`#00E676`)
   - `[ERROR]`: Vivid Red (`#FF5252`)
   - `[WARNING]`: Amber Orange (`#FFB74D`)
   - `[SWITCH MODE]`: Neon Purple (`#E040FB`)
4. **Backward Compatibility & Smart Level Detection**:
   - `logger.log(msg, level)` accepts standard levels (`"info"`, `"success"`, `"error"`, `"warning"`, `"switch mode"`).
   - If a plain string is received without an explicit level (e.g. from third-party callbacks), logger performs smart keyword detection (`502`/`switching` -> `switch mode`, `error`/`failed` -> `error`, `downloaded`/`converted`/`completed` -> `success`).

---

## 2. Architecture & Components

### 2.1 `core/logger.py`
- Add dedicated helper methods:
  - `logger.switch_mode(message: str)`
  - `logger.success(message: str)`
  - `logger.info(message: str)`
  - `logger.warning(message: str)`
  - `logger.error(message: str)`
- Update `log(message: str, level: str = "info")`:
  - Normalize level to canonical tag: `"INFO"`, `"SUCCESS"`, `"ERROR"`, `"WARNING"`, `"SWITCH MODE"`.
  - Format UI line: `[{timestamp}] [{canonical_tag}] {clean_message}`
  - File logger: map `"switch mode"` and `"success"` to `logging.INFO` with clear message tag.
  - Broadcast `cb(formatted_ui, canonical_level)`.

### 2.2 `ui/components/log_console.py`
- Register CTkTextbox tags:
  - `self.textbox.tag_config("info", foreground="#64B5F6")`
  - `self.textbox.tag_config("success", foreground="#00E676")`
  - `self.textbox.tag_config("error", foreground="#FF5252")`
  - `self.textbox.tag_config("warning", foreground="#FFB74D")`
  - `self.textbox.tag_config("switch_mode", foreground="#E040FB")`
- In `append_message(message: str, level: str = None)`:
  - Match level or inspect `[TAG]` token at beginning of message.
  - Insert message into textbox tagged with the matching color style.

### 2.3 `core/ftp_service.py`
- Update log emissions in `FTPDownloader`:
  - 502 PASV mode switch: `log_callback(f"[{self.plc_name}] Notice: 502 PASV not implemented. Switching to Active (PORT) mode.", "switch_mode")`
  - Downloaded file: `log_callback(..., "success")`
  - Converted CSV: `log_callback(..., "success")`
  - Batch completed: `log_callback(..., "success")`
  - Download / access errors: `log_callback(..., "error")`

### 2.4 `ui/views/dashboard_view.py`
- Update `log_cb(msg, level=None)`:
  - Forward both `msg` and `level` directly to `logger.log(msg, level=level or "info")`.

---

## 3. Verification Plan
1. **Unit Tests (`tests/test_config_and_logger.py`)**:
   - Verify `logger.switch_mode`, `logger.success`, `logger.info`, `logger.warning`, `logger.error`.
   - Verify that UI callback receives correct timestamped format `[HH:MM:SS.mmm] [TAG] ...` and level tag.
2. **Syntax and Integration**:
   - Run `python -m py_compile` across all files.
   - Run `python -m unittest discover -s tests`.
