# Omron FINS W200.00 Pre-Download Safety Interlock Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Interlock FTP downloads by checking Omron PLC bit `W200.00` via FINS/UDP port 9600 before connecting or pulling data, skipping download if the machine is actively running or if FINS is unreachable.

**Architecture:** Build a lightweight, dependency-free `core/fins_service.py` module using Python standard `socket` and `struct`. In `core/ftp_service.py`, query `check_omron_w200_bit()` at the start of `download_files()`.

**Tech Stack:** Python 3.12 built-in `socket`, `struct`, `unittest`.

## Global Constraints
- DEV mode only (`python main.py`, Python 3.12).
- Zero external package dependencies (must run completely offline on factory computers).
- Preserves all existing logging conventions and tags (`[WARNING]`, `[SUCCESS]`, etc.).

---

### Task 1: Create `core/fins_service.py`

**Files:**
- Create: `core/fins_service.py`

- [ ] **Step 1: Implement frame builder, response parser, and UDP query**
  - `build_fins_read_bit_frame(node_id: int, area_code: int = 0x31, word: int = 200, bit: int = 0) -> bytes`
  - `parse_fins_read_bit_response(response: bytes) -> tuple[bool, bool | None, str]`
  - `check_omron_w200_bit(host: str, port: int = 9600, timeout: float = 2.0) -> tuple[bool, bool | None, str]`
- [ ] **Step 2: Verify syntax with `py_compile`**

---

### Task 2: Unit tests for `core/fins_service.py`

**Files:**
- Create: `tests/test_fins_service.py`

- [ ] **Step 1: Write unit tests covering:**
  - Correct 18-byte FINS frame generation (header + memory read command for W200.00).
  - Response parsing for bit ON (`0x01` -> `True`), bit OFF (`0x00` -> `False`), and error response codes (`MRES != 0`).
  - Timeout and socket exception handling.
- [ ] **Step 2: Run test with `python -m unittest tests/test_fins_service.py`**

---

### Task 3: Integrate FINS check into `core/ftp_service.py`

**Files:**
- Modify: `core/ftp_service.py`

- [ ] **Step 1: Call `check_omron_w200_bit` in `FTPDownloader.download_files()`**
  - If FINS check fails (timeout / network error):
    - Emit warning log: `[WARNING] [{self.plc_name}] ⚠️ ไม่สามารถตรวจสอบสถานะเครื่องจักรได้ ({fins_msg}) ข้ามการดาวน์โหลดเพื่อความปลอดภัย`
    - Return `False`.
  - If `is_on`:
    - Emit warning log: `[WARNING] [{self.plc_name}] ⚠️ เครื่องจักรกำลังทำงาน (W200.00 = ON) ข้ามการดาวน์โหลดเพื่อความปลอดภัย`
    - Return `False`.
  - If `not is_on`:
    - Proceed with existing FTP connection and file downloading.
- [ ] **Step 2: Verify syntax and run tests**

---

### Task 4: Integration testing and verification

**Files:**
- Modify: `tests/test_ftp_logging.py`

- [ ] **Step 1: Add mock tests for W200.00 interlock behavior in `test_ftp_logging.py`**
- [ ] **Step 2: Run full test suite (`python -m unittest discover -s tests`)**
- [ ] **Step 3: Commit completed implementation**
