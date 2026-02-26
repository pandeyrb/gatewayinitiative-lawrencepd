#!/usr/bin/env python3
"""
Database Setup Utility — converts checkpoint CSV to DuckDB for fast querying.

Usage:
    python db_setup.py                          # Build from CSV (skip if .duckdb exists)
    python db_setup.py --rebuild                # Force rebuild from CSV
    python db_setup.py --append new_data.csv    # Append new rows only
"""

import argparse
import os
import sys
import time

import duckdb


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, "checkpoint15_misdemeanor_warrant.csv")
DB_PATH = os.path.join(SCRIPT_DIR, "incidents.duckdb")


def build_database(csv_path: str, db_path: str) -> None:
    """Create a DuckDB database from the checkpoint CSV."""
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV file not found: {csv_path}")
        sys.exit(1)

    print(f"Reading CSV: {csv_path}")
    start = time.time()

    conn = duckdb.connect(db_path)

    # Drop existing table if rebuilding
    conn.execute("DROP TABLE IF EXISTS incidents")

    # Create table from CSV using DuckDB's native reader (much faster than pandas)
    conn.execute(f"""
        CREATE TABLE incidents AS
        SELECT
            CAST("Date" AS TIMESTAMP) AS Date,
            "Type"          AS type,
            "Location"      AS location,
            "Arrested"      AS arrested,
            "Location Prefix" AS location_prefix,
            "DOB"           AS dob,
            "Charges"       AS charges,
            CAST(latitude  AS DOUBLE) AS latitude,
            CAST(longitude AS DOUBLE) AS longitude,
            "Cleaned Location" AS cleaned_location,
            person_id,
            category,
            "Year"          AS year,
            crime_severity,
            CAST("Age" AS DOUBLE) AS age,
            statutes,
            standardized_charges,
            CAST("has_warrant" AS BOOLEAN) AS has_warrant,
            CAST("is_misdemeanor" AS BOOLEAN) AS is_misdemeanor
        FROM read_csv_auto('{csv_path}', header=true, all_varchar=false)
    """)

    # Create indexes on the columns used for filtering
    print("Creating indexes…")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_year        ON incidents(year)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_category    ON incidents(category)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_severity    ON incidents(crime_severity)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_lat_lon     ON incidents(latitude, longitude)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_misdemeanor ON incidents(is_misdemeanor)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_warrant     ON incidents(has_warrant)")

    # Composite index for the most common filter combination
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_filters
        ON incidents(year, category, crime_severity)
    """)

    # Update statistics for the query optimizer
    conn.execute("ANALYZE incidents")

    # Verify
    row_count = conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
    null_coords = conn.execute(
        "SELECT COUNT(*) FROM incidents WHERE latitude IS NULL OR longitude IS NULL"
    ).fetchone()[0]

    elapsed = time.time() - start
    print(f"Done in {elapsed:.1f}s")
    print(f"  Total rows:     {row_count:,}")
    print(f"  Null lat/lon:   {null_coords:,}")
    print(f"  Valid coords:   {row_count - null_coords:,}")
    print(f"  Database file:  {db_path}")
    print(f"  Database size:  {os.path.getsize(db_path) / 1_048_576:.1f} MB")

    conn.close()


def append_data(csv_path: str, db_path: str) -> None:
    """Append new rows from a CSV, skipping duplicates by incident_num."""
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found: {db_path}. Run without --append first.")
        sys.exit(1)
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV file not found: {csv_path}")
        sys.exit(1)

    print(f"Appending new rows from: {csv_path}")
    start = time.time()

    conn = duckdb.connect(db_path)

    before_count = conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]

    # Insert only rows whose (Date, person_id, Type) combo doesn't already exist
    conn.execute(f"""
        INSERT INTO incidents
        SELECT
            CAST("Date" AS TIMESTAMP) AS Date,
            "Type"          AS type,
            "Location"      AS location,
            "Arrested"      AS arrested,
            "Location Prefix" AS location_prefix,
            "DOB"           AS dob,
            "Charges"       AS charges,
            CAST(latitude  AS DOUBLE) AS latitude,
            CAST(longitude AS DOUBLE) AS longitude,
            "Cleaned Location" AS cleaned_location,
            person_id,
            category,
            "Year"          AS year,
            crime_severity,
            CAST("Age" AS DOUBLE) AS age,
            statutes,
            standardized_charges,
            CAST("has_warrant" AS BOOLEAN) AS has_warrant,
            CAST("is_misdemeanor" AS BOOLEAN) AS is_misdemeanor
        FROM read_csv_auto('{csv_path}', header=true, all_varchar=false) AS new_data
        WHERE md5(CAST(new_data."Date" AS VARCHAR) || COALESCE(new_data.person_id, '') || COALESCE(new_data."Type", ''))
        NOT IN (
            SELECT md5(CAST(Date AS VARCHAR) || COALESCE(person_id, '') || COALESCE(type, ''))
            FROM incidents
        )
    """)

    # Re-analyze after insert
    conn.execute("ANALYZE incidents")

    after_count = conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
    new_rows = after_count - before_count

    elapsed = time.time() - start
    print(f"Done in {elapsed:.1f}s")
    print(f"  Rows before:  {before_count:,}")
    print(f"  New rows:     {new_rows:,}")
    print(f"  Rows after:   {after_count:,}")

    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Build or update the incidents DuckDB database.")
    parser.add_argument(
        "--rebuild", action="store_true",
        help="Force rebuild the database from the checkpoint CSV"
    )
    parser.add_argument(
        "--append", type=str, metavar="CSV_FILE",
        help="Append new rows from a CSV file (skips duplicates by Incident #)"
    )
    args = parser.parse_args()

    if args.append:
        append_data(args.append, DB_PATH)
    elif args.rebuild or not os.path.exists(DB_PATH):
        build_database(CSV_PATH, DB_PATH)
    else:
        print(f"Database already exists: {DB_PATH}")
        print(f"  Size: {os.path.getsize(DB_PATH) / 1_048_576:.1f} MB")
        conn = duckdb.connect(DB_PATH, read_only=True)
        row_count = conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
        print(f"  Rows: {row_count:,}")
        conn.close()
        print("Use --rebuild to recreate from CSV, or --append <file> to add new data.")


if __name__ == "__main__":
    main()
