import streamlit as st
from sqlite3 import connect
from folium import Map, Marker, Popup
from folium.plugins import HeatMap
from folium.map import LayerControl
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

# OpenCage Geocoding API Key
OPENCAGE_API_KEY = "df263d30e41d4d2aa961b5005de6c5be"  # Your OpenCage API key

# Hardcoded list of countries
def get_countries():
    return [
        "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", 
        "Antigua and Barbuda", "Argentina", "Armenia", "Australia", 
        "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", 
        "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", 
        "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", 
        "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Côte d'Ivoire", 
        "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", 
        "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", 
        "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czechia", "Denmark", 
        "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", 
        "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", 
        "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", 
        "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", 
        "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hungary", "Iceland", 
        "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", 
        "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", 
        "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", 
        "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", 
        "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", 
        "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", 
        "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", 
        "Myanmar (formerly Burma)", "Namibia", "Nauru", "Nepal", "Netherlands", 
        "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", 
        "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", 
        "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", 
        "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", 
        "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", 
        "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", 
        "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", 
        "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", 
        "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", 
        "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", 
        "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", 
        "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", 
        "United Arab Emirates", "United Kingdom", "United States of America", 
        "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", 
        "Zambia", "Zimbabwe"
    ]

# Convert city name to latitude and longitude using OpenCage Geocoding API
def get_coordinates(city_name):
    try:
        # Add a delay to avoid hitting the rate limit
        time.sleep(1)  # 1 second delay between requests
        url = f"https://api.opencagedata.com/geocode/v1/json?q={city_name}&key={OPENCAGE_API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                latitude = data['results'][0]['geometry']['lat']
                longitude = data['results'][0]['geometry']['lng']
                return latitude, longitude
            else:
                st.warning(f"No results found for {city_name}.")
                return None, None
        else:
            st.error(f"Geocoding service unavailable. Please try again later. Error: {response.status_code}")
            return None, None
    except Exception as e:
        st.error(f"Geocoding service unavailable. Please try again later. Error: {e}")
        return None, None

# Get the area name (address) from latitude and longitude using OpenCage Geocoding API
def get_area_name(latitude, longitude):
    location_key = f"{latitude},{longitude}"
    cached_area = db_query('SELECT area_name FROM area_names WHERE location = ?', (location_key,))
    if cached_area:
        return cached_area[0][0]

    try:
        time.sleep(1)  # Delay to avoid rate limits
        url = f"https://api.opencagedata.com/geocode/v1/json?q={latitude}+{longitude}&key={OPENCAGE_API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                area_name = data['results'][0]['formatted']
                db_query('''
                    INSERT OR IGNORE INTO area_names (location, area_name)
                    VALUES (?, ?)
                ''', (location_key, area_name))
                return area_name
            else:
                return "Unknown area"
        else:
            return "Unknown area (geocoding error)"
    except Exception as e:
        return f"Unknown area (geocoding error: {e})"

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
    reports = db_query('SELECT category, location, context FROM reports')
    
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
            _, location, context = report
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
            # Add a marker for the searched location
            Marker(
                location=[latitude, longitude],
                popup=f"<b>Searched Location:</b> {search_query}",
                icon=None,
            ).add_to(folium_map)

            # Check if there are any vibes reports for the searched location
            reports_in_area = db_query('SELECT category, context FROM reports WHERE location = ?', (f"{latitude},{longitude}",))
            if reports_in_area:
                for report in reports_in_area:
                    category, context = report
                    Marker(
                        location=[latitude, longitude],
                        popup=f"<b>Report:</b> {category}<br><b>Context:</b> {context}",
                        icon=None,
                    ).add_to(folium_map)
            else:
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

# Main Menu
def main_menu():
    st.title("Vibe Check App")
    init_db()

    user_id = st.number_input("Enter your user ID", value=123)
    st.write(f"Welcome, User {user_id}!")

    # Create a column for the submit report button
    if st.button("Submit a Report", key="submit_report_button"):
        st.session_state.page = "submit_report"

    # Display the selected page
    if "page" not in st.session_state:
        st.session_state.page = "home"

    if st.session_state.page == "submit_report":
        submit_report(user_id)
    else:
        # Home Page with Heatmap, Search Bar, and Recent Reports
        st.subheader("Interactive Heatmap")
        show_disasters = st.checkbox("Show Natural Disasters", key="show_disasters_home")
        selected_country = st.selectbox("Select a country", get_countries(), key="country_select")
        search_query = st.text_input("Search for a city or country")

        # Generate heatmap based on selected country or search query
        if selected_country or search_query:
            if selected_country:
                latitude, longitude = get_coordinates(selected_country)
            else:
                latitude, longitude = get_coordinates(search_query)
            
            if latitude is not None and longitude is not None:
                folium_map = generate_heatmap(center_location=[latitude, longitude], show_disasters=show_disasters, search_query=search_query)
                st_folium(folium_map, width=700, height=500)
        else:
            folium_map = generate_heatmap(show_disasters=show_disasters)
            st_folium(folium_map, width=700, height=500)

if __name__ == '__main__':
    main_menu()
