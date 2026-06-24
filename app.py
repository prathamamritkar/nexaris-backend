"""NEXARIS Streamlit Frontend - Resource Request UI
Secure interface for submitting resource requests to the NEXARIS backend
"""
import streamlit as st
import requests
import os
from datetime import datetime
import logging
import html as _html
import json as _json

logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================
BACKEND_URL = os.getenv(
    "NEXARIS_BACKEND_URL",
    "http://localhost:8000"
).rstrip("/")


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
html,body,[class*="css"]{font-family:'Space Grotesk',monospace}
.stApp{background-color:#050505;color:#ffffff}
h1,h2,h3,h4,h5,h6,p,span,label{color:#ffffff!important}
.main-header{font-weight:800;font-size:clamp(1.8rem,6vw,3rem);color:#ffffff!important;margin-bottom:0.2rem;text-align:center;text-transform:uppercase;letter-spacing:clamp(2px,1vw,4px)}
.sub-header{font-weight:600;font-size:clamp(0.9rem,3vw,1.2rem);color:#E0E0E0!important;margin-bottom:clamp(1.5rem,4vh,2.5rem);text-align:center;text-transform:uppercase;letter-spacing:2px}
.block-container{background:#000000!important;border:2px solid #333333!important;border-radius:16px!important;padding:clamp(1.5rem,4vw,3rem)!important;max-width:600px!important;margin:clamp(1rem,5vh,4rem) auto!important}
audio{filter:invert(1) hue-rotate(180deg) contrast(1.5);border-radius:8px;width:100%;margin-top:2rem}
[data-testid="stSidebar"]{background-color:#050505!important;border-right:2px solid #333333!important}
[data-testid="stSidebar"] [data-testid="stMetric"]{align-items:flex-start!important;background:#0a0a0a;border:1px solid #2a2a2a;border-radius:10px;padding:0.75rem 1rem!important;margin-bottom:0.5rem!important}
[data-testid="stSidebar"] [data-testid="stMetricValue"] > div{justify-content:flex-start!important; font-size:1.4rem!important;}
[data-testid="stSidebar"] [data-testid="stMetricLabel"] > div{justify-content:flex-start!important;}
[data-testid="stSidebar"] [data-testid="stMetricLabel"]{font-size:0.9rem!important;opacity:0.8}
[data-testid="stAlert"]{background-color:#0d0d0d!important;border:2px solid #555555!important;border-radius:10px!important;color:#ffffff!important}
[data-testid="stAlert"][data-baseweb="notification"]{border-left:6px solid #FF4500!important;border-radius:10px!important}
.block-container [data-testid="stMarkdownContainer"]{text-align:center!important;width:100%}
.stButton>button{background:linear-gradient(135deg,#C00000 0%,#E60000 60%,#FF2200 100%)!important;color:#ffffff!important;border-radius:10px!important;border:1.5px solid #FF4D4D!important;height:clamp(60px,10vh,90px);font-weight:800;font-size:clamp(1rem,2.5vw,1.2rem);letter-spacing:3px;text-transform:uppercase;margin-top:1rem;width:100%;box-shadow:0 4px 20px rgba(230,0,0,0.35),inset 0 1px 0 rgba(255,255,255,0.08);transition:all 0.18s cubic-bezier(0.4,0,0.2,1)}
.stButton>button:hover{background:linear-gradient(135deg,#E60000 0%,#FF2200 60%,#FF4500 100%)!important;border-color:#FF7755!important;border-radius:10px!important;box-shadow:0 6px 28px rgba(255,69,0,0.5),inset 0 1px 0 rgba(255,255,255,0.12)!important;transform:translateY(-2px)}
.stButton>button:active{background:linear-gradient(135deg,#990000 0%,#CC0000 100%)!important;border-color:#FF4D4D!important;border-radius:10px!important;box-shadow:0 2px 8px rgba(200,0,0,0.4)!important;transform:translateY(0px)}
.stButton>button:focus:not(:active){border-color:#FF7755!important;border-radius:10px!important;box-shadow:0 0 0 3px rgba(255,69,0,0.25),0 4px 20px rgba(230,0,0,0.35)!important;outline:none!important}
.stButton>button[kind="secondary"]{background:transparent!important;border:1.5px solid #444!important;border-radius:10px!important;color:#ccc!important;box-shadow:none!important}
.stButton>button[kind="secondary"]:hover{border-color:#888!important;color:#fff!important;background:#111!important}
[data-testid="stSpinner"]{border-radius:10px!important}
[data-testid="stSpinner"] svg circle{stroke:#FF4500!important}
</style>
""", unsafe_allow_html=True)


# Fetch localization context
lang_code = get_browser_language()
t = TRANSLATIONS.get(lang_code, TRANSLATIONS['en'])

# ==================== UI COMPONENTS ====================
st.markdown(f"<div class='main-header'>🛰️ {t['title']}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='sub-header'>{t['subtitle']}</div>", unsafe_allow_html=True)

# ---- Security-escaped interpolation values ----
_ep       = _html.escape(f"{BACKEND_URL}/api/v1/ingest/audio", quote=True)
_aria     = _html.escape(t['instructions'], quote=True)
_status0  = _html.escape(t['instructions'], quote=True)
_js_ok    = _json.dumps(str(t['success'])[:80])
_js_err   = _json.dumps(str(t['error'])[:40])
_js_hint  = _json.dumps(str(t['instructions'])[:120])

st.components.v1.html(f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy"
      content="default-src 'none'; style-src 'unsafe-inline' https://fonts.googleapis.com https://fonts.gstatic.com; font-src https://fonts.gstatic.com; connect-src {_html.escape(BACKEND_URL, quote=True)}; script-src 'unsafe-inline';">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;800&display=swap');
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:transparent;font-family:'Space Grotesk',sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:200px;gap:16px}}
  #mic-btn{{
    width:84px;height:84px;border-radius:50%;
    border:2.5px solid #00AEEF;background:#080808;
    font-size:2.2rem;cursor:pointer;
    display:flex;align-items:center;justify-content:center;
    transition:border-color 0.3s ease,background 0.3s ease;
    animation:idlePulse 2.8s ease-in-out infinite;
    outline:none;user-select:none;
  }}
  #mic-btn.recording{{border-color:#FF4500;background:#1a0500;animation:recPulse 0.85s ease-in-out infinite;}}
  #mic-btn:hover:not(.recording){{border-color:#00D4FF;background:#05121a;}}
  #mic-btn:disabled{{opacity:0.4;cursor:not-allowed;animation:none;}}
  @keyframes idlePulse{{
    0%,100%{{box-shadow:0 0 0 0 rgba(0,174,239,0),0 0 8px rgba(0,174,239,0.15)}}
    50%{{box-shadow:0 0 0 12px rgba(0,174,239,0),0 0 22px rgba(0,174,239,0.6)}}
  }}
  @keyframes recPulse{{
    0%,100%{{box-shadow:0 0 0 0 rgba(255,69,0,0),0 0 10px rgba(255,69,0,0.35)}}
    50%{{box-shadow:0 0 0 18px rgba(255,69,0,0),0 0 34px rgba(255,69,0,0.95)}}
  }}
  #status{{font-size:0.72rem;letter-spacing:2px;text-transform:uppercase;color:#555;text-align:center;min-height:1.2em;transition:color 0.3s}}
  #status.rec{{color:#FF4500}}#status.ok{{color:#00AEEF}}#status.err{{color:#FF4D4D}}
  #result{{font-size:0.7rem;color:#888;max-width:340px;word-break:break-all;text-align:center;display:none;background:#0d0d0d;border:1px solid #2a2a2a;border-radius:8px;padding:8px 12px;margin-top:4px}}
</style>
</head>
<body>
<button id="mic-btn" aria-label="{_aria}" data-ep="{_ep}">🎤</button>
<div id="status">{_status0}</div>
<div id="result" aria-live="polite"></div>
<script>
(()=>{{
  'use strict';

  /* ── DOM refs ── */
  const btn    = document.getElementById('mic-btn');
  const status = document.getElementById('status');
  const result = document.getElementById('result');

  /* ── Constants ── */
  const MAX_BLOB_BYTES  = 10 * 1024 * 1024; // 10 MB hard limit
  const MAX_REC_MS      = 30_000;           // 30 s max recording
  const FETCH_TIMEOUT   = 30_000;           // 30 s fetch abort
  const ALLOWED_SCHEMES = ['https:', 'http:'];

  /* ── Safely resolve and validate ENDPOINT ── */
  let ENDPOINT;
  try {{
    const raw = btn.getAttribute('data-ep') || '';
    const u   = new URL(raw);
    if (!ALLOWED_SCHEMES.includes(u.protocol))
      throw new Error('Bad scheme');
    // Strip any embedded credentials from URL
    u.username = '';
    u.password = '';
    ENDPOINT = u.toString();
  }} catch(_) {{
    btn.disabled = true;
    status.textContent = 'Config error';
    return;
  }}

  /* ── State ── */
  let recorder = null, chunks = [], isRecording = false,
      activeStream = null, autoStopTimer = null, busy = false;

  /* ── Mic track cleanup on page unload ── */
  window.addEventListener('beforeunload', () => {{
    if (activeStream) activeStream.getTracks().forEach(t => t.stop());
  }});

  /* ── Safe text setter: coerce to string, cap length, strip control chars ── */
  const safeText = (v, max=120) =>
    String(v ?? '').replace(/[\x00-\x1F\x7F]/g, '').slice(0, max);

  /* ── Display helpers ── */
  const setStatus = (msg, cls='') => {{
    status.textContent = safeText(msg, 80);
    status.className   = cls;
  }};
  const resetUI = () => {{
    setStatus({_js_hint});
    result.style.display = 'none';
    result.textContent   = '';
  }};

  /* ── Click handler with lock ── */
  btn.addEventListener('click', async () => {{
    if (busy) return; // prevent double-submit
    busy = true;
    try {{
      await handleClick();
    }} finally {{
      busy = false;
    }}
  }});

  async function handleClick() {{
    if (!isRecording) {{
      /* ── Start recording ── */
      let stream;
      try {{
        stream = await navigator.mediaDevices.getUserMedia({{ audio: true, video: false }});
      }} catch (_) {{
        setStatus('Mic access denied', 'err');
        return;
      }}
      activeStream = stream;
      recorder     = new MediaRecorder(stream);
      chunks       = [];

      recorder.ondataavailable = e => {{
        if (e.data && e.data.size > 0) chunks.push(e.data);
      }};

      recorder.onstop = async () => {{
        clearTimeout(autoStopTimer);
        activeStream = null;
        stream.getTracks().forEach(t => t.stop());

        setStatus('Sending...');
        result.style.display = 'none';

        /* ── Assemble & validate blob ── */
        const blob = new Blob(chunks, {{ type: 'audio/webm' }});
        if (blob.size === 0) {{ setStatus('Empty recording', 'err'); setTimeout(resetUI, 3000); return; }}
        if (blob.size > MAX_BLOB_BYTES) {{ setStatus('Recording too large', 'err'); setTimeout(resetUI, 3000); return; }}

        /* ── POST with timeout ── */
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT);
        try {{
          const fd = new FormData();
          fd.append('file', blob, 'recording.webm');
          const res  = await fetch(ENDPOINT, {{
            method:  'POST',
            body:    fd,
            headers: {{ 'x-nexaris-origin': 'streamlit-ui' }},
            signal:  controller.signal
          }});
          clearTimeout(timer);

          if (!res.ok) {{
            // Redact server detail to avoid leaking internal errors
            setStatus({_js_err} + ': ' + String(res.status), 'err');
            setTimeout(resetUI, 4000);
            return;
          }}

          /* ── Parse & sanitize response (prototype-pollution safe) ── */
          let data;
          try {{ data = await res.json(); }} catch(_) {{ data = {{}}; }}
          const nodes  = Object.hasOwn(data, 'mapped_nodes')  ? String(Number(data.mapped_nodes))  : null;
          const dstat  = Object.hasOwn(data, 'status')        ? safeText(data.status, 40)          : null;
          const safe   = nodes ? `Nodes mapped: ${{nodes}}` : (dstat || 'OK');

          setStatus({_js_ok}, 'ok');
          result.textContent   = safe;
          result.style.display = 'block';
          setTimeout(resetUI, 4000);

        }} catch (e) {{
          clearTimeout(timer);
          const msg = e.name === 'AbortError' ? 'Timeout' : 'Offline';
          setStatus({_js_err} + ': ' + msg, 'err');
          setTimeout(resetUI, 4000);
        }}
      }};

      recorder.start(100); // collect in 100 ms chunks
      isRecording = true;
      btn.classList.add('recording');
      setStatus('Recording...', 'rec');

      /* ── Auto-stop after MAX_REC_MS ── */
      autoStopTimer = setTimeout(() => {{
        if (isRecording) {{
          recorder.stop();
          isRecording = false;
          btn.classList.remove('recording');
          setStatus('Processing...');
        }}
      }}, MAX_REC_MS);

    }} else {{
      /* ── Manual stop ── */
      clearTimeout(autoStopTimer);
      recorder.stop();
      isRecording = false;
      btn.classList.remove('recording');
      setStatus('Processing...');
    }}
  }}
}})();
</script>
</body>
</html>
""", height=280, scrolling=False)

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
