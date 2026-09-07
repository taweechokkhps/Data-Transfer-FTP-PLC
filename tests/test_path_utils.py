import os
import sys
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.path_utils import sanitize_remote_path, format_local_save_dir, parse_date_from_filename, format_batch_save_dir
import datetime

def test_sanitize_remote_path():
    assert sanitize_remote_path(r"C:\Users\user\Documents\TEST") == "/Documents/TEST"
    assert sanitize_remote_path(r"C:\Users\user\Documents\TEST", strip_user=False) == "/Users/user/Documents/TEST"
    assert sanitize_remote_path("C:/Users/user/Documents/Projects/data_record/TEST/Data-TEST") == "/Documents/Projects/data_record/TEST/Data-TEST"
    assert sanitize_remote_path("D:/Data/Logs") == "/Data/Logs"
    assert sanitize_remote_path(r"\0_CARD\log0") == "/0_CARD/log0"
    assert sanitize_remote_path("0_CARD\\log0\\") == "/0_CARD/log0"
    assert sanitize_remote_path("//0_CARD///log0//") == "/0_CARD/log0"
    assert sanitize_remote_path("") == "/"
    assert sanitize_remote_path("/") == "/"
    assert sanitize_remote_path("   ") == "/"

def test_format_local_save_dir(tmp_path):
    target = tmp_path / "downloads"
    p = format_local_save_dir(str(target), "PLC_1", "MC1", separate_by_date=False)
    assert p == target / "PLC_1" / "MC1"
    assert p.exists()

def test_parse_date_from_filename():
    assert parse_date_from_filename("020425.txt") == datetime.date(2025, 4, 2)
    assert parse_date_from_filename("311224.csv") == datetime.date(2024, 12, 31)
    assert parse_date_from_filename("invalid.txt") is None
    assert parse_date_from_filename("999999.txt") is None

def test_format_batch_save_dir(tmp_path):
    target = tmp_path / "downloads"
    p = format_batch_save_dir(str(target), "LINE 1", "MC1", "(01-04-2025 - 15-04-2025)")
    assert p == target / "LINE 1" / "MC1" / "(01-04-2025 - 15-04-2025)"
    assert p.exists()

if __name__ == "__main__":
    test_sanitize_remote_path()
    test_parse_date_from_filename()
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        test_format_local_save_dir(Path(td))
        test_format_batch_save_dir(Path(td))
    print("ALL TESTS PASSED!")
