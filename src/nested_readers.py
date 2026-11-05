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

def read_json_records(path: str, record_path: str, encoding: str = "utf-8") -> pd.DataFrame:
    """Read nested JSON; record_path is the key holding the list of records."""
    p = _check_file(path, ".json")
    with open(p, encoding=encoding) as f:
        doc = json.load(f)
    if not isinstance(doc, dict) or record_path not in doc:
        raise SchemaError(f"Missing JSON key {record_path!r} in {path}")
    records = doc[record_path]               # everything else is metadata
    if not isinstance(records, list):
        raise SchemaError(f"{record_path!r} in {path} is not a list of records")
    return _to_object_frame([flatten_record(r) for r in records])

def read_parquet_records(path: str, engine: str = "pyarrow") -> pd.DataFrame:
    """Read Parquet and keep every value as-is (strings); no casting yet."""
    p = _check_file(path, ".parquet")
    return _to_object_frame(pd.read_parquet(p, engine=engine))

def map_columns(df: pd.DataFrame, mapping: dict[str, str], source_file: str) -> pd.DataFrame:
    """Rename source columns to canonical names; fail if any required one is missing."""
    df = df.rename(columns=mapping)
    missing = set(CANONICAL_COLUMNS) - set(df.columns)
    if missing:
        raise SchemaError(f"{source_file}: missing required columns {sorted(missing)}")
    return df[CANONICAL_COLUMNS].copy()

def trim_text(df: pd.DataFrame) -> pd.DataFrame:
    """Strip surrounding whitespace from text values only."""
    return pd.DataFrame({c: pd.Series([v.strip() if isinstance(v, str) else v for v in df[c]],
                                      index=df.index, dtype=object)
                         for c in df.columns})
