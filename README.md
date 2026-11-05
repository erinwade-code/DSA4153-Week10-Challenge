# DSA4153 Week 10 Group Challenge

## Setup
    python -m venv .venv
    # Windows: .venv\Scripts\activate    Mac/Linux: source .venv/bin/activate
    pip install -r requirements.txt
    python -m unittest discover tests -v
    python main.py --config config.json

## Team ownership
| Member | Name | Git identity (email) | Branch | Responsibility |
|---|---|---|---|---|
| 1 | Erin Wade Acuna | erinwade.acuna@ust.edu.ph | member1-readers | CSV and Excel readers, format configuration, reader checks |
| 2 | Neo Carl Jacinto | neocarl.jacinto@ust.edu.ph | member2-readers | Nested JSON and Parquet readers, column mapping, normalization checks |
| 3 | Lance Wesley Santos | lancewesley.santos@ust.edu.ph | member3-validation | Row validation, quarantine, duplicates/conflicts, rejection checks |
| 4 | John Oswald Amon | johnoswald.amon@ust.edu.ph | member4-analysis | pandas analysis, NumPy matrix, calculation checks |
| 5 | | | member5-export | Export/reload comparison, staging, CLI/audit, failure checks |

## Reader output contract (all readers must follow this)
A pandas DataFrame, all values as strings, with columns exactly:
`source_file, source_record, country, continent, year, lifeExp, pop, gdpPercap`
- `source_record` is the one-based data-record order (excludes header, comments, metadata).
- Readers do not trim, clean, cast, or drop rows. Validation does that.
- File-level problems raise `src.common.FileLevelError`.
