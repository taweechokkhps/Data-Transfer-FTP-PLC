import os
import sys
from datetime import date
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ui.components.date_picker import (
    parse_display_date,
    format_display_date,
    get_month_matrix,
    validate_date_range,
)


class TestDatePickerUtils(unittest.TestCase):
    def test_parse_display_date(self):
        self.assertEqual(parse_display_date("02/04/2025"), date(2025, 4, 2))
        self.assertEqual(parse_display_date("31/12/2026"), date(2026, 12, 31))
        self.assertIsNone(parse_display_date("invalid"))
        self.assertIsNone(parse_display_date("32/01/2025"))
        self.assertIsNone(parse_display_date(""))

    def test_format_display_date(self):
        self.assertEqual(format_display_date(date(2025, 4, 2)), "02/04/2025")
        self.assertEqual(format_display_date(date(2026, 12, 31)), "31/12/2026")

    def test_get_month_matrix(self):
        matrix = get_month_matrix(2025, 5)  # May 2025: May 1 is Thursday
        self.assertIsInstance(matrix, list)
        self.assertGreaterEqual(len(matrix), 5)
        # May 1, 2025 is Thursday -> index 3 in Monday-based week
        found_one = False
        for row in matrix:
            if 1 in row:
                self.assertEqual(row.index(1), 3)
                found_one = True
                break
        self.assertTrue(found_one)
        # Check total days in May is 31
        flat_days = [d for row in matrix for d in row if d > 0]
        self.assertEqual(len(flat_days), 31)
        self.assertEqual(flat_days[-1], 31)

    def test_validate_date_range(self):
        # Valid range
        ok, err, s, e = validate_date_range("01/05/2025", "03/05/2025")
        self.assertTrue(ok)
        self.assertEqual(err, "")
        self.assertEqual(s, date(2025, 5, 1))
        self.assertEqual(e, date(2025, 5, 3))

        # Same start and end (valid single day)
        ok, err, s, e = validate_date_range("01/05/2025", "01/05/2025")
        self.assertTrue(ok)

        # Invalid format
        ok, err, s, e = validate_date_range("invalid", "03/05/2025")
        self.assertFalse(ok)
        self.assertIn("Invalid", err)

        # Start after end
        ok, err, s, e = validate_date_range("05/05/2025", "01/05/2025")
        self.assertFalse(ok)
        self.assertIn("Start date cannot be after end date", err)


if __name__ == "__main__":
    unittest.main()
