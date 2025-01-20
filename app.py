import streamlit as st
import requests
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

# Function to fetch earthquake data (USGS API)
def fetch_earthquake_data():
    try:
        url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=100"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            earthquakes = []
            for feature in data['features']:
                magnitude = feature['properties']['mag']
                if magnitude >= 4:  # You can adjust the threshold here
                    lat = feature['geometry']['coordinates'][1]
                    lon = feature['geometry']['coordinates'][0]
                    earthquakes.append([lat, lon, magnitude])
            return earthquakes
        else:
            st.error("Error fetching earthquake data.")
            return []
    except Exception as e:
        st.error(f"Error fetching earthquake data: {e}")
        return []

# Function to fetch hurricane data (Example NOAA API)
def fetch_hurricane_data():
    try:
        # Replace with actual NOAA API endpoint for hurricanes
        # Example URL (you will need to use the correct endpoint with proper data)
        url = "https://www.nhc.noaa.gov/gis/forecast/archive/"
        response = requests.get(url)
        if response.status_code == 200:
            hurricanes = []
            # Example parsing (actual parsing depends on the data format)
            return hurricanes
        else:
            st.error("Error fetching hurricane data.")
            return []
    except Exception as e:
        st.error(f"Error fetching hurricane data: {e}")
        return []

# Function to fetch flood data (NWS API)
def fetch_flood_data():
    try:
        url = "https://api.weather.gov/alerts"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            floods = []
            for feature in data['features']:
                lat = feature['geometry']['coordinates'][1]
                lon = feature['geometry']['coordinates'][0]
                severity = feature['properties']['severity']
                floods.append([lat, lon, severity])
            return floods
        else:
            st.error("Error fetching flood data.")
            return []
    except Exception as e:
        st.error(f"Error fetching flood data: {e}")
        return []

# Function to fetch tornado data (SPC API)
def fetch_tornado_data():
    try:
        url = "https://www.spc.noaa.gov/products/wwa/"
        response = requests.get(url)
        if response.status_code == 200:
            tornadoes = []
            return tornadoes
        else:
            st.error("Error fetching tornado data.")
            return []
    except Exception as e:
        st.error(f"Error fetching tornado data: {e}")
        return []

# Function to fetch wildfire data (NASA FIRMS API)
def fetch_wildfire_data():
    try:
        url = "https://firms.modaps.eosdis.nasa.gov/api/"
        response = requests.get(url)
        if response.status_code == 200:
            wildfires = []
            return wildfires
        else:
            st.error("Error fetching wildfire data.")
            return []
    except Exception as e:
        st.error(f"Error fetching wildfire data: {e}")
        return []

# Function to generate a natural disaster heatmap
def generate_natural_disaster_heatmap():
    # Fetch data for all disaster types
    earthquakes = fetch_earthquake_data()
    hurricanes = fetch_hurricane_data()
    floods = fetch_flood_data()
    tornadoes = fetch_tornado_data()
    wildfires = fetch_wildfire_data()

    # Create a map object
    folium_map = folium.Map(location=[20, 0], zoom_start=2)  # World view

    # Adding earthquake data to the heatmap
    if earthquakes:
        heat_data = [[e[0], e[1], e[2] * 10] for e in earthquakes]  # Scaling magnitude
        HeatMap(heat_data).add_to(folium_map)

    # Adding hurricane data to the heatmap
    if hurricanes:
        heat_data = [[h[0], h[1], h[2] * 10] for h in hurricanes]  # Scaling intensity
        HeatMap(heat_data).add_to(folium_map)

    # Adding flood data to the heatmap
    if floods:
        heat_data = [[f[0], f[1], f[2] * 10] for f in floods]  # Scaling severity
        HeatMap(heat_data).add_to(folium_map)

    # Adding tornado data to the heatmap
    if tornadoes:
        heat_data = [[t[0], t[1], t[2] * 10] for t in tornadoes]  # Scaling strength
        HeatMap(heat_data).add_to(folium_map)

    # Adding wildfire data to the heatmap
    if wildfires:
        heat_data = [[w[0], w[1], w[2] * 10] for w in wildfires]  # Scaling intensity
        HeatMap(heat_data).add_to(folium_map)

    return folium_map

# Streamlit App to display the map
def display_map():
    st.title("Natural Disaster Heatmap")
    folium_map = generate_natural_disaster_heatmap()
    st_folium(folium_map, width=700, height=500)

if __name__ == "__main__":
    display_map()
