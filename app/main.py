import sys
from pathlib import Path

# Ensure project root is on sys.path so `import app...` works when Streamlit runs the script
sys.path.append(str(Path(__file__).resolve().parents[1]))

import os
import json
import streamlit as st
import base64
import html as _html
import streamlit.components.v1 as components
from app.services.oriki_service import get_oriki_result
from app.services.tts import text_to_speech, get_voice_candidates, is_yarngpt_api_available
from app.services import nla_client
from app.services.oriki_glossary import build_glossary, language_options

st.set_page_config(page_title="Oríkì — Indigenous Praise Poetry", layout="wide")


def inject_theme():
    """Inject the 'Clay' editorial-heritage theme: fonts, tokens, motion, widget overrides."""
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Gentium+Plus:ital,wght@0,400;0,700;1,400&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root{
  --bg:#faf8f5; --surface:#ffffff; --ink:#1c1a17; --muted:#5c5347;
  --line:#e7e2da; --accent:#b5502e; --accent-weak:#f0e0d8; --ok:#1f6f52;
  --serif:'Gentium Plus',Georgia,serif; --sans:'Space Grotesk',system-ui,sans-serif;
}
html,body,[class*="css"],.stApp{background:var(--bg);color:var(--ink);font-family:var(--sans);}
.block-container{max-width:1180px;padding-top:3.75rem;}
@keyframes fadeUp{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}
@keyframes breathe{0%,100%{opacity:1;transform:scale(1);}50%{opacity:.55;transform:scale(.82);}}
@keyframes shimmer{0%{background-position:-320px 0;}100%{background-position:320px 0;}}
.masthead,.rail-block,.stage-wrap{animation:fadeUp .6s cubic-bezier(0.16,1,0.3,1) both;}
.rail-block{animation-delay:.08s;} .stage-wrap{animation-delay:.16s;}
/* Masthead */
.masthead{display:flex;justify-content:space-between;align-items:flex-end;gap:1.5rem;
  border-bottom:1px solid var(--line);padding-bottom:1.4rem;margin-bottom:1.8rem;flex-wrap:wrap;}
.kicker{font-family:var(--sans);font-size:.72rem;font-weight:600;letter-spacing:.22em;
  line-height:1.5;text-transform:uppercase;color:var(--accent);}
.display{font-family:var(--serif);font-weight:700;font-size:clamp(2.6rem,6vw,4.2rem);
  line-height:.95;letter-spacing:-.01em;margin:.3rem 0 .4rem;color:var(--ink);}
.lede{font-family:var(--sans);color:var(--muted);font-size:1rem;max-width:52ch;line-height:1.6;margin:0;}
/* Status pill */
.pill{display:inline-flex;align-items:center;gap:.5rem;font-family:var(--sans);
  font-size:.8rem;font-weight:500;padding:.4rem .8rem;border-radius:999px;border:1px solid var(--line);
  background:var(--surface);white-space:nowrap;}
.pill .dot{width:8px;height:8px;border-radius:50%;animation:breathe 2.4s ease-in-out infinite;}
.pill-ok .dot{background:var(--ok);} .pill-ok{color:var(--ok);}
.pill-warn .dot{background:var(--accent);} .pill-warn{color:var(--accent);}
/* Rail */
.rail-title{font-family:var(--sans);font-size:.72rem;font-weight:600;letter-spacing:.18em;
  text-transform:uppercase;color:var(--muted);margin:0 0 .2rem;}
/* Buttons */
.stButton>button{font-family:var(--sans);font-weight:600;border-radius:10px;min-height:44px;
  border:1px solid var(--accent);background:var(--accent);color:#fff;
  transition:transform .12s ease, box-shadow .2s ease;box-shadow:0 6px 16px -8px rgba(181,80,46,.6);}
