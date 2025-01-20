import streamlit as st
import pandas as pd
import json
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from folium.plugins import TimestampedGeoJson
from datetime import datetime
from io import BytesIO
import pyttsx3

# Social Integration
st.sidebar.title("Share on Social Media")
if st.sidebar.button("Share this App"):
    st.sidebar.info("Link copied! Share it with your friends.")

# AI-Powered Insights
def sentiment_analysis(report_context):
    # Simple sentiment analysis example (dummy function)
    if "happy" in report_context.lower():
        return "Positive"
    elif "danger" in report_context.lower():
        return "Negative"
    return "Neutral"

# Offline Mode
st.sidebar.title("Offline Mode")
offline_data = BytesIO()
if st.sidebar.button("Download Offline Data"):
    with pd.ExcelWriter(offline_data) as writer:
        reports = db_query('SELECT * FROM reports')
        pd.DataFrame(reports).to_excel(writer, index=False)
    st.sidebar.download_button(
        label="Download Data", data=offline_data.getvalue(), file_name="offline_vibe_data.xlsx"
    )

# Accessibility Features
st.sidebar.title("Accessibility Options")
high_contrast = st.sidebar.checkbox("Enable High Contrast")
text_to_speech = st.sidebar.checkbox("Enable Text-to-Speech")

def read_text_aloud(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

if text_to_speech:
    read_text_aloud("Welcome to the Vibe App!")

# Emergency Integration
def send_sos():
    st.error("SOS Sent! Help is on the way.")
st.sidebar.button("Send SOS", on_click=send_sos)

# Neighborhood History Archive
def generate_timeline():
    reports = db_query('SELECT category, location, timestamp FROM reports')
    features = []
    for report in reports:
        lat, lon = map(float, report[1].split(","))
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat],
            },
            "properties": {
                "time": report[2],
                "popup": report[0],
            },
        })
    return TimestampedGeoJson({"type": "FeatureCollection", "features": features})

# Feedback and Support
st.sidebar.title("Feedback and Support")
feedback = st.sidebar.text_area("Leave Feedback")
if st.sidebar.button("Submit Feedback"):
    st.success("Thank you for your feedback!")

# Privacy Settings
st.sidebar.title("Privacy Settings")
data_sharing = st.sidebar.radio("Share My Data:", ["Yes", "No"])

# Append Historical Data Timeline to Map
if st.sidebar.checkbox("Show Historical Data"):
    timeline = generate_timeline()
    timeline.add_to(folium_map)
    st_folium(folium_map, width=700, height=500)
