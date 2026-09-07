"""Converter service for transforming PLC text files into standard CSV."""

import csv
import io
from pathlib import Path
from typing import Tuple

ENCODINGS_TO_TRY = ["utf-8-sig", "utf-8", "cp874", "tis-620", "latin-1"]


def detect_delimiter(first_line: str) -> str:
    """Detects delimiter from the first line of text."""
    if "\t" in first_line:
        return "\t"
    if ";" in first_line and "," not in first_line:
        return ";"
    if "," in first_line:
        return ","
    return "\t"


def convert_txt_to_csv(src_txt_path: Path, dest_csv_path: Path) -> Tuple[bool, str, int]:
    """Converts a delimited text file (.txt) into standard Comma-Separated Values (.csv).

    Output is encoded with utf-8-sig for seamless compatibility with
    terminal tools (cat/type) and spreadsheet software (Excel).

    Returns:
        (success: bool, error_message: str, row_count: int)
    """
    src_path = Path(src_txt_path)
    dest_path = Path(dest_csv_path)

    if not src_path.exists():
        return False, f"Source file does not exist: {src_path}", 0

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Read content trying common industrial/Thai/UTF encodings
    raw_content = None
    used_encoding = "utf-8"
    for enc in ENCODINGS_TO_TRY:
        try:
            with open(src_path, "r", encoding=enc) as f:
                raw_content = f.read()
                used_encoding = enc
                break
        except (UnicodeDecodeError, Exception):
            continue

    if raw_content is None:
        return False, f"Failed to decode source file with any known encoding: {src_path}", 0

    lines = raw_content.splitlines()
    if not lines:
        # Empty file, create empty CSV
        with open(dest_path, "w", encoding="utf-8-sig", newline="") as f:
            pass
        return True, "", 0

    # Determine delimiter from non-empty header line
    sample_line = next((line for line in lines if line.strip()), lines[0])
    delimiter = detect_delimiter(sample_line)

    row_count = 0
    temp_dest = dest_path.with_suffix(".tmp")
    try:
        with open(temp_dest, "w", encoding="utf-8-sig", newline="") as out_f:
            writer = csv.writer(out_f, delimiter=",", quoting=csv.QUOTE_MINIMAL)
            reader = csv.reader(io.StringIO(raw_content), delimiter=delimiter)
            for row in reader:
                writer.writerow(row)
                row_count += 1

        if dest_path.exists():
            dest_path.unlink()
        temp_dest.replace(dest_path)
        return True, "", row_count
    except Exception as e:
        if temp_dest.exists():
            temp_dest.unlink(missing_ok=True)
        return False, str(e), 0
