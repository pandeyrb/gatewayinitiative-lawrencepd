# Database Setup — Lawrence PD Incident Dashboard

This document explains how the app's DuckDB database is built and used. It's aimed at
someone new to the project (e.g. a student) who needs to understand the data layer
before touching `streamlit-app/main_v3.py`.

## 1. Overview

The app used to load `checkpoint15_misdemeanor_warrant.csv` directly into a pandas DataFrame on every run. That CSV currently holds **~424,000 rows** and grows over
time, and reloading it on every filter change was slow.

`streamlit-app/db_setup.py` converts that CSV into a **DuckDB** database
(`streamlit-app/incidents.duckdb`) — a single-file, indexed, SQL-queryable database.
`main_v3.py` queries that file directly instead of re-reading and re-filtering the
whole CSV in pandas.

Two Streamlit caching decorators matter here, and the app uses both:

- `@st.cache_data` — caches the *return value* of a function (a DataFrame, a list of
  years, etc.). Used for anything that returns data.
- `@st.cache_resource` — caches a *live object* that shouldn't be copied/serialized,
  like a database connection. Used once, for the DuckDB connection itself.

## 2. Building the database (`db_setup.py`)

```bash
cd streamlit-app
python db_setup.py                          # build only if incidents.duckdb doesn't exist yet
python db_setup.py --rebuild                # drop and recreate from the CSV
python db_setup.py --append new_data.csv    # add new rows only, skipping duplicates
```

`incidents.duckdb` is **gitignored** (see root `.gitignore`), so after cloning the
repo fresh, this file will not exist until someone runs `db_setup.py` locally.

### What the build step does

1. Reads `checkpoint15_misdemeanor_warrant.csv` using DuckDB's native `read_csv_auto()`
   (faster than loading through pandas first).
2. Creates a table named `incidents`, casting and renaming columns along the way — see
   the schema table below.
3. Builds indexes on the columns the app filters by most often: `year`, `category`,
   `crime_severity`, `(latitude, longitude)`, `is_misdemeanor`, `has_warrant`, plus a
   composite index on `(year, category, crime_severity)` for the common combined filter.
4. Runs `ANALYZE incidents` so DuckDB's query planner has fresh statistics.
5. Prints a verification summary: row count, how many rows are missing lat/lon, and
   the resulting file size.

### Updating with new data (`--append`)

`append_data()` inserts only rows that are genuinely new. It builds an MD5 hash of
`Date + person_id + type` for each incoming row and excludes any row whose hash
already exists in the table:

```sql
WHERE md5(Date || person_id || type) NOT IN (
    SELECT md5(Date || person_id || type) FROM incidents
)
```

This is what makes re-running the scraper/append step **idempotent** — running it
again on data that's already been ingested won't create duplicate rows. Use
`--rebuild` instead if you need a clean rebuild from the checkpoint CSV (e.g. after
the CSV's schema changes).

## 3. Schema

| Column (in `incidents`) | Source CSV column | Type | Notes |
|---|---|---|---|
| `Date` | `Date` | `TIMESTAMP` | cast from string |
| `type` | `Type` | varchar | renamed |
| `location` | `Location` | varchar | renamed |
| `arrested` | `Arrested` | varchar | renamed |
| `location_prefix` | `Location Prefix` | varchar | renamed |
| `dob` | `DOB` | varchar | renamed |
| `charges` | `Charges` | varchar | renamed |
| `latitude` | `latitude` | `DOUBLE` | cast |
| `longitude` | `longitude` | `DOUBLE` | cast |
| `cleaned_location` | `Cleaned Location` | varchar | renamed |
| `person_id` | `person_id` | varchar | anonymized hash (see root CLAUDE.md) |
| `category` | `category` | varchar | FBI-style crime category |
| `year` | `Year` | varchar | renamed |
| `crime_severity` | `crime_severity` | varchar | "Serious" / "Not-Serious" |
| `age` | `Age` | `DOUBLE` | cast, renamed |
| `statutes` | `statutes` | varchar | |
| `standardized_charges` | `standardized_charges` | varchar | |
| `has_warrant` | `has_warrant` | `BOOLEAN` | cast |
| `is_misdemeanor` | `is_misdemeanor` | `BOOLEAN` | cast |

## 4. How `main_v3.py` consumes the database

### Connection

```python
@st.cache_resource
def get_db_connection():
    db_path = os.path.join(SCRIPT_DIR, "incidents.duckdb")
    if not os.path.exists(db_path):
        return None
    return duckdb.connect(db_path, read_only=True)
```

- Opened **read-only** — the Streamlit app never writes to the database; all writes
  happen offline via `db_setup.py`.
- Cached with `@st.cache_resource` so the connection is opened once per app session,
  not on every rerun.
- Returns `None` if the `.duckdb` file is missing (e.g. right after a fresh clone,
  before anyone has run `db_setup.py`).

### Fallback pattern: DuckDB path vs. pandas path

`_use_duckdb()` checks whether `get_db_connection()` returned a real connection. Based
on that, Tab 3 ("Spatial Insights") picks between two parallel code paths for every
piece of derived data:

| Data needed | DuckDB version | pandas fallback |
|---|---|---|
| Distinct incident categories | `get_incident_types_duckdb()` | `get_incident_types_pandas()` |
| Distinct years | `get_unique_years_duckdb()` | (computed inline from the loaded CSV) |
| Filtered incidents | `filter_data_duckdb()` | `filter_data_pandas()` |
| Map hotspot bins | `calculate_hotspots_duckdb()` | `calculate_hotspots_pandas()` |

This means the app **degrades gracefully**: if `incidents.duckdb` doesn't exist, it
falls back to loading and filtering the CSV directly with pandas via `load_data()`
(slower, but functional). This is why a student can clone the repo and run the app
immediately, even before running `db_setup.py` — though performance will be much
better after building the database.

### Query functions are also cached

Every `_duckdb` and `_pandas` function above is wrapped in `@st.cache_data`, keyed on
its arguments (selected years, categories, severity filter, hotspot percentile). So
picking the same filter combination twice in one session reuses the cached result
instead of re-querying.

## 5. Gotchas

- **The `.duckdb` file is gitignored.** After cloning, you must run
  `python db_setup.py` from `streamlit-app/` before the fast path is available.
- **The connection is read-only.** There's no code path in the app that modifies
  `incidents.duckdb` — all updates happen by re-running `db_setup.py` (`--append` or
  `--rebuild`) separately.
- **Indexes only pay off on the DuckDB path.** They have no effect on the pandas
  fallback path — that code filters DataFrames in memory instead.
- **Dedup key is `Date + person_id + type`**, not a formal `incident_num`/primary key.
  If two genuinely different incidents share all three values, `--append` would
  incorrectly treat the second as a duplicate and skip it.
