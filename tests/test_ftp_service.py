import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.ftp_service import list_remote_directories, test_connection

def test_ftp_listing_live():
    ok, dirs_or_err = list_remote_directories("192.168.1.169", 21, "user", "156900", "/")
    if ok:
        assert isinstance(dirs_or_err, list)
        assert "Documents" in dirs_or_err
        print(f"FTP directories found: {dirs_or_err[:5]}... (Total: {len(dirs_or_err)})")

    ok_conn, msg = test_connection("192.168.1.169", 21, "user", "156900")
    assert ok_conn is True
    print(f"Test connection result: {msg}")

if __name__ == "__main__":
    test_ftp_listing_live()
    print("FTP SERVICE TESTS PASSED!")
