"""NEXARIS Streamlit Frontend - Resource Request UI
Secure interface for submitting resource requests to the NEXARIS backend
"""
import streamlit as st
import requests
import os
from datetime import datetime
import logging
from audio_recorder_streamlit import audio_recorder

logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================
BACKEND_URL = os.getenv(
    "NEXARIS_BACKEND_URL",
    "http://localhost:8000"
).rstrip("/")

API_TIMEOUT = int(os.getenv("NEXARIS_API_TIMEOUT", "30"))

# Validation constraints
CITIZEN_ID_PATTERN = r"^[a-zA-Z0-9_-]{3,64}$"
LOCATION_MAX_LENGTH = 500

# Resource types - curated list to prevent injection
ALLOWED_RESOURCES = [
    "Insulin",
    "Blood Pack",
    "Oxygen Cylinder",
    "Clean Water",
    "Medicines",
    "Vaccines",
    "First Aid Kit",
    "Food Supplies"
]

URGENCY_LEVELS = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]


def backend_url_accessible(url: str, timeout: int = 5) -> bool:
    """Check if backend health endpoint is accessible"""
    try:
        response = requests.get(f"{url}/health", timeout=timeout)
        return response.status_code == 200
    except Exception:
        return False


# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="NEXARIS Resource Request",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("🛰️ NEXARIS Resource Request Node")
st.caption("Secure Resource Orchestration Platform")

# ==================== SESSION STATE ====================
if "last_request" not in st.session_state:
    st.session_state.last_request = None

# ==================== UI COMPONENTS ====================
st.subheader("1. Acoustic Intent Capture (Sarvam AI)")
st.write("Speak your resource request naturally (e.g., 'We need 50 blood packs at the central clinic urgently').")

# The Microphone Widget
audio_bytes = audio_recorder(text="Click to Record", recording_color="#e84545", neutral_color="#666666")

if audio_bytes:
    st.audio(audio_bytes, format="audio/wav")
    
    if st.button("⚡ Process Vernacular Audio", type="primary", use_container_width=True):
        with st.spinner("Translating via Sarvam AI & Mapping to Topological Core..."):
            try:
                # Package the audio file for the backend
                files = {"file": ("recording.wav", audio_bytes, "audio/wav")}
                
                # Hit the specific Audio/Sarvam endpoint, NOT the text endpoint
                response = requests.post(
                    f"{BACKEND_URL}/api/v1/ingest/audio",
                    files=files,
                    timeout=API_TIMEOUT
                )
                
                if response.status_code == 200:
                    st.success("✅ Acoustic-to-Topological Mapping Complete!")
                    st.json(response.json())
                else:
                    st.error(f"Engine Error: {response.json().get('detail', 'Unknown Error')}")
                    
            except Exception as e:
                st.error(f"Connection Failed: {e}")

# ==================== SIDEBAR INFO ====================
with st.sidebar:
    st.subheader("ℹ️ System Info")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Backend", "Connected" if backend_url_accessible(BACKEND_URL) else "Offline")
    with col2:
        st.metric("Timestamp", datetime.utcnow().strftime("%H:%M:%S"))

    st.markdown("---")
    st.markdown(
        """
    **🛰️ About NEXARIS**

    Resource orchestration for critical supply chains.
    All requests are securely transmitted and logged.
    """
    )





if __name__ == "__main__":
    pass
