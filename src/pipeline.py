"""Pipeline: recover each input, compare the formats, analyse, export, verify."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src.common import CANONICAL_COLUMNS, FileLevelError
from src.export_staging import StagingExporter
from src.nested_readers import load_nested
from src.population import (asia_pop_life, asia_pop_total, build_population_matrix,
                            generate_validation_rows, phil_pop_life,
                            population_index, population_index_table)
from src.readers import read_with_format
from src.validation import (check_conflicting_keys, remove_exact_duplicates,
                            validate_and_quarantine)

AUDIT_COLUMNS = ["step", "source_file", "operation", "rule", "rows_before", "rows_after"]
NUMERIC_DTYPES = {"year": "int64", "pop": "int64",
                  "lifeExp": "float64", "gdpPercap": "float64"}
EXPORT_FORMATS = ("csv", "xlsx", "json", "parquet")


class ValidationReport:
    """Collects every check (check, expected, actual, tolerance, pass)."""

    COLUMNS = ["check", "expected", "actual", "tolerance", "pass"]

    def __init__(self) -> None:
        """Start with an empty list of check rows."""
        self.rows: list[dict] = []

    def add(self, check: str, expected, actual, tolerance=0, passed=None) -> bool:
        """Record one check; if passed is None, pass means expected == actual."""
        ok = bool(expected == actual) if passed is None else bool(passed)
        self.rows.append({"check": check, "expected": expected, "actual": actual,
                          "tolerance": tolerance, "pass": ok})
        return ok

    def extend(self, rows: list[dict]) -> None:
        """Add rows that already use the validation.csv keys."""
        for row in rows:
            self.add(row["check"], row["expected"], row["actual"],
                     row["tolerance"], row["pass"])

    @property
    def all_passed(self) -> bool:
        """True when every recorded check passed."""
        return all(row["pass"] for row in self.rows)

    def failures(self) -> list[dict]:
        """Return the rows that failed."""
        return [row for row in self.rows if not row["pass"]]

    def to_frame(self) -> pd.DataFrame:
        """Return the report as a DataFrame in validation.csv column order."""
        return pd.DataFrame(self.rows, columns=self.COLUMNS)


def log_step(audit: list[dict], step: str, source_file: str, operation: str,
             rule: str, before: int, after: int) -> None:
    """Append one audit record."""
    audit.append({"step": step, "source_file": source_file, "operation": operation,
                  "rule": rule, "rows_before": int(before), "rows_after": int(after)})


def read_input(cfg: dict, audit: list[dict]) -> pd.DataFrame:
    """Read one input as unvalidated strings: source_file, source_record, 6 fields."""
    path, fmt = cfg["path"], cfg["format"]
    name = Path(path).name
    if fmt in ("json", "parquet"):
        settings = {**cfg, "source_to_canonical":
                    cfg.get("source_to_canonical") or cfg["column_map"]}
        raw = load_nested(settings, audit)
        raw.insert(0, "source_file", name)
    else:
        raw = read_with_format(cfg)  # raises FileLevelError for unsupported formats
        log_step(audit, "read", name, f"read_{fmt}",
                 "parse documented layout, keep original strings", len(raw), len(raw))
    return raw


def to_canonical_types(valid: pd.DataFrame) -> pd.DataFrame:
    """Trim text and cast validated values to the canonical types."""
    out = valid.copy()
    for col in ("country", "continent"):
        out[col] = out[col].astype(str).str.strip()
    for col in ("year", "pop"):
        out[col] = out[col].map(lambda v: int(float(v))).astype("int64")
    for col in ("lifeExp", "gdpPercap"):
        out[col] = out[col].map(float).astype("float64")
    return out


def format_quarantine(rejected: pd.DataFrame) -> pd.DataFrame:
    """Shape rejected rows as source_file, source_record, reason, six fields."""
    cols = ["source_file", "source_record", "reason"] + CANONICAL_COLUMNS
    if rejected.empty:
        return pd.DataFrame(columns=cols)
    return rejected.rename(columns={"rejection_reason": "reason"})[cols]


def recover_file(cfg: dict, audit: list[dict]) -> dict:
    """Parse, validate, quarantine, deduplicate, check keys and sort one input."""
    name = Path(cfg["path"]).name
    raw = read_input(cfg, audit)
    valid_raw, rejected = validate_and_quarantine(raw)  # validate BEFORE casting
    log_step(audit, "validate", name, "validate_and_quarantine",
             "domain, finite, integral, range rules", len(raw), len(valid_raw))
    typed = to_canonical_types(valid_raw)
    deduped, dup_log = remove_exact_duplicates(typed)
    log_step(audit, "deduplicate", name, "remove_exact_duplicates",
             "exact duplicate of all six fields", len(typed), len(deduped))
    check_conflicting_keys(deduped[CANONICAL_COLUMNS])  # raises ConflictingKeyError
    log_step(audit, "conflict_check", name, "check_conflicting_keys",
             "same (country, year) with different values stops the run",
             len(deduped), len(deduped))
    canonical = (deduped[CANONICAL_COLUMNS].sort_values(["country", "year"])
                 .reset_index(drop=True))
    log_step(audit, "sort", name, "sort_values", "country, then year",
             len(deduped), len(canonical))
    return {"name": cfg.get("name", name), "raw_rows": len(raw),
            "valid_rows": len(typed), "canonical": canonical,
            "quarantine": format_quarantine(rejected), "duplicates": dup_log}


def compare_tables(left: pd.DataFrame, right: pd.DataFrame,
                   abs_tol: float = 1e-8) -> list[str]:
    """Compare two canonical tables by key; return a list of mismatch messages."""
    a = left.set_index(["country", "year"]).sort_index()
    b = right.set_index(["country", "year"]).sort_index()
    if a.index.has_duplicates or b.index.has_duplicates:
        return ["duplicate keys present"]
    only_left, only_right = a.index.difference(b.index), b.index.difference(a.index)
    if len(only_left) or len(only_right):
        return [f"keys differ: {len(only_left)} only left, {len(only_right)} only right"]
    b = b.loc[a.index]
    problems: list[str] = []
    bad = int((a["continent"].astype(str) != b["continent"].astype(str)).sum())
    if bad:
        problems.append(f"continent text differs in {bad} rows")
    bad = int((a["pop"].to_numpy() != b["pop"].to_numpy()).sum())
    if bad:
        problems.append(f"pop differs in {bad} rows")
    for col in ("lifeExp", "gdpPercap"):
        x, y = a[col].to_numpy(dtype=float), b[col].to_numpy(dtype=float)
        if int((np.isnan(x) != np.isnan(y)).sum()):
            problems.append(f"{col} missingness differs")
        bad = int((~np.isclose(x, y, rtol=0.0, atol=abs_tol, equal_nan=True)).sum())
        if bad:
            problems.append(f"{col} differs beyond {abs_tol} in {bad} rows")
    return problems


def export_canonical(df: pd.DataFrame, folder: Path) -> None:
    """Write canonical.csv/.xlsx/.json/.parquet without row indexes."""
    folder.mkdir(parents=True, exist_ok=True)
    df.to_csv(folder / "canonical.csv", index=False)
    df.to_excel(folder / "canonical.xlsx", sheet_name="observations", index=False)
    df.to_json(folder / "canonical.json", orient="records", indent=2)
    df.to_parquet(folder / "canonical.parquet", index=False)


def reload_export(path: Path, fmt: str) -> pd.DataFrame:
    """Reload one exported file exactly as stored."""
    if fmt == "csv":
        return pd.read_csv(path, dtype={"country": str, "continent": str},
                           keep_default_na=False)
    if fmt == "xlsx":
        return pd.read_excel(path, sheet_name="observations")
    if fmt == "json":
        return pd.read_json(path, orient="records", convert_dates=False)
    return pd.read_parquet(path)


def apply_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Reapply the declared canonical column order and types."""
    missing = set(CANONICAL_COLUMNS) - set(df.columns)
    if missing:
        raise FileLevelError(f"reloaded export is missing columns {sorted(missing)}")
    out = df[CANONICAL_COLUMNS].copy()
    for col in ("country", "continent"):
        out[col] = out[col].astype(str)
    for col, dtype in NUMERIC_DTYPES.items():
        out[col] = out[col].astype(dtype)
    return out


