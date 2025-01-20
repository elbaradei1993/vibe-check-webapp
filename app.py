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
import pycountry

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

# Get a list of world countries
def get_countries():
    return [country.name for country in pycountry.countries]

# Convert city name to latitude and longitude
def get_coordinates(city_name):
    try:
        location = geolocator.geocode(city_name)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except GeocoderTimedOut:
        return None, None

# Get the area name (address) from latitude and longitude
def get_area_name(latitude, longitude):
    location_key = f"{latitude},{longitude}"
    cached_area = db_query('SELECT area_name FROM area_names WHERE location = ?', (location_key,))
    if cached_area:
        return cached_area[0][0]

    try:
        time.sleep(1)  # Delay to avoid rate limits
        location = geolocator.reverse((latitude, longitude), exactly_one=True, timeout=10)
        if location:
            area_name = location.address
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
        CREATE TABLE IF NOT EXISTS area_names (
            location TEXT PRIMARY KEY,
            area_name TEXT
        )
    ''')

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
        return []

# Generate Heatmap
def generate_heatmap(center_location=None, show_disasters=False, search_query=None):
    reports = db_query('SELECT category, location FROM reports')
    
    color_mapping = {
        'Crowded': 'red',
        'Noisy': 'blue',
        'Festive': 'green',
        'Calm': 'purple',
        'Suspicious': 'orange'
    }

    # Initialize the map
    if center_location:
        folium_map = Map(location=center_location, zoom_start=10)
    else:
        folium_map = Map(location=[0, 0], zoom_start=2)

    # Add vibes reports to the heatmap
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
                icon=None,
            ).add_to(folium_map)

    # Add search query marker if provided
    if search_query:
        latitude, longitude = get_coordinates(search_query)
        if latitude is not None and longitude is not None:
            Marker(
                location=[latitude, longitude],
                popup=f"<b>Searched Location:</b> {search_query}",
                icon=None,
            ).add_to(folium_map)

            # Check if there are any vibes reports for the searched location
            reports_in_area = db_query('SELECT category, context FROM reports WHERE location = ?', (f"{latitude},{longitude}",))
            if not reports_in_area:
                st.warning(f"No vibes reports have been submitted for {search_query} yet.")

    LayerControl().add_to(folium_map)
    return folium_map

# Submit Report
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
            latitude, longitude = get_coordinates(city_name)
            if latitude is not None and longitude is not None:
                db_query('''
                    INSERT INTO reports (user_id, category, context, location)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, category, context, f"{latitude},{longitude}"))
                st.success("Report submitted successfully!")

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
        selected_country = st.selectbox("Select a country", get_countries(), key="country_select")
        if selected_country:
            latitude, longitude = get_coordinates(selected_country)
            if latitude is not None and longitude is not None:
                folium_map = generate_heatmap(center_location=[latitude, longitude], show_disasters=show_disasters)
                st_folium(folium_map, width=700, height=500)
    elif st.session_state.page == "list_reports":
        list_reports()
    else:
        # Home Page with Heatmap and Search Bar
        st.subheader("Interactive Heatmap")
        show_disasters = st.checkbox("Show Natural Disasters", key="show_disasters_home")
        search_query = st.text_input("Search for a city or country")
        if search_query:
            folium_map = generate_heatmap(show_disasters=show_disasters, search_query=search_query)
            st_folium(folium_map, width=700, height=500)
        else:
            folium_map = generate_heatmap(show_disasters=show_disasters)
            st_folium(folium_map, width=700, height=500)

    # Back button
    if st.session_state.page != "home":
        if st.button("Back to Home"):
            st.session_state.page = "home"

if __name__ == '__main__':
    main_menu()
