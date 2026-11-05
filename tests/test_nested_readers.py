import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.nested_readers import (CANONICAL_COLUMNS, SchemaError, load_nested,
                                read_json_records, trim_text)

JSON_MAP = {"identity.country": "country", "identity.continent": "continent",
            "identity.year": "year", "measures.lifeExp": "lifeExp",
            "measures.pop": "pop", "measures.gdpPercap": "gdpPercap"}
PQ_MAP = {"COUNTRY": "country", "CONTINENT": "continent", "YEAR": "year",
          "LIFE_EXP": "lifeExp", "POPULATION": "pop", "GDP_PER_CAPITA": "gdpPercap"}


def json_row(country=" Peru ", year=1952):
    return {"identity": {"country": country, "continent": "Americas", "year": year},
            "measures": {"lifeExp": 43.9, "pop": 8025700, "gdpPercap": 3758.5}}


class NestedReaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())  # fixtures live outside data/

    def _json(self, doc, name="t.json"):
        p = self.tmp / name
        p.write_text(json.dumps(doc), encoding="utf-8")
        return str(p)

    def _settings(self, path):
        return {"format": "json", "path": path, "record_path": "records",
                "source_to_canonical": JSON_MAP}

    def test_json_normal_ignores_metadata(self):
        p = self._json({"metadata": {"note": "x"}, "records": [json_row(), json_row(year=1957)]})
        audit = []
        df = load_nested(self._settings(p), audit)
        self.assertEqual(list(df.columns), ["source_record"] + CANONICAL_COLUMNS)
        self.assertEqual(len(df), 2)
        self.assertEqual(df["country"].iloc[0], "Peru")
        self.assertEqual(df["source_record"].tolist(), [1, 2])
        self.assertEqual(len(audit), 2)

    def test_json_preserves_bad_values(self):
        row = json_row(year=1952.5)
        row["measures"]["pop"] = "abc"
        df = load_nested(self._settings(self._json({"records": [row]})), [])
        self.assertEqual(df["year"].iloc[0], 1952.5)
        self.assertEqual(df["pop"].iloc[0], "abc")

    def test_json_missing_record_key(self):
        with self.assertRaises(SchemaError):
            read_json_records(self._json({"metadata": {}}), "records")

    def test_json_missing_column(self):
        row = json_row()
        del row["measures"]["gdpPercap"]
        with self.assertRaises(SchemaError):
            load_nested(self._settings(self._json({"records": [row]})), [])

    def test_json_missing_field_in_one_record_becomes_none(self):
        bad = json_row()
        del bad["measures"]["pop"]
        df = load_nested(self._settings(self._json({"records": [json_row(), bad]})), [])
        self.assertIsNone(df["pop"].iloc[1])

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            read_json_records(str(self.tmp / "nope.json"), "records")

    def test_unsupported_extension(self):
        p = self.tmp / "x.txt"
        p.write_text("hi")
        with self.assertRaises(ValueError):
            read_json_records(str(p), "records")

    def test_parquet_keeps_strings(self):
        p = str(self.tmp / "t.parquet")
        pd.DataFrame([{"COUNTRY": " Peru ", "CONTINENT": "Americas", "YEAR": "1952",
                       "LIFE_EXP": "43.9", "POPULATION": "8025700",
                       "GDP_PER_CAPITA": "3758.5"}]).to_parquet(p)
        df = load_nested({"format": "parquet", "path": p, "source_to_canonical": PQ_MAP}, [])
        self.assertEqual(df["year"].iloc[0], "1952")
        self.assertEqual(df["country"].iloc[0], "Peru")

    def test_trim_only_text(self):
        df = trim_text(pd.DataFrame({"a": [" x ", 5]}, dtype=object))
        self.assertEqual(df["a"].tolist(), ["x", 5])


if __name__ == "__main__":
    unittest.main()
