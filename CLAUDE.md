# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lawrence Police Dashboard — a data pipeline and Streamlit web app that transforms publicly available daily police log PDFs from the Lawrence (MA) Police Department into interactive visualizations. The dataset covers 2018–2024 incident reports with ~8,500+ incidents including geocoded locations, FBI-style crime categories, crime severity, anonymized person IDs, and standardized charges.

## Running the App

```bash
# Activate the virtual environment
source venv/Scripts/activate   # Windows (Git Bash)

# Run the current version of the Streamlit app
streamlit run streamlit-app/main_v3.py

# The app runs on port 8501 by default
```

The devcontainer (Codespaces) auto-runs `streamlit run streamlit-app/main.py` — but local development uses `main_v3.py` as the latest version.

### Database Setup

The app uses DuckDB for fast querying instead of loading CSV directly:
```bash
cd streamlit-app
python db_setup.py              # Build from CSV (skip if .duckdb exists)
python db_setup.py --rebuild    # Force rebuild
python db_setup.py --append new_data.csv  # Append new rows
```

Source CSV: `streamlit-app/checkpoint15_misdemeanor_warrant.csv`
Database: `streamlit-app/incidents.duckdb`

### Install Dependencies

```bash
pip install -r requirements.txt                # Root-level (full pipeline deps)
pip install -r streamlit-app/requirements.txt  # Streamlit app only (streamlit, pandas, folium, duckdb, plotly, etc.)
```

## Architecture

### Data Pipeline (scripts/)

Jupyter notebooks that run sequentially to process raw PDFs into analysis-ready data. Each produces a numbered checkpoint CSV:

1. **download_pdfs.ipynb** — Scrapes daily log PDFs from the Lawrence PD website
2. **convert_pdfs.ipynb** — Extracts text from PDFs using Tesseract OCR + pdfplumber (2023-2024 scanned PDFs require OCR)
3. **clean_csv.ipynb** — Cleans columns, drops invalid rows, separates Location into prefix/address, unnests multiple arrests per row
4. **date_check.ipynb** — Identifies and fills in missing dates
5. **hash.ipynb** — SHA-256 hashes Name+DOB into anonymous `person_id`
6. **geocode_merge.ipynb** / **address_mapping.ipynb** — Geocodes addresses via OpenCage API + OpenStreetMap
7. **categorize_visualize.ipynb** — Maps incident Types to FBI-style crime categories and crime_severity
8. **age.ipynb** — Computes age from DOB
9. **scripts/charges/** — Standardizes raw charge text into structured fields (statutes, standardized_charges, has_warrant, is_misdemeanor)

### Secondary Data (scripts/secondary_data_scripts/)

Notebooks that produce GeoJSON boundary layers for the map:
- Poverty, unemployment, household income, median age — census tract choropleth layers
- Liquor retail, schools, places of worship — POI geocoded CSVs

### Streamlit App (streamlit-app/)

- **main_v3.py** — Current active version. Three tabs: "About the Project", "Data Trends" (embedded Tableau), "Spatial Insights" (Folium map with filters, heatmap, POI overlays, choropleth layers)
- **main_v2.py** — Previous version (kept for reference)
- **main.py** — Original version (used by devcontainer/Codespaces)
- **db_setup.py** — CLI tool to build/rebuild the DuckDB database from checkpoint CSV
- **test.py** — Sandbox for testing new map layers (e.g., unemployment)
- **boundaries/** — GeoJSON files for census tract overlays (poverty, unemployment, income, age, city boundary)
- **icons/** — Custom marker icons for POI types

### Key Data Columns in incidents table

`Date`, `type`, `location`, `arrested`, `charges`, `latitude`, `longitude`, `person_id`, `category`, `year`, `crime_severity`, `age`, `statutes`, `standardized_charges`, `has_warrant`, `is_misdemeanor`

## Important Notes

- **config.json** contains the OpenCage API key and is gitignored. Required only for geocoding scripts, not for running the app.
- CSV and PDF files are gitignored except for specific whitelisted files (see `.gitignore`). The checkpoint CSV in `streamlit-app/` is tracked.
- The app center coordinates are `[42.70, -71.155]` (Lawrence, MA).
- Tableau dashboards are embedded via HTML snippets — the data for those lives on Tableau Public, not in this repo.
- Python 3.11 is the target version (per devcontainer config).
