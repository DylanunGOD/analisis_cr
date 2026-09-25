"""Shared paths and loading helpers for the data scripts.

Everything is resolved from the repository root (not from the directory the
script is launched from), so the scripts work no matter where you run them.

Data layer convention:
    data/raw/        read-only, never modified (source of truth)
    data/interim/    output of mechanical cleaning (duplicates, dtypes)
    data/processed/  datasets ready for analysis/modelling
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"

# Single traceability log: every cleaning step appends a row here.
CHANGELOG = REPORTS / "cleaning_changelog.csv"

# utf-8-sig strips the BOM carried by product_category_name_translation.csv
# and behaves like plain utf-8 for the files that do not have one.
ENCODING = "utf-8-sig"


def raw_datasets():
    """List the CSV files in data/raw, sorted by name."""
    return sorted(RAW.glob("*.csv"))


def load_csv(path):
    """Read a CSV using the project-wide encoding.

    low_memory=False stops pandas from inferring different dtypes per chunk in
    the large files (geolocation has ~1M rows).
    """
    return pd.read_csv(path, sep=",", encoding=ENCODING, low_memory=False)