def verify_exports(canonical: pd.DataFrame, folder: Path, report: ValidationReport,
                   audit: list[dict], abs_tol: float) -> None:
    """Reload all four exports, reapply the schema and compare with the original."""
    for fmt in EXPORT_FORMATS:
        name = f"canonical.{fmt}"
        loaded = reload_export(folder / name, fmt)
        converted = [c for c, t in NUMERIC_DTYPES.items()
                     if c in loaded.columns and str(loaded[c].dtype) != t]
        typed = apply_schema(loaded)
        problems = compare_tables(canonical, typed, abs_tol)
        report.add(f"round trip {fmt}: row count", len(canonical), len(typed))
        report.add(f"round trip {fmt}: values match", 0, len(problems), abs_tol,
                   not problems)
        report.add(f"round trip {fmt}: dtypes after schema", str(NUMERIC_DTYPES),
                   str({c: str(typed[c].dtype) for c in NUMERIC_DTYPES}))
        log_step(audit, "round_trip", name, "reload_and_reapply_schema",
                 f"types converted after reload: {converted or 'none'}",
                 len(loaded), len(typed))


def add_reconciliation_checks(report: ValidationReport, results: list[dict],
                              exp: dict) -> None:
    """Add per-file and total row reconciliation checks."""
    for r in results:
        n, q = r["name"], len(r["quarantine"])
        d, c = len(r["duplicates"]), len(r["canonical"])
        report.add(f"{n}: raw rows", exp["raw_rows"], r["raw_rows"])
        report.add(f"{n}: rejected rows", exp["rejected_rows"], q)
        report.add(f"{n}: valid before deduplication",
                   exp["valid_before_deduplication"], r["valid_rows"])
        report.add(f"{n}: duplicate copies removed", exp["exact_duplicates_removed"], d)
        report.add(f"{n}: canonical rows", exp["canonical_rows"], c)
        report.add(f"{n}: raw = rejected + duplicates + canonical",
                   r["raw_rows"], q + d + c)
    report.add("total quarantined records", exp["rejected_rows"] * len(results),
               sum(len(r["quarantine"]) for r in results))
    report.add("total duplicate copies removed",
               exp["exact_duplicates_removed"] * len(results),
               sum(len(r["duplicates"]) for r in results))


