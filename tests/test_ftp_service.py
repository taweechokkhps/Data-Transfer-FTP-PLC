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

    def test_cancel_and_disconnect(self):
        import socket
        downloader = FTPDownloader(
            host="127.0.0.1",
            port=21,
            username="user",
            password="pwd",
            machines=[{"name": "MC1", "remote_dir": "/MEMCARD"}],
            local_target_dir="./downloads",
            file_extensions=[".txt"],
            separate_by_date=False,
            plc_name="LINE 1"
        )
        mock_ftp = MagicMock()
        mock_sock = MagicMock()
        mock_ftp.sock = mock_sock
        downloader.ftp = mock_ftp
        downloader.is_running = True

        downloader.cancel()

        self.assertFalse(downloader.is_running)
        mock_sock.settimeout.assert_called()
        mock_ftp.abort.assert_called_once()
        mock_ftp.quit.assert_called_once()
        mock_sock.shutdown.assert_called_with(socket.SHUT_RDWR)
        mock_sock.close.assert_called_once()
        self.assertIsNone(downloader.ftp)

    def test_stop_delegates_to_cancel(self):
        downloader = FTPDownloader(
            host="127.0.0.1",
            port=21,
            username="user",
            password="pwd",
            machines=[{"name": "MC1", "remote_dir": "/MEMCARD"}],
            local_target_dir="./downloads",
            file_extensions=[".txt"],
            separate_by_date=False,
            plc_name="LINE 1"
        )
        downloader.cancel = MagicMock()
        downloader.stop()
        downloader.cancel.assert_called_once()

    def test_calculate_download_eta_warmup(self):
        from core.ftp_service import calculate_download_eta
        # 0 or 1 file downloaded -> warm-up
        self.assertEqual(calculate_download_eta(remaining=10, actual_durations=[]), "คำนวณ...")
        self.assertEqual(calculate_download_eta(remaining=10, actual_durations=[1.0]), "คำนวณ...")

    def test_calculate_download_eta_minutes_and_seconds(self):
        from core.ftp_service import calculate_download_eta
        # 20 files remaining, average 10s per file -> 200s -> ~3m
        self.assertEqual(calculate_download_eta(remaining=20, actual_durations=[10.0, 10.0]), "~3m")
        # 2 files remaining, average 15s per file -> 30s -> ~30s
        self.assertEqual(calculate_download_eta(remaining=2, actual_durations=[15.0, 15.0]), "~30s")
        # 0 files remaining -> empty
        self.assertEqual(calculate_download_eta(remaining=0, actual_durations=[1.0, 1.0]), "")

    def test_emit_progress_backwards_compatible(self):
        from core.ftp_service import _emit_progress
        # 2-arg callback
        called_2 = []
        _emit_progress(lambda c, t: called_2.append((c, t)), 10, 20, 10, "~1m")
        self.assertEqual(called_2, [(10, 20)])

        # 4-arg keyword callback
        called_4 = []
        def rich_cb(c, t, remaining=0, eta_str=""):
            called_4.append((c, t, remaining, eta_str))
        _emit_progress(rich_cb, 10, 20, 10, "~1m")
        self.assertEqual(called_4, [(10, 20, 10, "~1m")])

    def test_live_connection_if_available(self):
        try:
            ok, msg = test_connection("192.168.1.169", 21, "user", "156900", timeout=2)
            if ok:
                print("Live test connection OK")
        except Exception:
            pass

if __name__ == "__main__":
    unittest.main()