.stButton>button:hover{background:#a3472a;border-color:#a3472a;color:#fff;}
.stButton>button:active{transform:translateY(1px);}
.stButton>button:focus-visible{outline:2px solid var(--ink);outline-offset:2px;}
/* Word breakdown list */
.gloss-list{border-top:1px solid var(--line);}
.gloss-row{border-bottom:1px solid var(--line);padding:.9rem 0;}
.gloss-word{font-family:var(--serif);font-size:1.15rem;font-weight:700;color:var(--ink);}
.gloss-meta{font-family:var(--sans);font-size:.9rem;color:var(--muted);line-height:1.55;margin-top:.25rem;}
.gloss-meta .tag{color:var(--accent);font-weight:600;}
.gloss-none{font-style:italic;}
.skeleton .shimmer{height:14px;border-radius:6px;margin:.5rem 0;
  background:linear-gradient(90deg,var(--line) 0%,#f3efe8 50%,var(--line) 100%);
  background-size:640px 100%;animation:shimmer 1.3s infinite linear;}
/* Mobile / tablet: collapse the asymmetric columns into a single stack */
@media (max-width: 768px){
  .block-container{padding-top:2.75rem;padding-left:1rem;padding-right:1rem;}
  [data-testid="stHorizontalBlock"]{flex-direction:column;gap:1.25rem;}
  [data-testid="stColumn"]{width:100%!important;flex:1 1 100%!important;min-width:0!important;}
  .masthead{margin-bottom:1.4rem;padding-bottom:1.1rem;}
  .masthead-right{margin-top:.2rem;}
  .stButton>button{width:100%;}
}
/* Respect users who prefer reduced motion */
@media (prefers-reduced-motion: reduce){
  .masthead,.rail-block,.stage-wrap{animation:none;}
  .pill .dot{animation:none;}
  .skeleton .shimmer{animation:none;}
  .stButton>button{transition:none;}
}
</style>
        """,
        unsafe_allow_html=True,
    )


def render_masthead(api_langs):
    """Left-aligned masthead + live API status pill (no emojis)."""
    if api_langs:
        pill = ('<span class="pill pill-ok"><span class="dot"></span>'
                'Nigerian Languages API connected</span>')
    else:
        pill = ('<span class="pill pill-warn"><span class="dot"></span>'
                'API unavailable — local data</span>')
    st.markdown(
        f"""
<div class="masthead">
  <div class="masthead-left">
    <div class="kicker">Indigenous Praise Poetry</div>
    <h1 class="display">Oríkì</h1>
    <p class="lede">Generate and hear traditional Yorùbá, Igbo, and Hausa
      praise poetry — then read it back word by word.</p>
  </div>
  <div class="masthead-right">{pill}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_stage(text, audio_bytes):
    """Editorial 'stage': paper surface, Gentium display type, underline karaoke, empty state."""
    if not text:
        components.html(
            """
<div style="font-family:'Space Grotesk',system-ui,sans-serif;color:#5c5347;
  background:#fff;border:1px dashed #e7e2da;border-radius:18px;
  padding:48px 28px;text-align:center;line-height:1.6;">
  <div style="font-family:'Gentium Plus',Georgia,serif;font-size:1.5rem;color:#1c1a17;margin-bottom:.4rem;">Oríkì</div>
  Your praise poem will appear here. Choose a language and press
  <em>Generate Oríkì</em>.
</div>
            """,
            height=240,
        )
        return

    # Pass the poem to JS as a proper string literal (json.dumps handles quotes,
    # backslashes, and non-ASCII); guard against a "</script>" break-out.
    js_text = json.dumps(text).replace('</', '<\\/')
    data_url = ''
    if audio_bytes:
        mime = 'audio/mpeg'
        try:
            if audio_bytes[:4] == b'RIFF':
                mime = 'audio/wav'
        except Exception:
            pass
        b64 = base64.b64encode(audio_bytes).decode('ascii')
        data_url = f"data:{mime};base64,{b64}"

    html = """
<div style="font-family:'Gentium Plus',Georgia,serif;">
  <div id="player_container" style="margin-bottom:14px"></div>
  <div id="oriki_container" style="max-height:360px;overflow:auto;padding:28px 30px;
    border:1px solid #e7e2da;border-radius:18px;background:#fff;font-size:22px;
    line-height:1.7;color:#1c1a17;box-shadow:0 20px 40px -18px rgba(28,26,23,0.18);"></div>
</div>
<style>
.oriki_word{white-space:pre-wrap;transition:color .25s ease;}
.oriki_highlight{color:#b5502e;box-shadow:inset 0 -0.5em 0 #f0e0d8;border-radius:2px;}
#player_container audio{width:100%;height:38px;}
</style>
<script>
const text = {JS_TEXT};
const words = text.split(/(\\s+)/);
const cont = document.getElementById('oriki_container');
cont.innerHTML = '';
words.forEach((w,i)=>{const s=document.createElement('span');s.className='oriki_word';
  s.dataset.idx=i;s.textContent=w;cont.appendChild(s);});
const dataUrl = '{DATA_URL}';
if (dataUrl) {
  const audio=new Audio(dataUrl);audio.controls=true;
  document.getElementById('player_container').appendChild(audio);
  let per=0,lastIdx=-1;
  audio.addEventListener('loadedmetadata',()=>{per=audio.duration/(words.length||1);});
  audio.addEventListener('timeupdate',()=>{
    if(!per)return;const idx=Math.floor(audio.currentTime/per);
    if(idx===lastIdx)return;lastIdx=idx;
    document.querySelectorAll('.oriki_highlight').forEach(e=>e.classList.remove('oriki_highlight'));
    const el=document.querySelector('.oriki_word[data-idx="'+idx+'"]');
    if(el){el.classList.add('oriki_highlight');el.scrollIntoView({behavior:'smooth',block:'center'});}
  });
}
</script>
"""
    html = html.replace('{DATA_URL}', data_url).replace('{JS_TEXT}', js_text)
    components.html(html, height=460)


def render_error_state(title, subtitle):
    """Editorial error card for 'no oríkì found' / 'service unavailable' states."""
    components.html(
        f"""
<div style="font-family:'Space Grotesk',system-ui,sans-serif;color:#5c5347;
  background:#fff;border:1px dashed #d9b3a6;border-radius:18px;
  padding:44px 28px;text-align:center;line-height:1.6;">
  <div style="font-family:'Gentium Plus',Georgia,serif;font-size:1.45rem;
    color:#b5502e;margin-bottom:.5rem;">{_html.escape(title)}</div>
  <div style="max-width:42ch;margin:0 auto;">{_html.escape(subtitle)}</div>
</div>
        """,
        height=240,
    )


def _gloss_row_html(row):
    """Render one Word Breakdown row as a hairline-divided list item."""
    if row["status"] != "found":
        return (f'<div class="gloss-row"><span class="gloss-word">{_html.escape(row["word"])}</span>'
                f'<div class="gloss-meta gloss-none">no dictionary or corpus match</div></div>')
    lines = []
    for match in row["matches"]:
        if match["kind"] == "definition":
            label = "definition"
            meta = " · ".join(p for p in [match.get("dialect_name"), match.get("pos")] if p)
            gloss = match.get("gloss") or match.get("headword") or "—"
        else:
            label = "corpus example"
            meta = match.get("dialect_name") or ""
            gloss = match.get("gloss") or "—"
        meta_str = f" ({_html.escape(meta)})" if meta else ""
        lines.append(f'<span class="tag">{label}</span>{meta_str}: {_html.escape(str(gloss))}')
    body = "<br>".join(lines)
    return (f'<div class="gloss-row"><span class="gloss-word">{_html.escape(row["word"])}</span>'
            f'<div class="gloss-meta">{body}</div></div>')


def render_breakdown(text, language, api_langs):
    """Word Breakdown glossary: skeleton loader then a divide-y list; inline states."""
    if not text:
        return
    with st.expander("Word breakdown — powered by the Nigerian Languages API", expanded=False):
        if not api_langs:
            st.info("The Nigerian Languages API is unavailable right now, so the word "
                    "breakdown can't load. Oríkì generation and audio still work.")
            return
        slot = st.empty()
        slot.markdown(
            '<div class="skeleton">' + ''.join(
                f'<div class="shimmer" style="width:{w}%"></div>' for w in (40, 70, 55, 65)
            ) + '</div>',
            unsafe_allow_html=True,
        )
        glossary = build_glossary(text, language, nla_client)
        rows = glossary["rows"]
        html_rows = "".join(_gloss_row_html(r) for r in rows)
        slot.markdown(f'<div class="gloss-list">{html_rows}</div>', unsafe_allow_html=True)
        if glossary["truncated"]:
            st.caption(f"Showing the first {len(rows)} of {glossary['total_words']} words.")
        st.caption("Word data provided by the Nigerian Languages API (dara-ze5e.onrender.com).")


# --- Session defaults ---
if 'last_result' not in st.session_state:
    st.session_state['last_result'] = ""
if 'language' not in st.session_state:
    st.session_state['language'] = 'yoruba'
if 'voice' not in st.session_state:
    st.session_state['voice'] = 'Auto'

# --- Page ---
inject_theme()

_api_languages = nla_client.get_languages()
render_masthead(_api_languages)

rail, stage = st.columns([5, 7], gap="large")

with rail:
    st.markdown('<div class="rail-block">', unsafe_allow_html=True)
    st.markdown('<p class="rail-title">Compose</p>', unsafe_allow_html=True)

    _LOCAL_LANGS = ["yoruba", "igbo", "hausa"]
    _lang_choices = language_options(_api_languages, _LOCAL_LANGS, allowed=_LOCAL_LANGS)
    language = st.selectbox("Language", _lang_choices, key='language')

    voice_choices = ["Auto"] + get_voice_candidates(language)
    st.selectbox("Voice", voice_choices, key='voice')

    api_available = is_yarngpt_api_available()

    name = st.text_input("Your name (optional)")

    if st.button("Generate Oríkì"):
        res = get_oriki_result(language, name or None)
        st.session_state['last_result'] = res.get('text') or ""
        st.session_state['last_status'] = res.get('status')
        st.session_state['last_name'] = res.get('name')
        st.session_state['last_meaning'] = res.get('meaning')
        st.session_state['last_source'] = res.get('source')
        st.session_state.pop('last_audio', None)  # drop stale audio for the new poem

    if st.button("Play audio", key='play_audio'):
        if st.session_state.get('last_result'):
            selected_voice = st.session_state.get('voice')
            if selected_voice == 'Auto':
                selected_voice = None
            audio = text_to_speech(st.session_state['last_result'], language, voice=selected_voice)
            if audio:
                st.session_state['last_audio'] = audio
            else:
                st.error("Text-to-speech failed. Set `YARNGPT_API_KEY` or install `gTTS`.")
        else:
            st.warning("Generate an Oríkì first.")

    if not api_available:
        st.caption("YarnGPT key missing — audio falls back to gTTS if installed.")
    st.markdown('</div>', unsafe_allow_html=True)

with stage:
    st.markdown('<div class="stage-wrap">', unsafe_allow_html=True)
    _status = st.session_state.get('last_status')
    if _status == 'not_found':
        _nm = st.session_state.get('last_name')
        if _nm:
            render_error_state(
                f'No oríkì for "{_nm}" yet',
                "We don't have a praise poem for that name in the collection "
                "yet. Try another name, or leave the name blank for a random "
                "oríkì.")
        else:
            render_error_state(
                'No oríkì available',
                'The collection returned no praise poem. Please try again.')
    elif _status == 'unavailable':
        render_error_state(
            'Oríkì service unavailable',
            'The Nigerian Languages API is unreachable right now and no local '
            'oríkì is available. Please try again shortly.')
    else:
        render_stage(
            st.session_state.get('last_result', ''),
            st.session_state.get('last_audio', b""),
        )
        _meaning = st.session_state.get('last_meaning')
        if _meaning and st.session_state.get('last_result'):
            st.caption(f"Meaning: {_meaning}")
    st.markdown('</div>', unsafe_allow_html=True)

render_breakdown(
    st.session_state.get('last_result', ''),
    st.session_state.get('language', 'yoruba'),
    _api_languages,
)
