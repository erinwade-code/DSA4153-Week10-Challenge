"""Readers for nested JSON and Parquet inputs, with column mapping."""
import json
from pathlib import Path

import pandas as pd

CANONICAL_COLUMNS: list[str] = ["country", "continent", "year", "lifeExp", "pop", "gdpPercap"]


class SchemaError(Exception):
    """File-level error: bad structure or missing required column."""


def flatten_record(record: dict, parent: str = "", sep: str = ".") -> dict:
    """Flatten nested dicts into one level, e.g. {'a': {'b': 1}} -> {'a.b': 1}."""
    flat: dict = {}
    for key, value in record.items():
        name = f"{parent}{sep}{key}" if parent else key
        if isinstance(value, dict):
            flat.update(flatten_record(value, name, sep))
        else:
            flat[name] = value
    return flat


def _check_file(path: str, suffix: str) -> Path:
    """Stop early if the file is missing or has the wrong extension."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    if p.suffix.lower() != suffix:
        raise ValueError(f"Unsupported format {p.suffix!r}, expected {suffix!r}")
    return p


def read_json_records(path: str, records_key: list[str]) -> pd.DataFrame:
    """Read nested JSON; records_key is the path to the list, e.g. ['data', 'records']."""
    p = _check_file(path, ".json")
    with open(p, encoding="utf-8") as f:
        node = json.load(f)
    for key in records_key:            # walk down the outer metadata object
        if not isinstance(node, dict) or key not in node:
            raise SchemaError(f"Missing JSON key {key!r} in {path}")
        node = node[key]
    if not isinstance(node, list):
        raise SchemaError(f"Expected a list of records at {records_key} in {path}")
    rows = [flatten_record(r) for r in node]
    # dtype=object keeps original values (1952 stays int, not 1952.0)
    return pd.DataFrame(rows, dtype=object)

