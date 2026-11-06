"""Stopgap: build asia_selected_year.csv from the CSV input only."""
import json
from pathlib import Path

import pandas as pd

from src.common import CANONICAL_COLUMNS
from src.population import asia_pop_life, phil_pop_life
from src.readers import read_csv_records
from src.validation import remove_exact_duplicates, validate_and_quarantine

cfg = json.loads(Path("config.json").read_text(encoding="utf-8"))
year = int(cfg.get("reporting_year", 2007))
csv_cfg = next(i for i in cfg["inputs"] if i["format"] == "csv")

raw = read_csv_records(csv_cfg)
valid, rejected = validate_and_quarantine(raw)  # validate before casting
for col in ("country", "continent"):
    valid[col] = valid[col].astype(str).str.strip()
for col in ("year", "pop"):
    valid[col] = valid[col].map(lambda v: int(float(v))).astype("int64")
for col in ("lifeExp", "gdpPercap"):
    valid[col] = valid[col].map(float).astype("float64")

clean, dups = remove_exact_duplicates(valid)
canonical = clean[CANONICAL_COLUMNS].sort_values(["country", "year"]).reset_index(drop=True)
print("raw", len(raw), "rejected", len(rejected), "duplicates", len(dups),
      "canonical", len(canonical))

out = Path("outputs")
out.mkdir(exist_ok=True)
asia = asia_pop_life(canonical, year)
asia.to_csv(out / "asia_selected_year.csv", index=False)
phil_pop_life(canonical).to_csv(out / "country_history.csv", index=False)
print("asia rows", len(asia), "population", int(asia["pop"].sum()))