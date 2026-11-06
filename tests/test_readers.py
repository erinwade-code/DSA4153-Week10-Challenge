import json
import tempfile
import unittest
from pathlib import Path

from src.common import CANONICAL_COLUMNS, FileLevelError
from src.readers import read_csv_records, read_excel_records, read_with_format

CFG = json.loads(Path("config.json").read_text(encoding="utf-8"))
CSV_CFG = next(i for i in CFG["inputs"] if i["format"] == "csv")
XLSX_CFG = next(i for i in CFG["inputs"] if i["format"] == "xlsx")
EXPECTED_COLS = ["source_file", "source_record"] + CANONICAL_COLUMNS


class ReaderTests(unittest.TestCase):
    def test_csv_record_count_and_columns(self):
        df = read_csv_records(CSV_CFG)
        self.assertEqual(len(df), 1712)
        self.assertEqual(list(df.columns), EXPECTED_COLS)
        self.assertEqual(df["source_record"].iloc[0], 1)
        self.assertEqual(df["source_record"].iloc[-1], 1712)

    def test_excel_record_count_and_columns(self):
        df = read_excel_records(XLSX_CFG)
        self.assertEqual(len(df), 1712)
        self.assertEqual(list(df.columns), EXPECTED_COLS)

    def test_values_are_strings(self):
        for df in (read_csv_records(CSV_CFG), read_excel_records(XLSX_CFG)):
            for col in CANONICAL_COLUMNS:
                self.assertTrue(all(isinstance(v, str) for v in df[col]))

    def test_csv_keeps_comma_and_accent_text(self):
        df = read_csv_records(CSV_CFG)
        self.assertIn("Congo, Rep.", set(df["country"]))

    def test_csv_and_excel_same_countries(self):
        a = read_csv_records(CSV_CFG)
        b = read_excel_records(XLSX_CFG)
        self.assertEqual(set(a["country"]), set(b["country"]))

    def test_missing_file(self):
        with self.assertRaises(FileLevelError):
            read_csv_records({**CSV_CFG, "path": "data/does_not_exist.csv"})

    def test_unsupported_format(self):
        with self.assertRaises(FileLevelError):
            read_with_format({**CSV_CFG, "format": "txt", "path": "data/unsupported.txt"})

    def test_missing_column_file(self):
        with self.assertRaises(FileLevelError):
            read_csv_records({**CSV_CFG, "path": "data/missing_column.csv"})

    def test_wrong_sheet_name(self):
        with self.assertRaises(FileLevelError):
            read_excel_records({**XLSX_CFG, "sheet": "no_such_sheet"})

    def test_reordered_records_keep_original_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "mini.csv"
            header = ";".join(CSV_CFG["column_map"])
            p.write_text("# c1\n# c2\n" + header + "\n"
                         "B;Asia;2007;70.5;100;5.5\nA;Asia;1952;40;50;3\n",
                         encoding="cp1252")
            df = read_csv_records({**CSV_CFG, "path": str(p)})
            self.assertEqual(list(df["country"]), ["B", "A"])
            self.assertEqual(list(df["source_record"]), [1, 2])


if __name__ == "__main__":
    unittest.main()