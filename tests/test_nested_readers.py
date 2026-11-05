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

