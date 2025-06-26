import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
import pandas as pd
from datetime import datetime

# --- LOGIN SECTION ---
USERNAME = "Balaji"
PASSWORD = "Balaji1809"

def login():
    st.title("🔐 Login Required")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_btn = st.button("Login")
    if login_btn:
        if username == USERNAME and password == PASSWORD:
            st.session_state["authenticated"] = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid username or password")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login()
    st.stop()

# --- DASHBOARD SECTION ---

# Blynk setup
BLYNK_AUTH = "3_MjP7lytpKxKJez9XJHYfuAJgka0Rpw"  # Your Blynk Auth token
PHASE_PIN = "v0"
ACCURACY_PIN = "v1"

# Function to fetch data from Blynk
def fetch_blynk_data():
    url = f"https://blynk.cloud/external/api/get?token={BLYNK_AUTH}&{PHASE_PIN}&{ACCURACY_PIN}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return {PHASE_PIN: "N/A", ACCURACY_PIN: 0}
    except Exception as e:
        return {PHASE_PIN: "Error", ACCURACY_PIN: 0}

st.set_page_config(page_title="Therapy", layout="centered")
st.title("🧤Therapy")

if st.button("Logout"):
    st.session_state["authenticated"] = False
    st.rerun()

# --- Flicker-free auto-refresh ---
st_autorefresh(interval=2000, limit=None, key="dashboardrefresh")  # 2000ms = 2 seconds

# Data buffer for time series
if "data_log" not in st.session_state:
    st.session_state["data_log"] = pd.DataFrame(columns=["Time", "Accuracy"])

# Fetch latest data
blynk_data = fetch_blynk_data()
phase = blynk_data.get(PHASE_PIN, "Unknown")
try:
    accuracy = float(blynk_data.get(ACCURACY_PIN, 0))
except:
    accuracy = 0

now = datetime.now().strftime("%H:%M:%S")
new_row = pd.DataFrame([[now, accuracy]], columns=["Time", "Accuracy"])
st.session_state["data_log"] = pd.concat([st.session_state["data_log"], new_row], ignore_index=True)

# Limit to last 50 entries
if len(st.session_state["data_log"]) > 50:
    st.session_state["data_log"] = st.session_state["data_log"].iloc[-50:]

# --- UI ---
phase_placeholder = st.empty()
accuracy_placeholder = st.empty()
chart_placeholder = st.empty()

phase_placeholder.subheader(f"📌 Current Phase: `{phase}`")
accuracy_placeholder.metric("🎯 Accuracy (%)", f"{accuracy:.2f}")
chart_placeholder.line_chart(st.session_state["data_log"].set_index("Time"))
