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
