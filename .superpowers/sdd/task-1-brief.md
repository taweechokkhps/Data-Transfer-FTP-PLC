# Task 1: Core Path Utilities & Unit Tests

**Files:**
- Create: `core/__init__.py`
- Create: `core/path_utils.py`
- Test: `tests/test_path_utils.py`

**Interfaces:**
- Produces:
  - `sanitize_remote_path(path: str) -> str`
  - `format_local_save_dir(base_dir: str, plc_name: str, sub_dir: str = "", separate_by_date: bool = True) -> Path`

### Requirements & Steps:
1. Write failing test in `tests/test_path_utils.py`:
```python
import os
import sys
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.path_utils import sanitize_remote_path, format_local_save_dir

def test_sanitize_remote_path():
    assert sanitize_remote_path(r"C:\Users\user\Documents\TEST") == "/Users/user/Documents/TEST"
    assert sanitize_remote_path("D:/Data/Logs") == "/Data/Logs"
    assert sanitize_remote_path(r"\0_CARD\log0") == "/0_CARD/log0"
    assert sanitize_remote_path(r"0_CARD\log0\") == "/0_CARD/log0"
    assert sanitize_remote_path("//0_CARD///log0//") == "/0_CARD/log0"
    assert sanitize_remote_path("") == "/"
    assert sanitize_remote_path("/") == "/"
    assert sanitize_remote_path("   ") == "/"

def test_format_local_save_dir(tmp_path):
    target = tmp_path / "downloads"
    p = format_local_save_dir(str(target), "PLC_1", "MC1", separate_by_date=False)
    assert p == target / "PLC_1" / "MC1"
    assert p.exists()

if __name__ == "__main__":
    test_sanitize_remote_path()
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        test_format_local_save_dir(Path(td))
    print("ALL TESTS PASSED!")
```

2. Run test to verify it fails (`py -3.12 tests/test_path_utils.py`).
3. Implement `core/__init__.py` and `core/path_utils.py`:
```python
import re
import datetime
from pathlib import Path

def sanitize_remote_path(path_str: str) -> str:
    if not path_str or not path_str.strip():
        return "/"
    
    cleaned = path_str.strip()
    cleaned = re.sub(r'^[a-zA-Z]:', '', cleaned)
    cleaned = cleaned.replace('\\', '/')
    cleaned = re.sub(r'/+', '/', cleaned)
    if len(cleaned) > 1 and cleaned.endswith('/'):
        cleaned = cleaned[:-1]
    if not cleaned.startswith('/'):
        cleaned = '/' + cleaned
        
    return cleaned

def format_local_save_dir(base_dir: str, plc_name: str, sub_dir: str = "", separate_by_date: bool = True) -> Path:
    target = Path(base_dir) / plc_name
    if sub_dir:
        target = target / sub_dir
    if separate_by_date:
        date_str = datetime.datetime.now().strftime("%d-%m-%Y")
        target = target / date_str
        
    target.mkdir(parents=True, exist_ok=True)
    return target
```
4. Run test to verify it passes (`py -3.12 tests/test_path_utils.py`).
5. Commit with message: `feat(core): add path utilities with sanitization and tests`.
6. Write summary report to `.superpowers/sdd/task-1-report.md`.
