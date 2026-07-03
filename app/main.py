import sys
from pathlib import Path

# Ensure project root is on sys.path so `import app...` works when Streamlit runs the script
sys.path.append(str(Path(__file__).resolve().parents[1]))

import os
import streamlit as st
import base64
import html as _html
import streamlit.components.v1 as components
from app.services.oriki_service import get_oriki, generate_smart_oriki
from app.services.tts import text_to_speech, get_voice_candidates, is_yarngpt_api_available
from app.services import nla_client
from app.services.oriki_glossary import build_glossary, language_options

st.title("AI Indigenous Oríkì Generator")

if 'last_result' not in st.session_state:
    st.session_state['last_result'] = ""
if 'language' not in st.session_state:
    st.session_state['language'] = 'yoruba'
if 'voice' not in st.session_state:
    st.session_state['voice'] = 'Auto'

# Live connection status to the Nigerian Languages API (visible proof).
_api_languages = nla_client.get_languages()
if _api_languages:
    st.caption("🟢 Connected to the Nigerian Languages API")
else:
    st.caption("🔴 Nigerian Languages API unavailable — using local data only")

# Language dropdown driven live from the API, with a local fallback.
_lang_choices = language_options(_api_languages, ["yoruba", "igbo", "hausa"])
language = st.selectbox("Select Language", _lang_choices, key='language')

# Voice override selector (Auto uses best-effort candidates)
voice_choices = ["Auto"] + get_voice_candidates(language)
st.selectbox("Voice (override)", voice_choices, key='voice')

api_available = is_yarngpt_api_available()
if api_available:
    st.info("YarnGPT TTS API key is available.")
else:
    st.warning("YarnGPT TTS API key is missing. Audio will fall back to gTTS if installed.")

name = st.text_input("Enter your name (optional)")

if st.button("Generate Oríkì"):
    if name:
        result = get_oriki(language, name)
    else:
        result = generate_smart_oriki(language)

    st.session_state['last_result'] = result
    st.success(result)
# Controls area (Play button) placed before the Oríkì display so it stays visible
controls = st.container()
with controls:
    if st.button("Play Audio 🔊", key='play_audio'):
        if st.session_state.get('last_result'):
            selected_voice = st.session_state.get('voice')
            if selected_voice == 'Auto':
                selected_voice = None
            if not api_available:
                st.info("YarnGPT API is unavailable; attempting gTTS fallback.")
            audio = text_to_speech(st.session_state['last_result'], language, voice=selected_voice)
            if audio:
                st.session_state['last_audio'] = audio
            else:
                st.error("Text-to-speech failed. Ensure `YARNGPT_API_KEY` is set or install `gTTS`.")
        else:
            st.warning("Generate an Oríkì first before playing audio.")

# Display area: render the generated Oríkì inside a scrollable HTML component
text_to_display = st.session_state.get('last_result', '')
audio_bytes = st.session_state.get('last_audio', b"")

def render_oriki_component(text, audio_bytes):
    safe_text = _html.escape(text)
    data_url = ''
    if audio_bytes:
        mime = 'audio/mpeg'
        try:
            if audio_bytes.startswith(b'RIFF'):
                mime = 'audio/wav'
        except Exception:
            pass
        b64 = base64.b64encode(audio_bytes).decode('ascii')
        data_url = f"data:{mime};base64,{b64}"

    html = """
<div style="font-size:18px;line-height:1.6;">
  <div id="player_container" style="margin-bottom:8px"></div>
  <div id="oriki_container" style="max-height:360px;overflow:auto;padding:12px;border:1px solid #ddd;border-radius:6px;background:#fff"></div>
</div>
<style>
.oriki_word{white-space:pre-wrap}
.oriki_highlight{background-color: #fff59d}
</style>
<script>
const text = `{SAFE_TEXT}`;
const words = text.split(/(\\s+)/);
const cont = document.getElementById('oriki_container');
cont.innerHTML = '';
words.forEach((w,i)=>{
  const span = document.createElement('span');
  span.className = 'oriki_word';
  span.dataset.idx = i;
  span.textContent = w;
  cont.appendChild(span);
});

const dataUrl = '{DATA_URL}';
if (dataUrl) {
  const audio = new Audio(dataUrl);
  audio.controls = true;
  document.getElementById('player_container').appendChild(audio);

  let per = 0;
  let lastIdx = -1;
  audio.addEventListener('loadedmetadata', ()=>{
    const wc = words.length || 1;
    per = audio.duration / wc;
  });
  audio.addEventListener('timeupdate', ()=>{
    if (!per) return;
    const idx = Math.floor(audio.currentTime / per);
    if (idx === lastIdx) return;
    lastIdx = idx;
    document.querySelectorAll('.oriki_highlight').forEach(e=>e.classList.remove('oriki_highlight'));
    const el = document.querySelector('.oriki_word[data-idx="'+idx+'"]');
    if (el) {
      el.classList.add('oriki_highlight');
      el.scrollIntoView({behavior:'smooth',block:'center'});
    }
  });
}
</script>
"""
    html = html.replace('{DATA_URL}', data_url).replace('{SAFE_TEXT}', safe_text)
    components.html(html, height=420)

render_oriki_component(text_to_display, audio_bytes)

# --- Word Breakdown / Glossary (powered by the Nigerian Languages API) ---
if text_to_display:
    with st.expander("Word breakdown (powered by the Nigerian Languages API)"):
        if not _api_languages:
            st.info(
                "The Nigerian Languages API is unavailable right now, so the "
                "word breakdown can't load. Oríkì generation and audio still work."
            )
        else:
            with st.spinner("Looking up words in the Nigerian Languages API…"):
                glossary = build_glossary(text_to_display, language, nla_client)
            rows = glossary["rows"]
            if glossary["truncated"]:
                st.caption(
                    f"Showing the first {len(rows)} of "
                    f"{glossary['total_words']} words."
                )
            for row in rows:
                if row["status"] != "found":
                    st.markdown(f"**{row['word']}** — _no dictionary/corpus match_")
                    continue
                st.markdown(f"**{row['word']}**")
                for match in row["matches"]:
                    label = (
                        "definition" if match["kind"] == "definition"
                        else "corpus example"
                    )
                    meta = " · ".join(
                        p for p in [match.get("dialect_name"), match.get("pos")]
                        if p
                    )
                    gloss = match.get("gloss") or "—"
                    st.markdown(f"- _{label}_ ({meta}): {gloss}")
        st.caption(
            "Word data provided by the Nigerian Languages API "
            "(dara-ze5e.onrender.com)."
        )

# accent preview removed per user request

