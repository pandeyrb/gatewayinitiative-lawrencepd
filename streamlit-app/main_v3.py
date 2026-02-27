import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import folium
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import st_folium
import os
import json
import duckdb


# =============================================================
# MODULE-LEVEL CONSTANTS — allocated once, never recreated
# =============================================================

TABLEAU_HTML_CATEGORY = """
<div class='tableauPlaceholder' id='viz1755837857221' style='position: relative'>
    <noscript>
        <a href='#'>
            <img alt='Dashboard 1 ' src='https://public.tableau.com/static/images/In/Incidentspercategorytogetherwithpercentageandseriousv_non-serious/Dashboard1/1_rss.png' style='border: none' />
        </a>
    </noscript>
    <object class='tableauViz' style='display:none;'>
        <param name='host_url' value='https%3A%2F%2Fpublic.tableau.com%2F' />
        <param name='embed_code_version' value='3' />
        <param name='site_root' value='' />
        <param name='name' value='Incidentspercategorytogetherwithpercentageandseriousv_non-serious/Dashboard1' />
        <param name='tabs' value='no' />
        <param name='toolbar' value='yes' />
        <param name='static_image' value='https://public.tableau.com/static/images/In/Incidentspercategorytogetherwithpercentageandseriousv_non-serious/Dashboard1/1.png' />
        <param name='animate_transition' value='yes' />
        <param name='display_static_image' value='yes' />
        <param name='display_spinner' value='yes' />
        <param name='display_overlay' value='yes' />
        <param name='display_count' value='yes' />
        <param name='language' value='en-US' />
    </object>
</div>
<script type='text/javascript'>
    var divElement = document.getElementById('viz1755837857221');
    var vizElement = divElement.getElementsByTagName('object')[0];
    if (divElement.offsetWidth > 800) {
        vizElement.style.width='100%';
        vizElement.style.height='827px';
    } else if (divElement.offsetWidth > 500) {
        vizElement.style.width='100%';
        vizElement.style.height='827px';
    } else {
        vizElement.style.width='100%';
        vizElement.style.height='1127px';
    }
    var scriptElement = document.createElement('script');
    scriptElement.src = 'https://public.tableau.com/javascripts/api/viz_v1.js';
    vizElement.parentNode.insertBefore(scriptElement, vizElement);
</script>
"""

TABLEAU_HTML_YEAR = """
<div class='tableauPlaceholder' id='viz1755839651562' style='position: relative'>
    <noscript>
        <a href='#'>
            <img alt='Dashboard 1 ' src='https://public.tableau.com/static/images/In/IncidentsPerYear/Dashboard1/1_rss.png' style='border: none' />
        </a>
    </noscript>
    <object class='tableauViz' style='display:none;'>
        <param name='host_url' value='https%3A%2F%2Fpublic.tableau.com%2F' />
        <param name='embed_code_version' value='3' />
        <param name='site_root' value='' />
        <param name='name' value='IncidentsPerYear/Dashboard1' />
        <param name='tabs' value='no' />
        <param name='toolbar' value='yes' />
        <param name='static_image' value='https://public.tableau.com/static/images/In/IncidentsPerYear/Dashboard1/1.png' />
        <param name='animate_transition' value='yes' />
        <param name='display_static_image' value='yes' />
        <param name='display_spinner' value='yes' />
        <param name='display_overlay' value='yes' />
        <param name='display_count' value='yes' />
        <param name='language' value='en-US' />
    </object>
</div>
<script type='text/javascript'>
    var divElement = document.getElementById('viz1755839651562');
    var vizElement = divElement.getElementsByTagName('object')[0];
    if (divElement.offsetWidth > 800) {
        vizElement.style.width='100%';
        vizElement.style.height='827px';
    } else if (divElement.offsetWidth > 500) {
        vizElement.style.width='100%';
        vizElement.style.height='827px';
    } else {
        vizElement.style.width='100%';
        vizElement.style.height='877px';
    }
    var scriptElement = document.createElement('script');
    scriptElement.src = 'https://public.tableau.com/javascripts/api/viz_v1.js';
    vizElement.parentNode.insertBefore(scriptElement, vizElement);
</script>
"""

TABLEAU_HTML_MONTH = """
<div class='tableauPlaceholder' id='viz1755839865249' style='position: relative'>
    <noscript>
        <a href='#'>
            <img alt='Dashboard 1 ' src='https://public.tableau.com/static/images/In/IncidentsPerMonth/Dashboard1/1_rss.png' style='border: none' />
        </a>
    </noscript>
    <object class='tableauViz' style='display:none;'>
        <param name='host_url' value='https%3A%2F%2Fpublic.tableau.com%2F' />
        <param name='embed_code_version' value='3' />
        <param name='site_root' value='' />
        <param name='name' value='IncidentsPerMonth/Dashboard1' />
        <param name='tabs' value='no' />
        <param name='toolbar' value='yes' />
        <param name='static_image' value='https://public.tableau.com/static/images/In/IncidentsPerMonth/Dashboard1/1.png' />
        <param name='animate_transition' value='yes' />
        <param name='display_static_image' value='yes' />
        <param name='display_spinner' value='yes' />
        <param name='display_overlay' value='yes' />
        <param name='display_count' value='yes' />
        <param name='language' value='en-US' />
    </object>
</div>
<script type='text/javascript'>
    var divElement = document.getElementById('viz1755839865249');
    var vizElement = divElement.getElementsByTagName('object')[0];
    if (divElement.offsetWidth > 800) {
        vizElement.style.width='100%';
        vizElement.style.height='827px';
    } else if (divElement.offsetWidth > 500) {
        vizElement.style.width='100%';
        vizElement.style.height='827px';
    } else {
        vizElement.style.width='100%';
        vizElement.style.height='877px';
    }
    var scriptElement = document.createElement('script');
    scriptElement.src = 'https://public.tableau.com/javascripts/api/viz_v1.js';
    vizElement.parentNode.insertBefore(scriptElement, vizElement);
</script>
"""

