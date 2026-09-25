"""First cleaning step: drop exact duplicate rows.

Reads from data/raw (never modified), writes the result to data/interim and
records every change in reports/cleaning_changelog.csv.

The changelog is cumulative: each run appends new rows instead of overwriting,
so the history of what was done and when is preserved.

Usage:
    python src/data/clean_duplicates.py
"""

from datetime import datetime

import pandas as pd

from paths import CHANGELOG, INTERIM, REPORTS, load_csv, raw_datasets

SCRIPT = "clean_duplicates.py"


def log_changes(events):
    """Append the events to the changelog, writing the header if it is new."""
    REPORTS.mkdir(parents=True, exist_ok=True)
    changelog = pd.DataFrame(events)
    changelog.to_csv(
        CHANGELOG,
        mode="a",
        header=not CHANGELOG.exists(),
        index=False,
        encoding="utf-8",
    )
    return changelog


def drop_duplicate_rows(df):
    """Drop exact duplicate rows and reset the index.

    All columns are compared (exact duplicate). Business-key duplicates -for
    instance the same zip_code with different coordinates- are handled later,
    once the rule for each dataset has been decided.
    """
    return df.drop_duplicates().reset_index(drop=True)


def clean():
    """Deduplicate every raw CSV and record the changes."""
    INTERIM.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat(timespec="seconds")
    events = []

    for path in raw_datasets():
        df = load_csv(path)
        before = len(df)

        cleaned = drop_duplicate_rows(df)
        after = len(cleaned)

        output = INTERIM / f"{path.stem}.csv"
        cleaned.to_csv(output, index=False, encoding="utf-8")

        events.append({
            "timestamp": timestamp,
            "dataset": path.stem,
            "step": "drop_duplicates",
            "script": SCRIPT,
            "input": f"data/raw/{path.name}",
            "output": f"data/interim/{output.name}",
            "rows_before": before,
            "rows_after": after,
            "rows_removed": before - after,
            "pct_removed": round(100 * (before - after) / before, 2) if before else 0.0,
            "columns": cleaned.shape[1],
            "details": "exact duplicates across all columns",
        })

        print(f"{path.stem}: {before:,} -> {after:,} rows "
              f"(-{before - after:,}) saved to data/interim/{output.name}")

    changelog = log_changes(events)
    print(f"\nChangelog updated: {CHANGELOG}")
    return changelog


if __name__ == "__main__":
    clean()
