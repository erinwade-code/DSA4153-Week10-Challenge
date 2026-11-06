# CSV and Excel readers
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.common import CANONICAL_COLUMNS, FileLevelError


def map_columns(raw: pd.DataFrame, column_map: dict[str, str],
                source_file: str) -> pd.DataFrame:
    """Rename source columns to canonical names; add source_file/source_record."""
    if set(column_map.values()) != set(CANONICAL_COLUMNS):
        raise FileLevelError(f"{source_file}: column_map must cover exactly "
                             f"{CANONICAL_COLUMNS}")
    missing = set(column_map) - set(raw.columns)
    if missing:
        raise FileLevelError(f"{source_file}: missing required column(s): "
                             f"{sorted(missing)}")
    out = raw[list(column_map)].rename(columns=column_map)[CANONICAL_COLUMNS].copy()
    out.insert(0, "source_file", Path(source_file).name)
    out.insert(1, "source_record", range(1, len(out) + 1))
    return out.reset_index(drop=True)


def _check_exists(path: str) -> None:
    """Raise FileLevelError if the input file is missing."""
    if not Path(path).is_file():
        raise FileLevelError(f"Input file not found: {path}")


def read_csv_records(cfg: dict) -> pd.DataFrame:
    """Read the delimited text file using the settings in cfg."""
    path = cfg["path"]
    _check_exists(path)
    try:
        raw = pd.read_csv(path, encoding=cfg["encoding"], sep=cfg["delimiter"],
                          skiprows=cfg.get("skip_lines", 0),
                          dtype=str, keep_default_na=False)
    except (UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise FileLevelError(f"{path}: cannot parse CSV ({exc})") from exc
    return map_columns(raw, cfg["column_map"], path)


def read_excel_records(cfg: dict) -> pd.DataFrame:
    """Read the observations sheet (skipping the Readme sheet) as strings."""
    path = cfg["path"]
    _check_exists(path)
    try:
        raw = pd.read_excel(path, sheet_name=cfg["sheet"], dtype=str,
                            keep_default_na=False, engine="openpyxl")
    except ValueError as exc:
        raise FileLevelError(f"{path}: cannot read sheet {cfg['sheet']!r} ({exc})") from exc
    return map_columns(raw, cfg["column_map"], path)


READERS = {"csv": read_csv_records, "xlsx": read_excel_records}


def read_with_format(cfg: dict) -> pd.DataFrame:
    """Dispatch to a reader by cfg['format']; reject unsupported formats."""
    fmt = cfg.get("format", Path(cfg["path"]).suffix.lstrip(".").lower())
    if fmt not in READERS:
        raise FileLevelError(f"Unsupported format {fmt!r} for {cfg['path']}")
    return READERS[fmt](cfg)