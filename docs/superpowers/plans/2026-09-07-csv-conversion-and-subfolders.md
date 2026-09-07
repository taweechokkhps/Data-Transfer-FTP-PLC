# CSV Conversion & Subfolder Organization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatically organize downloaded PLC files into `plaintext/` and `csv/` subfolders within each batch directory, converting Tab-delimited `.txt` files into standard Comma-Separated Values (`.csv`) in DEV mode.

**Architecture:** A lightweight `core/converter_service.py` module with `convert_txt_to_csv` function using Python's built-in `csv` module. `core/path_utils.py` provides batch subdirectory helpers. `FTPDownloader` saves raw files to `plaintext/`, runs `convert_txt_to_csv` into `csv/`, and logs per-file conversion timings in milliseconds.

**Tech Stack:** Python 3.12, standard `csv`, `pathlib`, `time`.

## Global Constraints
- Target directory hierarchy: `<target_dir>/<plc_name>/<machine_name>/(<date_range>)/plaintext/` and `<target_dir>/<plc_name>/<machine_name>/(<date_range>)/csv/`
- Output CSV encoding: `utf-8-sig` (Excel and terminal compatible).
- DEV mode only (no Nuitka build).
- Millisecond precision timing logged for conversion.

---

### Task 1: Converter Service (`core/converter_service.py`)

**Files:**
- Create: `core/converter_service.py`
- Create: `tests/test_converter_service.py`

**Interfaces:**
- Produces: `convert_txt_to_csv(src_txt_path: Path, dest_csv_path: Path) -> tuple[bool, str, int]`
  - `src_txt_path`: Path to input file
  - `dest_csv_path`: Path to output CSV file
  - Returns `(success, error_msg, row_count)`

- [ ] **Step 1: Write unit tests for converter**
Test converting Tab-delimited lines, handling headers, quotes, comma preservation if already csv.

- [ ] **Step 2: Run test to verify failure**
Run: `.\venv\Scripts\python.exe tests/test_converter_service.py`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement `core/converter_service.py`**
Implement `convert_txt_to_csv` using `csv.reader(delimiter='\t')` and `csv.writer(delimiter=',')` with UTF-8 BOM (`utf-8-sig`).

- [ ] **Step 4: Run test to verify it passes**
Run: `.\venv\Scripts\python.exe tests/test_converter_service.py`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add core/converter_service.py tests/test_converter_service.py
git commit -m "feat: implement convert_txt_to_csv in converter_service"
```

---

### Task 2: Subfolder Helpers in `core/path_utils.py`

**Files:**
- Modify: `core/path_utils.py`
- Modify: `tests/test_path_utils.py`

**Interfaces:**
- Produces: `get_batch_subdirs(batch_dir: Path) -> tuple[Path, Path]`
  - Returns `(plaintext_dir, csv_dir)`, automatically creating them if they don't exist.

- [ ] **Step 1: Write test for `get_batch_subdirs`**
Add test in `tests/test_path_utils.py`.

- [ ] **Step 2: Implement `get_batch_subdirs` in `core/path_utils.py`**
Implement function ensuring `plaintext/` and `csv/` exist.

- [ ] **Step 3: Run test to verify it passes**
Run: `.\venv\Scripts\python.exe tests/test_path_utils.py`
Expected: ALL TESTS PASSED!

- [ ] **Step 4: Commit**
```bash
git add core/path_utils.py tests/test_path_utils.py
git commit -m "feat: add get_batch_subdirs helper in path_utils"
```

---

### Task 3: Integrate Subfolders & Auto CSV Conversion in `FTPDownloader`

**Files:**
- Modify: `core/ftp_service.py`

**Interfaces:**
- Consumes: `get_batch_subdirs` from `core.path_utils`
- Consumes: `convert_txt_to_csv` from `core.converter_service`

- [ ] **Step 1: Update download & conversion logic in `FTPDownloader.download_files`**
Save raw file to `plaintext_dir / pure_filename`.
Convert to `csv_dir / f"{pure_filename_stem}.csv"`.
Measure and log conversion time in milliseconds.
Update incremental download check to verify both `plaintext` and `csv` files exist.

- [ ] **Step 2: Verify with real sample file `010525.txt`**
Test download and conversion flow against live or mock data.

- [ ] **Step 3: Commit**
```bash
git add core/ftp_service.py
git commit -m "feat: save files into plaintext and auto-convert to csv subfolder"
```

---

### Task 4: Full Verification in DEV Mode

**Files:**
- All tests across test suite.

- [ ] **Step 1: Run complete test suite**
Run: `.\venv\Scripts\python.exe tests/test_path_utils.py; .\venv\Scripts\python.exe tests/test_config_and_logger.py; .\venv\Scripts\python.exe tests/test_ftp_service.py; .\venv\Scripts\python.exe tests/test_date_picker.py; .\venv\Scripts\python.exe tests/test_converter_service.py`
Expected: ALL TESTS PASSED!

- [ ] **Step 2: Restart DEV app for user testing**
Launch `main.py` in background.