TABLEAU_VIZ_MAP = {
    "Incidents Per Category": TABLEAU_HTML_CATEGORY,
    "Incidents Per Year": TABLEAU_HTML_YEAR,
    "Incidents Per Month": TABLEAU_HTML_MONTH,
}

MAP_PADDING_CSS = """
    <style>
    .leaflet-bottom.leaflet-right {
    margin-bottom: 10px;
    margin-right: 10px;
    }
    </style>
"""

CUSTOM_CLUSTER_CSS_JS = """
<style>
.marker-cluster-small,
.marker-cluster-medium,
.marker-cluster-large {
    display:flex;
    align-items:center;
    justify-content:center;
    border-radius:50%;
    font-weight:700;
    text-align:center;
    line-height:1;
    border:2px solid rgba(60,60,60,0.7);
    box-shadow:0 0 6px rgba(0,0,0,0.25);
}
/* pale yellow for few incidents */
.marker-cluster-small {
    background-color:#FFF7E1!important;
    color:#222!important;
    width:30px;
    height:30px;
    font-size:13px;
}
/* amber for medium clusters */
.marker-cluster-medium {
    background-color:#FFD166!important;
    color:#222!important;
    width:42px;
    height:42px;
    font-size:15px;
}
/* coral-red for dense clusters */
.marker-cluster-large {
    background-color:#EF476F!important;
    color:#fff!important;
    width:54px;
    height:54px;
    font-size:16px;
}
.marker-cluster div{
    background:none!important;
    border:none!important;
    box-shadow:none!important;
}
</style>

<script>
L.MarkerClusterGroup.prototype.options.iconCreateFunction=function(cluster){
var c=' marker-cluster-',n=cluster.getChildCount();
if(n<50){c+='small';}
else if(n<250){c+='medium';}
else{c+='large';}
return new L.DivIcon({html:'<div><span>'+n+'</span></div>',
    className:'marker-cluster'+c,iconSize:new L.Point(40,40)});
};
</script>
"""

POI_STYLE_MAP = {
    "Restaurant": {"color": "black", "icon": "cutlery"},
    "Liquor Store": {"color": "black", "icon": "shopping-cart"},
    "Bar or Lounge": {"color": "black", "icon": "glass"},
    "Nightclub": {"color": "black", "icon": "music"},
    "Grocery Store w/ Liquor": {"color": "black", "icon": "shopping-cart"},
    "Convenience Store": {"color": "black", "icon": "shopping-cart"},
    "Social Club": {"color": "black", "icon": "star"},
}

SCHOOL_ICON_URL = "https://cdn-icons-png.flaticon.com/512/3135/3135810.png"
WORSHIP_ICON_URL = "https://cdn-icons-png.flaticon.com/512/4258/4258470.png"
NONPROFIT_ICON_URL = "https://cdn-icons-png.flaticon.com/512/1946/1946429.png"

POI_TYPES_LIST = [
    "Bar or Lounge",
    "Convenience Store",
    "Grocery Store w/ Liquor",
    "Liquor Store",
    "Nightclub",
    "Restaurant",
    "Social Club",
    "Schools",
    "Places of Worship",
    "Non-Profits",
]

LEGEND_STYLE = """
    position: fixed;
    bottom: 40px;
    left: 40px;
    z-index: 9999;
    background: white;
    padding: 12px 14px;
    border: 1px solid #ccc;
    border-radius: 8px;
    font-size: 13px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.12);
    line-height: 1.6;
"""

POVERTY_LEGEND_HTML = f"""
<div style="{LEGEND_STYLE}">
    <strong style="color: black;">Poverty Estimate (%)</strong><br>
    <span style="color: black;">
        <i style="background:#f7fbff;width:20px;height:10px;display:inline-block;"></i> 0 - 8%<br>
        <i style="background:#deebf7;width:20px;height:10px;display:inline-block;"></i> 8 - 16%<br>
        <i style="background:#c6dbef;width:20px;height:10px;display:inline-block;"></i> 16 - 20%<br>
        <i style="background:#9ecae1;width:20px;height:10px;display:inline-block;"></i> 20 - 28%<br>
        <i style="background:#6baed6;width:20px;height:10px;display:inline-block;"></i> 28 - 37%<br>
        <i style="background:#3182bd;width:20px;height:10px;display:inline-block;"></i> 37%+
    </span>
</div>
"""

UNEMPLOYMENT_LEGEND_HTML = f"""
<div style="{LEGEND_STYLE}">
    <strong style="color: black;">Unemployment Rate (%)</strong><br>
    <span style="color: black;">
        <i style="background:#f7fbff;width:20px;height:10px;display:inline-block;"></i> 2.3%<br>
        <i style="background:#deebf7;width:20px;height:10px;display:inline-block;"></i> 2.4 - 5.2%<br>
        <i style="background:#9ecae1;width:20px;height:10px;display:inline-block;"></i> 5.3 - 8.3%<br>
        <i style="background:#6baed6;width:20px;height:10px;display:inline-block;"></i> 8.4 - 10.4%<br>
        <i style="background:#3182bd;width:20px;height:10px;display:inline-block;"></i> 10.5 - 12.8%<br>
    </span>
</div>
"""

HOUSEHOLD_INCOME_LEGEND_HTML = f"""
<div style="{LEGEND_STYLE}">
    <strong style="color: black;">Median Household Income (USD)</strong><br>
    <span style="color: black;">
        <i style="background:#deebf7;width:20px;height:10px;display:inline-block;"></i> $23k - $33k<br>
        <i style="background:#9ecae1;width:20px;height:10px;display:inline-block;"></i> $33k - $41k<br>
        <i style="background:#6baed6;width:20px;height:10px;display:inline-block;"></i> $41k - $61k<br>
        <i style="background:#3182bd;width:20px;height:10px;display:inline-block;"></i> $61k - $76k<br>
        <i style="background:#08519c;width:20px;height:10px;display:inline-block;"></i> $76k - $88k<br>
    </span>
</div>
"""

