"""Audit of the raw CSV files: nulls, dtypes and duplicate rows.

This is a READ-ONLY step: nothing under data/raw is modified. Its purpose is to
decide what to clean before touching the data.

Writes two reports to reports/:
    audit_datasets.csv  -> one row per CSV (overview)
    audit_columns.csv   -> one row per column (the detail used for cleaning)

Usage:
    python src/data/preview.py
"""

import pandas as pd

from paths import REPORTS, load_csv, raw_datasets


def dataset_summary(df, name):
    """Overview of a DataFrame: size, dtypes, nulls and duplicates."""
    dtypes = df.dtypes.value_counts()
    cells = df.shape[0] * df.shape[1]
    nulls = int(df.isna().sum().sum())
    duplicates = int(df.duplicated().sum())

    return {
        "dataset": name,
        "rows": df.shape[0],
        "columns": df.shape[1],
        "object_columns": int(df.select_dtypes(include="object").shape[1]),
        "numeric_columns": int(df.select_dtypes(include="number").shape[1]),
        "columns_with_nulls": int((df.isna().sum() > 0).sum()),
        "null_cells": nulls,
        "pct_null_cells": round(100 * nulls / cells, 2) if cells else 0.0,
        "duplicate_rows": duplicates,
        "pct_duplicate_rows": round(100 * duplicates / len(df), 2) if len(df) else 0.0,
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 1),
        "dtypes": ", ".join(f"{k}={v}" for k, v in dtypes.items()),
    }


def column_summary(df, name):
    """Per-column detail: dtype, nulls, unique values and a sample value."""
    nulls = df.isna().sum()
    detail = pd.DataFrame(
        {
            "dataset": name,
            "column": df.columns,
            "dtype": df.dtypes.astype(str).values,
            "is_object": df.dtypes.eq("object").values,
            "nulls": nulls.values,
            "pct_nulls": (100 * nulls / len(df)).round(2).values if len(df) else 0.0,
            "non_nulls": df.notna().sum().values,
            "unique_values": df.nunique(dropna=True).values,
        }
    )
    # First non-null value of each column, useful to spot formats (dates, ids).
    detail["sample"] = [
        df[c].dropna().iloc[0] if df[c].notna().any() else pd.NA for c in df.columns
    ]
    return detail


def audit():
    """Walk data/raw, print the diagnosis and save both reports."""
    REPORTS.mkdir(parents=True, exist_ok=True)

    summaries, columns = [], []

    for path in raw_datasets():
        df = load_csv(path)
        name = path.stem

        summaries.append(dataset_summary(df, name))
        columns.append(column_summary(df, name))

        print(f"\n=== {name} ===")
        print(f"rows={df.shape[0]:,}  columns={df.shape[1]}  "
              f"object={df.select_dtypes(include='object').shape[1]}  "
              f"duplicates={df.duplicated().sum():,}")

        with_nulls = df.isna().sum()
        with_nulls = with_nulls[with_nulls > 0].sort_values(ascending=False)
        if with_nulls.empty:
            print("  no nulls")
        else:
            for column, n in with_nulls.items():
                print(f"  {column}: {n:,} nulls ({100 * n / len(df):.2f}%)")

    datasets_table = pd.DataFrame(summaries)
    columns_table = pd.concat(columns, ignore_index=True)

    datasets_table.to_csv(REPORTS / "audit_datasets.csv", index=False, encoding="utf-8")
    columns_table.to_csv(REPORTS / "audit_columns.csv", index=False, encoding="utf-8")

    print("\n--- Overview ---")
    print(datasets_table[["dataset", "rows", "columns", "object_columns",
                          "null_cells", "duplicate_rows"]].to_string(index=False))
    print(f"\nReports saved to {REPORTS}")

    return datasets_table, columns_table


if __name__ == "__main__":
    audit()
