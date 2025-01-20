import streamlit as st
import requests
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

# Function to fetch earthquake data from USGS API
def fetch_earthquake_data():
    try:
        url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=100"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            earthquakes = []
            for feature in data['features']:
                magnitude = feature['properties']['mag']
                if magnitude >= 4:  # Filter for significant earthquakes
                    lat = feature['geometry']['coordinates'][1]
                    lon = feature['geometry']['coordinates'][0]
                    earthquakes.append([lat, lon, magnitude, feature['properties']['place']])
            return earthquakes
        return []
    except Exception as e:
        return []

# Function to fetch hurricane data from NOAA (mockup example)
def fetch_hurricane_data():
    try:
        # You can replace this with a real NOAA/NHC API endpoint for hurricane data
        url = "https://www.nhc.noaa.gov/gis/forecast/archive/"
        response = requests.get(url)
        if response.status_code == 200:
            hurricanes = []
            # Here, you'll need to parse the actual data returned by the API
            return hurricanes  # Mockup data
        return []
    except Exception as e:
        return []

# Function to fetch flood data from NWS API
def fetch_flood_data():
    try:
        url = "https://api.weather.gov/alerts"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            floods = []
            if data and 'features' in data:
                for feature in data['features']:
                    if 'geometry' in feature and 'coordinates' in feature['geometry']:
                        lat = feature['geometry']['coordinates'][1]
                        lon = feature['geometry']['coordinates'][0]
                        severity = feature['properties'].get('severity', 'Unknown')
                        event = feature['properties'].get('event', 'Flood')
                        description = feature['properties'].get('headline', 'No description available.')
                        floods.append([lat, lon, severity, event, description])
            return floods
        return []
    except Exception as e:
        return []

# Function to fetch wildfire data from NASA FIRMS API
def fetch_wildfire_data():
    try:
        url = "https://firms.modaps.eosdis.nasa.gov/api/"
        response = requests.get(url)
        if response.status_code == 200:
            wildfires = []
            # Parse the actual wildfire data here
            return wildfires  # Mockup data
        return []
    except Exception as e:
        return []

# Function to fetch tornado data from NWS API
def fetch_tornado_data():
    try:
        url = "https://api.weather.gov/alerts/active?area=US&eventType=tornado"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            tornadoes = []
            if data and 'features' in data:
                for feature in data['features']:
                    lat = feature['geometry']['coordinates'][1]
                    lon = feature['geometry']['coordinates'][0]
                    severity = feature['properties'].get('severity', 'Unknown')
                    event = feature['properties'].get('event', 'Tornado')
                    description = feature['properties'].get('headline', 'No description available.')
                    tornadoes.append([lat, lon, severity, event, description])
            return tornadoes
        return []
    except Exception as e:
        return []

# Function to fetch volcanic eruption data (SO2 emissions) from Smithsonian Institution
def fetch_volcanic_eruption_data():
    try:
        url = "https://volcano.si.edu/feeds/SO2.csv"
        response = requests.get(url)
        if response.status_code == 200:
            eruptions = []
            # Parse the volcanic eruption data
            return eruptions  # Mockup data
        return []
    except Exception as e:
        return []

# Function to generate a natural disaster heatmap
def generate_natural_disaster_heatmap():
    # Fetch data for all disaster types
    earthquakes = fetch_earthquake_data()
    hurricanes = fetch_hurricane_data()
    floods = fetch_flood_data()
    wildfires = fetch_wildfire_data()
    tornadoes = fetch_tornado_data()
    eruptions = fetch_volcanic_eruption_data()

    # Create a map object with OpenStreetMap as the base layer
    folium_map = folium.Map(location=[20, 0], zoom_start=2)  # Centering on the globe

    # Adding earthquake data to the map
    if earthquakes:
        for e in earthquakes:
            lat, lon, mag, location = e
            folium.Marker(
                [lat, lon],
                popup=f"Earthquake\nMagnitude: {mag}\nLocation: {location}",
            ).add_to(folium_map)
        heat_data = [[e[0], e[1], e[2] * 10] for e in earthquakes]  # Scaling magnitude
        HeatMap(heat_data).add_to(folium_map)

    # Adding hurricane data to the map
    if hurricanes:
        for h in hurricanes:
            folium.Marker(
                [h[0], h[1]],
                popup="Hurricane Details",
            ).add_to(folium_map)
        heat_data = [[h[0], h[1], 10] for h in hurricanes]  # Scaling intensity
        HeatMap(heat_data).add_to(folium_map)

    # Adding flood data to the map
    if floods:
        for f in floods:
            lat, lon, severity, event, description = f
            folium.Marker(
                [lat, lon],
                popup=f"{event}\nSeverity: {severity}\nDescription: {description}",
            ).add_to(folium_map)
        heat_data = [[f[0], f[1], 10] for f in floods]  # Floods typically don't have a magnitude
        HeatMap(heat_data).add_to(folium_map)

    # Adding wildfire data to the map
    if wildfires:
        for w in wildfires:
            folium.Marker(
                [w[0], w[1]],
                popup="Wildfire Details",
            ).add_to(folium_map)
        heat_data = [[w[0], w[1], 10] for w in wildfires]  # Scaling intensity
        HeatMap(heat_data).add_to(folium_map)

    # Adding tornado data to the map
    if tornadoes:
        for t in tornadoes:
            lat, lon, severity, event, description = t
            folium.Marker(
                [lat, lon],
                popup=f"{event}\nSeverity: {severity}\nDescription: {description}",
            ).add_to(folium_map)
        heat_data = [[t[0], t[1], 10] for t in tornadoes]  # Scaling intensity
        HeatMap(heat_data).add_to(folium_map)

    # Adding volcanic eruption data to the map
    if eruptions:
        for e in eruptions:
            folium.Marker(
                [e[0], e[1]],
                popup="Volcanic Eruption Details",
            ).add_to(folium_map)
        heat_data = [[e[0], e[1], 10] for e in eruptions]  # Scaling intensity
        HeatMap(heat_data).add_to(folium_map)

    return folium_map

# Streamlit App to display the map
def display_map():
    st.title("Natural Disaster Tracker")
    folium_map = generate_natural_disaster_heatmap()
    st_folium(folium_map, width=700, height=500)

if __name__ == "__main__":
    display_map()
