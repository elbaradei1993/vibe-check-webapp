import streamlit as st
import requests
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from sqlite3 import connect
from datetime import datetime

# Initialize database tables (if not already present)
def init_db():
    db_query('''CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category TEXT,
        context TEXT,
        location TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        upvotes INTEGER DEFAULT 0,
        downvotes INTEGER DEFAULT 0
    )''')
    db_query('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        reputation INTEGER DEFAULT 0
    )''')

def db_query(query, args=()):
    conn = connect('vibe_bot.db')
    cursor = conn.cursor()
    cursor.execute(query, args)
    conn.commit()
    result = cursor.fetchall()
    conn.close()
    return result

# Function to submit a vibe report
def submit_report(user_id):
    st.subheader("Submit a Vibe Report")
    categories = ['Crowded', 'Noisy', 'Festive', 'Calm', 'Suspicious']
    category = st.selectbox("Select a category", categories)
    city_name = st.text_input("Enter the city name")
    context = st.text_area("Enter context notes")
    if st.button("Submit Report"):
        lat, lon = get_coordinates(city_name)
        if lat and lon:
            db_query('''INSERT INTO reports (user_id, category, context, location) VALUES (?, ?, ?, ?)''', 
                     (user_id, category, context, f"{lat},{lon}"))
            st.success("Report submitted successfully!")

# Function to fetch coordinates using OpenCage API
def get_coordinates(city_name):
    try:
        # OpenCage API Key
        api_key = 'df263d30e41d4d2aa961b5005de6c5be'
        url = f"https://api.opencagedata.com/geocode/v1/json?q={city_name}&key={api_key}"
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

# Function to generate a live vibe map with filters
def generate_vibe_map(vibe_category=None, time_frame=None):
    reports = db_query('''SELECT category, location, timestamp FROM reports WHERE 1''')
    
    if vibe_category:
        reports = [r for r in reports if r[0] == vibe_category]
    
    if time_frame:
        if time_frame == "24 hours":
            time_limit = datetime.now() - timedelta(days=1)
            reports = [r for r in reports if datetime.strptime(r[2], '%Y-%m-%d %H:%M:%S') > time_limit]

    folium_map = folium.Map(location=[0, 0], zoom_start=2)
    for category, location, timestamp in reports:
        lat, lon = map(float, location.split(","))
        color = get_vibe_color(category)
        folium.Marker([lat, lon], popup=f"Category: {category} | Time: {timestamp}", icon=folium.Icon(color=color)).add_to(folium_map)

    return folium_map

def get_vibe_color(category):
    colors = {
        'Crowded': 'red',
        'Noisy': 'blue',
        'Festive': 'green',
        'Calm': 'purple',
        'Suspicious': 'orange'
    }
    return colors.get(category, 'gray')

# Function to handle voting on reports
def vote_on_report(report_id, vote_type):
    if vote_type == 'upvote':
        db_query('''UPDATE reports SET upvotes = upvotes + 1 WHERE id = ?''', (report_id,))
    elif vote_type == 'downvote':
        db_query('''UPDATE reports SET downvotes = downvotes + 1 WHERE id = ?''', (report_id,))

# Function to handle gamification (reputation)
def update_reputation(user_id):
    user_reports = db_query('''SELECT COUNT(*) FROM reports WHERE user_id = ?''', (user_id,))
    reputation = user_reports[0][0]  # Assign reputation based on number of reports
    db_query('''UPDATE users SET reputation = ? WHERE user_id = ?''', (reputation, user_id))

# Displaying features on Streamlit
def display_vibe_features():
    st.title("Vibe Check App")
    
    user_id = st.number_input("Enter your user ID", value=123)
    
    st.sidebar.subheader("Submit a Vibe Report")
    if st.sidebar.button("Submit Report"):
        submit_report(user_id)

    vibe_category = st.sidebar.selectbox("Filter by Vibe Type", ["All", "Crowded", "Noisy", "Festive", "Calm", "Suspicious"])
    time_frame = st.sidebar.selectbox("Filter by Time Frame", ["All", "24 hours", "This Week"])
    
    st.subheader("Live Vibe Map")
    vibe_map = generate_vibe_map(vibe_category if vibe_category != "All" else None, time_frame if time_frame != "All" else None)
    st_folium(vibe_map, width=700, height=500)

    st.sidebar.subheader("Gamification")
    st.sidebar.write(f"Your Reputation: {get_user_reputation(user_id)}")
    if st.sidebar.button("Upvote Report"):
        vote_on_report(1, 'upvote')
    elif st.sidebar.button("Downvote Report"):
        vote_on_report(1, 'downvote')

# Function to get user's reputation
def get_user_reputation(user_id):
    reputation = db_query('''SELECT reputation FROM users WHERE user_id = ?''', (user_id,))
    return reputation[0][0] if reputation else 0

if __name__ == "__main__":
    init_db()
    display_vibe_features()
