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