MEDIAN_AGE_LEGEND_HTML = f"""
<div style="{LEGEND_STYLE}">
    <strong style="color: black;">Median Age (years)</strong><br>
    <span style="color: black;">
        <i style="background:#f7fbff;width:20px;height:10px;display:inline-block;"></i> 28 - 32<br>
        <i style="background:#deebf7;width:20px;height:10px;display:inline-block;"></i> 32 - 36<br>
        <i style="background:#9ecae1;width:20px;height:10px;display:inline-block;"></i> 36 - 41<br>
        <i style="background:#6baed6;width:20px;height:10px;display:inline-block;"></i> 41 - 45<br>
        <i style="background:#3182bd;width:20px;height:10px;display:inline-block;"></i> 45 - 50<br>
        <i style="background:#08519c;width:20px;height:10px;display:inline-block;"></i> 50 - 54<br>
    </span>
</div>
"""


# =============================================================
# CACHED DATA LOADING FUNCTIONS
# =============================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


@st.cache_data
def load_lawrence_boundary():
    file_path = os.path.join(SCRIPT_DIR, "boundaries", "lawrence_boundary.geojson")
    with open(file_path, "r") as f:
        return json.load(f)


@st.cache_data
def load_data():
    file_path = os.path.join(SCRIPT_DIR, "checkpoint15_misdemeanor_warrant.csv")
    df = pd.read_csv(file_path)
    data = df[["latitude", "longitude", "category", "crime_severity", "Date"]].dropna()
    # Ensure lat/lon are numeric (once, at load time — eliminates per-row lambda checks later)
    data["latitude"] = pd.to_numeric(data["latitude"], errors="coerce")
    data["longitude"] = pd.to_numeric(data["longitude"], errors="coerce")
    data = data.dropna(subset=["latitude", "longitude"])
    data["Date"] = pd.to_datetime(data["Date"])
    data["year"] = data["Date"].dt.year
    return data


@st.cache_data
def load_charge_data():
    csv_path = os.path.join(
        SCRIPT_DIR, "..", "scripts", "charges", "unique_charges_standardized.csv"
    )
    return pd.read_csv(csv_path)


@st.cache_data
def load_liquor_data():
    csv_path = os.path.join(SCRIPT_DIR, "liquor_retail_geocoded.csv")
    return pd.read_csv(csv_path).dropna(subset=["latitude", "longitude"])


@st.cache_data
def load_school_data():
    csv_path = os.path.join(SCRIPT_DIR, "school_geocoded.csv")
    return pd.read_csv(csv_path).dropna(subset=["latitude", "longitude"])


@st.cache_data
def load_worship_data():
    csv_path = os.path.join(SCRIPT_DIR, "places_of_worship_geocoded.csv")
    return pd.read_csv(csv_path).dropna(subset=["latitude", "longitude"])


@st.cache_data
def load_nonprofit_data():
    csv_path = os.path.join(SCRIPT_DIR, "nonprofits_geocoded.csv")
    return pd.read_csv(csv_path).dropna(subset=["latitude", "longitude"])


# Pre-load all GeoJSON boundary files (small files, ~64 KB each)
@st.cache_data
def load_boundary(filename):
    filepath = os.path.join(SCRIPT_DIR, "boundaries", filename)
    with open(filepath, "r") as f:
        return json.load(f)


# =============================================================
# DUCKDB CONNECTION
# =============================================================


@st.cache_resource
def get_db_connection():
    """Return a read-only DuckDB connection, or None if .duckdb file missing."""
    db_path = os.path.join(SCRIPT_DIR, "incidents.duckdb")
    if not os.path.exists(db_path):
        return None
    return duckdb.connect(db_path, read_only=True)


def _use_duckdb():
    """Check whether DuckDB is available for this session."""
    return get_db_connection() is not None


# =============================================================
# CACHED COMPUTATION FUNCTIONS — DuckDB with pandas fallback
# =============================================================


def _build_where_clause(selected_years, selected_incidents, serious_crime_filter):
    """Build a SQL WHERE clause from the sidebar filter values."""
    clauses = ["latitude IS NOT NULL", "longitude IS NOT NULL"]

    if selected_years:
        year_list = ",".join(str(int(y)) for y in selected_years)
        clauses.append(f"year IN ({year_list})")

    if "All" not in selected_incidents and selected_incidents:
        cats = ",".join(
            f"'{c.replace(chr(39), chr(39) + chr(39))}'" for c in selected_incidents
        )
        clauses.append(f"category IN ({cats})")

    if serious_crime_filter == "Serious Only":
        clauses.append("crime_severity = 'Serious'")
    elif serious_crime_filter == "Non-Serious Only":
        clauses.append("crime_severity = 'Not-Serious'")

    return " AND ".join(clauses)


# --- Incident types ---


@st.cache_data
def get_incident_types_duckdb():
    """Get distinct categories via SQL."""
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT DISTINCT category FROM incidents WHERE category IS NOT NULL ORDER BY category"
    ).fetchall()
    return ["All"] + [r[0] for r in rows]


@st.cache_data
def get_incident_types_pandas(_data_categories):
    """Fallback: compute sorted incident types from pandas column."""
    return ["All"] + sorted(_data_categories)


# --- Unique years ---


@st.cache_data
def get_unique_years_duckdb():
    conn = get_db_connection()
    rows = conn.execute("SELECT DISTINCT year FROM incidents ORDER BY year").fetchall()
    return [int(r[0]) for r in rows]


# --- Filter data ---


