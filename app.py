"""NEXARIS Streamlit Frontend - Resource Request UI
Secure interface for submitting resource requests to the NEXARIS backend
"""
import streamlit as st
import requests
import os
from datetime import datetime, timezone
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
        'button': "⚡ Transmit Request",
        'success': "✅ Received - Dispatch Coordinated",
        'error': "❌ Connection Interrupted - Please Retry"
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

# Tactical Flat UI (Military/HUD Design)
st.markdown("""
<style>
    /* Deep Space Black Background */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;800&display=swap');
    .stApp { background-color: #050505; color: #ffffff; font-family: 'Space Grotesk', monospace; }
    
    /* Tactical Typography */
    h1, h2, h3, .main-header, .sub-header { color: #FFFFFF !important; text-transform: uppercase; letter-spacing: 2px; }
    .main-header { font-weight: 800; font-size: clamp(1.8rem, 6vw, 3rem); text-align: center; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 0.2rem;}
    .sub-header { font-weight: 600; font-size: clamp(0.9rem, 3vw, 1.2rem); text-align: center; margin-bottom: clamp(1.5rem, 4vh, 2.5rem); }
    p, span, label { color: #E0E0E0 !important; }
    
    /* Flat Design Neon Buttons (Psychologically Reassuring Tactical Blue) */
    .stButton>button {
        background-color: #0066FF !important;
        color: white !important;
        border-radius: 0px !important; 
        border: 2px solid #3385FF !important;
        height: 70px;
        font-weight: 800;
        letter-spacing: 2px;
        text-transform: uppercase;
        transition: all 0.2s ease-in-out;
        width: 100%;
        margin-top: 1rem;
    }
    .stButton>button:hover { background-color: #0052CC !important; border-color: #FFF !important; box-shadow: 0px 0px 15px rgba(51, 133, 255, 0.5) !important; transform: none; }
    .stButton>button:active { background-color: #003D99 !important; border-color: #3385FF !important; }
    .stButton>button:focus:not(:active) { outline: none !important; }
    
    /* Text Inputs */
    .stTextInput>div>div>input { background-color: #111; color: #00E5FF; border: 1px solid #333; border-radius: 0px; }
    .stTextInput>div>div>input:focus { border-color: #00E5FF; }
    
    /* Status Badges */
    .success-badge { color: #00E5FF; border: 1px solid #00E5FF; padding: 10px; text-align: center; font-weight: bold; }
    .error-badge { color: #FF2A2A; border: 1px solid #FF2A2A; padding: 10px; text-align: center; font-weight: bold; }

    /* Other elements */
    .block-container { background: #000000 !important; border: 2px solid #333333 !important; padding: clamp(1.5rem,4vw,3rem) !important; max-width: 600px !important; margin: clamp(1rem,5vh,4rem) auto !important; }
    audio { filter: invert(1) hue-rotate(180deg) contrast(1.5); border-radius: 0px; width: 100%; margin-top: 2rem; }
    [data-testid="stSidebar"] { background-color: #050505 !important; border-right: 2px solid #333333 !important; }
    [data-testid="stSidebar"] [data-testid="stMetric"] { background: #0a0a0a; border: 1px solid #2a2a2a; padding: 0.75rem 1rem !important; margin-bottom: 0.5rem !important; }
</style>
<script>
// accessibility and lazy load optimizations
const observer=new MutationObserver(()=>{
    document.querySelectorAll('iframe').forEach(i=>{
        if(!i.hasAttribute('loading'))i.setAttribute('loading','lazy');
        if(i.title.includes('audio_recorder') && !i.dataset.a11y){
            i.dataset.a11y="true";
            try{
                i.onload=()=>{
                    const b=i.contentWindow.document.querySelector('button,svg');
                    if(b&&!b.hasAttribute('aria-label'))b.setAttribute('aria-label','Start voice recording');
                };
            }catch(e){}
        }
    });
});
observer.observe(document.body,{childList:true,subtree:true});
</script>
""", unsafe_allow_html=True)


# Fetch localization context
lang_code_auto = get_browser_language()
if lang_code_auto not in TRANSLATIONS:
    lang_code_auto = 'en'

with st.sidebar:
    st.subheader("🌐 Language / भाषा")
    lang_options = list(TRANSLATIONS.keys())
    lang_index = lang_options.index(lang_code_auto)
    lang_code = st.selectbox("Select Language", lang_options, index=lang_index, label_visibility="collapsed")

t = TRANSLATIONS.get(lang_code, TRANSLATIONS['en'])

# ==================== UI COMPONENTS ====================
st.markdown(f"<div class='main-header'>🛰️ {t['title']}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='sub-header'>{t['subtitle']}</div>", unsafe_allow_html=True)

st.html("""
<script>
const observer=new MutationObserver(()=>{
    try {
        window.parent.document.querySelectorAll('iframe').forEach(i=>{
            if(!i.hasAttribute('loading')) i.setAttribute('loading','lazy');
            if(i.title && i.title.includes('audio_recorder') && !i.dataset.a11y){
                i.dataset.a11y="true";
                // Do NOT override i.onload, it breaks Streamlit's ComponentRegistry
                i.addEventListener('load', ()=>{
                    try{
                        const b=i.contentWindow.document.querySelector('button,svg');
                        if(b&&!b.hasAttribute('aria-label')) b.setAttribute('aria-label','Start voice recording');
                    }catch(e){}
                });
            }
        });
    } catch(e) {}
});
observer.observe(window.parent.document.body,{childList:true,subtree:true});
</script>
""")

st.subheader("ACOUSTIC CAPTURE")
st.write(t['instructions'])

# The Microphone Widget
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    audio_bytes = audio_recorder(text="INITIALIZE MIC", recording_color="#0066FF", neutral_color="#444444")

st.subheader("MANUAL OVERRIDE")
text_fallback = st.text_input(
    "Enter request manually:", 
    placeholder="e.g., 'Urgently need 50 blood packs at North Crossroad'",
    help="Type your resource request here if you cannot use voice or if the microphone is unavailable."
)

if audio_bytes or text_fallback:
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button(t['button'], use_container_width=True):
        with st.spinner("TRANSMITTING TO T-CORE..."):
            try:
                if audio_bytes:
                    files = {"file": ("recording.wav", audio_bytes, "audio/wav")}
                    response = requests.post(
                        f"{BACKEND_URL}/api/v1/ingest/audio",
                        files=files,
                        timeout=API_TIMEOUT
                    )
                else:
                    response = requests.post(
                        f"{BACKEND_URL}/api/v1/ingest/text", 
                        json={"text": text_fallback}, 
                        timeout=API_TIMEOUT
                    )
                    
                if response.status_code == 200:
                    st.markdown(f"<div class='success-badge' role='status' aria-live='polite'>{t['success']}</div>", unsafe_allow_html=True)
                    data = response.json()
                    
                    if "structured_payload" in data:
                        payload = data["structured_payload"].get("entities", {})
                        st.info(f"**Item**: {payload.get('item')}\n\n**Urgency**: {payload.get('urgency')}\n\n**Location**: {payload.get('location_context')}")
                else:
                    st.markdown(f"<div class='error-badge' role='alert' aria-live='assertive'>{t['error']}: {response.json().get('detail', 'Unknown Error')}</div>", unsafe_allow_html=True)
                    
            except Exception as e:
                st.markdown(f"<div class='error-badge' role='alert' aria-live='assertive'>NETWORK FAILURE: {e}</div>", unsafe_allow_html=True)

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
    st.metric("Timestamp (UTC)", datetime.now(timezone.utc).strftime("%H:%M:%S"))

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
