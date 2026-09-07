import os
import sys
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.path_utils import sanitize_remote_path, format_local_save_dir

def test_sanitize_remote_path():
    assert sanitize_remote_path(r"C:\Users\user\Documents\TEST") == "/Users/user/Documents/TEST"
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

if __name__ == "__main__":
    test_sanitize_remote_path()
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        test_format_local_save_dir(Path(td))
    print("ALL TESTS PASSED!")