@st.cache_data
def filter_data_duckdb(selected_years, selected_incidents, serious_crime_filter):
    """Run an indexed SQL query and return a pandas DataFrame."""
    conn = get_db_connection()
    where = _build_where_clause(
        selected_years, selected_incidents, serious_crime_filter
    )
    query = f"""
        SELECT latitude, longitude, category, crime_severity, Date, year
        FROM incidents
        WHERE {where}
    """
    df = conn.execute(query).df()
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def filter_data_pandas(data, selected_years, selected_incidents, serious_crime_filter):
    """Fallback: filter with pandas boolean indexing."""
    if "All" in selected_incidents:
        filtered = data[data["year"].isin(selected_years)]
    else:
        filtered = data[
            (data["category"].isin(selected_incidents))
            & (data["year"].isin(selected_years))
        ]
    if serious_crime_filter == "Serious Only":
        filtered = filtered[filtered["crime_severity"] == "Serious"]
    elif serious_crime_filter == "Non-Serious Only":
        filtered = filtered[filtered["crime_severity"] == "Not-Serious"]
    return filtered


# --- Hotspot calculation ---


@st.cache_data
def calculate_hotspots_duckdb(
    selected_years, selected_incidents, serious_crime_filter, hotspot_percentile
):
    """Single SQL query: bin → group → percentile filter."""
    conn = get_db_connection()
    where = _build_where_clause(
        selected_years, selected_incidents, serious_crime_filter
    )
    query = f"""
        WITH binned AS (
            SELECT ROUND(latitude, 3) AS lat_bin,
                   ROUND(longitude, 3) AS lon_bin
            FROM incidents
            WHERE {where}
        ),
        counts AS (
            SELECT lat_bin, lon_bin, COUNT(*) AS count
            FROM binned
            GROUP BY lat_bin, lon_bin
        ),
        cutoff AS (
            SELECT PERCENTILE_CONT({hotspot_percentile / 100})
                   WITHIN GROUP (ORDER BY count) AS val
            FROM counts
        )
        SELECT c.lat_bin, c.lon_bin, c.count
        FROM counts c, cutoff
        WHERE c.count >= cutoff.val
        ORDER BY c.count DESC
    """
    rows = conn.execute(query).fetchall()
    return [[r[0], r[1], r[2]] for r in rows]


@st.cache_data
def calculate_hotspots_pandas(lat_series, lon_series, hotspot_percentile):
    """Fallback: pandas groupby hotspot calculation."""
    lat_bin = lat_series.round(3)
    lon_bin = lon_series.round(3)
    counts = (
        pd.DataFrame({"lat_bin": lat_bin, "lon_bin": lon_bin})
        .groupby(["lat_bin", "lon_bin"])
        .size()
        .reset_index(name="count")
    )
    cutoff = counts["count"].quantile(hotspot_percentile / 100)
    top_points = counts[counts["count"] >= cutoff]
    return top_points[["lat_bin", "lon_bin", "count"]].values.tolist()


# --- Choropleth helper (unchanged, always from GeoJSON) ---


@st.cache_data
def build_choropleth_df(geojson_data, value_key="Estimate"):
    """Cache GeoJSON → DataFrame conversion for choropleth layers."""
    return pd.DataFrame(
        [
            {
                "tract": feature["properties"].get("tract"),
                value_key: feature["properties"].get(value_key),
            }
            for feature in geojson_data.get("features", [])
            if feature.get("properties")
            and feature["properties"].get("tract")
            and feature["properties"].get(value_key) is not None
        ]
    )


# =============================================================
# APP LAYOUT
# =============================================================

st.set_page_config(page_title="Lawrence Police Incidents Dashboard", layout="wide")

# ----- Global custom CSS -----
st.markdown(
    """
<style>
/* ---- Typography & spacing ---- */
h1 { font-size: 2rem !important; font-weight: 700 !important; letter-spacing: -0.02em; }
h2 { font-size: 1.45rem !important; font-weight: 600 !important; }
h3 { font-size: 1.15rem !important; font-weight: 600 !important; }

/* Tighten default Streamlit padding */
.block-container { padding-top: 2rem !important; padding-bottom: 1rem !important; }

/* ---- Tab styling ---- */
button[data-baseweb="tab"] {
    font-size: 1rem !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.2rem !important;
}

/* ---- Metric / KPI card ---- */
.kpi-row {
    display: flex; gap: 1rem; margin-bottom: 1.2rem; flex-wrap: wrap;
}
.kpi-card {
    flex: 1 1 160px;
    background: white;
    border: 1px solid #e0e4e8;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    min-width: 140px;
}
.kpi-card .kpi-value {
    font-size: 1.6rem; font-weight: 700; color: #0079c1; line-height: 1.2;
}
.kpi-card .kpi-label {
    font-size: 0.78rem; color: #666; text-transform: uppercase; letter-spacing: 0.04em;
    margin-top: 0.15rem;
}

/* ---- Info card used on About tab ---- */
.info-card {
    background: white;
    border: 1px solid #e0e4e8;
    border-left: 4px solid #0079c1;
    border-radius: 8px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.info-card h4 {
    margin: 0 0 0.5rem 0; font-size: 1rem; font-weight: 600; color: #0079c1;
}
.info-card p, .info-card li {
    font-size: 0.92rem; line-height: 1.55; color: #333;
}

/* ---- Footer ---- */
.app-footer {
    margin-top: 3rem;
    padding: 1.25rem 0;
    border-top: 1px solid #e0e4e8;
    text-align: center;
    font-size: 0.8rem;
    color: #888;
}
.app-footer a { color: #0079c1; text-decoration: none; }
.app-footer a:hover { text-decoration: underline; }

/* ---- Sidebar polish ---- */
section[data-testid="stSidebar"] {
    background-color: #f8fafb !important;
}
section[data-testid="stSidebar"] .stMarkdown h2 {
    font-size: 1.05rem !important; font-weight: 700 !important;
    border-bottom: 2px solid #0079c1; padding-bottom: 0.4rem; margin-bottom: 0.8rem;
}

/* ---- Expander styling ---- */
details summary {
    font-weight: 600 !important; font-size: 0.9rem !important;
}
</style>
""",
    unsafe_allow_html=True,
)

