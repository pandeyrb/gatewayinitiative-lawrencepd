import streamlit as st
import streamlit.components.v1 as components
# streamlit_app.py
import pandas as pd
import streamlit as st
import numpy as np
import folium
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import st_folium
from pathlib import Path
import os
import json
from folium import Element


st.set_page_config(page_title="Lawrence Police Incidents Dashboard", layout="wide")

st.title("Lawrence Police Incidents Dashboard")

# Initialize active_tab in session_state
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "About Project"

# Callback to track tab clicks
def set_tab(tab_name):
    st.session_state.active_tab = tab_name

st.markdown(
    """
    <style>
    div[data-testid="stHorizontalBlock"] > div:first-child > div > button > span {
        font-size: 18px !important;
        font-weight: 600 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# Tabs
tab1, tab2, tab3 = st.tabs(["About the Project", "Data Trends", "Spatial Insights"])

# About the Project tab
with tab1:
    set_tab("## About the Project")

    st.markdown("""

    The Lawrence Police Dashboard transforms publicly available daily police log data from the Lawrence Police Department into powerful, interactive visualizations. The dashboard highlights when, where, and what kinds of incidents occur, with the aim of equipping residents, community organizations, and policymakers to understand public safety patterns and make informed decisions. 

    By integrating additional data like socioeconomic and demographic factors, we provide a deeper understanding of the many influences on public safety, helping the community work together toward safer neighborhoods.

    ---

    ### What the Dashboard Shows
    - Incident trends over time (monthly, yearly)
    - Spatial patterns across neighborhoods and points of interest
    - Breakdown by incident category, with filters for year and category and “serious crime”

    ---

    ### Data Sources
    - Lawrence Police Department Daily Logs: Publicly available incident-level entries with timestamps and locations. (Source: https://www.lawpd.com/DocumentCenter/Index/237)
    - Context Data Layers (in progress): Neighborhood‑level socioeconomic and demographic indicators (e.g., poverty rates) added at census‑tract scales to preserve privacy and support equitable insights. (Source: https://data.census.gov)
    - Points of Interests (POIs): Optional map overlays to provide context around nearby places, including bars or lounges, convenience stores, grocery stores that sell alcohol, liquor stores, nightclubs, restaurants, and social clubs. (Source: https://www.mass.gov/info-details/abcc-active-licenses)

    ---

    ### Incident categories
    - Motor Vehicle Incidents: Traffic stops, crashes, disabled/abandoned cars, towing, road hazards, lockouts.
    - Preventive Policing: Extra patrols, building/business checks, park‑and‑walks, selective enforcement.
    - Public Disturbances: Disorder/noise, trespassing, unwanted guests, neighbor disputes, drinking in public, dumping, fireworks.
    - Fire and Arson Incidents: Fire calls and alarms (buildings/vehicles), assist fire department, arson.
    - Domestic Disputes and Protection: Domestic incidents, restraining orders (serve/violation), emergency orders, keep‑the‑peace.
    - Suspicious/Unusual Activity: Suspicious person/vehicle, gang intel, video extraction, annoying/harassing calls.
    - Law Enforcement Operations: Investigations, warrants, transports, pursuits, mutual aid, escorts/details, evidence handling, specialized unit deployments.
    - Medical/Welfare Assistance: Welfare checks, ambulance assists, person down, suicide attempts, missing/lost persons.
    - Property Crimes: Burglary/B&E (home/vehicle), theft/attempts (incl. shoplifting), vandalism, stolen/recovered property, lost/found.
    - Financial Crimes and Fraud: Counterfeit, forgery/uttering, identity theft, fraud, bribery.
    - Violent/Weapons Offenses: Assaults, threats, stalking, sex offenses, shots‑fired/weapons calls, homicide, robberies, home invasion.
    - Drug and Substance Use: Drug investigations, overdoses, evidence seizures, violations.
    - Court/Admin Procedures: Court service/time, warrants, Sections 12/35, escorts, training, alarm excusals.
    - Other: Miscellaneous service calls (e.g., wires down, animals, notifications, 911 hang‑ups, street closures, civil/admin items).

    ---

    ### Serious crimes
    Serious crimes highlight higher‑harm and higher‑risk events—violent offenses (e.g., assaults with weapons, robberies, shootings, home invasions), sex offenses and child/elder harm, major property crimes (burglary, significant theft, arson), kidnapping and domestic incidents with protective‑order violations, drug‑related emergencies and enforcement, and critical incidents like vehicle pursuits and fatalities.
    
    ---         

    ### About Data Trends

    The **Data Trends** tab contains three Tableau views.

    #### How to use this tab
    - Open **Data Trends**, then pick a view from **Choose a Tableau view** from the sidebar.
    - Use the filters on the right side of the Tableau viz, Category and Crime Severity, to refine what you see.
    - Hover to see exact values, click legend items to highlight, and use the toolbar to download or view full screen.

    #### The three views

    **Incidents Per Category**
    - Bar chart of the number of incidents by category.
    - Pie chart showing the percent share by category.
    - Pie chart showing Serious vs Non-Serious counts for the current filters.

    **Incidents Per Year**
    - Line chart of total incidents by year.
    - Use this to spot multi-year trends, peaks, and declines.
    - Category and Crime Severity filters still apply.

    **Incidents Per Month**
    - Line chart of incidents by month, across all years 2018-2024.
    - Helpful for seasonality and month to month changes.
    - Category and Crime Severity filters still apply.


    ### Data context
    - Source, Lawrence Police Department daily logs.
    - Entries reflect calls for service and their respective reports, not court outcomes.      
        """)

with tab2:
    set_tab("Data Trends")
    # st.title("📊 Data Trends")

    if st.session_state.active_tab == "Data Trends":
        with st.sidebar: 
            st.header("Data Trends Controls") 
            viz_choice = st.selectbox( 
                "Choose a Tableau view",
                ["Incidents Per Category", "Incidents Per Year", "Incidents Per Month"], 
                index=0,
            ) 
    else: 
        viz_choice = None

    if viz_choice:
        st.markdown(f"### {viz_choice}")

        # --- Incidents Per Category --- 
        html_code_incidents_per_category = """
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

        # --- Incidents Per Year --- 
        html_code_incidents_per_year = """
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

        # --- Incidents Per Month ---
        html_code_incidents_per_month = """
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

        # Map the selection to the correct HTML 
        viz_html_map = {
            "Incidents Per Category": html_code_incidents_per_category,
            "Incidents Per Year": html_code_incidents_per_year,
            "Incidents Per Month": html_code_incidents_per_month,
        }

        # Render only the chosen viz
        components.html(viz_html_map[viz_choice], height=850, scrolling=True)

# Map Insights tab
with tab3:
    set_tab("Spatial Insights")
    # -----------------------------
    # 📍 LOAD LAWRENCE BOUNDARY 
    # -----------------------------
    @st.cache_data
    def load_lawrence_boundary():
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, "boundaries", "lawrence_boundary.geojson")
        with open(file_path, "r") as f:
            lawrence_geojson = json.load(f)
            return lawrence_geojson
    lawrence_geojson = load_lawrence_boundary()

    # -----------------------------
    # 📊 LOAD DATA
    # -----------------------------

    @st.cache_data
    def load_data():
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, "checkpoint11_combined_data.csv")
        df = pd.read_csv(file_path)
        data = df[['latitude', 'longitude', 'category', 'crime_severity', 'Incident #', 'Date']].dropna()
        data['Date'] = pd.to_datetime(data['Date'])
        data['year'] = data['Date'].dt.year
        return data

    data = load_data()

    # -----------------------------
    # 🍺 LOAD LIQUOR RETAIL DATA
    # -----------------------------

    @st.cache_data
    def load_liquor_data():
        csv_path = os.path.join(os.path.dirname(__file__), "liquor_retail_geocoded.csv")
        return pd.read_csv(csv_path).dropna(subset=["latitude", "longitude"])

    liquor_df = load_liquor_data()

    # -----------------------------
    #  LOAD SCHOOL DATA
    # -----------------------------
    @st.cache_data
    def load_school_data():
        csv_path = os.path.join(os.path.dirname(__file__), "school_geocoded.csv")
        return pd.read_csv(csv_path).dropna(subset=["latitude", "longitude"])

    school_df = load_school_data()

    # -----------------------------
    #  LOAD PLACES OF WORSHIP DATA
    # -----------------------------
    @st.cache_data
    def load_worship_data():
        csv_path = os.path.join(os.path.dirname(__file__), "places_of_worship_geocoded.csv")
        return pd.read_csv(csv_path).dropna(subset=["latitude", "longitude"])

    pow_df = load_worship_data()

    # -----------------------------
    #  LOAD RECREATIONAL SPACES DATA
    # -----------------------------
    # @st.cache_data
    # def load_rec_data():
    #     csv_path = os.path.join(os.path.dirname(__file__), "recreation_spaces_geocoded.csv")
    #     return pd.read_csv(csv_path).dropna(subset=["latitude", "longitude"])

    # rec_df = load_rec_data()


    incident_types = ["All"] + sorted(data['category'].dropna().unique())

    # -----------------------------
    # 🧰 SIDEBAR FILTERS
    # -----------------------------
    if st.session_state.active_tab == "Spatial Insights":

        with st.sidebar:
            st.header("🔍 Filters")
            # selected_year = st.selectbox("📅 Select Year", sorted(data['year'].unique()))
            selected_year = st.multiselect(
            "📅 Select Year(s)",
            sorted(data['year'].unique().tolist()),
            default=sorted(data['year'].unique().tolist())  # show all years by default
            )
            st.markdown("---")
            st.subheader("📌 Incident Categories")
            selected_incidents = st.multiselect("Choose incidents to view:", incident_types, default="Violent and Weapon Offenses")
            serious_crime_filter = st.selectbox(
            "🚨 Filter by Serious Crime",
            ["All", "Serious Only", "Non-Serious Only"])
            # -----------------------------
            # Heatmap Toggle
            # -----------------------------
            heatmap_enabled = st.sidebar.toggle("Show Heatmap", value=False)

            # -----------------------------
            # Secondary Data Selectbox
            # -----------------------------
            
            secondary_choice = st.selectbox(
                "Show Secondary Data",
                ["None", "Poverty Data", "Median Household Income", "Unemployment Data"],
                index=0
            )
            poverty_layer_enabled = secondary_choice == "Poverty Data"
            unemployment_layer_enabled = secondary_choice == "Unemployment Data"
            median_household_income_layer_enabled = secondary_choice == "Median Household Income"

            # -----------------------------
            # 🗺️ POI Toggle and Category Filters
            # -----------------------------
            show_poi = st.toggle("Show Points of Interest", value=False)

            selected_poi_types = []
            if show_poi:
                poi_types = [
                    "All", "Bar or Lounge", "Convenience Store", 
                    "Grocery Store w/ Liquor", "Liquor Store", 
                    "Nightclub", "Restaurant", "Social Club", 
                    "Schools", "Places of Worship"#, "Recreational Spaces"
                ]
                poi_types_with_all = ["All"] + poi_types

                selected_poi_types = st.multiselect("Choose POI Types (*Note: Liquor vendors only):", poi_types, default=["Schools"])

                if "All" in selected_poi_types:
                    selected_poi_types = poi_types
                    selected_poi_types.remove("All")
                else:
                    selected_poi_types = selected_poi_types


        # -----------------------------
        # 🧹 FILTER DATA
        # -----------------------------
        if "All" in selected_incidents:
            filtered_data = data[data['year'].isin(selected_year)]
        else:
            filtered_data = data[(data['category'].isin(selected_incidents)) & 
                                (data['year'].isin(selected_year))]


        filtered_data = filtered_data.dropna(subset=['latitude', 'longitude'])
        if serious_crime_filter == "Serious Only":
            filtered_data = filtered_data[filtered_data['crime_severity'] == 'Serious']
        elif serious_crime_filter == "Non-Serious Only":
            filtered_data = filtered_data[filtered_data['crime_severity'] == 'Not-Serious']
        else:
            filtered_data = filtered_data

        st.markdown(f"### Total Incidents for selected filters:  {len(filtered_data)}")

        # -----------------------------
        # 🗺️ CREATE MAP
        # -----------------------------
        if not filtered_data.empty:
            # m = folium.Map(location=[42.707, -71.155], zoom_start=14, control_scale=True)
            m = folium.Map(location=[42.70, -71.155],zoom_start=14,control_scale=True,tiles="CartoDB positron")

            # Add extra padding around map
            m.get_root().html.add_child(folium.Element("""
                <style>
                .leaflet-bottom.leaflet-right {
                    margin-bottom: 10px;
                    margin-right: 10px;
                }
                </style>
            """))

            # Add Lawrence city boundary
            folium.GeoJson(
                lawrence_geojson,
                name="Lawrence Border",
                style_function=lambda x: {
                    'color': 'black',
                    'weight': 3,
                    'fillOpacity': 0
                }
            ).add_to(m)

            # Add Poverty Choropleth Layer (Toggleable)
            if poverty_layer_enabled:
                poverty_path = os.path.join(os.path.dirname(__file__), "boundaries", "poverty_boundary.geojson")
                with open(poverty_path, "r") as f:
                    poverty_data = json.load(f)

                # convert choropleth_data to a df, better runtime performance than lists of lists
                choropleth_data = pd.DataFrame([
                    {
                        "tract": feature["properties"].get("tract"),
                        "Estimate": feature["properties"].get("Estimate")
                    }
                    for feature in poverty_data["features"]
                    if feature["properties"].get("tract") and feature["properties"].get("Estimate") is not None
                ])
                
                folium.Choropleth(
                    geo_data=poverty_data,
                    name="Poverty Index",
                    data=choropleth_data,
                    columns=["tract", "Estimate"],
                    key_on="feature.properties.tract",
                    fill_color="OrRd",
                    fill_opacity=0.7,
                    line_opacity=0.2,
                    legend_name="Percent Below Poverty Line (%)",
                ).add_to(m)

                # -----------------------------
                # 🧾 ADD CUSTOM POVERTY LEGEND
                # -----------------------------
                legend_html = """
                <div style="
                    position: fixed; 
                    bottom: 40px; 
                    left: 40px; 
                    z-index:9999; 
                    background-color: white; 
                    padding: 10px; 
                    border:2px solid gray; 
                    border-radius: 5px;
                    font-size: 14px;
                    box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
                ">
                    <strong style="color: black;">Poverty Estimate (%)</strong><br>
                    <span style="color: black;">
                        <i style="background:#fff5eb;width:20px;height:10px;display:inline-block;"></i> 0–8%<br>
                        <i style="background:#fcbba1;width:20px;height:10px;display:inline-block;"></i> 8–15.6%<br>
                        <i style="background:#fc9272;width:20px;height:10px;display:inline-block;"></i> 15.6–20.3%<br>
                        <i style="background:#fb6a4a;width:20px;height:10px;display:inline-block;"></i> 20.3–28.4%<br>
                        <i style="background:#de2d26;width:20px;height:10px;display:inline-block;"></i> 28.4–36.7%<br>
                        <i style="background:#a50f15;width:20px;height:10px;display:inline-block;"></i> 36.7%+
                    </span>
                </div>
                """

                m.get_root().html.add_child(folium.Element(legend_html))


            # -------------------------------------------------------
            # Add Unemployment Choropleth Layer, mirrors poverty
            # -------------------------------------------------------
            if unemployment_layer_enabled:
                unemployment_path = os.path.join(os.path.dirname(__file__), "boundaries", "unemployment_boundary.geojson")
                with open(unemployment_path, "r") as f:
                    unemployment_data = json.load(f)

                # build DataFrame like poverty, using tract and Estimate
                unemployment_df = pd.DataFrame([
                    {
                        "tract": feature["properties"].get("tract"),
                        "Estimate": feature["properties"].get("Estimate")
                    }
                    for feature in unemployment_data.get("features", [])
                    if feature.get("properties")
                    and feature["properties"].get("tract")
                    and feature["properties"].get("Estimate") is not None
                ])

                folium.Choropleth(
                    geo_data=unemployment_data,
                    name="Unemployment Data",
                    data=unemployment_df,
                    columns=["tract", "Estimate"],
                    key_on="feature.properties.tract",
                    fill_color="OrRd", 
                    fill_opacity=0.7,
                    line_opacity=0.2,
                    legend_name="Unemployment Rate (%)",
                ).add_to(m)

                # -----------------------------
                # Unemployment Legend, same style as poverty legend
                # -----------------------------
                unemployment_legend_html = """
                <div style="
                    position: fixed; 
                    bottom: 40px; 
                    left: 40px; 
                    z-index:9999; 
                    background-color: white; 
                    padding: 10px; 
                    border:2px solid gray; 
                    border-radius: 5px;
                    font-size: 14px;
                    box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
                ">
                    <strong style="color: black;">Unemployment Rate (%)</strong><br>
                    <span style="color: black;">
                        <i style="background:#fff5f0;width:20px;height:10px;display:inline-block;"></i> 2.3%<br>
                        <i style="background:#fcbba1;width:20px;height:10px;display:inline-block;"></i> 2.4 – 5.2%<br>
                        <i style="background:#fc9272;width:20px;height:10px;display:inline-block;"></i> 5.3 – 8.3%<br>
                        <i style="background:#fb6a4a;width:20px;height:10px;display:inline-block;"></i> 8.4 – 10.4%<br>
                        <i style="background:#cb181d;width:20px;height:10px;display:inline-block;"></i> 10.5 – 12.8%<br>
                    </span>
                </div>
                """
                m.get_root().html.add_child(folium.Element(unemployment_legend_html))

            # -------------------------------------------------------
            # Add Median Household Income Choropleth Layer
            # -------------------------------------------------------
            if median_household_income_layer_enabled:
                median_household_income_path = os.path.join(os.path.dirname(__file__), "boundaries", "household_income_boundary.geojson")
                with open(median_household_income_path, "r") as f:
                    median_household_income_data = json.load(f)

                # build DataFrame using tract and Estimate
                median_household_income_df = pd.DataFrame([
                    {
                        "tract": feature["properties"].get("tract"),
                        "Estimate": feature["properties"].get("Estimate")
                    }
                    for feature in median_household_income_data.get("features", [])
                    if feature.get("properties")
                    and feature["properties"].get("tract")
                    and feature["properties"].get("Estimate") is not None
                ])

                folium.Choropleth(
                    geo_data=median_household_income_data,
                    name="Median Household Income",
                    data=median_household_income_df,
                    columns=["tract", "Estimate"],
                    key_on="feature.properties.tract",
                    fill_color="OrRd", 
                    fill_opacity=0.7,
                    line_opacity=0.2,
                    legend_name="Median Household Income (%)",
                ).add_to(m)

                # ----------------------------- 
                # Median Household Income Legend (USD)
                # -----------------------------
                median_household_income_data_legend_html = """
                <div style="
                    position: fixed; 
                    bottom: 40px; 
                    left: 40px; 
                    z-index:9999; 
                    background-color: white; 
                    padding: 10px; 
                    border:2px solid gray; 
                    border-radius: 5px;
                    font-size: 14px;
                    box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
                ">
                    <strong style="color: black;">Median Household Income (USD)</strong><br>
                    <span style="color: black;">
                        <i style="background:#cb181d;width:20px;height:10px;display:inline-block;"></i> $76k to $88k<br>
                        <i style="background:#fb6a4a;width:20px;height:10px;display:inline-block;"></i> $61k to $76k<br>
                        <i style="background:#fc9272;width:20px;height:10px;display:inline-block;"></i> $41k to $61k<br>
                        <i style="background:#fcbba1;width:20px;height:10px;display:inline-block;"></i> $33k to $41k<br>
                        <i style="background:#fff5f0;width:20px;height:10px;display:inline-block;"></i> $23k to $33k<br>
                    </span>
                </div>
                """
                m.get_root().html.add_child(folium.Element(median_household_income_data_legend_html))

            # -----------------------------
            # 🧼 Define POI marker style
            # -----------------------------
            # Neutral PNGs for Streamlit-safe icons
            school_icon_url = "https://cdn-icons-png.flaticon.com/512/3135/3135810.png"  
            worship_icon_url = "https://cdn-icons-png.flaticon.com/512/4258/4258470.png" 
            # rec_icon_url = "https://cdn-icons-png.flaticon.com/512/2169/2169407.png"  


            poi_style_map = {
                "Restaurant": {"color": "black", "icon": "cutlery"},#, "prefix": "glyphicon"},
                "Liquor Store": {"color": "black", "icon": "shopping-cart"},# "prefix": "glyphicon"},
                "Bar or Lounge": {"color": "black", "icon": "glass"},# "prefix": "glyphicon"},
                "Nightclub": {"color": "black", "icon": "music"}, #"prefix": "glyphicon"},
                "Grocery Store w/ Liquor": {"color": "black", "icon": "shopping-cart"}, #"prefix": "glyphicon"},
                "Convenience Store": {"color": "black", "icon": "shopping-cart"}, # "prefix": "glyphicon"},
                "Social Club": {"color": "black", "icon": "star"}, #"prefix": "glyphicon"},
                "Schools": {"color": "black", "icon_url": school_icon_url}, #"prefix": "glyphicon"},
                "Places of Worship": {"color": "black", "icon_url": worship_icon_url}, #"prefix": "glyphicon"},
                # "Recreational Spaces": {"icon_url": rec_icon_url}
            }


            # -----------------------------
            # 📍 Add POI Markers to Map
            # -----------------------------
            if show_poi and selected_poi_types:
                for poi_type in selected_poi_types:
                    if poi_type == "Schools":
                        df = school_df
                        for _, row in df.iterrows():
                            folium.Marker(
                                location=[row["latitude"], row["longitude"]],
                                popup=f'{row["NAME"]} ({poi_type})',
                                tooltip=row["NAME"],
                                icon=folium.CustomIcon(poi_style_map[poi_type]["icon_url"], icon_size=(20, 20))
                            ).add_to(m)
                        continue

                    if poi_type == "Places of Worship":
                        df = pow_df
                        for _, row in df.iterrows():
                            folium.Marker(
                                location=[row["latitude"], row["longitude"]],
                                popup=f'{row["NAME"]} ({poi_type})',
                                tooltip=row["NAME"],
                                icon=folium.CustomIcon(poi_style_map[poi_type]["icon_url"], icon_size=(30, 30))
                            ).add_to(m)
                        continue

                    

                    # all others remain the same
                    df = liquor_df[liquor_df["TYPE"] == poi_type]
                    style = poi_style_map.get(poi_type, {"color": "gray", "icon": "info-sign"})#, "prefix": "glyphicon"})
                    for _, row in df.iterrows():
                        folium.Marker(
                            location=[row["latitude"], row["longitude"]],
                            popup=f'{row["NAME"]} ({poi_type})',
                            tooltip=row["NAME"],
                            icon=folium.Icon(color=style["color"], icon=style["icon"])#, prefix=style["prefix"])
                        ).add_to(m)
                
                # -----------------------------
                # 🧾 POI Legend
                # -----------------------------
                legend_lines = ["<b>POI Legend</b><br>"]
                for poi_type in selected_poi_types:
                    if poi_type == "Schools":
                        legend_lines.append(f'<img src="{school_icon_url}" width="14"> Schools<br>')
                    elif poi_type == "Places of Worship":
                        legend_lines.append(f'<img src="{worship_icon_url}" width="16"> Places of Worship<br>')
                    
                    else:
                        style = poi_style_map.get(poi_type, {})
                        color = style.get("color", "gray")
                        icon = style.get("icon", "info-sign")
                        legend_lines.append(f'<i class="glyphicon glyphicon-{icon}" style="color:{color}"></i> {poi_type}<br>')


                # legend_lines = ["<b>POI Legend</b><br>"]
                # for poi_type in selected_poi_types:
                #     style = poi_style_map.get(poi_type, {})
                #     color = style.get("color", "gray")
                #     icon = style.get("icon", "info-sign")
                #     legend_lines.append(
                #     f'<i class="glyphicon glyphicon-{icon}" style="color:{color}"></i> {poi_type}<br>'
                #     )

                poi_legend_html = f"""
                <div style="
                    position: fixed;
                    bottom: 220px;
                    left: 40px;
                    width: 280px;
                    background-color: white;
                    border:2px solid gray;
                    border-radius: 5px;
                    z-index:9999;
                    font-size:14px;
                    padding: 10px;
                    box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
                ">
                <span style="color:black;">
                {''.join(legend_lines)}
                </span>
                </div>
                """

                m.get_root().html.add_child(folium.Element(poi_legend_html))
            # -----------------------------
            # Add Heatmap or Clustered Markers
            # -----------------------------
            if heatmap_enabled:
                heat_data = filtered_data[['latitude', 'longitude']].dropna()
                heat_data = heat_data[
                    (heat_data['latitude'].apply(lambda x: isinstance(x, (float, int)))) &
                    (heat_data['longitude'].apply(lambda x: isinstance(x, (float, int))))
                ]
                heat_list = heat_data[['latitude', 'longitude']].values.tolist()
                if heat_list:
                    HeatMap(heat_list).add_to(m)
            else:
                # Custom JS/CSS for cluster colors:
                custom_css_js_fixed_circle = """
                <style>
                .marker-cluster-small,
                .marker-cluster-medium,
                .marker-cluster-large{
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    border-radius: 50% !important;
                    border: none !important;
                    box-shadow: 0 0 8px rgba(0,0,0,0.3);
                    color: white !important;
                    font-weight: bold !important;
                    text-align: center !important;
                    padding: 0 !important;
                    margin: 0 !important;
                }

                .marker-cluster-small {
                    width: 30px !important;
                    height: 30px !important;
                    font-size: 14px !important;
                    background-color: #0072B2 !important;
                }

                .marker-cluster-medium {
                    width: 40px !important;
                    height: 40px !important;
                    font-size: 16px !important;
                    background-color: #E69F00 !important;
                }

                .marker-cluster-large {
                    width: 50px !important;
                    height: 50px !important;
                    font-size: 18px !important;
                    background-color: #D55E00 !important;
                }

                .marker-cluster div {
                    background: none !important;
                    border: none !important;
                    box-shadow: none !important;
                    padding: 0 !important;
                    margin: 0 !important;
                }
                </style>

                <script>
                L.MarkerClusterGroup.prototype.options.iconCreateFunction = function (cluster) {
                    var count = cluster.getChildCount();
                    var c = ' marker-cluster-';
                    var size = 30;
                    if (count < 50) {
                        c += 'small';
                        size = 25;
                    } else if (count < 250) {
                        c += 'medium';
                        size = 50;
                    } else {
                        c += 'large';
                        size = 70;
                    }
                    return new L.DivIcon({
                        html: '<div><span>' + count + '</span></div>',
                        className: 'marker-cluster' + c,
                        iconSize: new L.Point(size, size)
                    });
                };
                </script>
                """

                m.get_root().html.add_child(folium.Element(custom_css_js_fixed_circle))


                marker_cluster = MarkerCluster().add_to(m)
                for _, row in filtered_data.iterrows():
                    popup_text = f"{row['Date']}<br>{row['category']}"
                    folium.CircleMarker(
                        location=(row['latitude'], row['longitude']),
                        radius=6,
                        color="#0072B2",
                        fill=True,
                        fill_opacity=0.8,
                        popup=popup_text
                    ).add_to(marker_cluster)



                # Add Layer Control and render
                # folium.LayerControl().add_to(m)
                # st_data = st_folium(m, width="100%", height=750)


            # Add Layer Control (for toggling on/off the choropleth)
            folium.LayerControl().add_to(m)

            # Render the map in Streamlit
            st_data = st_folium(m, width="100%", height=750)

        else:
            st.warning("No data to display on the map for the selected filters.")

    else:
        st.sidebar.empty()  # hides sidebar for other tabs