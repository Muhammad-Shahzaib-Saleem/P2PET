import streamlit as st
import requests
import time

# -------------------------
# Configuration
# -------------------------
API_URL = "http://<PI_IP>:8000/meter"  # replace <PI_IP> with your Raspberry Pi IP
REFRESH_INTERVAL = 1  # seconds

st.set_page_config(page_title="WEM3080 Energy Meter", layout="wide")

st.title("📊 WEM3080 Energy Meter Dashboard")

# Create placeholders for each measurement
placeholders = {
    "Voltage": st.empty(),
    "Current": st.empty(),
    "ActivePower": st.empty(),
    "ReactivePower": st.empty(),
    "Frequency": st.empty(),
    "ApparentPower": st.empty(),
    "PowerFactor": st.empty(),
    "ImportkWh": st.empty(),
    "ExportkWh": st.empty(),
    "ImportVARh": st.empty(),
    "ExportVARh": st.empty(),
}

st.markdown("---")

# -------------------------
# Main loop to fetch & display
# -------------------------
while True:
    try:
        response = requests.get(API_URL, timeout=2)
        if response.status_code == 200:
            data = response.json()
            
            # Update placeholders
            placeholders["Voltage"].metric("Voltage (V)", f"{data.get('Voltage', 'N/A')}")
            placeholders["Current"].metric("Current (A)", f"{data.get('Current', 'N/A')}")
            placeholders["ActivePower"].metric("Active Power (W)", f"{data.get('ActivePower', 'N/A')}")
            placeholders["ReactivePower"].metric("Reactive Power (VAR)", f"{data.get('ReactivePower', 'N/A')}")
            placeholders["Frequency"].metric("Frequency (Hz)", f"{data.get('Frequency', 'N/A')}")
            placeholders["ApparentPower"].metric("Apparent Power (VA)", f"{data.get('ApparentPower', 'N/A')}")
            placeholders["PowerFactor"].metric("Power Factor", f"{data.get('PowerFactor', 'N/A')}")
            placeholders["ImportkWh"].metric("Import kWh", f"{data.get('ImportkWh', 'N/A')}")
            placeholders["ExportkWh"].metric("Export kWh", f"{data.get('ExportkWh', 'N/A')}")
            placeholders["ImportVARh"].metric("Import VARh", f"{data.get('ImportVARh', 'N/A')}")
            placeholders["ExportVARh"].metric("Export VARh", f"{data.get('ExportVARh', 'N/A')}")
        else:
            st.error(f"API Error: {response.status_code}")
    except Exception as e:
        st.error(f"Connection Error: {e}")

    time.sleep(REFRESH_INTERVAL)
