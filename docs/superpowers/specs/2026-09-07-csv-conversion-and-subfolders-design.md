# Design Spec: CSV Conversion & Subfolder Organization

**Date:** 2026-09-07  
**Status:** Approved by User  
**Scope:** DEV mode only (no Nuitka build)

---

## 1. Objectives & Requirements
1. **Batch Folder Subdirectories**:
   - Inside each batch directory:
     `<target_dir> / <plc_name> / <machine_name> / (start_date - end_date)`
   - Create two separate subdirectories:
     - `plaintext/`: stores original files directly retrieved from PLC (e.g. `010525.txt`).
     - `csv/`: stores auto-converted CSV files (e.g. `010525.csv`).
2. **Text to CSV Converter (`core/converter_service.py`)**:
   - PLC log files use Tab (`\t`) delimiters.
   - The converter parses Tab-delimited rows into standard Comma-Separated Values (CSV).
   - Handles quoting according to RFC 4180 standard using Python's built-in `csv` module.
   - Encodes output using `utf-8-sig` (compatible with both terminal `cat` / `type` and Excel).
   - If input is already `.csv`, it copies or normalizes it into `csv/`.
3. **Integration into Download Process (`core/ftp_service.py`)**:
   - In `FTPDownloader.download_files`:
     - Creates both `batch_dir / "plaintext"` and `batch_dir / "csv"`.
     - Downloads remote file to `plaintext_path = batch_dir / "plaintext" / filename`.
     - Converts `plaintext_path` to `csv_path = batch_dir / "csv" / f"{Path(filename).stem}.csv"`.
     - Logs conversion timing in milliseconds:
       `[LINE 1][MC1] Converted to csv/010525.csv in 15.2 ms`.
   - Incremental download check:
     - If `plaintext_path` exists with matching file size AND `csv_path` exists, skip downloading.
4. **Dev Workflow**:
   - Verify with Python test suite and run via `main.py`.

---

## 2. Architecture & Components

### 2.1 `core/converter_service.py`
- `convert_txt_to_csv(src_txt_path: Path, dest_csv_path: Path) -> tuple[bool, str, int]`:
  - Reads `src_txt_path` line by line.
  - Detects delimiter (tab `\t`, semicolon, or comma; default `\t`).
  - Writes standard CSV to `dest_csv_path`.
  - Returns `(success, error_message, row_count)`.

### 2.2 `core/path_utils.py`
- Update `format_batch_save_dir(base_dir, plc_name, machine_name, batch_folder_name)`:
  - Continues returning the batch directory `Path`.
  - Can provide helper `get_batch_subdirs(batch_dir)` returning `(plaintext_dir, csv_dir)`.

### 2.3 `core/ftp_service.py`
- Calls `convert_txt_to_csv` right after downloading each file to `plaintext_dir`.
- Logs completion with millisecond duration.

---

## 3. Verification Plan
- Unit tests in `tests/test_converter_service.py` testing:
  - Tab-delimited `.txt` conversion to CSV.
  - Multi-line data, numeric fields, quoted text.
  - Output readable by standard `csv.reader`.
- Integration test with sample `010525.txt`.
- DEV mode run verification.
