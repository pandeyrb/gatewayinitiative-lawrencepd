# Lawrence Police Department — Data Pipeline Documentation

This document describes the complete data pipeline for the Lawrence Police Dashboard project, from raw PDF ingestion through cleaning, enrichment, and delivery to the Streamlit app. It is intended as an onboarding reference for new team members.

---

## 1. Overview

The pipeline transforms publicly available daily police log PDFs from the Lawrence (MA) Police Department into a structured, analysis-ready dataset powering an interactive Streamlit dashboard. The dataset covers 2018–2024 and contains ~424,000 incident records.

**The pipeline produces a single final artifact:** `checkpoint15_misdemeanor_warrant.csv` — a 20-column CSV with geocoded incidents, anonymized person IDs, FBI-style crime categories, standardized charges, and misdemeanor/warrant flags.

**The goal of automation:** Currently, each step below is a manually-run Jupyter notebook. Your task is to automate this into a single end-to-end pipeline that can ingest new data and produce an updated dataset and dashboard.

---

## 2. Prerequisites

| Requirement | Why |
|---|---|
| Python 3.11 | Target version (per devcontainer config) |
| Virtual environment | `venv/` in repo root; activate with `source venv/Scripts/activate` (Windows Git Bash) |
| Tesseract OCR | Required for scanned PDF extraction (2023-2024 missing-date PDFs) |
| OpenCage API key | Stored in `config.json` (gitignored); required only for geocoding step |
| `requirements.txt` | Root-level file has all pipeline dependencies; `pip install -r requirements.txt` |

---

## 3. Pipeline Diagram

```
PHASE 1: DATA INGESTION
========================
   Lawrence PD Website
   (lawpd.com/DocumentCenter/View/{id})
          │
          ▼
   ┌──────────────────┐
   │ Step 1: Download  │  scripts/download_pdfs.ipynb
   │ PDFs              │  → data/pdfs/ (2018-2022)
   │                   │  → data/2023_2024_pdfs/ (2023-2024)
   └────────┬─────────┘
            ▼
   ┌──────────────────┐
   │ Step 2: Convert   │  scripts/convert_pdfs.ipynb
   │ PDFs → CSV        │  → Raw CSVs (8 columns)
   └────────┬─────────┘
            ▼
   ┌──────────────────┐
   │ Step 3: Find      │  scripts/date_check.ipynb
   │ Missing Dates     │  → scripts/missing_dates.txt (96 dates)
   └────────┬─────────┘
            ▼
   ┌──────────────────┐
   │ Step 4: Process   │  scripts/convert_pdfs.ipynb (missing dates section)
   │ Missing PDFs      │  → data/missing_dates_csv/unclean_missing_dates.csv
   └────────┬─────────┘
            ▼

PHASE 2: CLEANING & ENRICHMENT
================================
   ┌──────────────────┐
   │ Step 5: Clean &   │  scripts/clean_csv.ipynb
   │ Deduplicate       │  → CP1, CP2
   └────────┬─────────┘
            ▼
   ┌──────────────────┐
   │ Step 6: Geocode   │  scripts/address_mapping.ipynb
   │ Addresses         │  → geocoded_addresses_final.csv
   └────────┬─────────┘
            ▼
   ┌──────────────────┐
   │ Step 7: Merge     │  scripts/geocode_merge.ipynb
   │ Geocoded Data     │  → CP3, CP4
   └────────┬─────────┘
            ▼
   ┌──────────────────┐
   │ Step 8: Hash PII  │  scripts/hash.ipynb
   │ (Anonymize)       │  → CP5
   └────────┬─────────┘
            ▼
   ┌──────────────────┐
   │ Step 9: Categorize │  scripts/categorize_visualize.ipynb
   │ & Classify         │  → CP6, CP7, CP8, CP9
   └────────┬──────────┘
            ▼
   ┌──────────────────┐
   │ Step 10: Combine   │  (merge main + missing dates datasets)
   │ Datasets           │  → CP10
   └────────┬──────────┘
            ▼
   ┌──────────────────┐
   │ Step 11: Readable  │  scripts/Standardize_Categories.ipynb
   │ Category Names     │  → CP11
   └────────┬──────────┘
            ▼
   ┌──────────────────┐
   │ Step 12: Compute   │  scripts/age.ipynb
   │ Age                │  → CP12
   └────────┬──────────┘
            ▼
   ┌──────────────────┐
   │ Step 13: Clean &   │  scripts/charges/clean_charges.ipynb
   │ Expand Charges     │  → CP13
   └────────┬──────────┘
            ▼
   ┌──────────────────┐
   │ Step 14: Standard- │  scripts/charges/standardize_charges.ipynb
   │ ize Charges        │  → CP14
   └────────┬──────────┘
            ▼
   ┌──────────────────┐
   │ Step 15: Misde-    │  scripts/charges/add_misdemeanor_warrant_cols.ipynb
   │ meanor & Warrant   │  → CP15 (FINAL)
   └────────┬──────────┘
            ▼

PHASE 3: APP DELIVERY
======================
   ┌──────────────────┐
   │ Step 16: Copy CP15 │  → streamlit-app/checkpoint15_misdemeanor_warrant.csv
   │ to App Directory   │
   └────────┬──────────┘
            ▼
   ┌──────────────────┐
   │ Step 17: Build     │  python streamlit-app/db_setup.py
   │ DuckDB             │  → streamlit-app/incidents.duckdb
   └────────┬──────────┘
            ▼
   ┌──────────────────┐
   │ Step 18: Launch    │  streamlit run streamlit-app/main_v3.py
   │ Dashboard          │  → http://localhost:8501
   └──────────────────┘
```

