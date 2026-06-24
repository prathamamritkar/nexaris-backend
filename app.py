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

# Translation dictionary based on browser language
TRANSLATIONS = {
    'hi': {
        'title': 'NEXARIS | नेक्सारिस',
        'subtitle': 'Secure Voice Resource Node',
        'instructions': "Tap and speak your request | अपना अनुरोध बोलें",
        'button': "⚡ Process | ⚡ संसाधित करें",
        'success': "✅ Sent | ✅ प्रेषित",
        'error': "❌ Error | ❌ त्रुटि"
    },
    'mr': {
        'title': 'NEXARIS | नेक्सारिस',
        'subtitle': 'Secure Voice Resource Node',
        'instructions': "Tap and speak your request | तुमची विनंती सांगा",
        'button': "⚡ Process | ⚡ प्रक्रिया करा",
        'success': "✅ Sent | ✅ पाठवले",
        'error': "❌ Error | ❌ त्रुटी"
    },
    'gu': {
        'title': 'NEXARIS | નેક્સારિસ',
        'subtitle': 'Secure Voice Resource Node',
        'instructions': "Tap and speak your request | તમારી વિનંતી બોલો",
        'button': "⚡ Process | ⚡ પ્રક્રિયા કરો",
        'success': "✅ Sent | ✅ મોકલાયું",
        'error': "❌ Error | ❌ ભૂલ"
    },
    'kn': {
        'title': 'NEXARIS | ನೆಕ್ಸಾರಿಸ್',
        'subtitle': 'Secure Voice Resource Node',
        'instructions': "Tap and speak your request | ನಿಮ್ಮ ವಿನಂತಿಯನ್ನು ಹೇಳಿ",
        'button': "⚡ Process | ⚡ ಪ್ರಕ್ರಿಯೆಗೊಳಿಸಿ",
        'success': "✅ Sent | ✅ ಕಳುಹಿಸಲಾಗಿದೆ",
        'error': "❌ Error | ❌ ದೋಷ"
    },
    'ml': {
        'title': 'NEXARIS | നെക്സാരിസ്',
        'subtitle': 'Secure Voice Resource Node',
        'instructions': "Tap and speak your request | നിങ്ങളുടെ അഭ്യർത്ഥന പറയുക",
        'button': "⚡ Process | ⚡ പ്രോസസ്സ് ചെയ്യുക",
        'success': "✅ Sent | ✅ അയച്ചു",
        'error': "❌ Error | ❌ പിശക്"
    },
    'ta': {
        'title': 'NEXARIS | நெக்ஸாரிஸ்',
        'subtitle': 'Secure Voice Resource Node',
        'instructions': "Tap and speak your request | உங்கள் கோரிக்கையை பேசவும்",
        'button': "⚡ Process | ⚡ செயலாக்கு",
        'success': "✅ Sent | ✅ அனுப்பப்பட்டது",
        'error': "❌ Error | ❌ பிழை"
    },
    'te': {
        'title': 'NEXARIS | నెక్సారిస్',
        'subtitle': 'Secure Voice Resource Node',
        'instructions': "Tap and speak your request | మీ అభ్యర్థనను మాట్లాడండి",
        'button': "⚡ Process | ⚡ ప్రాసెస్ చేయండి",
        'success': "✅ Sent | ✅ పంపబడింది",
        'error': "❌ Error | ❌ లోపం"
    },
    'bn': {
        'title': 'NEXARIS | নেক্সারিস',
        'subtitle': 'Secure Voice Resource Node',
        'instructions': "Tap and speak your request | আপনার অনুরোধ বলুন",
        'button': "⚡ Process | ⚡ প্রক্রিয়া করুন",
        'success': "✅ Sent | ✅ প্রেরিত",
        'error': "❌ Error | ❌ ত্রুটি"
    },
    'pa': {
        'title': 'NEXARIS | ਨੈਕਸਾਰਿਸ',
        'subtitle': 'Secure Voice Resource Node',
        'instructions': "Tap and speak your request | ਆਪਣੀ ਬੇਨਤੀ ਬੋਲੋ",
        'button': "⚡ Process | ⚡ ਕਾਰਵਾਈ ਕਰੋ",
        'success': "✅ Sent | ✅ ਭੇਜਿਆ ਗਿਆ",
        'error': "❌ Error | ❌ ਗਲਤੀ"
    },
    'or': {
        'title': 'NEXARIS | ନେକ୍ସାରିସ୍',
        'subtitle': 'Secure Voice Resource Node',
        'instructions': "Tap and speak your request | ଆପଣଙ୍କର ଅନୁରୋଧ କୁହନ୍ତୁ",
        'button': "⚡ Process | ⚡ ପ୍ରକ୍ରିୟା କରନ୍ତୁ",
        'success': "✅ Sent | ✅ ପଠାଗଲା",
        'error': "❌ Error | ❌ ତ୍ରୁଟି"
    },
    'en': {
        'title': 'NEXARIS Node',
        'subtitle': 'Secure Voice Resource Node',
        'instructions': "Tap and speak your resource request",
        'button': "⚡ Process Request",
        'success': "✅ Request Processed & Mapped",
        'error': "❌ Engine Error"
    }
}

