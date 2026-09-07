import os
import sys
import unittest
from unittest.mock import MagicMock
import ftplib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.ftp_service import list_remote_directories, test_connection, FTPDownloader

class TestFTPService(unittest.TestCase):
    def test_ftp_pasv_fallback_on_502(self):
        downloader = FTPDownloader(
            host="127.0.0.1",
            port=21,
            username="user",
            password="pwd",
            machines=[{"name": "MC1", "remote_dir": "/MEMCARD"}],
            local_target_dir="./downloads",
            file_extensions=[".txt"],
            separate_by_date=False,
            plc_name="LINE 1",
            ftp_mode="auto"
        )
        
        # Mock ftp instance
        mock_ftp = MagicMock()
        downloader.ftp = mock_ftp

        # Simulate 502 error on first call, success on second
        first_call = True
        def mock_nlst():
            nonlocal first_call
            if first_call:
                first_call = False
                raise ftplib.error_perm("502 PASV command not implemented.")
            return ["010525.txt", "020525.txt"]

        mock_ftp.nlst.side_effect = mock_nlst

        logs = []
        result = downloader._safe_nlst(log_callback=logs.append)
        
        # Verify it caught 502, called set_pasv(False), and succeeded
        mock_ftp.set_pasv.assert_called_with(False)
        self.assertTrue(downloader.is_active_mode)
        self.assertEqual(result, ["010525.txt", "020525.txt"])
        self.assertTrue(any("502 PASV not implemented" in log for log in logs))

    def test_live_connection_if_available(self):
        try:
            ok, msg = test_connection("192.168.1.169", 21, "user", "156900", timeout=2)
            if ok:
                print("Live test connection OK")
        except Exception:
            pass

if __name__ == "__main__":
    unittest.main()
