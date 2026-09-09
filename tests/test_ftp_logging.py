import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import MagicMock
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.ftp_service import FTPDownloader
from core.path_utils import format_batch_save_dir, get_batch_subdirs

class TestFTPDuplicateAndDownloadLogging(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.downloader = FTPDownloader(
            host="127.0.0.1",
            port=21,
            username="user",
            password="pwd",
            machines=[{"name": "MC1", "remote_dir": "/MEMCARD"}],
            local_target_dir=self.test_dir,
            file_extensions=[".txt"],
            separate_by_date=False,
            plc_name="LINE 1",
            ftp_mode="auto"
        )
        self.mock_ftp = MagicMock()
        self.downloader.ftp = self.mock_ftp
        # Mock connect so it returns True without real network
        self.downloader.connect = MagicMock(return_value=(True, "Connected"))
        # Mock CWD
        self.downloader._try_cwd = MagicMock(return_value=(True, "/MEMCARD"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_all_files_duplicate_summary_log(self):
        # 2 past files: e.g. 010120.txt, 020120.txt
        filenames = ["010120.txt", "020120.txt"]
        self.downloader._safe_nlst = MagicMock(return_value=filenames)
        
        # Pre-create local files and CSV files to simulate existing duplicates
        # Batch folder name for all past files
        save_dir = format_batch_save_dir(self.test_dir, "LINE 1", "MC1", "(01-01-2020 - 02-01-2020) ALL")
        pt_dir, csv_dir = get_batch_subdirs(save_dir)
        for fn in filenames:
            (pt_dir / fn).write_text("dummy data")
            (csv_dir / f"{Path(fn).stem}.csv").write_text("col1,col2\nval1,val2")

        logs = []
        def log_cb(msg, level="info"):
            logs.append((level, msg))

        self.downloader.download_files(log_callback=log_cb)

        # Verify summary log for all duplicate files
        all_dup_logs = [msg for lvl, msg in logs if "ไฟล์ทั้งหมดมีอยู่แล้วในเครื่อง" in msg and "ซ้ำ 2 ไฟล์" in msg]
        self.assertEqual(len(all_dup_logs), 1)
        # Ensure no download retr was triggered
        self.downloader.mock_retr = MagicMock()
        self.assertFalse(any("กำลังดาวน์โหลด:" in msg for lvl, msg in logs))

    def test_mixed_duplicate_and_new_files_log(self):
        # 1 past file (already existing), 1 new file
        filenames = ["010120.txt", "020120.txt"]
        self.downloader._safe_nlst = MagicMock(return_value=filenames)

        save_dir = format_batch_save_dir(self.test_dir, "LINE 1", "MC1", "(01-01-2020 - 02-01-2020) ALL")
        pt_dir, csv_dir = get_batch_subdirs(save_dir)
        # Only create 010120.txt locally
        (pt_dir / "010120.txt").write_text("dummy data")
        (csv_dir / "010120.csv").write_text("col1,col2\nval1,val2")

        # Mock retrieval for 020120.txt
        def mock_retr(cmd, callback, log_callback=None):
            callback(b"data line 1\tdata line 2\n")
        self.downloader._safe_retrbinary = MagicMock(side_effect=mock_retr)

        logs = []
        def log_cb(msg, level="info"):
            logs.append((level, msg))

        self.downloader.download_files(log_callback=log_cb)

        # Verify mixed duplicate warning
        mixed_dup_logs = [msg for lvl, msg in logs if "ตรวจพบไฟล์ซ้ำ" in msg and "ซ้ำ 1 ไฟล์" in msg]
        self.assertEqual(len(mixed_dup_logs), 1)

        # Verify new file download progression log
        downloading_logs = [msg for lvl, msg in logs if "กำลังดาวน์โหลด: 020120.txt" in msg]
        self.assertEqual(len(downloading_logs), 1)

        # Verify download success log
        downloaded_logs = [msg for lvl, msg in logs if "Downloaded 020120.txt" in msg]
        self.assertEqual(len(downloaded_logs), 1)

    def test_no_duplicate_all_new_files_log(self):
        filenames = ["010120.txt"]
        self.downloader._safe_nlst = MagicMock(return_value=filenames)

        def mock_retr(cmd, callback, log_callback=None):
            callback(b"line 1\n")
        self.downloader._safe_retrbinary = MagicMock(side_effect=mock_retr)

        logs = []
        def log_cb(msg, level="info"):
            logs.append((level, msg))

        self.downloader.download_files(log_callback=log_cb)

        # Verify NO duplicate warning is emitted
        self.assertFalse(any("ซ้ำ" in msg for lvl, msg in logs))
        # Verify download progression
        self.assertTrue(any("กำลังดาวน์โหลด: 010120.txt" in msg for lvl, msg in logs))
        self.assertTrue(any("Downloaded 010120.txt" in msg for lvl, msg in logs))

if __name__ == "__main__":
    unittest.main()
