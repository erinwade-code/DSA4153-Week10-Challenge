from pathlib import Path
import pandas as pd

from src.validation import (
    validate_and_quarantine,
    check_conflicting_keys,
    remove_exact_duplicates,
)

# Original CSV settings from the assignment
input_path = Path("data/country_records.csv")
output_dir = Path("outputs")
output_dir.mkdir(exist_ok=True)

# Read the CSV using its actual format
records = pd.read_csv(
    input_path,
    sep=";",
    encoding="cp1252",
    skiprows=2,
)

# Map raw columns to canonical names
records = records.rename(
    columns={
        "CountryName": "country",
        "ContinentName": "continent",
        "ObservationYear": "year",
        "LifeYears": "lifeExp",
        "PopulationPersons": "pop",
        "GDPPerPerson": "gdpPercap",
    }
)

# Keep only canonical columns
records = records[
    ["country", "continent", "year", "lifeExp", "pop", "gdpPercap"]
]

# Validate and quarantine invalid rows
valid_records, rejected_records = validate_and_quarantine(records)

# Detect conflicting country-year records
check_conflicting_keys(valid_records)

# Remove exact duplicates
clean_records, duplicate_log = remove_exact_duplicates(valid_records)

# Sort the cleaned dataset
clean_records = clean_records.sort_values(
    ["country", "year"]
).reset_index(drop=True)

# Save output files
clean_records.to_csv(output_dir / "country_records_clean.csv", index=False)
rejected_records.to_csv(output_dir / "quarantine.csv", index=False)
duplicate_log.to_csv(output_dir / "duplicate_log.csv", index=False)

print(f"Cleaned rows: {len(clean_records)}")
print(f"Quarantined rows: {len(rejected_records)}")
print(f"Duplicate copies removed: {len(duplicate_log)}")
print(f"Saved cleaned CSV to: {output_dir / 'country_records_clean.csv'}")