def add_domain_checks(report: ValidationReport, canonical: pd.DataFrame,
                      manifest: dict) -> None:
    """Add key, domain and control checks for the shared canonical table."""
    ctrl = manifest["controls"]
    continents, years = set(manifest["allowed_continents"]), set(manifest["allowed_years"])
    life, pop, gdp = (canonical[c].to_numpy() for c in ("lifeExp", "pop", "gdpPercap"))
    report.add("canonical: column order", str(manifest["canonical_order"]),
               str(list(canonical.columns)))
    report.add("canonical: duplicate (country, year) keys", 0,
               int(canonical.duplicated(["country", "year"]).sum()))
    report.add("canonical: missing values", 0, int(canonical.isna().sum().sum()))
    report.add("canonical: disallowed continents", 0,
               int((~canonical["continent"].isin(continents)).sum()))
    report.add("canonical: disallowed years", 0,
               int((~canonical["year"].isin(years)).sum()))
    report.add("canonical: lifeExp outside (0, 120]", 0,
               int(((life <= 0) | (life > 120)).sum()))
    report.add("canonical: pop not > 0", 0, int((pop <= 0).sum()))
    report.add("canonical: gdpPercap not > 0", 0, int((gdp <= 0).sum()))
    report.add("canonical: countries", ctrl["countries"], int(canonical["country"].nunique()))
    report.add("canonical: Philippines rows", ctrl["philippines_rows"],
               int((canonical["country"] == "Philippines").sum()))
    total, count = asia_pop_total(canonical, "Asia", 2007)
    report.add("control: Asia 2007 population", ctrl["asia_2007_population"], total)
    report.add("control: Asia 2007 rows", ctrl["asia_2007_rows"], count)
    mask = ((canonical["country"].to_numpy() == "Philippines")
            & (canonical["year"].to_numpy() == 2007))
    report.add("control: Philippines 2007 population",
               ctrl["philippines_2007_population"], int(pop[mask].sum()))