def get_browser_language():
    """Fetch the browser language from Streamlit context headers."""
    try:
        if hasattr(st, 'context') and hasattr(st.context, 'headers'):
            accept_lang = st.context.headers.get("Accept-Language", "en")
            # Parse primary language (e.g., 'hi-IN,hi;q=0.9,en-US;q=0.8' -> 'hi')
            primary_lang = accept_lang.split(',')[0].split('-')[0].lower()
            return primary_lang
    except Exception:
        pass
    return 'en'

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
    page_icon="🛰️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Modern UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Space Grotesk', monospace;
    }
    
    /* Force pure black background and neon accents */
    .stApp { background-color: #050505; color: #ffffff; }
    
    /* Fix invisible text by explicitly coloring standard Streamlit typography */
    h1, h2, h3, h4, h5, h6, p, span, label {
        color: #ffffff !important;
    }
    
    .main-header {
        font-weight: 800;
        font-size: clamp(1.8rem, 6vw, 3rem);
        color: #ffffff !important;
        margin-bottom: 0.2rem;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: clamp(2px, 1vw, 4px);
    }
    .sub-header {
        font-weight: 600;
        font-size: clamp(0.9rem, 3vw, 1.2rem);
        color: #FF4500 !important;
        margin-bottom: clamp(1.5rem, 4vh, 2.5rem);
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .block-container {
        /* Apply the flat tactical design natively to the main Streamlit container */
        background: #000000 !important;
        border: 2px solid #333333 !important;
        border-radius: 0px !important;
        padding: clamp(1.5rem, 4vw, 3rem) !important;
        max-width: 600px !important; /* Keep it compact and focused */
        margin: clamp(1rem, 5vh, 4rem) auto !important; /* Proper browser margins */
        text-align: center !important;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    
    /* Center all subheaders and text */
    [data-testid="stMarkdownContainer"] {
        text-align: center !important;
        width: 100%;
    }
    
    /* Massive circular button styling for the Audio Recorder iframe */
    iframe[title*="audio_recorder"] {
        background-color: #E60000 !important;
        border-radius: 50% !important;
        border: 2px solid #FF4D4D !important;
        box-shadow: 0 0 clamp(20px, 5vw, 40px) rgba(230, 0, 0, 0.4) !important;
        margin: 0 auto !important;
        display: block !important;
        width: clamp(100px, 25vw, 160px) !important;
        height: clamp(100px, 25vw, 160px) !important;
        transition: transform 0.2s ease;
    }
    
    iframe[title*="audio_recorder"]:hover {
        transform: scale(1.05);
        background-color: #FF1A1A !important;
    }
    
    /* Make buttons massive, flat, and high-contrast */
    .stButton>button {
        background-color: #E60000 !important;
        color: white !important;
        border-radius: 0px !important; /* Hard edges = tactical feel */
        border: 1px solid #FF4D4D !important;
        height: clamp(60px, 10vh, 90px);
        font-weight: 800;
        font-size: clamp(1rem, 2.5vw, 1.2rem);
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    .stButton>button:hover { 
        background-color: #FF1A1A !important; 
        border-color: white !important; 
    }
</style>
""", unsafe_allow_html=True)

# Fetch localization context
lang_code = get_browser_language()
t = TRANSLATIONS.get(lang_code, TRANSLATIONS['en'])

# ==================== UI COMPONENTS ====================
st.markdown(f"<div class='main-header'>🛰️ {t['title']}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='sub-header'>{t['subtitle']}</div>", unsafe_allow_html=True)

st.subheader("🎙️ " + t['instructions'])

# The Microphone Widget
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    audio_bytes = audio_recorder(
        text="", 
        recording_color="#ff4b4b", 
        neutral_color="#8b949e",
        icon_name="microphone",
        icon_size="3x"
    )

if audio_bytes:
    st.audio(audio_bytes, format="audio/wav")
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button(t['button'], type="primary", use_container_width=True):
        with st.spinner("Processing..."):
            try:
                files = {"file": ("recording.wav", audio_bytes, "audio/wav")}
                
                response = requests.post(
                    f"{BACKEND_URL}/api/v1/ingest/audio",
                    files=files,
                    timeout=API_TIMEOUT
                )
                
                if response.status_code == 200:
                    st.success(t['success'])
                    st.json(response.json())
                else:
                    st.error(f"{t['error']}: {response.json().get('detail', 'Unknown Error')}")
                    
            except Exception as e:
                st.error(f"Connection Failed: {e}")

# ==================== SIDEBAR INFO ====================
with st.sidebar:
    st.subheader("ℹ️ System Status")
    is_connected = backend_url_accessible(BACKEND_URL)
    
    st.metric(
        label="NEXARIS Core", 
        value="Online" if is_connected else "Offline",
        delta="Connected" if is_connected else "Disconnected",
        delta_color="normal" if is_connected else "inverse"
    )
    
    st.metric("System Language", lang_code.upper())
    st.metric("Timestamp (UTC)", datetime.utcnow().strftime("%H:%M:%S"))

    st.markdown("---")
    st.markdown(
        """
        **🛰️ NEXARIS Enterprise**
        Next-gen resource orchestration.
        End-to-end encrypted and verified.
        """
    )

if __name__ == "__main__":
    pass
