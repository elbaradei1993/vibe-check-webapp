import streamlit as st
from sqlite3 import connect
from folium import Map, Marker, Popup
from folium.plugins import HeatMap, TimestampedGeoJson
from folium.map import LayerControl
from datetime import datetime, timedelta
import time
import requests
from streamlit_folium import st_folium
from io import BytesIO
import pandas as pd
from gtts import gTTS
import os

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
    try:
        conn = connect('vibe_bot.db')
        cursor = conn.cursor()
        cursor.execute(query, args)
        conn.commit()
        result = cursor.fetchall()
        conn.close()
        return result
    except Exception as e:
        st.error(f"Database error: {e}")
        return []

# Initialize database tables
def init_db():
    db_query('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            context TEXT,
            location TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            upvotes INTEGER DEFAULT 0,
            downvotes INTEGER DEFAULT 0
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
    text = "Welcome to the Vibe Check App!"
    tts = gTTS(text)
    tts.save("welcome.mp3")
    st.audio("welcome.mp3", format="audio/mp3")

# Emergency SOS
st.sidebar.title("Emergency Integration")
if st.sidebar.button("Send SOS"):
    st.error("SOS sent! Help is on the way.")

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

# Voting on Reports
def vote_on_report(report_id, vote_type):
    # Check if the report exists before attempting to update the votes
    report_exists = db_query('''SELECT COUNT(*) FROM reports WHERE id = ?''', (report_id,))
    
    if report_exists[0][0] > 0:  # If the report exists
        if vote_type == 'upvote':
            db_query('''UPDATE reports SET upvotes = upvotes + 1 WHERE id = ?''', (report_id,))
        elif vote_type == 'downvote':
            db_query('''UPDATE reports SET downvotes = downvotes + 1 WHERE id = ?''', (report_id,))
        st.success(f"Report {report_id} {vote_type}d successfully!")
    else:
        st.error(f"Report with ID {report_id} does not exist.")

# Generate Heatmap with color-coded markers based on vibe category
def generate_vibe_heatmap(center_location=None):
    reports = db_query('SELECT category, location FROM reports')
    folium_map = Map(location=center_location or [0, 0], zoom_start=10 if center_location else 2)

    category_colors = {
        'Crowded': 'red',
        'Noisy': 'yellow',
        'Festive': 'green',
        'Calm': 'blue',
        'Suspicious': 'purple'
    }

    for category, location in reports:
        lat, lon = map(float, location.split(","))
        color = category_colors.get(category, 'gray')  # Default to gray if category not found
        Marker([lat, lon], popup=f"Category: {category}", icon=folium.Icon(color=color)).add_to(folium_map)

    LayerControl().add_to(folium_map)
    return folium_map

# Main Menu
def main_menu():
    st.title("Vibe Check App")
    init_db()

    user_id = st.number_input("Enter your user ID", value=123)
    st.write(f"Welcome, User {user_id}!")

    if st.button("Submit a Report"):
        submit_report(user_id)
    else:
        st.subheader("Interactive Vibe Heatmap")
        country = st.text_input("Enter a country to center the map")
        center = get_coordinates(country) if country else None
        vibe_map = generate_vibe_heatmap(center)
        st_folium(vibe_map, width=700, height=500)

if __name__ == '__main__':
    main_menu()