st.title("Lawrence Police Incidents Dashboard")
st.caption("Exploring public safety patterns in Lawrence, MA  |  Data: 2018 -- 2024")

# Initialize active_tab in session_state
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "About Project"


def set_tab(tab_name):
    st.session_state.active_tab = tab_name


# Tabs
tab1, tab2, tab3 = st.tabs(["About the Project", "Data Trends", "Spatial Insights"])


# =============================================================
# TAB 1 — ABOUT THE PROJECT
# =============================================================
with tab1:
    set_tab("About the Project")

    # Hero section
    st.markdown(
        """
<div class="info-card" style="border-left-color: #0079c1;">
<h4>About This Dashboard</h4>
<p>
The Lawrence Police Dashboard transforms publicly available daily police log data
from the Lawrence Police Department into interactive visualizations. It highlights
<strong>when, where, and what kinds</strong> of incidents occur, equipping residents,
community organizations, and policymakers to understand public safety patterns and
make informed decisions.
</p>
<p>
By integrating socioeconomic and demographic context layers, we provide a deeper
understanding of the influences on public safety, helping the community work
together toward safer neighborhoods.
</p>
</div>
""",
        unsafe_allow_html=True,
    )

    # Three-column feature highlights
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown(
            """
<div class="info-card">
<h4>Temporal Trends</h4>
<p>Incident counts by year and month reveal seasonal patterns, long-term trends,
and the impact of policy changes.</p>
</div>""",
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            """
<div class="info-card">
<h4>Spatial Insights</h4>
<p>Interactive maps with heatmaps, hotspot analysis, and points of interest
show <em>where</em> incidents concentrate.</p>
</div>""",
            unsafe_allow_html=True,
        )
    with col_c:
        st.markdown(
            """
<div class="info-card">
<h4>Context Layers</h4>
<p>Overlay poverty, unemployment, income, and median age data at the
census-tract level for equity-informed analysis.</p>
</div>""",
            unsafe_allow_html=True,
        )

    # Data Sources
    st.markdown("---")
    st.subheader("Data Sources")
    st.markdown("""
| Source | Description |
|--------|-------------|
| [Lawrence PD Daily Logs](https://www.lawpd.com/DocumentCenter/Index/237) | Incident-level entries with timestamps and locations (2018 -- 2024) |
| [U.S. Census ACS](https://data.census.gov) | Neighborhood socioeconomic indicators at census-tract scale |
| [MA ABCC Licenses](https://www.mass.gov/info-details/abcc-active-licenses) | Points of interest -- bars, liquor stores, restaurants, etc. |
""")

    # Collapsible: Incident Categories
    with st.expander("Incident Categories (14 groups)", expanded=False):
        st.markdown("""
| Category | Examples |
|----------|----------|
| Motor Vehicle Incidents | Traffic stops, crashes, towing, road hazards, lockouts |
| Preventive Policing | Extra patrols, building checks, park-and-walks |
| Public Disturbances | Noise, trespassing, neighbor disputes, fireworks |
| Fire and Arson | Fire calls, alarms, arson |
| Domestic Disputes | Domestic incidents, restraining orders, keep-the-peace |
| Suspicious Activity | Suspicious person/vehicle, gang intel, harassing calls |
| Law Enforcement Ops | Investigations, warrants, transports, mutual aid |
| Medical/Welfare | Welfare checks, ambulance assists, missing persons |
| Property Crimes | Burglary, theft, vandalism, stolen/recovered property |
| Financial Crimes | Counterfeit, identity theft, fraud, forgery |
| Violent/Weapons Offenses | Assaults, threats, shots fired, robberies, homicide |
| Drug and Substance Use | Drug investigations, overdoses, seizures |
| Court/Admin Procedures | Court service, warrants, Sections 12/35, training |
| Other | Wires down, animals, 911 hang-ups, civil items |
""")

    # Collapsible: What are "Serious Crimes"?
    with st.expander("What are Serious Crimes?", expanded=False):
        st.markdown("""
Serious crimes highlight higher-harm and higher-risk events:

- **Violent offenses** -- assaults with weapons, robberies, shootings, home invasions
- **Sex offenses** and child/elder harm
- **Major property crimes** -- burglary, significant theft, arson
- **Kidnapping** and domestic incidents with protective-order violations
- **Drug emergencies** and enforcement actions
- **Critical incidents** -- vehicle pursuits, fatalities
""")

    # How to use Data Trends
    with st.expander("How to Use the Data Trends Tab", expanded=False):
        st.markdown("""
1. Open **Data Trends**, then pick a view from the sidebar.
2. Use the Tableau filters (Category, Crime Severity) on the right side of the viz.
3. Hover for exact values, click legend items to highlight, use the toolbar to download.

**Available views:**

| View | What It Shows |
|------|--------------|
| Incidents Per Category | Bar chart + pie charts by category and severity |
| Incidents Per Year | Line chart of annual totals (spot multi-year trends) |
| Incidents Per Month | Line chart across all years (spot seasonality) |
""")

    # Data context notice
    st.info(
        "**Data context:** Entries reflect calls for service and officer reports, "
        "not court outcomes or convictions.",
        icon=None,
    )

    # Footer
    st.markdown(
        """
<div class="app-footer">
    Lawrence Police Incidents Dashboard &nbsp;&middot;&nbsp;
    Data: <a href="https://www.lawpd.com/DocumentCenter/Index/237">Lawrence PD Daily Logs</a> &nbsp;&middot;&nbsp;
    Built with <a href="https://streamlit.io">Streamlit</a>
</div>
""",
        unsafe_allow_html=True,
    )