def run_analysis(canonical: pd.DataFrame, cfg: dict, year: int, staging: Path,
                 report: ValidationReport, audit: list[dict]) -> None:
    """Build the pandas and NumPy outputs for the configured year."""
    countries = cfg.get("matrix_countries", ["Philippines", "Indonesia", "Thailand"])
    years = cfg.get("matrix_years", [1982, 1987, 1992, 1997, 2002, 2007])
    country = cfg.get("history_country", "Philippines")

    asia = asia_pop_life(canonical, year)
    history = phil_pop_life(canonical, country)
    matrix = build_population_matrix(canonical, countries, years)
    index = population_index(matrix)
    table = population_index_table(index, countries, years)

    asia.to_csv(staging / "asia_selected_year.csv", index=False)
    history.to_csv(staging / "country_history.csv", index=False)
    table.to_csv(staging / "population_index.csv", index=False)
    log_step(audit, "analysis", "canonical", "asia_pop_life",
             f"Asia, year {year}, rank method=min", len(canonical), len(asia))
    log_step(audit, "analysis", "canonical", "phil_pop_life",
             f"{country} history", len(canonical), len(history))
    log_step(audit, "analysis", "canonical", "population_index",
             "NumPy broadcast, first year = 100", matrix.size, index.size)

    report.add("NumPy: matrix shape before broadcasting",
               str((len(countries), len(years))), str(matrix.shape))
    report.add("NumPy: baseline column shape", str((len(countries), 1)),
               str(matrix[:, [0]].shape))
    report.add("NumPy: index shape after broadcasting",
               str((len(countries), len(years))), str(index.shape))
    report.extend(generate_validation_rows(canonical, countries, years,
                                           year=year, country=country))
    back = pd.read_csv(staging / "asia_selected_year.csv")
    report.add("export round trip: asia_selected_year rows", len(asia), len(back))
    report.add("export round trip: asia_selected_year population",
               int(asia["pop"].sum()), int(back["pop"].sum()))


def run_pipeline(cfg: dict, report: ValidationReport) -> bool:
    """Run everything in a staging folder; publish only if all checks pass."""
    audit: list[dict] = []
    manifest = json.loads(Path(cfg["manifest"]).read_text(encoding="utf-8"))
    year = int(cfg.get("reporting_year", 2007))
    abs_tol = float(cfg.get("tolerance", 1e-8))
    out_dir = Path(cfg.get("output_dir", "outputs"))
    exporter = StagingExporter(str(out_dir), cfg.get("staging_dir", "staging"))
    exporter.prepare_staging()
    staging = Path(exporter.staging_dir)

    results = [recover_file(c, audit) for c in cfg["inputs"]]  # errors stop the run
    add_reconciliation_checks(report, results, manifest["expected_per_file"])

    base, agree = results[0], True
    for other in results[1:]:
        problems = compare_tables(base["canonical"], other["canonical"], abs_tol)
        report.add(f"agreement: {base['name']} vs {other['name']}", 0, len(problems),
                   abs_tol, not problems)
        for p in problems:
            print(f"  mismatch {other['name']}: {p}", file=sys.stderr)
        agree = agree and not problems
    log_step(audit, "agreement", "all inputs", "compare_tables",
             f"by key; abs_tol={abs_tol}, rel_tol=0", len(results), len(results))
    if not agree:
        return False  # the shared canonical table is created only after agreement

    canonical = base["canonical"].copy()
    export_canonical(canonical, staging)
    log_step(audit, "export", "canonical", "export_canonical",
             "csv, xlsx, json, parquet; no index", len(canonical), len(canonical))
    verify_exports(canonical, staging, report, audit, abs_tol)
    report.add("StagingExporter round trip (all four formats)", True,
               exporter.verify_roundtrip_exports(canonical, abs_tol))
    add_domain_checks(report, canonical, manifest)
    run_analysis(canonical, cfg, year, staging, report, audit)

    pd.concat([r["quarantine"] for r in results], ignore_index=True).to_csv(
        staging / "quarantine.csv", index=False)
    pd.concat([r["duplicates"] for r in results], ignore_index=True).to_csv(
        staging / "duplicate_log.csv", index=False)
    pd.DataFrame(audit, columns=AUDIT_COLUMNS).to_csv(staging / "audit_log.csv", index=False)
    report.to_frame().to_csv(staging / "validation.csv", index=False)

    if not report.all_passed:
        return False
    exporter.publish_staging()
    (out_dir / "failed_validation_report.csv").unlink(missing_ok=True)
    return True


def write_failure_report(output_dir: str, report: ValidationReport,
                         error: Exception | None = None) -> Path:
    """Save failed_validation_report.csv (never touches published outputs)."""
    if error is not None:
        report.add("processing error", "no error", f"{type(error).__name__}: {error}",
                   0, False)
    path = Path(output_dir) / "failed_validation_report.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    report.to_frame().to_csv(path, index=False)
    return path