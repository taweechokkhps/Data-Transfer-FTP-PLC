# Enhanced Duplicate File & Download Logging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide clear logging when duplicate files are skipped (as a concise summary) and explicit progression logs for files being downloaded.

**Architecture:** In `core/ftp_service.py` (`FTPDownloader.download_files`), partition candidate files into skipped (existing unchanged files) and to_download files. Emit summary log for skipped files and informative per-file download logs for new files.

**Tech Stack:** Python 3.12, ftplib, unittest

## Global Constraints
- DEV mode only (`python main.py`, Python 3.12, no Nuitka compilation).
- Preserves all existing logging levels and tags (`[INFO]`, `[SUCCESS]`, `[WARNING]`, `[ERROR]`, `[SWITCH MODE]`).
- Do not affect Auto Pull countdown logic or GUI performance.

---

### Task 1: Add duplicate detection, summary logging, and download notification in `core/ftp_service.py`

**Files:**
- Modify: `core/ftp_service.py:430-495`

- [ ] **Step 1: Implement file categorization helper in `FTPDownloader`**
  Add helper method or inline logic to classify candidate files:
  - If both `local_filepath.exists()` and `csv_filepath.exists()`:
    - Check if past file (`f_date and f_date < today`) -> classified as skipped.
    - If today or unknown date -> check `self.ftp.size(filename) == local_filepath.stat().st_size` -> classified as skipped.
  - Otherwise -> classified as to_download.

- [ ] **Step 2: Emit duplicate file summary log**
  - If all files are skipped (`skipped_count > 0` and `len(to_download) == 0`):
    - `_emit_log(log_callback, f"[{self.plc_name}][{m_name}] ไฟล์ทั้งหมดมีอยู่แล้วในเครื่อง (ซ้ำ {skipped_count} ไฟล์ - ข้ามการดาวน์โหลด)", "info")`
  - If mixed (`skipped_count > 0` and `len(to_download) > 0`):
    - `_emit_log(log_callback, f"[{self.plc_name}][{m_name}] ตรวจพบไฟล์ซ้ำ {skipped_count} ไฟล์ (ข้ามการดาวน์โหลด)", "info")`

- [ ] **Step 3: Emit download start log for each file in `to_download`**
  - Before calling `_safe_retrbinary`:
    - `_emit_log(log_callback, f"[{self.plc_name}][{m_name}] กำลังดาวน์โหลด: {pure_filename}", "info")`
  - Keep existing `[SUCCESS]` logs after retrieval and CSV conversion.

- [ ] **Step 4: Verify syntax**
  - `python -m py_compile core/ftp_service.py`

---

### Task 2: Add automated unit test for duplicate and download logging

**Files:**
- Create/Modify: `tests/test_ftp_logging.py`

- [ ] **Step 1: Write mock test verifying log messages**
  - Mock FTP connection and remote file listing.
  - Test Case 1: All files existing locally -> assert summary log emitted containing "ไฟล์ทั้งหมดมีอยู่แล้วในเครื่อง" or "ข้ามการดาวน์โหลด".
  - Test Case 2: New files -> assert log containing "กำลังดาวน์โหลด:" and "Downloaded".
  - Test Case 3: Mixed files -> assert summary log for duplicates + "กำลังดาวน์โหลด:" for new file.

- [ ] **Step 2: Run test suite**
  - `python -m unittest discover -s tests`

- [ ] **Step 3: Commit implementation and tests**
  - `git commit -m "feat(ftp): add duplicate file summary and download progress logging"`
