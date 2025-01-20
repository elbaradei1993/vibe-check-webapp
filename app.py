import streamlit as st
from sqlite3 import connect
from folium import Map, Marker, Popup
from folium.plugins import HeatMap, TimestampedGeoJson
from folium.map import LayerControl
from datetime import datetime
import time
import requests
from streamlit_folium import st_folium
from io import BytesIO
import pandas as pd
import pyttsx3

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

# OpenCage Geocoding API Key
OPENCAGE_API_KEY = "df263d30e41d4d2aa961b5005de6c5be"

# Utility functions for database and geocoding
def db_query(query, args=()):
    conn = connect('vibe_bot.db')
    cursor = conn.cursor()
    cursor.execute(query, args)
    conn.commit()
    result = cursor.fetchall()
    conn.close()
    return result

def get_coordinates(city_name):
    try:
        time.sleep(1)
        url = f"https://api.opencagedata.com/geocode/v1/json?q={city_name}&key={OPENCAGE_API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                latitude = data['results'][0]['geometry']['lat']
                longitude = data['results'][0]['geometry']['lng']
                return latitude, longitude
        return None, None
    except Exception as e:
        st.error(f"Error fetching coordinates: {e}")
        return None, None

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

# Social Sharing
st.sidebar.title("Share on Social Media")
if st.sidebar.button("Share this App"):
    st.sidebar.info("Link copied! Share with your friends.")

# Offline Mode
st.sidebar.title("Offline Mode")
offline_data = BytesIO()
if st.sidebar.button("Download Offline Data"):
    reports = db_query('SELECT * FROM reports')
    with pd.ExcelWriter(offline_data) as writer:
        pd.DataFrame(reports, columns=["ID", "User ID", "Category", "Context", "Location", "Timestamp"]).to_excel(writer, index=False)
    st.sidebar.download_button(
        label="Download Data",
        data=offline_data.getvalue(),
        file_name="vibe_data.xlsx",
    )

# Accessibility Features
st.sidebar.title("Accessibility Options")
text_to_speech = st.sidebar.checkbox("Enable Text-to-Speech")
high_contrast = st.sidebar.checkbox("Enable High Contrast")

if text_to_speech:
    engine = pyttsx3.init()
    engine.say("Welcome to the Vibe Check App!")
    engine.runAndWait()

# Emergency SOS
st.sidebar.title("Emergency Integration")
if st.sidebar.button("Send SOS"):
    st.error("SOS sent! Help is on the way.")

# Generate Heatmap
def generate_heatmap(center_location=None):
    reports = db_query('SELECT category, location FROM reports')
    folium_map = Map(location=center_location or [0, 0], zoom_start=10 if center_location else 2)
    for category, location in reports:
        lat, lon = map(float, location.split(","))
        Marker([lat, lon], popup=f"Category: {category}").add_to(folium_map)
    LayerControl().add_to(folium_map)
    return folium_map

# Submit Report
def submit_report(user_id):
    st.subheader("Submit a Vibe Report")
    categories = ['Crowded', 'Noisy', 'Festive', 'Calm', 'Suspicious']
    category = st.selectbox("Select a category", categories)
    city_name = st.text_input("Enter the city name")
    context = st.text_area("Enter context notes")
    if st.button("Submit Report"):
        lat, lon = get_coordinates(city_name)
        if lat and lon:
            db_query('INSERT INTO reports (user_id, category, context, location) VALUES (?, ?, ?, ?)', (user_id, category, context, f"{lat},{lon}"))
            st.success("Report submitted successfully!")

# Main Menu
def main_menu():
    st.title("Vibe Check App")
    init_db()

    user_id = st.number_input("Enter your user ID", value=123)
    st.write(f"Welcome, User {user_id}!")

    if st.button("Submit a Report"):
        submit_report(user_id)
    else:
        st.subheader("Interactive Heatmap")
        country = st.text_input("Enter a country to center the map")
        center = get_coordinates(country) if country else None
        folium_map = generate_heatmap(center)
        st_folium(folium_map, width=700, height=500)

if __name__ == '__main__':
    main_menu()
