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

def _to_object_frame(rows) -> pd.DataFrame:
    """Build an object-dtype frame; missing cells become None, never NaN."""
    df = pd.DataFrame(rows)
    return pd.DataFrame({c: pd.Series([None if pd.isna(v) else v for v in df[c]],
                                      index=df.index, dtype=object)
                         for c in df.columns})
