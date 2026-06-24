"""NEXARIS Streamlit Frontend - Resource Request UI
Secure interface for submitting resource requests to the NEXARIS backend
"""
import streamlit as st
import requests
import os
from datetime import datetime
import logging

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
st.subheader("1. Submit Resource Request")

# Input fields
citizen_id = st.text_input(
    "Citizen Identifier",
    placeholder="e.g., citizen_mumbai_001",
    help="Alphanumeric identifier for request tracking"
).strip()

col1, col2 = st.columns(2)
with col1:
    item = st.selectbox(
        "Resource Type",
        ALLOWED_RESOURCES,
        help="Select the required resource from the curated list"
    )
with col2:
    urgency = st.selectbox(
        "Urgency Level",
        URGENCY_LEVELS,
        help="Set the priority of this request"
    )

location_context = st.text_area(
    "Location Details",
    placeholder="e.g., 'Community health clinic near North Highway'",
    max_chars=LOCATION_MAX_LENGTH,
    height=80,
    help="Describe the location where the resource is needed"
).strip()

st.markdown("---")

# ==================== VALIDATION & SUBMISSION ====================
if st.button("📤 Submit Request", use_container_width=True, type="primary"):
    # Input validation
    errors = []

    if not citizen_id:
        errors.append("Citizen Identifier is required")
    elif len(citizen_id) < 3 or len(citizen_id) > 64:
        errors.append("Citizen ID must be 3-64 characters")
    elif not all(c.isalnum() or c in "_-" for c in citizen_id):
        errors.append("Citizen ID can only contain letters, numbers, underscores, and hyphens")

    if not location_context:
        errors.append("Location details are required")
    elif len(location_context) > LOCATION_MAX_LENGTH:
        errors.append(f"Location must be under {LOCATION_MAX_LENGTH} characters")

    if errors:
        st.error("❌ Please fix the following errors:")
        for error in errors:
            st.write(f"  • {error}")
    else:
        # Prepare secure payload
        payload = {
            "citizen_id": citizen_id,
            "intent": "RESOURCE_REQUEST",
            "item": item,
            "urgency": urgency,
            "location_context": location_context
        }

        with st.spinner("📡 Submitting request to NEXARIS backend..."):
            try:
                # Call backend API
                response = requests.post(
                    f"{BACKEND_URL}/api/v1/ingest",
                    json=payload,
                    timeout=API_TIMEOUT
                )

                if response.status_code == 200:
                    st.success("✅ Request successfully submitted to the network!")
                    st.json(response.json())
                    st.session_state.last_request = payload

                elif response.status_code == 400:
                    st.error(f"❌ Invalid request: {response.json().get('detail', 'Please check your input')}")

                elif response.status_code == 503:
                    st.error("❌ Backend service temporarily unavailable. Please try again later.")

                else:
                    st.error(f"❌ Error: {response.status_code} - {response.json().get('message', 'Unknown error')}")

            except requests.Timeout:
                st.error("❌ Request timed out. Backend is not responding. Please check your connection.")
            except requests.ConnectionError:
                st.error(f"❌ Could not connect to backend at {BACKEND_URL}. Please verify the server is running.")
            except Exception as e:
                logger.error(f"Request submission error: {e}")
                st.error(f"❌ An error occurred: {str(e)[:100]}")

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


def backend_url_accessible(url: str, timeout: int = 5) -> bool:
    """Check if backend health endpoint is accessible"""
    try:
        response = requests.get(
            f"{url}/health",
            timeout=timeout
        )
        return response.status_code == 200
    except Exception:
        return False


if __name__ == "__main__":
    pass