---

## 4. Phase 1: Data Ingestion

### Step 1: Download PDFs

**Notebook:** `scripts/download_pdfs.ipynb`
**Input:** Lawrence PD website — `https://lawpd.com/DocumentCenter/View/{id}`
**Output:** PDF files organized by year and month:
- `data/pdfs/{YYYY}_{monthname}/` (2018-2022, ID range 2274–49898)
- `data/2023_2024_pdfs/{YYYY}_{monthname}/` (2023-2024, ID range 45274–65274)
- `data/failures.csv` (log of failed downloads)

The notebook iterates through document IDs on the Lawrence PD website, downloading each PDF. It parses the filename from the HTTP `Content-Disposition` header, extracts the date using the pattern `MM-DD-YYYY.pdf`, and organizes files into year/month subdirectories.

**Key transformations:**
- Filename parsing: regex `^(\d{2})-(\d{2})-(\d{4})$` to extract date from filename
- PDFs without parseable dates go to `data/no_date/` with a headline extracted from the first page
- Failed downloads (non-200 status, non-PDF content type) logged to `failures.csv`

**Gotchas:**
- The ID ranges overlap (45274–49898 covered by both runs). Duplicates are handled by filename — same date = same file path = overwrite.
- 10-second timeout per request. Flaky network = missing files. Check `failures.csv` afterward.
- The website structure may change; ID ranges may need updating for future years.

---

### Step 2: Convert PDFs to CSV

