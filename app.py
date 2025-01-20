import streamlit as st
from sqlite3 import connect
from folium import Map, Marker, Popup
from folium.plugins import HeatMap
from folium.map import LayerControl
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from datetime import datetime
import time
import requests
from streamlit_folium import st_folium

# Custom CSS for styling
st.markdown(
    """
    <style>
    .stButton button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
        border: none;
        cursor: pointer;
    }
    .stButton button:hover {
        background-color: #45a049;
    }
    .card {
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);
        margin: 10px 0;
        background-color: #f9f9f9;
    }
    .card h3 {
        margin-top: 0;
    }
    .card p {
        margin-bottom: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize the geocoder
geolocator = Nominatim(user_agent="vibe_bot")

def get_coordinates(city_name):
    """Convert city name to latitude and longitude."""
    try:
        location = geolocator.geocode(city_name)
        if location:
            return location.latitude, location.longitude
        else:
            st.error(f"Could not find coordinates for {city_name}. Please check the city name.")
            return None, None
    except GeocoderTimedOut:
        st.error("Geocoding service timed out. Please try again.")
        return None, None

def get_area_name(latitude, longitude):
    """Get the area name (address) from latitude and longitude."""
    location_key = f"{latitude},{longitude}"

    # Check if the area name is already cached
    cached_area = db_query('SELECT area_name FROM area_names WHERE location = ?', (location_key,))
    if cached_area:
        return cached_area[0][0]

    try:
        # Add a delay to avoid hitting the rate limit
        time.sleep(1)  # 1 second delay between requests

        # Increase the timeout for the Nominatim API
        location = geolocator.reverse((latitude, longitude), exactly_one=True, timeout=10)
        if location:
            area_name = location.address
            # Cache the area name in the database
            db_query('''
                INSERT OR IGNORE INTO area_names (location, area_name)
                VALUES (?, ?)
            ''', (location_key, area_name))
            return area_name
        else:
            return "Unknown area"
    except GeocoderTimedOut:
        return "Unknown area (geocoding timeout)"

# Database operations
def db_query(query, args=()):
    conn = connect('vibe_bot.db')
    cursor = conn.cursor()
    cursor.execute(query, args)
    conn.commit()
    result = cursor.fetchall()
    conn.close()
    return result

# Initialize database tables
def init_db():
    db_query('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            context TEXT,
            location TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    db_query('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            reputation INTEGER DEFAULT 0
        )
    ''')
    db_query('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id INTEGER,
            category TEXT,
            UNIQUE(user_id, category)
        )
    ''')
    db_query('''
        CREATE TABLE IF NOT EXISTS votes (
            user_id INTEGER,
            report_id INTEGER,
            vote_type TEXT
        )
    ''')
    db_query('''
        CREATE TABLE IF NOT EXISTS badges (
            user_id INTEGER,
            badge_name TEXT,
            UNIQUE(user_id, badge_name)
        )
    ''')
    db_query('''
        CREATE TABLE IF NOT EXISTS area_names (
            location TEXT PRIMARY KEY,
            area_name TEXT
        )
    ''')

# Helper function to get subscribers for a category
def get_subscribers(category):
    return db_query('SELECT user_id FROM subscriptions WHERE category = ?', (category,))

# Vibe Reporting
def submit_report(user_id):
    st.subheader("Submit a Vibe Report")
    categories = ['Crowded', 'Noisy', 'Festive', 'Calm', 'Suspicious']
    category = st.selectbox("Select a category", categories)
    city_name = st.text_input("Enter the city name")
    context = st.text_area("Enter context notes")

    if st.button("Submit Report", key="submit_report"):
        if not category or not city_name or not context:
            st.error("All fields are required!")
        else:
            # Convert city name to coordinates
            latitude, longitude = get_coordinates(city_name)
            if latitude is not None and longitude is not None:
                # Save the report to the database
                db_query('''
                    INSERT INTO reports (user_id, category, context, location)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, category, context, f"{latitude},{longitude}"))

                # Award reputation points
                db_query('''
                    UPDATE users
                    SET reputation = reputation + 10
                    WHERE user_id = ?
                ''', (user_id,))

                st.success("Report submitted successfully!")

# Fetch real-time earthquake data from USGS
def fetch_earthquake_data():
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        earthquakes = []
        for feature in data['features']:
            lat = feature['geometry']['coordinates'][1]
            lon = feature['geometry']['coordinates'][0]
            magnitude = feature['properties']['mag']
            place = feature['properties']['place']
            time = datetime.fromtimestamp(feature['properties']['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            earthquakes.append((lat, lon, magnitude, place, time))
        return earthquakes
    else:
        st.error("Failed to fetch earthquake data.")
        return []

# Fetch real-time flood data from ReliefWeb API
def fetch_flood_data():
    url = "https://api.reliefweb.int/v1/disasters?appname=VibesCheck&profile=list&preset=latest&query[value]=flood"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        floods = []
        for disaster in data['data']:
            try:
                # Check if the disaster has a country and location
                if 'country' in disaster['fields'] and disaster['fields']['country']:
                    country_data = disaster['fields']['country'][0]
                    if 'location' in country_data:
                        lat = country_data['location']['lat']
                        lon = country_data['location']['lon']
                    else:
                        # Skip if location data is missing
                        continue
                else:
                    # Skip if country data is missing
                    continue

                # Extract other fields
                severity = disaster['fields'].get('status', 'Unknown')
                location = country_data.get('name', 'Unknown location')
                time = disaster['fields']['date'].get('created', 'Unknown time')

                floods.append((lat, lon, severity, location, time))
            except KeyError as e:
                # Log the error and skip this disaster entry
                st.warning(f"Skipping a disaster entry due to missing data: {e}")
                continue
        return floods
    else:
        st.error("Failed to fetch flood data.")
        return []

# Fetch real-time wildfire data from NASA FIRMS
def fetch_wildfire_data():
    url = "https://firms.modaps.eosdis.nasa.gov/api/country/csv/VIIRS_SNPP_NRT/USA/1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.text.splitlines()
        wildfires = []
        for line in data[1:]:  # Skip header
            fields = line.split(',')
            try:
                lat = float(fields[0])
                lon = float(fields[1])
                brightness = float(fields[2])
                time = fields[5]
                wildfires.append((lat, lon, brightness, time))
            except (IndexError, ValueError) as e:
                # Log the error and skip this entry
                st.warning(f"Skipping a wildfire entry due to invalid data: {e}")
                continue
        return wildfires
    else:
        st.error("Failed to fetch wildfire data.")
        return []

# Fetch real-time hurricane data from NOAA
def fetch_hurricane_data():
    url = "https://www.nhc.noaa.gov/gtwo.xml"
    response = requests.get(url)
    if response.status_code == 200:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)
        hurricanes = []
        for storm in root.findall('.//storm'):
            name = storm.find('name').text
            lat = float(storm.find('latitude').text)
            lon = float(storm.find('longitude').text)
            wind_speed = int(storm.find('windSpeed').text)
            hurricanes.append((lat, lon, name, wind_speed))
        return hurricanes
    else:
        st.error("Failed to fetch hurricane data.")
        return []

# Fetch real-time volcanic eruption data from Smithsonian
def fetch_volcano_data():
    url = "https://volcano.si.edu/feeds/volcanoes.json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        volcanoes = []
        for volcano in data:
            lat = volcano['latitude']
            lon = volcano['longitude']
            name = volcano['name']
            status = volcano['status']
            volcanoes.append((lat, lon, name, status))
        return volcanoes
    else:
        st.error("Failed to fetch volcano data.")
        return []

# Generate Heatmap
def generate_heatmap(show_disasters=False):
    reports = db_query('SELECT category, location FROM reports')
    
    color_mapping = {
        'Crowded': 'red',
        'Noisy': 'blue',
        'Festive': 'green',
        'Calm': 'purple',
        'Suspicious': 'orange'
    }

    folium_map = Map(location=[0, 0], zoom_start=2)

    for category, color in color_mapping.items():
        category_reports = [report for report in reports if report[0] == category]
        heatmap_data = []
        for report in category_reports:
            _, location = report
            latitude, longitude = map(float, location.split(','))
            heatmap_data.append([latitude, longitude])
        
        if heatmap_data:
            HeatMap(
                heatmap_data,
                name=category,
                gradient={'0.4': color},
                radius=15,
                blur=10,
                max_zoom=1,
            ).add_to(folium_map)

    # Add natural disaster data if enabled
    if show_disasters:
        # Fetch and display earthquake data
        earthquakes = fetch_earthquake_data()
        for lat, lon, magnitude, place, time in earthquakes:
            popup = Popup(
                f"<b>Earthquake</b><br>"
                f"Magnitude: {magnitude}<br>"
                f"Location: {place}<br>"
                f"Time: {time}",
                max_width=300,
            )
            Marker(
                location=[lat, lon],
                popup=popup,
                icon=None,  # Use default icon
            ).add_to(folium_map)

        # Fetch and display flood data
        floods = fetch_flood_data()
        if floods:  # Only add flood markers if data is available
            for lat, lon, severity, location, time in floods:
                popup = Popup(
                    f"<b>Flood</b><br>"
                    f"Severity: {severity}<br>"
                    f"Location: {location}<br>"
                    f"Time: {time}",
                    max_width=300,
                )
                Marker(
                    location=[lat, lon],
                    popup=popup,
                    icon=None,  # Use default icon or a custom flood icon
                ).add_to(folium_map)
        else:
            st.warning("No flood data available to display.")

        # Fetch and display wildfire data
        wildfires = fetch_wildfire_data()
        if wildfires:
            for lat, lon, brightness, time in wildfires:
                popup = Popup(
                    f"<b>Wildfire</b><br>"
                    f"Brightness: {brightness}<br>"
                    f"Time: {time}",
                    max_width=300,
                )
                Marker(
                    location=[lat, lon],
                    popup=popup,
                    icon=None,  # Use default icon or a custom wildfire icon
                ).add_to(folium_map)
        else:
            st.warning("No wildfire data available to display.")

        # Fetch and display hurricane data
        hurricanes = fetch_hurricane_data()
        if hurricanes:
            for lat, lon, name, wind_speed in hurricanes:
                popup = Popup(
                    f"<b>Hurricane</b><br>"
                    f"Name: {name}<br>"
                    f"Wind Speed: {wind_speed} mph",
                    max_width=300,
                )
                Marker(
                    location=[lat, lon],
                    popup=popup,
                    icon=None,  # Use default icon or a custom hurricane icon
                ).add_to(folium_map)
        else:
            st.warning("No hurricane data available to display.")

        # Fetch and display volcano data
        volcanoes = fetch_volcano_data()
        if volcanoes:
            for lat, lon, name, status in volcanoes:
                popup = Popup(
                    f"<b>Volcano</b><br>"
                    f"Name: {name}<br>"
                    f"Status: {status}",
                    max_width=300,
                )
                Marker(
                    location=[lat, lon],
                    popup=popup,
                    icon=None,  # Use default icon or a custom volcano icon
                ).add_to(folium_map)
        else:
            st.warning("No volcano data available to display.")

    LayerControl().add_to(folium_map)
    return folium_map

# List Reports
def list_reports():
    st.subheader("Recent Reports")
    reports = db_query('SELECT id, category, location FROM reports')
    if not reports:
        st.info("No reports found.")
        return

    for report in reports:
        report_id, category, location = report
        latitude, longitude = location.split(',')
        area_name = get_area_name(latitude, longitude)
        
        # Display report as a card
        st.markdown(
            f"""
            <div class="card">
                <h3>Report ID: {report_id}</h3>
                <p><strong>Category:</strong> {category}</p>
                <p><strong>Location:</strong> {area_name}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# Main Menu
def main_menu():
    st.title("Vibe Check App")
    init_db()

    user_id = st.number_input("Enter your user ID", value=123)
    st.write(f"Welcome, User {user_id}!")

    # Create columns for buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Submit a Report", key="submit_report_button"):
            st.session_state.page = "submit_report"
    with col2:
        if st.button("Generate Heatmap", key="generate_heatmap_button"):
            st.session_state.page = "generate_heatmap"
    with col3:
        if st.button("List Recent Reports", key="list_reports_button"):
            st.session_state.page = "list_reports"

    # Display the selected page
    if "page" not in st.session_state:
        st.session_state.page = "home"

    if st.session_state.page == "submit_report":
        submit_report(user_id)
    elif st.session_state.page == "generate_heatmap":
        show_disasters = st.checkbox("Show Natural Disasters", key="show_disasters")
        folium_map = generate_heatmap(show_disasters=show_disasters)
        st_folium(folium_map, width=700, height=500)
    elif st.session_state.page == "list_reports":
        list_reports()
    else:
        # Home Page with Heatmap and Search Bar
        st.subheader("Interactive Heatmap")
        show_disasters = st.checkbox("Show Natural Disasters", key="show_disasters_home")
        folium_map = generate_heatmap(show_disasters=show_disasters)
        st_folium(folium_map, width=700, height=500)

        # Search Bar
        st.subheader("Search for a Location")
        search_query = st.text_input("Enter a city or country")
        if search_query:
            latitude, longitude = get_coordinates(search_query)
            if latitude is not None and longitude is not None:
                folium_map = Map(location=[latitude, longitude], zoom_start=10)
                HeatMap([[latitude, longitude]]).add_to(folium_map)
                st_folium(folium_map, width=700, height=500)

if __name__ == '__main__':
    main_menu()