# =============================================================
# TAB 2 — DATA TRENDS
# =============================================================
with tab2:
    set_tab("Data Trends")

    if st.session_state.active_tab == "Data Trends":
        with st.sidebar:
            st.markdown("## Data Trends")
            viz_choice = st.selectbox(
                "Choose a view",
                [
                    "Incidents Per Category",
                    "Incidents Per Year",
                    "Incidents Per Month",
                    "Charge Analysis",
                ],
                index=0,
                help="Tableau views have built-in filters. Charge Analysis uses pre-aggregated charge data.",
            )
    else:
        viz_choice = None

    if viz_choice and viz_choice != "Charge Analysis":
        st.subheader(viz_choice)
        components.html(TABLEAU_VIZ_MAP[viz_choice], height=850, scrolling=True)

    elif viz_choice == "Charge Analysis":
        charge_df = load_charge_data()

        # ── Top-K Charge Frequency ──────────────────────────────────────────
        st.subheader("Charge Frequency")
        top_k = st.slider(
            "Number of top charges to show", min_value=5, max_value=25, value=10, step=1
        )

        color_map = {"Misdemeanor": "#4C72B0", "Felony": "#DD8452", "Either": "#55A868"}

        top_charges = charge_df.nlargest(top_k, "total_count").sort_values(
            "total_count", ascending=True
        )
        fig_bar = px.bar(
            top_charges,
            x="total_count",
            y="base_charge",
            orientation="h",
            color="charge_class",
            color_discrete_map=color_map,
            labels={
                "total_count": "Count",
                "base_charge": "Charge",
                "charge_class": "Class",
            },
            title=f"Top {top_k} Most Frequent Charges",
        )
        fig_bar.update_layout(
            height=max(400, top_k * 28),
            yaxis=dict(tickfont=dict(size=11)),
            legend_title_text="Charge Class",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # ── Misdemeanor Distribution ────────────────────────────────────────
        st.subheader("Misdemeanor Distribution")
        col1, col2 = st.columns([1, 2])

        with col1:
            class_counts = charge_df.groupby("charge_class", as_index=False)[
                "total_count"
            ].sum()
            fig_donut = px.pie(
                class_counts,
                values="total_count",
                names="charge_class",
                hole=0.5,
                color="charge_class",
                color_discrete_map=color_map,
                title="Charge Class Split",
            )
            fig_donut.update_traces(textposition="inside", textinfo="percent+label")
            fig_donut.update_layout(showlegend=False)
            st.plotly_chart(fig_donut, use_container_width=True)

        with col2:
            mis_df = (
                charge_df[charge_df["charge_class"] == "Misdemeanor"]
                .nlargest(top_k, "total_count")
                .sort_values("total_count", ascending=True)
            )
            fig_mis = px.bar(
                mis_df,
                x="total_count",
                y="base_charge",
                orientation="h",
                color_discrete_sequence=["#4C72B0"],
                labels={"total_count": "Count", "base_charge": "Charge"},
                title=f"Top {top_k} Misdemeanor Charges",
            )
            fig_mis.update_layout(
                height=max(400, top_k * 28),
                yaxis=dict(tickfont=dict(size=11)),
                showlegend=False,
            )
            st.plotly_chart(fig_mis, use_container_width=True)

    # Footer
    st.markdown(
        """
<div class="app-footer">
    Lawrence Police Incidents Dashboard &nbsp;&middot;&nbsp;
    Data: <a href="https://www.lawpd.com/DocumentCenter/Index/237">Lawrence PD Daily Logs</a> &nbsp;&middot;&nbsp;
    Built with <a href="https://streamlit.io">Streamlit</a>
</div>
""",
        unsafe_allow_html=True,
    )


# =============================================================
# TAB 3 — SPATIAL INSIGHTS
# =============================================================
with tab3:
    set_tab("Spatial Insights")

    # Detect whether DuckDB is available
    use_db = _use_duckdb()

    # Load shared data (cached)
    with st.spinner("Loading incident data..."):
        lawrence_geojson = load_lawrence_boundary()
        liquor_df = load_liquor_data()
        school_df = load_school_data()
        pow_df = load_worship_data()
        nonprofit_df = load_nonprofit_data()
        data = None if use_db else load_data()

    # Compute incident types and years
    if use_db:
        incident_types = get_incident_types_duckdb()
        all_years = get_unique_years_duckdb()
    else:
        incident_types = get_incident_types_pandas(
            tuple(data["category"].dropna().unique())
        )
        all_years = sorted(data["year"].unique().tolist())

    # Choropleth data is loaded lazily below, after the overlay selector is rendered

    # -----------------------------
    # SIDEBAR CONTROLS
    # -----------------------------
    if st.session_state.active_tab == "Spatial Insights":
        with st.sidebar:
            st.markdown("## Map Controls")

            with st.expander("Filters", expanded=True):
                selected_year = st.multiselect(
                    "Year(s)",
                    all_years,
                    default=[2022, 2023, 2024],
                    help="Select one or more years to include.",
                )
                selected_incidents = st.multiselect(
                    "Incident Categories",
                    incident_types,
                    default="Violent and Weapon Offenses",
                    help="Choose 'All' or pick specific categories.",
                )
                serious_crime_filter = st.selectbox(
                    "Crime Severity",
                    ["All", "Serious Only", "Non-Serious Only"],
                    help="Filter by serious or non-serious classification.",
                )

            with st.expander("Map Layers", expanded=False):
                heatmap_enabled = st.toggle(
                    "Show Heatmap",
                    value=False,
                    help="Replace cluster markers with a continuous heatmap.",
                )
                secondary_choice = st.selectbox(
                    "Socioeconomic Overlay",
                    [
                        "None",
                        "Poverty Data",
                        "Median Household Income",
                        "Unemployment Data",
                        "Median Age",
                    ],
                    index=0,
                    help="Overlay census-tract level context data on the map.",
                )
                poverty_layer_enabled = secondary_choice == "Poverty Data"
                unemployment_layer_enabled = secondary_choice == "Unemployment Data"
                median_household_income_layer_enabled = (
                    secondary_choice == "Median Household Income"
                )
                median_age_layer_enabled = secondary_choice == "Median Age"

            # Load choropleth data only when an overlay is actually selected
            if poverty_layer_enabled:
                poverty_geojson = load_boundary("poverty_boundary.geojson")
                poverty_choro_df = build_choropleth_df(poverty_geojson, "Estimate")
            elif unemployment_layer_enabled:
                unemployment_geojson = load_boundary("unemployment_boundary.geojson")
                unemployment_choro_df = build_choropleth_df(
                    unemployment_geojson, "Estimate"
                )
            elif median_household_income_layer_enabled:
                household_income_geojson = load_boundary(
                    "household_income_boundary.geojson"
                )
                household_income_choro_df = build_choropleth_df(
                    household_income_geojson, "Estimate"
                )
            elif median_age_layer_enabled:
                median_age_geojson = load_boundary("median_age_boundary.geojson")
                median_age_choro_df = build_choropleth_df(
                    median_age_geojson, "MedianAge"
                )

            with st.expander("Hotspot Analysis", expanded=False):
                hotspot_enabled = st.toggle(
                    "Show Hotspot Areas",
                    value=False,
                    help="Highlight areas with the highest incident density.",
                )
                hotspot_percentile = st.slider(
                    "Percentile Threshold",
                    70,
                    95,
                    90,
                    step=5,
                    help="Show only grid cells above this percentile in incident count.",
                )
                grid_size_m = st.selectbox(
                    "Grid Cell Size", ["250m", "500m", "1km"], index=1
                )
                hotspot_only = st.checkbox("Hide individual incidents", value=True)

            with st.expander("Points of Interest", expanded=False):
                show_poi = st.toggle(
                    "Show POIs",
                    value=False,
                    help="Show nearby bars, schools, places of worship, etc.",
                )
                selected_poi_types = []
                if show_poi:
                    selected_poi_types = st.multiselect(
                        "POI Types", POI_TYPES_LIST, default=["Non-Profits"]
                    )

        # -----------------------------
        # FILTER DATA
        # -----------------------------
        if use_db:
            filtered_data = filter_data_duckdb(
                tuple(selected_year),
                tuple(selected_incidents),
                serious_crime_filter,
            )
        else:
            filtered_data = filter_data_pandas(
                data,
                tuple(selected_year),
                tuple(selected_incidents),
                serious_crime_filter,
            )

        # --- KPI summary row ---
        n_incidents = len(filtered_data)
        year_range = (
            f"{min(selected_year)}--{max(selected_year)}" if selected_year else "N/A"
        )
        n_categories = len(set(filtered_data["category"])) if n_incidents else 0
        severity_label = (
            serious_crime_filter if serious_crime_filter != "All" else "All Severities"
        )

        st.markdown(
            f"""
<div class="kpi-row">
    <div class="kpi-card">
        <div class="kpi-value">{n_incidents:,}</div>
        <div class="kpi-label">Total Incidents</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-value">{year_range}</div>
        <div class="kpi-label">Year Range</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-value">{n_categories}</div>
        <div class="kpi-label">Categories</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-value">{severity_label}</div>
        <div class="kpi-label">Severity Filter</div>
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

        # -----------------------------
        # MAP
        # -----------------------------
        if not filtered_data.empty:
            with st.spinner("Building map..."):
                m = folium.Map(
                    location=[42.70, -71.155],
                    zoom_start=14,
                    control_scale=True,
                    tiles="CartoDB positron",
                )

                m.get_root().html.add_child(folium.Element(MAP_PADDING_CSS))

                folium.GeoJson(
                    lawrence_geojson,
                    name="Lawrence Border",
                    style_function=lambda x: {
                        "color": "#333",
                        "weight": 2.5,
                        "fillOpacity": 0,
                        "dashArray": "6 3",
                    },
                ).add_to(m)

                # Hotspots
                if hotspot_enabled and not filtered_data.empty:
                    if use_db:
                        heat_data = calculate_hotspots_duckdb(
                            tuple(selected_year),
                            tuple(selected_incidents),
                            serious_crime_filter,
                            hotspot_percentile,
                        )
                    else:
                        heat_data = calculate_hotspots_pandas(
                            filtered_data["latitude"],
                            filtered_data["longitude"],
                            hotspot_percentile,
                        )

                    heat_layer = folium.FeatureGroup(name="Hotspot Heatmap")
                    HeatMap(
                        heat_data,
                        radius=18,
                        blur=12,
                        min_opacity=0.35,
                        max_zoom=13,
                        gradient={
                            0.2: "#FFF3B0",
                            0.4: "#FFD166",
                            0.6: "#FAA307",
                            0.8: "#E85D04",
                            1.0: "#9D0208",
                        },
                    ).add_to(heat_layer)
                    heat_layer.add_to(m)

                # Socioeconomic layers
                if poverty_layer_enabled:
                    folium.Choropleth(
                        geo_data=poverty_geojson,
                        name="Poverty Index",
                        data=poverty_choro_df,
                        columns=["tract", "Estimate"],
                        key_on="feature.properties.tract",
                        fill_color="Blues",
                        fill_opacity=0.5,
                        line_opacity=0.3,
                        legend_name="Percent Below Poverty Line (%)",
                    ).add_to(m)
                    m.get_root().html.add_child(folium.Element(POVERTY_LEGEND_HTML))

                if unemployment_layer_enabled:
                    folium.Choropleth(
                        geo_data=unemployment_geojson,
                        name="Unemployment Data",
                        data=unemployment_choro_df,
                        columns=["tract", "Estimate"],
                        key_on="feature.properties.tract",
                        fill_color="PuBu",
                        fill_opacity=0.7,
                        line_opacity=0.2,
                        legend_name="Unemployment Rate (%)",
                    ).add_to(m)
                    m.get_root().html.add_child(
                        folium.Element(UNEMPLOYMENT_LEGEND_HTML)
                    )

                if median_household_income_layer_enabled:
                    folium.Choropleth(
                        geo_data=household_income_geojson,
                        name="Median Household Income",
                        data=household_income_choro_df,
                        columns=["tract", "Estimate"],
                        key_on="feature.properties.tract",
                        fill_color="PuBu",
                        fill_opacity=0.7,
                        line_opacity=0.2,
                        legend_name="Median Household Income (%)",
                    ).add_to(m)
                    m.get_root().html.add_child(
                        folium.Element(HOUSEHOLD_INCOME_LEGEND_HTML)
                    )

                if median_age_layer_enabled:
                    folium.Choropleth(
                        geo_data=median_age_geojson,
                        name="Median Age",
                        data=median_age_choro_df,
                        columns=["tract", "MedianAge"],
                        key_on="feature.properties.tract",
                        fill_color="PuBu",
                        fill_opacity=0.7,
                        line_opacity=0.2,
                        legend_name="Median Age (years)",
                    ).add_to(m)
                    m.get_root().html.add_child(folium.Element(MEDIAN_AGE_LEGEND_HTML))

                # Points of Interest
                if show_poi and selected_poi_types:
                    poi_group = folium.FeatureGroup(name="Points of Interest")
                    for poi_type in selected_poi_types:
                        if poi_type == "Schools":
                            for row in school_df.itertuples(index=False):
                                folium.Marker(
                                    [row.latitude, row.longitude],
                                    tooltip=row.NAME,
                                    icon=folium.CustomIcon(
                                        SCHOOL_ICON_URL, icon_size=(20, 20)
                                    ),
                                ).add_to(poi_group)
                        elif poi_type == "Places of Worship":
                            for row in pow_df.itertuples(index=False):
                                folium.Marker(
                                    [row.latitude, row.longitude],
                                    tooltip=row.NAME,
                                    icon=folium.CustomIcon(
                                        WORSHIP_ICON_URL, icon_size=(28, 28)
                                    ),
                                ).add_to(poi_group)
                        elif poi_type == "Non-Profits":
                            for row in nonprofit_df.itertuples(index=False):
                                folium.Marker(
                                    [row.latitude, row.longitude],
                                    popup=f"{row.Name}<br>{row.Address}",
                                    tooltip=row.Name,
                                    icon=folium.CustomIcon(
                                        NONPROFIT_ICON_URL, icon_size=(24, 24)
                                    ),
                                ).add_to(poi_group)
                        else:
                            dfp = liquor_df[liquor_df["TYPE"] == poi_type]
                            style = POI_STYLE_MAP.get(
                                poi_type, {"color": "gray", "icon": "info-sign"}
                            )
                            for row in dfp.itertuples(index=False):
                                folium.Marker(
                                    [row.latitude, row.longitude],
                                    popup=f"{row.NAME} ({poi_type})",
                                    tooltip=row.NAME,
                                    icon=folium.Icon(
                                        color=style["color"], icon=style["icon"]
                                    ),
                                ).add_to(poi_group)
                    poi_group.add_to(m)

                    # POI Legend
                    legend_lines = ["<b>POI Legend</b><br>"]
                    for poi_type in selected_poi_types:
                        if poi_type == "Schools":
                            legend_lines.append(
                                f'<img src="{SCHOOL_ICON_URL}" width="14"> Schools<br>'
                            )
                        elif poi_type == "Places of Worship":
                            legend_lines.append(
                                f'<img src="{WORSHIP_ICON_URL}" width="16"> Places of Worship<br>'
                            )
                        elif poi_type == "Non-Profits":
                            legend_lines.append(
                                f'<img src="{NONPROFIT_ICON_URL}" width="16"> Non-Profits<br>'
                            )
                        else:
                            style = POI_STYLE_MAP.get(poi_type, {})
                            color = style.get("color", "gray")
                            icon = style.get("icon", "info-sign")
                            legend_lines.append(
                                f'<i class="glyphicon glyphicon-{icon}" style="color:{color}"></i> {poi_type}<br>'
                            )

                    poi_legend_html = f"""
                    <div style="
                        position: fixed; bottom: 220px; left: 40px; width: 260px;
                        background: white; border: 1px solid #ccc; border-radius: 8px;
                        z-index: 9999; font-size: 13px; padding: 12px 14px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.12);
                    ">
                    <span style="color:#222;">{"".join(legend_lines)}</span>
                    </div>
                    """
                    m.get_root().html.add_child(folium.Element(poi_legend_html))

                # Incidents: heatmap or clusters
                if heatmap_enabled:
                    heat_list = filtered_data[["latitude", "longitude"]].values.tolist()
                    if heat_list:
                        HeatMap(heat_list).add_to(m)
                else:
                    m.get_root().html.add_child(folium.Element(CUSTOM_CLUSTER_CSS_JS))
                    cluster_group = folium.FeatureGroup(name="Incident Clusters")
                    marker_cluster = MarkerCluster().add_to(cluster_group)
                    for row in filtered_data.itertuples(index=False):
                        popup_text = f"{row.Date}<br>{row.category}"
                        folium.CircleMarker(
                            location=(float(row.latitude), float(row.longitude)),
                            radius=6,
                            color="#808080",
                            fill=True,
                            fill_color="#F2E8CF",
                            fill_opacity=0.8,
                            popup=popup_text,
                        ).add_to(marker_cluster)
                    cluster_group.add_to(m)

                folium.LayerControl().add_to(m)

            # Render map
            st_data = st_folium(m, width="100%", height=700, key="main_map")

        else:
            st.warning(
                "No data to display for the selected filters. Try adjusting the year or category selection."
            )

        # Footer
        st.markdown(
            """
<div class="app-footer">
    Lawrence Police Incidents Dashboard &nbsp;&middot;&nbsp;
    Data: <a href="https://www.lawpd.com/DocumentCenter/Index/237">Lawrence PD Daily Logs</a> &nbsp;&middot;&nbsp;
    Built with <a href="https://streamlit.io">Streamlit</a>
</div>
""",
            unsafe_allow_html=True,
        )

    else:
        st.sidebar.empty()
