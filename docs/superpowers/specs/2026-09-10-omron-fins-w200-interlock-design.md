# Design Spec: Omron FINS W200.00 Pre-Download Safety Interlock

**Date:** 2026-09-10  
**Status:** Approved by User  
**Scope:** DEV mode only (`python main.py`, Python 3.12, Offline-compatible using built-in libraries)

---

## 1. Objectives & Requirements
1. **Machine Activity Interlock (ป้องกันการแย่ง CompactFlash ระหว่างเครื่องจักรทำงาน)**:
   - Before attempting any FTP download (manual or Auto Pull), check Omron PLC bit `W200.00` over Omron FINS/UDP port 9600.
   - Fixed address: `W200.00` for all PLCs.
2. **Behavior on Active Machine (`W200.00 == 1 / ON`)**:
   - Machine is running / actively writing to the memory card.
   - Do NOT establish FTP connection or attempt file transfers.
   - Emit warning log:
     `[WARNING] [{plc_name}] ⚠️ เครื่องจักรกำลังทำงาน (W200.00 = ON) ข้ามการดาวน์โหลดเพื่อความปลอดภัย`
   - Finish safely without raising connection or transfer errors.
3. **Behavior on FINS Check Failure / Timeout**:
   - If FINS communication times out (e.g. PLC offline or FINS port unreachable):
   - For industrial safety, do NOT attempt download.
   - Emit warning log:
     `[WARNING] [{plc_name}] ⚠️ ไม่สามารถตรวจสอบสถานะเครื่องจักรได้ (FINS Timeout) ข้ามการดาวน์โหลดเพื่อความปลอดภัย`
4. **Behavior on Idle Machine (`W200.00 == 0 / OFF`)**:
   - Machine is idle / not writing.
   - Proceed directly to FTP connection, checking, and downloading as normal.

---

## 2. Architecture & Components

### 2.1 `core/fins_service.py` (New Module)
- Pure Python implementation using built-in `socket` and `struct` (zero external dependencies).
- Functions:
  - `build_fins_read_bit_frame(node_id: int, area_code: int = 0x31, word: int = 200, bit: int = 0) -> bytes`:
    - Constructs 18-byte FINS frame:
      - 10-byte FINS header (`ICF=0x80`, `RSV=0x00`, `GCT=0x02`, `DNA=0x00`, `DA1=node_id`, `DA2=0x00`, `SNA=0x00`, `SA1=0x00`, `SA2=0x00`, `SID=0x01`)
      - 8-byte Command: `01 01` (Memory Read), `31` (WR Bit), `00 C8 00` (Word 200, Bit 0), `00 01` (Count: 1).
  - `parse_fins_read_bit_response(response: bytes) -> tuple[bool, bool | None, str]`:
    - Validates FINS response header, checks Main/Sub response codes (`0x00, 0x00` = OK).
    - Extracts bit value (`0x01` -> `True`, `0x00` -> `False`).
  - `check_omron_w200_bit(host: str, port: int = 9600, timeout: float = 2.0) -> tuple[bool, bool | None, str]`:
    - Sends FINS/UDP packet to `(host, port)`.
    - Returns `(success, is_on, message)`.

### 2.2 `core/ftp_service.py` (`FTPDownloader.download_files`)
- At the start of `download_files()`:
  - Call `check_omron_w200_bit(self.host)`.
  - If not successful:
    - Log safety skip warning and return `False`.
  - If `is_on`:
    - Log machine active skip warning and return `False`.
  - If `not is_on`:
    - Proceed with existing FTP download process.

---

## 3. Verification Plan
1. **Unit Tests**:
   - `tests/test_fins_service.py`:
     - Test frame construction (verify byte contents).
     - Test response parsing for ON (`0x01`), OFF (`0x00`), and error response codes.
     - Test mock UDP server round-trip.
2. **FTPDownloader Integration Test**:
   - Mock FINS returning ON -> verify download skipped with warning log.
   - Mock FINS returning OFF -> verify download proceeds normally.
   - Mock FINS returning Timeout -> verify download skipped with warning log.
3. **Full Test Suite**:
   - `python -m unittest discover -s tests`
