# Design Spec: Enhanced Duplicate File & Download Logging

**Date:** 2026-09-09  
**Status:** Approved by User  
**Scope:** DEV mode only (`python main.py`, Python 3.12)

---

## 1. Objectives & Requirements
1. **Duplicate File Awareness (แจ้งเตือนไฟล์ซ้ำ)**:
   - When files already exist on the local disk (and for today's file, file size matches the PLC), log an informative summary so the user knows files are present and being skipped.
   - Use a summary count rather than logging every individual duplicate file to keep the log console clean and prevent UI flooding.
2. **Download Progression Logging (แจ้งชื่อไฟล์ที่กำลังดาวน์โหลด)**:
   - When new files or updated files need downloading, log an explicit `[INFO]` message identifying the file:
     `[INFO] [{plc_name}][{m_name}] กำลังดาวน์โหลด: {filename}`
   - After download finishes, keep existing detailed `[SUCCESS]` logs with file size and transfer duration.
   - After CSV conversion finishes, keep existing `[SUCCESS]` logs with converted rows and duration.
3. **Three Canonical Scenarios**:
   - **Scenario A (Mixed: duplicate + new files)**:
     - `[INFO] [{plc_name}][{m_name}] ตรวจพบไฟล์ซ้ำ {count} ไฟล์ (ข้ามการดาวน์โหลด)`
     - For each new file:
       - `[INFO] [{plc_name}][{m_name}] กำลังดาวน์โหลด: {filename}`
       - `[SUCCESS] [{plc_name}][{m_name}] Downloaded {filename} ({size} KB) in {dur} ms`
       - `[SUCCESS] [{plc_name}][{m_name}] Converted to csv/{csv} ({rows} rows) in {dur} ms`
   - **Scenario B (All duplicates: no new files)**:
     - `[INFO] [{plc_name}][{m_name}] ไฟล์ทั้งหมดมีอยู่แล้วในเครื่อง (ซ้ำ {count} ไฟล์ - ข้ามการดาวน์โหลด)`
     - No download attempts needed.
   - **Scenario C (No duplicates: all new files)**:
     - No duplicate warning.
     - Directly logs `กำลังดาวน์โหลด: {filename}` and download results for each file.

---

## 2. Architecture & Components

### 2.1 `core/ftp_service.py` (`FTPDownloader.download_files`)
- For each configured machine `m_name` in `files_by_machine`:
  - Before initiating downloads, categorize candidate files `t_files` into:
    - `skipped_files`: Files where both `plaintext` and `csv` exist locally, and either (a) file date is from a past date, or (b) file date is today/unknown and `local_size == remote_size`.
    - `to_download`: Files not existing locally, or today's files whose size on PLC is greater than local.
  - **Logging Rules**:
    - If `skipped_files` and not `to_download`:
      - Emit `_emit_log(log_callback, f"[{self.plc_name}][{m_name}] ไฟล์ทั้งหมดมีอยู่แล้วในเครื่อง (ซ้ำ {len(skipped_files)} ไฟล์ - ข้ามการดาวน์โหลด)", "info")`
      - Increment progress for all skipped files.
    - If `skipped_files` and `to_download`:
      - Emit `_emit_log(log_callback, f"[{self.plc_name}][{m_name}] ตรวจพบไฟล์ซ้ำ {len(skipped_files)} ไฟล์ (ข้ามการดาวน์โหลด)", "info")`
      - Increment progress for all skipped files.
    - For each file in `to_download`:
      - Emit `_emit_log(log_callback, f"[{self.plc_name}][{m_name}] กำลังดาวน์โหลด: {pure_filename}", "info")`
      - Perform binary retrieval (`_safe_retrbinary`)
      - Emit `[SUCCESS]` downloaded log with size and ms.
      - Convert to CSV and emit `[SUCCESS]` / `[WARNING]` conversion log.
      - Increment progress callback.

---

## 3. Verification Plan
1. **Syntax Check**:
   - `python -m py_compile core/ftp_service.py`
2. **Unit Tests**:
   - `python -m unittest discover -s tests`
3. **Behavioral Test**:
   - Test scenario with all existing files -> verify summary log emitted.
   - Test scenario with new files -> verify `กำลังดาวน์โหลด: ...` and download logs emitted.
