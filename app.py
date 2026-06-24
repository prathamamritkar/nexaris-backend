import streamlit as st
import requests

st.set_page_config(page_title="NEXARIS Kinetic Web Node", layout="centered")

st.title("🛰️ NEXARIS Kinetic Sensory Node")
st.caption("Vernacular-to-Topological Edge Interface")

# Input simulation container
st.subheader("1. Simulate Vernacular Input")
voice_transcript = st.text_area(
    "Spoken Intent Transcript (Simulating Sarvam AI V2V translation)",
    placeholder="e.g., 'We need urgent blood supplies at the community health clinic near the north highway cross.'"
)

# Meta-data extraction simulation
col1, col2 = st.columns(2)
with col1:
    item = st.selectbox("Extracted Resource Entity", ["Insulin", "Blood Pack", "Oxygen Cylinder", "Clean Water"])
with col2:
    urgency = st.selectbox("Computed Criticality Level", ["CRITICAL", "HIGH", "MEDIUM", "LOW"])

location_context = st.text_input("Geographic Context", "North Highway Intersection, Zone 4")
citizen_id = st.text_input("Citizen Identifier", "citizen_pune_404")

st.markdown("---")

# Execution trigger
if st.button("⚡ Execute Acoustic-to-Topological Mapping", use_container_width=True):
    # Construct the strict enterprise payload
    payload = {
        "citizen_id": citizen_id,
        "intent": "RESOURCE_REQUEST",
        "item": item,
        "urgency": urgency,
        "location_context": location_context
    }

    st.info("Dispatching payload to FastAPI Backend Engine...")

    try:
        # Connect to local or live backend depending on your setup
        # Once deployed to Render, change this URL to your Render web service URL
        backend_url = "http://127.0.0.1:8000/api/v1/ingest"
        response = requests.post(backend_url, json=payload)

        if response.status_code == 200:
            st.success("🎉 Success! Node relationship injected into the Topological Core (Neo4j). Check your Base44 Dashboard.")
            st.json(response.json())
        else:
            st.error(f"Engine rejected payload: {response.text}")
    except Exception as e:
        st.error(f"Could not connect to backend engine: {e}")
