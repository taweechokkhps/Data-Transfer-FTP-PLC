import os
import sys
import tempfile
import csv
from pathlib import Path
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.converter_service import convert_txt_to_csv

class TestConverterService(unittest.TestCase):
    def test_convert_tab_delimited_to_csv(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "sample.txt"
            dest = Path(td) / "sample.csv"

            # Create tab-delimited text
            content = (
                "Date [Machine]\tTime [Machine]\tPart no.\n"
                "4/3/2025\t0:49:40\t5971\n"
                "4/3/2025\t0:49:41\t5972\n"
            )
            src.write_text(content, encoding="utf-8")

            ok, err, count = convert_txt_to_csv(src, dest)
            self.assertTrue(ok)
            self.assertEqual(count, 3)
            self.assertTrue(dest.exists())

            # Read back using standard csv reader
            with open(dest, 'r', encoding='utf-8-sig', newline='') as f:
                reader = list(csv.reader(f))
                self.assertEqual(len(reader), 3)
                self.assertEqual(reader[0], ["Date [Machine]", "Time [Machine]", "Part no."])
                self.assertEqual(reader[1], ["4/3/2025", "0:49:40", "5971"])

    def test_convert_quoted_and_commas(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "quotes.txt"
            dest = Path(td) / "quotes.csv"

            content = "Col1\tCol2, with comma\tCol3\nVal1\tVal2, more comma\tVal3\n"
            src.write_text(content, encoding="utf-8")

            ok, err, count = convert_txt_to_csv(src, dest)
            self.assertTrue(ok)

            with open(dest, 'r', encoding='utf-8-sig', newline='') as f:
                reader = list(csv.reader(f))
                self.assertEqual(reader[0], ["Col1", "Col2, with comma", "Col3"])
                self.assertEqual(reader[1], ["Val1", "Val2, more comma", "Val3"])

    def test_nonexistent_file(self):
        ok, err, count = convert_txt_to_csv(Path("nonexistent.txt"), Path("out.csv"))
        self.assertFalse(ok)
        self.assertEqual(count, 0)

if __name__ == "__main__":
    unittest.main()
