import streamlit as st
from sqlite3 import connect
from folium import Map
from folium.plugins import HeatMap
from folium.map import LayerControl
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import time
import os

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

    if st.button("Submit"):
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

# Live Vibe Map (Heatmap)
def generate_heatmap():
    st.subheader("Generate Heatmap")
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

    LayerControl().add_to(folium_map)

    map_file = 'heatmap.html'
    folium_map.save(map_file)
    st.success(f"Heatmap saved to {map_file}")
    st.write("Open the heatmap in a new tab to view it.")

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
        st.write(f"**Report ID:** {report_id}")
        st.write(f"**Category:** {category}")
        st.write(f"**Location:** {area_name}")
        st.write("---")

# Main Menu
def main_menu():
    st.title("Vibe Check App")
    init_db()

    user_id = st.number_input("Enter your user ID", value=123)
    st.write(f"Welcome, User {user_id}!")

    menu = ["Submit a Report", "Generate Heatmap", "List Recent Reports"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Submit a Report":
        submit_report(user_id)
    elif choice == "Generate Heatmap":
        generate_heatmap()
    elif choice == "List Recent Reports":
        list_reports()

if __name__ == '__main__':
    main_menu()
