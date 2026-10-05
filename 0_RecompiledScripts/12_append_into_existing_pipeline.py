#!/usr/bin/env python3
"""
Append checkpoint11 rows into the existing checkpoint15 final CSV.

This script is intentionally idempotent: rows already present in checkpoint15 are
skipped using a stable incident key. New checkpoint11 rows are aligned to the
checkpoint15 schema before writing, so final-only columns that checkpoint11 does
not have are added as missing values.
"""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SOURCE = REPO_ROOT / "streamlit-app" / "checkpoint11_combined_data.csv"
DEFAULT_TARGET = REPO_ROOT / "streamlit-app" / "checkpoint15_misdemeanor_warrant.csv"

DEDUP_KEY = ["Incident #", "Date", "Type", "person_id"]


def normalize_key_part(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def build_row_key(df: pd.DataFrame, key_columns: list[str]) -> pd.Series:
    missing = [column for column in key_columns if column not in df.columns]
    if missing:
        raise ValueError(f"Missing dedupe key columns: {missing}")

    key = normalize_key_part(df[key_columns[0]])
    for column in key_columns[1:]:
        key = key + "||" + normalize_key_part(df[column])
    return key


def align_to_target_schema(source_df: pd.DataFrame, target_columns: list[str]) -> pd.DataFrame:
    aligned = source_df.copy()

    for column in target_columns:
        if column not in aligned.columns:
            aligned[column] = pd.NA

    return aligned[target_columns]


def append_checkpoint(source_path: Path, target_path: Path, dry_run: bool) -> None:
    if not source_path.exists():
        raise FileNotFoundError(f"Source CSV not found: {source_path}")
    if not target_path.exists():
        raise FileNotFoundError(f"Target CSV not found: {target_path}")

    source_df = pd.read_csv(source_path, low_memory=False)
    target_df = pd.read_csv(target_path, low_memory=False)

    source_aligned = align_to_target_schema(source_df, list(target_df.columns))

    existing_keys = set(build_row_key(target_df, DEDUP_KEY))
    source_keys = build_row_key(source_aligned, DEDUP_KEY)
    new_rows = source_aligned.loc[~source_keys.isin(existing_keys)].copy()

    # Drop all-NA columns from the incoming slice before concat; pandas fills
    # those target columns back with NA for appended rows.
    new_rows_for_concat = new_rows.dropna(axis=1, how="all")
    combined_df = pd.concat([target_df, new_rows_for_concat], ignore_index=True)

    print(f"Source rows:       {len(source_df):,}")
    print(f"Existing rows:     {len(target_df):,}")
    print(f"Rows to append:    {len(new_rows):,}")
    print(f"Final row count:   {len(combined_df):,}")
    print(f"Target columns:    {len(target_df.columns):,}")

    if dry_run:
        print("Dry run only. No files were changed.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = target_path.with_name(f"{target_path.stem}.backup_{timestamp}{target_path.suffix}")
    shutil.copy2(target_path, backup_path)

    combined_df.to_csv(target_path, index=False)

    print(f"Backup written:    {backup_path}")
    print(f"Updated CSV:       {target_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append checkpoint11_combined_data.csv into checkpoint15_misdemeanor_warrant.csv."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"CSV to append from. Default: {DEFAULT_SOURCE}",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=DEFAULT_TARGET,
        help=f"Existing final CSV to append into. Default: {DEFAULT_TARGET}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be appended without writing files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    append_checkpoint(
        source_path=args.source.resolve(),
        target_path=args.target.resolve(),
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
