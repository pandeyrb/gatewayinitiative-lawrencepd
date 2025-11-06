# Secondary Data Inventory

This folder stores the processed secondary datasets that back the optional map layers in the Streamlit application.  The raw CSV exports are kept in the project Drive (not in Git) because of size and licensing constraints.  Each subdirectory contains:

* the **raw inputs** you should download into the Drive before rerunning the notebook;
* a Jupyter notebook under `scripts/secondary_data_scripts/` that documents the cleaning steps; and
* the **GeoJSON boundary file** that is actually read by the app (a backup copy of the GeoJSON lives here, while the version used by Streamlit is synced to `streamlit-app/boundaries/`).

## Directory overview

```
secondary_data/
├── household_income/
│   ├── household_income_boundary_copy.geojson
│   └── tl_2024_25_tract/
│       ├── tl_2024_25_tract.cpg
│       ├── tl_2024_25_tract.dbf
│       ├── tl_2024_25_tract.prj
│       ├── tl_2024_25_tract.shp
│       └── tl_2024_25_tract.shx
├── unemployment_data/
│   ├── unemployment_boundary_copy.geojson
│   └── tl_2024_25_tract/
│       ├── tl_2024_25_tract.cpg
│       ├── tl_2024_25_tract.dbf
│       ├── tl_2024_25_tract.prj
│       ├── tl_2024_25_tract.shp
│       └── tl_2024_25_tract.shx
├── poverty_data/              # shared Drive only
│   ├── 2023_Poverty.csv
│   ├── poverty_percent_below.geojson
│   └── tl_2024_25_tract/
│       ├── tl_2024_25_tract.cpg
│       ├── tl_2024_25_tract.dbf
│       ├── tl_2024_25_tract.prj
│       ├── tl_2024_25_tract.shp
│       └── tl_2024_25_tract.shx
└── liquor_retail/             # shared Drive only
    ├── liquor_retail.csv
    ├── liquor_retail_geocoded.csv
    └── copy_liquor_retail_geocoded.csv
```

> ℹ️  The working shapefile download from TIGER/Line (`tl_2024_25_tract/…`) and the raw CSV exports are ignored by Git.  Keep those files in the shared Drive when you need to regenerate the GeoJSON or geocoded CSV outputs.  The poverty and liquor retail folders are Drive-only because they contain large or license-restricted datasets that should not be committed to the repository.  When you pull the shapefile from TIGER/Line, drop the full set of component files (`.cpg`, `.dbf`, `.prj`, `.shp`, `.shx`) into the matching `tl_YYYY_25_tract/` folder shown above so the notebooks can find them.

## Data inventory and CSV versions

| Layer | Raw CSV (Drive) | Source & release | Notebook | Output GeoJSON/CSV | Notes |
| --- | --- | --- | --- | --- | --- |
| Median Household Income | `household_income/median household income.csv` | U.S. Census Bureau, American Community Survey (ACS) **2019–2023 5-year Data Profile (DP03)**. Export filtered to Essex County, MA tracts. Downloaded 2025-09-08 for this project. | `scripts/secondary_data_scripts/household_income.ipynb` | `household_income_boundary_copy.geojson` → copy to `streamlit-app/boundaries/household_income_boundary.geojson` | Contains `Estimate` (median income in 2023 inflation-adjusted dollars) and `MoE` (margin of error). Requires the 2024 TIGER/Line tract shapefile in `household_income/tl_2024_25_tract/` when regenerating. |
| Unemployment Rate | `unemployment_data/unemployment.csv` | U.S. Census Bureau, ACS **2019–2023 5-year Data Profile (DP03)**. Export filtered to Essex County, MA tracts. Downloaded 2025-09-08 for this project. | `scripts/secondary_data_scripts/unemployment_data.ipynb` | `unemployment_boundary_copy.geojson` → copy to `streamlit-app/boundaries/unemployment_boundary.geojson` | Contains `Estimate` (percent unemployed, population 16+), and `MoE`. Uses the same 2024 TIGER/Line tract shapefile when regenerating. |
| Poverty Rate | `poverty_data/2023_Poverty.csv` | U.S. Census Bureau, ACS **2019–2023 5-year estimates (Table S1701 – Poverty Status)** filtered to Essex County, MA tracts. Stored only in the shared Drive due to size. | `scripts/secondary_data_scripts/geopandas_poverty.ipynb` | `poverty_data/poverty_percent_below.geojson` (Drive backup) → copy to `streamlit-app/boundaries/poverty_boundary.geojson` | Output tracks tract-level `Estimate` (% of population below poverty level) and `MoE`. Uses the shared TIGER/Line tract shapefile folder `poverty_data/tl_2024_25_tract/` when regenerating. |
| Liquor Retail POIs | `liquor_retail/liquor_retail.csv` | Massachusetts ABCC Active Licenses export (Lawrence-filtered) downloaded from https://www.mass.gov/info-details/abcc-active-licenses. Saved in shared Drive. | `scripts/secondary_data_scripts/liquor_retail.ipynb` | `liquor_retail/liquor_retail_geocoded.csv` (Drive backup) → copy to `streamlit-app/liquor_retail_geocoded.csv` | Notebook requires `config.json` with an OpenCage API key for geocoding. `copy_liquor_retail_geocoded.csv` keeps a timestamped archive of the version synced to Streamlit. |

## Updating a layer

1. Download the latest ACS Data Profile (DP03) tables for Essex County census tracts from [data.census.gov](https://data.census.gov/). Save the export to the matching CSV path in the Drive (e.g., `household_income/median household income.csv`). Record the ACS release (e.g., 2018–2022 vs. 2019–2023) in the table above when you update it.
2. Download the current TIGER/Line census tract shapefile for Massachusetts (state FIPS 25) from the [Census TIGER/Line](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html) site and place it in the appropriate subfolder. The notebooks expect the folder name `tl_YYYY_25_tract`.
3. Run the corresponding notebook in `scripts/secondary_data_scripts/` to clean the CSV, merge it with the tract geometry, and export a GeoJSON.
4. Copy the resulting GeoJSON (or the geocoded CSV for the liquor layer) into the `streamlit-app/` directory so the Streamlit app can pick up the refreshed data. Keep a backup copy in this directory or the shared Drive.
5. Update the "Source & release" column above with the new ACS release and the download date so others know which version is in use.

## Column conventions

* **Geography** – Original ACS geography label (e.g., `Census Tract 2501; Essex County; Massachusetts`). The notebooks standardize this to comma-separated text and extract the tract identifier for joins.
* **Estimate** – Numeric value converted from the ACS percentage or dollar string. Stored as `float` in the exported GeoJSON.
* **MoE** – Margin of error stripped of symbols (±, %). Stored as `float` in the exported GeoJSON.

Maintaining these conventions ensures the Streamlit layers and legends render correctly.