**Notebook:** `scripts/convert_pdfs.ipynb`
**Input:** PDF directories from Step 1
**Output:** Raw CSVs with 8 columns: `Incident #, Date, Type, Location, Arrested, Name, DOB, Charges`
- `data/pdfs/lawrence_2018_to_2022.csv`
- `data/pdfs/lawrence_2023_2024.csv` (and `new_lawrence_2023_2024.csv` with OCR)
- `skipped_files.csv` (PDFs that couldn't be parsed)

The notebook reads each PDF using pdfplumber, splits text into individual incidents using separator patterns (`===` or `---` lines of 10+ characters), then applies regex patterns to extract each field.

**Key transformations:**
- Text extraction via pdfplumber (vector-based, fast)
- Incident splitting on `[=-]{10,}` separator pattern
- 7 regex patterns for field extraction (Incident #, Date, Type, Location, Name, DOB, Charges)
- Charges from multiple lines joined with `"; "` separator
- HTML entity unescaping (`&amp;` → `&`)

**Gotchas:**
- **2018-2022 vs 2023-2024 are processed differently.** 2018-2022 uses strict folder validation (`yyyy_law_pd_data` pattern); 2023-2024 uses simpler flat month folders.
- PDFs without standard separators are **skipped entirely** (logged to `skipped_files.csv`). This is a known data loss point.
- Some 2023-2024 PDFs are scanned images, not text. Standard pdfplumber returns garbage. OCR fallback (pytesseract at 300 DPI) handles these but is slower and less reliable.
- Arrested/Name/DOB only extracted when the "Arrested:" keyword appears in the incident block. Rows without arrests have "N/A" for Name, DOB, and Charges.

---

### Step 3: Identify Missing Dates

**Notebook:** `scripts/date_check.ipynb`
**Input:** `data/checkpoints/checkpoint9_no_2025.csv` (produced later in the pipeline; this step runs after Step 9)
**Output:** `scripts/missing_dates.txt` — list of 96 dates not present in the dataset

Generates every expected date from 2018-01-01 to 2024-12-31, compares against dates actually in the dataset, and writes the missing ones.

**Key transformations:**
- Date comparison: `expected_dates - actual_dates`
- Output format: one `YYYY-MM-DD` per line

**Gotchas:**
- This step runs **after** Step 9 (it needs the cleaned checkpoint). The pipeline is not strictly linear here — you identify gaps, then go back and fill them.
- The `missing_dates.txt` file has annotations on some lines (e.g., "file does not exist", "press log w/ no info") — these are manual notes, not programmatic.

---

### Step 4: Process Missing Date PDFs

**Notebook:** `scripts/convert_pdfs.ipynb` (the missing dates section, later in the same notebook)
**Input:** `data/missing_pdfs/*.pdf` (manually downloaded PDFs for the 96 missing dates)
**Output:** `data/missing_dates_csv/unclean_missing_dates.csv`

Processes the missing-date PDFs using the same extraction logic as Step 2, but with an OCR fallback for scanned documents.

**Key transformations:**
- First tries pdfplumber extraction
- Validates output with `is_meaningful_police_log()` — checks for incident numbers and police-log keywords
- If validation fails, falls back to pytesseract OCR at 300 DPI
- OCR splits incidents on `(?=Incident\s+#?:\s*\d+)` pattern instead of separators

**Gotchas:**
- OCR is slow (~5-10 seconds per page). Budget time accordingly for 96+ PDFs.
- OCR quality varies. Some dates truly have no incident data ("press log w/ no info").

---

## 5. Phase 2: Cleaning & Enrichment

### Step 5: Clean & Deduplicate

**Notebook:** `scripts/clean_csv.ipynb`
**Input:** Raw CSVs from Steps 2 and 4
**Output:**
- `data/checkpoints/checkpoint1.csv` — raw data with deduplication
- `data/checkpoints/checkpoint2.csv` — cleaned with location separation

Combines raw extraction CSVs, deduplicates by `Incident #`, cleans the Location and Charges columns, and separates the Location field into a descriptive prefix and a street address.

**Key transformations:**
- Drop rows missing all key columns (Incident #, Date, Type, Location)
- Remove invalid single-letter entries in `Type`
- Remove URLs and artifacts from `Charges`
- Separate `Location` into `Location Prefix` (e.g., "SPEEDWAY GAS STATION") and clean `Location` (street address only)
- Regex-based unnesting of multiple arrests within a single incident (creates new rows for each person)
- Columns added: `Location Prefix`

**Gotchas:**
- The unnesting logic creates new rows — row count increases after this step. One incident with 3 arrests = 3 rows.
- Location prefix extraction is heuristic. Not all rows have a prefix.

---

### Step 6: Geocode Addresses

**Notebook:** `scripts/address_mapping.ipynb`
**Input:** `data/checkpoints/checkpoint2.csv`
**Output:** `data/archive/geocoded_addresses_final.csv` (geocoded address lookup table)

Geocodes unique street addresses to latitude/longitude using the OpenCage API (with OpenStreetMap data).

**Key transformations:**
- Address cleaning: normalize formats, remove unit numbers (#3, APT 1B, FL2)
- Append ", Lawrence, MA" to all addresses for geocoding context
- Multi-pass geocoding to work around OpenCage's daily free request limit
- Results cached to avoid re-geocoding the same address
- Merge multiple pass results into one deduplicated file

**Gotchas:**
- **Requires `config.json` with your OpenCage API key.** This file is gitignored. You'll need to create it: `{"OPENCAGE_API_KEY": "your_key_here"}`
- OpenCage free tier: 2,500 requests/day. With ~3,000+ unique addresses, this takes multiple days unless you upgrade.
- Some addresses can't be geocoded (internal locations like "POLICE STATION"). These remain as NaN.

---

### Step 7: Merge Geocoded Data

**Notebook:** `scripts/geocode_merge.ipynb`
**Input:**
- `data/checkpoints/checkpoint2.csv`
- `data/archive/geocoded_addresses_final.csv` (from Step 6)
**Output:**
- `data/checkpoints/checkpoint3_geocoded.csv`
- `data/checkpoints/checkpoint4_geocode_complete.csv`

Merges the geocoded latitude/longitude back into the main dataset. Does a two-pass lookup: exact match, then cleaned-address match. Also fills gaps using legacy checkpoint data if available.

**Key transformations:**
- Join on cleaned address string (appending ", Lawrence, MA")
- Use `.combine_first()` to preserve existing coordinates while filling gaps
- Columns added: `latitude`, `longitude`, `Cleaned Location`

**Gotchas:**
- ~95% of addresses get coordinates. The remaining 5% stay as NaN and won't appear on the map.
- Later in this notebook (or in categorize_visualize), out-of-Massachusetts coordinates are filtered out (checkpoint 8). This catches geocoding errors that resolved to wrong states.

---

### Step 8: Anonymize (Hash PII)

**Notebook:** `scripts/hash.ipynb`
**Input:** `data/checkpoints/checkpoint4_geocode_complete.csv`
**Output:** `data/checkpoints/checkpoint5_hashed.csv`

Replaces personally identifiable information (Name + DOB) with a SHA-256 hash to create an anonymous `person_id`. The `Name` column is then dropped.

**Key transformations:**
- For rows with `Charges` (i.e., arrests): `person_id = SHA256(Name + "_" + DOB)`
- Whitespace trimmed and null-safe before hashing
- Rows without charges get empty `person_id`
- Column added: `person_id` (64-char hex string)
- Column removed: `Name`
- A mapping file (`md_name_mapping.csv`) is saved as an intermediate but **not** included in final output

**Gotchas:**
- SHA-256 is one-way. Once `Name` is dropped, you cannot recover it from `person_id`.
- Rows without charges (the vast majority — ~99%) have no `person_id`, so they cannot be linked across incidents.
- `DOB` is retained (needed for age calculation in Step 12).

---

### Step 9: Categorize & Classify

**Notebook:** `scripts/categorize_visualize.ipynb`
**Input:** `data/checkpoints/checkpoint5_hashed.csv`
**Output:**
- `data/checkpoints/checkpoint6_category_crime_year.csv` — all rows with categories
- `data/checkpoints/checkpoint7_serious_crimes.csv` — serious crimes only
- `data/checkpoints/checkpoint8_mass_filtered.csv` — serious + within MA
- `data/checkpoints/checkpoint9_no_2025.csv` — serious + within MA + no 2025

Maps each incident's raw `Type` field to one of 14 FBI-style crime categories using keyword matching. Also assigns a crime severity label and extracts the year.

**Key transformations:**
- **Category mapping:** Keyword-based rules map `Type` (e.g., "ALARM/BURG", "NOISE ORD") to categories (e.g., "Property Crimes", "Public Disturbances"). Unmapped types go to "Other".
- **Severity classification:** Violent felonies, drug dealing, B&E, robbery, sexual assault = "Serious". Everything else = "Non-Serious".
- **Year extraction:** Parsed from `Date` timestamp.
- **Geographic filter (CP8):** Uses OSMnx/GeoPandas to remove coordinates outside Massachusetts.
- **Temporal filter (CP9):** Removes any 2025-dated rows.
- Columns added: `category`, `Year`, `crime_severity`

**The 14 categories:**
Motor Vehicle Incidents, Preventive Policing, Public Disturbances, Fire and Arson, Domestic Disputes and Protection, Suspicious/Unusual Activity, Law Enforcement Operations, Medical/Welfare Assistance, Property Crimes, Financial Crimes and Fraud, Violent and Weapon Offenses, Drug and Substance Use, Court and Admin Procedures, Other

**Gotchas:**
- CP7/CP8/CP9 are filtered subsets with far fewer rows (~12,800). CP6 retains all ~424k rows. Downstream steps use the full dataset (CP10+), not the filtered one.
- Category assignment is heuristic. Some Type values are ambiguous and may be miscategorized.
- The geographic filter requires GeoPandas + OSMnx — heavy dependencies that are slow on first run.

---

### Step 10: Combine Datasets

**Input:** CP9 (main dataset) + missing dates data (from Step 4, run through its own clean pipeline)
**Output:** `data/checkpoints/checkpoint10_combined_data.csv`

Merges the main dataset with the missing-dates records that went through their own parallel cleaning pipeline (clean → geocode → etc. in the `data/missing_dates_csv/md_checkpoints/` directory).

**Gotchas:**
- The missing-dates data goes through its own mini pipeline of cleaning steps (tracked with `md_checkpoint` prefixes). These mirror Steps 5-9 but for the smaller missing-dates dataset.
- CP10 is the first checkpoint that contains all ~424k rows (main + missing dates combined).

---

### Step 11: Standardize Category Names

**Notebook:** `scripts/Standardize_Categories.ipynb`
**Input:** `data/checkpoints/checkpoint10_combined_data.csv` (or copy)
**Output:** `data/checkpoints/checkpoint11_cleaned_category_copy.csv`

Converts internal category codes (e.g., `VIOLENT_AND_WEAPON_OFFENSES`) to human-readable names (e.g., "Violent and Weapon Offenses").

**Key transformations:**
- String replacement: underscores → spaces, title case
- Column modified: `category` (overwritten with readable names)

---

### Step 12: Compute Age

**Notebook:** `scripts/age.ipynb`
**Input:** `data/checkpoints/checkpoint11_cleaned_category_copy.csv`
**Output:** `data/checkpoints/checkpoint12_age.csv`

Calculates each arrested person's age at the time of the incident by comparing `DOB` to `Date`.

**Key transformations:**
- Parse `DOB` (MM/DD/YYYY) and `Date` to datetime
- Age = incident year - birth year, adjusted down by 1 if birthday hasn't occurred yet that year
- Column added: `Age` (float, NaN for non-arrested rows)

**Gotchas:**
- Only ~5,000 rows (~1.2%) have age data — most incidents don't involve arrests.
- Some OCR-misread birth years produce unrealistic ages. No automated validation is applied.

---

### Step 13: Clean & Expand Charges

**Notebook:** `scripts/charges/clean_charges.ipynb`
**Input:** `data/checkpoints/checkpoint12_age.csv`
**Output:** `data/checkpoints/checkpoint13_cleaned_charges.csv`

Splits the semicolon-delimited `Charges` field into individual columns, extracts statute references, and cleans charge text through 3 iterations.

**Key transformations:**
- Split `Charges` into `charge_1` through `charge_28` (max 28 charges per incident)
- Extract MA statute citations (e.g., "c266 s120") into `statute_1` through `statute_23`
- 3-pass charge cleaning: remove OCR artifacts, deduplicate, fix truncations
- 1,194 unique base charges identified
- Columns added: `charge_1`…`charge_28`, `statute_1`…`statute_23`, `cleaned_charges`, `statutes`

**Gotchas:**
- This step balloons the column count from ~18 to ~69. Most of these columns are sparse (most incidents have 0-3 charges).
- Charge text is often truncated in the original PDFs. The cleaning tries to fix this but can't recover truly missing text.

---

### Step 14: Standardize Charges

**Notebook:** `scripts/charges/standardize_charges.ipynb`
**Uses:** `scripts/charges/standardize_charges.py` (the 8-step pipeline logic)
**Input:** `data/checkpoints/checkpoint13_cleaned_charges.csv`
**Output:** `data/checkpoints/checkpoint14_standardized_charges.csv`
**Reference:** `scripts/charges/STANDARDIZATION_PROCESS.md` (detailed documentation of the 8-step process)

Normalizes 1,194 unique raw charges into 394 canonical standardized charges using an 8-step pipeline. Also classifies each charge as Felony, Misdemeanor, or Either.

**The 8-step pipeline:**
1. **Extract warrant type** — removes warrant prefixes (bench, standard, default, capias, child in need)
2. **Strip statute references** — removes MA statute citations from charge text
3. **Clean text artifacts** — remove trailing commas, encoding artifacts, normalize whitespace
4. **Extract offense number** — separates "1st", "2nd", "3rd", "subsequent" from base charge
5. **Canonical alias normalization** — 400+ curated mappings for truncations, misspellings, and variants
6. **Categorize** — assigns each charge to one of 17 charge categories
7. **Classify** — Felony / Misdemeanor / Either (per MA law; 2nd+ offenses may escalate)
8. **Aggregate** — merge identical base charges, sum counts

**Key transformations:**
- Column added: `standardized_charges` (semicolon-delimited canonical charges)
- Columns removed: all `charge_N` and `statute_N` columns (collapsed into `standardized_charges`)
- Output also produces `unique_charges_standardized.csv` (394 charges with category + classification + count) used by the app's Charge Analysis tab

**Gotchas:**
- The alias mapping table in `standardize_charges.py` is manually curated. New charge text variants will need new entries.
- "Either" means the charge can be prosecuted as felony or misdemeanor — depends on circumstances not in our data.

---

### Step 15: Add Misdemeanor & Warrant Flags

**Notebook:** `scripts/charges/add_misdemeanor_warrant_cols.ipynb`
**Input:** `data/checkpoints/checkpoint14_standardized_charges.csv`
**Output:** `data/checkpoints/checkpoint15_misdemeanor_warrant.csv` **(FINAL)**

Adds two boolean derivative columns based on the charge data.

**Key transformations:**
- `is_misdemeanor`: **True** only if ALL charges in the row are classified as Misdemeanor. False if any charge is Felony or Either. NaN if no charges.
- `has_warrant`: **True** if any charge had a warrant prefix (bench warrant, default warrant, etc.) in the original raw text. NaN if no charges.
- Columns added: `is_misdemeanor` (boolean), `has_warrant` (boolean)

**Gotchas:**
- `is_misdemeanor` is strict — a single non-misdemeanor charge makes the whole row False.
- `has_warrant` checks the original raw charge text (not standardized), because the warrant prefix is stripped during standardization.
- Rows without charges (~99%) have NaN for both columns, not False.

---

## 6. Phase 3: App Delivery

### Step 16: Copy Final Dataset to App Directory

Copy `data/checkpoints/checkpoint15_misdemeanor_warrant.csv` to `streamlit-app/checkpoint15_misdemeanor_warrant.csv`.

Also copy `unique_charges_standardized.csv` to `streamlit-app/unique_charges_standardized.csv` (used by the Charge Analysis tab).

---

### Step 17: Build DuckDB

**Script:** `streamlit-app/db_setup.py`

```bash
cd streamlit-app
python db_setup.py              # Build from CSV (skips if .duckdb already exists)
python db_setup.py --rebuild    # Force rebuild
python db_setup.py --append new_data.csv  # Append new rows (deduplicates)
```

Converts the checkpoint CSV into a DuckDB database (`incidents.duckdb`) for fast SQL querying. Creates indexes on `year`, `category`, `crime_severity`, `latitude/longitude`, `is_misdemeanor`, `has_warrant`, and a composite index on `(year, category, crime_severity)`.

The app can fall back to loading the CSV with pandas if DuckDB is unavailable, but DuckDB is significantly faster for filtering and hotspot calculations.

---

### Step 18: Launch Dashboard

```bash
streamlit run streamlit-app/main_v3.py
```

The dashboard runs at `http://localhost:8501` and has three tabs:

1. **About the Project** — description, data sources, category definitions
2. **Data Trends** — embedded Tableau dashboards (incidents per category/year/month) + interactive charge analysis charts
3. **Spatial Insights** — Folium map with incident markers/clusters, heatmap, hotspot analysis, socioeconomic choropleth overlays (poverty, unemployment, income, median age), and POI layers (liquor retail, schools, places of worship, nonprofits)

---

## 7. Secondary Data Pipelines

These are independent of the main pipeline and can be run anytime. They produce GeoJSON boundary layers and POI CSV files used by the Streamlit app's map.

### Census Tract Layers (GeoJSON)

Each notebook reads Census ACS data + TIGER shapefiles, merges them, and outputs a GeoJSON file.

| Notebook | Data Source | Output | Key Field |
|---|---|---|---|
| `scripts/secondary_data_scripts/geopandas_poverty.ipynb` | Census ACS poverty data | `streamlit-app/boundaries/poverty_boundary.geojson` | `Estimate` (% below poverty) |
| `scripts/secondary_data_scripts/unemployment_data.ipynb` | Census ACS unemployment | `streamlit-app/boundaries/unemployment_boundary.geojson` | `Estimate` (% unemployed) |
| `scripts/secondary_data_scripts/household_income.ipynb` | Census ACS income | `streamlit-app/boundaries/household_income_boundary.geojson` | `Estimate` ($ median income) |
| `scripts/secondary_data_scripts/age.ipynb` | Census ACS median age | `streamlit-app/boundaries/median_age_boundary.geojson` | `MedianAge` (years) |

**Common pattern:** Read CSV → normalize geography format → extract census tract name → merge with TIGER shapefile (FIPS 25/009 = MA/Essex County) → export GeoJSON.

### Point of Interest Layers (CSV)

| Notebook | Data Source | Output | Key Fields |
|---|---|---|---|
| `scripts/secondary_data_scripts/liquor_retail.ipynb` | MA ABCC active licenses | `streamlit-app/liquor_retail_geocoded.csv` | NAME, TYPE, latitude, longitude |
| `scripts/secondary_data_scripts/school_worship_geocoded.ipynb` | MA DESE schools + worship directories | `streamlit-app/school_geocoded.csv`, `streamlit-app/places_of_worship_geocoded.csv` | NAME, TYPE, latitude, longitude |
| `scripts/secondary_data_scripts/Rec_spaces_geocoded.ipynb` | Recreation spaces dataset | `streamlit-app/recreation_spaces_geocoded.csv` | NAME, latitude, longitude |

**Common pattern for schools/worship/recreation:** Source data uses MA State Plane coordinates (EPSG:26986). Notebooks convert to WGS84 (EPSG:4326) for lat/lon.

`streamlit-app/nonprofits_geocoded.csv` is pre-geocoded (no generation notebook).

---

## 8. Checkpoint Quick-Reference Table

| CP | File | Created By | What It Adds |
|---|---|---|---|
| 1 | `checkpoint1.csv` | clean_csv.ipynb | Raw data, deduplicated |
| 2 | `checkpoint2.csv` | clean_csv.ipynb | + `Location Prefix` (separated from Location) |
| 3 | `checkpoint3_geocoded.csv` | geocode_merge.ipynb | + `latitude`, `longitude` |
| 4 | `checkpoint4_geocode_complete.csv` | geocode_merge.ipynb | + `Cleaned Location` (gaps filled) |
| 5 | `checkpoint5_hashed.csv` | hash.ipynb | + `person_id`; Name dropped |
| 6 | `checkpoint6_category_crime_year.csv` | categorize_visualize.ipynb | + `category`, `Year`, `crime_severity` |
| 7 | `checkpoint7_serious_crimes.csv` | categorize_visualize.ipynb | Filtered: serious crimes only |
| 8 | `checkpoint8_mass_filtered.csv` | categorize_visualize.ipynb | Filtered: within MA only |
| 9 | `checkpoint9_no_2025.csv` | categorize_visualize.ipynb | Filtered: no 2025 data |
| 10 | `checkpoint10_combined_data.csv` | (merge) | Main + missing dates combined |
| 11 | `checkpoint11_cleaned_category_copy.csv` | Standardize_Categories.ipynb | Human-readable category names |
| 12 | `checkpoint12_age.csv` | age.ipynb | + `Age` |
| 13 | `checkpoint13_cleaned_charges.csv` | clean_charges.ipynb | + charge_1…28, statute_1…23, cleaned_charges |
| 14 | `checkpoint14_standardized_charges.csv` | standardize_charges.ipynb | + `standardized_charges`; charge/statute cols dropped |
| 15 | `checkpoint15_misdemeanor_warrant.csv` | add_misdemeanor_warrant_cols.ipynb | + `is_misdemeanor`, `has_warrant` **(FINAL)** |

---

## 9. Final Column Reference (CP15)

These are the 20 columns in the final dataset that powers the dashboard:

| Column | Type | Description | Source Step |
|---|---|---|---|
| `Date` | datetime | Incident timestamp (YYYY-MM-DD HH:MM:SS) | Step 2 |
| `Type` | string | Raw incident type (e.g., "ALARM/BURG") | Step 2 |
| `Location` | string | Street address | Step 5 |
| `Arrested` | string | "Yes" or "No" | Step 2 |
| `Location Prefix` | string | Descriptive location note (e.g., "SPEEDWAY GAS") | Step 5 |
| `DOB` | string | Date of birth (MM/DD/YYYY), "N/A" if no arrest | Step 2 |
| `Charges` | string | Raw charge text, semicolon-separated | Step 2 |
| `latitude` | float | WGS84 latitude | Step 7 |
| `longitude` | float | WGS84 longitude | Step 7 |
| `Cleaned Location` | string | Normalized address (units removed) | Step 7 |
| `person_id` | string | SHA-256 hash of Name+DOB (empty if no arrest) | Step 8 |
| `category` | string | FBI-style crime category (human-readable) | Step 9/11 |
| `Year` | int | Year extracted from Date | Step 9 |
| `crime_severity` | string | "Serious" or "Non-Serious" | Step 9 |
| `Age` | float | Age at time of incident (NaN if no DOB) | Step 12 |
| `statutes` | string | MA statute citations, semicolon-separated | Step 13 |
| `standardized_charges` | string | Canonical charge names, semicolon-separated | Step 14 |
| `has_warrant` | boolean | Any charge had a warrant prefix | Step 15 |
| `is_misdemeanor` | boolean | All charges classified as misdemeanor | Step 15 |
