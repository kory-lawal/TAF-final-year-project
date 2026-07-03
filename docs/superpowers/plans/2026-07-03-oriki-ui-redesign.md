# Oríkì UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restyle the Streamlit presentation layer of the AI Indigenous Oríkì Generator into an editorial-heritage design without touching the Python backend.

**Architecture:** Streamlit-native restyle via three levers — a `.streamlit/config.toml` base theme, a global CSS block injected with `st.markdown(unsafe_allow_html=True)`, and a rebuilt `components.html` stage. `app/main.py` is refactored from a flat script into render functions. All service calls and `st.session_state` keys are preserved verbatim.

**Tech Stack:** Streamlit, Python 3, Google Fonts (Gentium Plus, Space Grotesk), CSS animations. No new pip dependencies.

## Global Constraints

- Stack is **Streamlit** — no React, motion is CSS-only.
- **No new pip dependencies.** Fonts load from Google Fonts CDN via CSS `@import`.
- **Anti-emoji:** no emojis in markup or copy. Use CSS dots / text glyphs.
- **Diacritics:** display font must render Yoruba/Igbo/Hausa tone marks + subdots → **Gentium Plus**. UI chrome font → **Space Grotesk**. Serif never on UI chrome.
- **Colors (Palette A "Clay"):** `--bg #faf8f5`, `--surface #ffffff`, `--ink #1c1a17` (never `#000`), `--muted #6b6459`, `--line #e7e2da`, `--accent #b5502e`, `--accent-weak #f0e0d8`, `--ok #1f6f52`. Single accent, saturation < 80%.
- **No backend changes:** `app/services/*`, `app/utils/*`, `app/config.py` untouched.
- **Existing pytest suite must stay green.**
- Animate only `transform`/`opacity`. Button `:active` → `translateY(1px)`.

## File Structure

- **Create** `.streamlit/config.toml` — base theme so native widgets inherit the palette.
- **Modify** `app/main.py` — refactor into: `inject_theme()`, `render_masthead(api_langs)`, `render_composer()` (left rail), `render_stage(text, audio)` (rebuilt `render_oriki_component`), `render_breakdown(text, language, api_langs)`. Preserve all session-state keys: `last_result`, `language`, `voice`, `last_audio`.

Because this is a presentation-layer restyle with almost no new logic, the test gate for each task is: **`pytest` stays green** + **manual visual verification** via `streamlit run app/main.py`. New pure helpers get a unit test where one exists.

---

### Task 1: Streamlit base theme config

**Files:**
- Create: `.streamlit/config.toml`

**Interfaces:**
- Produces: base theme tokens Streamlit widgets inherit (primary/background/text colors).

- [ ] **Step 1: Create the config**

```toml
[theme]
base = "light"
primaryColor = "#b5502e"
backgroundColor = "#faf8f5"
secondaryBackgroundColor = "#ffffff"
textColor = "#1c1a17"
```

- [ ] **Step 2: Verify pytest still green**

Run: `pytest -q`
Expected: PASS (no code changed).

- [ ] **Step 3: Commit**

```bash
git add .streamlit/config.toml
git commit -m "feat: add Streamlit clay theme config"
```

---

### Task 2: Global CSS theme injection + fonts

**Files:**
- Modify: `app/main.py` (add `inject_theme()`, call it right after `st.set_page_config`)

**Interfaces:**
- Produces: `inject_theme() -> None` — injects `<style>` with fonts, `:root` tokens, keyframes (`fadeUp`, `breathe`), and Streamlit container overrides. Later tasks rely on these CSS classes: `.kicker`, `.display`, `.lede`, `.masthead`, `.pill`, `.pill-ok`, `.pill-warn`, `.dot`, `.rail-title`, `.stage-empty`, `.gloss-list`, `.gloss-row`, `.gloss-word`, `.gloss-meta`, `.skeleton`, `.shimmer`.

- [ ] **Step 1: Add `st.set_page_config` at top (before `st.title`) and `inject_theme()`**

Replace the current `st.title(...)` line. Add config + theme:

```python
st.set_page_config(page_title="Oríkì — Indigenous Praise Poetry", layout="wide")

def inject_theme():
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Gentium+Plus:ital,wght@0,400;0,700;1,400&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root{
  --bg:#faf8f5; --surface:#ffffff; --ink:#1c1a17; --muted:#6b6459;
  --line:#e7e2da; --accent:#b5502e; --accent-weak:#f0e0d8; --ok:#1f6f52;
  --serif:'Gentium Plus',Georgia,serif; --sans:'Space Grotesk',system-ui,sans-serif;
}
html,body,[class*="css"],.stApp{background:var(--bg);color:var(--ink);font-family:var(--sans);}
.block-container{max-width:1180px;padding-top:2.2rem;}
@keyframes fadeUp{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}
@keyframes breathe{0%,100%{opacity:1;transform:scale(1);}50%{opacity:.55;transform:scale(.82);}}
@keyframes shimmer{0%{background-position:-320px 0;}100%{background-position:320px 0;}}
.masthead,.rail-block,.stage-wrap{animation:fadeUp .6s cubic-bezier(0.16,1,0.3,1) both;}
.rail-block{animation-delay:.08s;} .stage-wrap{animation-delay:.16s;}
/* Masthead */
.masthead{display:flex;justify-content:space-between;align-items:flex-end;gap:1.5rem;
  border-bottom:1px solid var(--line);padding-bottom:1.4rem;margin-bottom:1.8rem;flex-wrap:wrap;}
.kicker{font-family:var(--sans);font-size:.72rem;font-weight:600;letter-spacing:.22em;
  text-transform:uppercase;color:var(--accent);}
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
.stButton>button{font-family:var(--sans);font-weight:600;border-radius:10px;
  border:1px solid var(--accent);background:var(--accent);color:#fff;
  transition:transform .12s ease, box-shadow .2s ease;box-shadow:0 6px 16px -8px rgba(181,80,46,.6);}
.stButton>button:hover{background:#a3472a;border-color:#a3472a;}
.stButton>button:active{transform:translateY(1px);}
/* Word breakdown list */
.gloss-list{border-top:1px solid var(--line);}
.gloss-row{border-bottom:1px solid var(--line);padding:.9rem 0;}
.gloss-word{font-family:var(--serif);font-size:1.15rem;font-weight:700;color:var(--ink);}
.gloss-meta{font-family:var(--sans);font-size:.9rem;color:var(--muted);line-height:1.55;margin-top:.25rem;}
.gloss-meta .tag{color:var(--accent);font-weight:600;}
.gloss-none{font-family:var(--sans);font-size:.85rem;color:var(--muted);font-style:italic;}
.skeleton .shimmer{height:14px;border-radius:6px;margin:.5rem 0;
  background:linear-gradient(90deg,var(--line) 0%,#f3efe8 50%,var(--line) 100%);
  background-size:640px 100%;animation:shimmer 1.3s infinite linear;}
</style>
        """,
        unsafe_allow_html=True,
    )

inject_theme()
```

- [ ] **Step 2: Manual check**

Run: `streamlit run app/main.py`
Expected: background is warm stone, fonts load, existing widgets still render (layout not final yet).

- [ ] **Step 3: Commit**

```bash
git add app/main.py
git commit -m "feat: inject clay theme CSS + fonts into Oríkì UI"
```

---

### Task 3: Masthead + live status pill (replaces title + emoji captions)

**Files:**
- Modify: `app/main.py` (replace the `st.title` + `st.caption` emoji status block)

**Interfaces:**
- Consumes: `nla_client.get_languages()` → `_api_languages` (list or falsy).
- Produces: `render_masthead(api_langs) -> None`.

- [ ] **Step 1: Replace the emoji status caption block**

Remove the old `st.caption("🟢 ...")` / `st.caption("🔴 ...")` lines. Add:

```python
def render_masthead(api_langs):
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

_api_languages = nla_client.get_languages()
render_masthead(_api_languages)
```

- [ ] **Step 2: Manual check** — masthead renders left-aligned, no emojis, pill shows correct state with breathing dot.

- [ ] **Step 3: Commit**

```bash
git add app/main.py
git commit -m "feat: add Oríkì masthead + CSS status pill (drop emoji)"
```

---

### Task 4: Asymmetric composer rail + stage columns

**Files:**
- Modify: `app/main.py` (wrap controls + display in `st.columns([5,7])`)

**Interfaces:**
- Consumes: `render_masthead`, existing service functions, session state.
- Produces: `render_composer(api_langs) -> tuple[str, bool]` returning `(language, api_available)`; left rail holds language/voice/name/generate/play. Stage column calls `render_stage`.

- [ ] **Step 1: Restructure controls + display into columns**

Replace the flat control section and the `render_oriki_component(...)` call with:

```python
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
        result = get_oriki(language, name) if name else generate_smart_oriki(language)
        st.session_state['last_result'] = result

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
    render_stage(st.session_state.get('last_result', ''),
                 st.session_state.get('last_audio', b""))
    st.markdown('</div>', unsafe_allow_html=True)
```

Delete the now-duplicated old `st.selectbox`/`st.button`/`st.text_input` lines above.

- [ ] **Step 2: Manual check** — two-column asymmetric layout; generating in the rail updates the stage; collapses to one column when the window narrows.

- [ ] **Step 3: Commit**

```bash
git add app/main.py
git commit -m "feat: asymmetric composer/stage layout for Oríkì UI"
```

---

### Task 5: Rebuilt stage component (paper surface, Gentium display, underline karaoke, empty state)

**Files:**
- Modify: `app/main.py` (`render_oriki_component` → `render_stage`)

**Interfaces:**
- Consumes: `text` (str), `audio_bytes` (bytes).
- Produces: `render_stage(text, audio_bytes) -> None`.

- [ ] **Step 1: Replace `render_oriki_component` with `render_stage`**

```python
def render_stage(text, audio_bytes):
    if not text:
        components.html(
            """
<div style="font-family:'Space Grotesk',sans-serif;color:#6b6459;
  background:#fff;border:1px dashed #e7e2da;border-radius:18px;
  padding:48px 28px;text-align:center;">
  <div style="font-family:'Gentium Plus',serif;font-size:1.5rem;color:#1c1a17;margin-bottom:.4rem;">Oríkì</div>
  Your praise poem will appear here. Choose a language and press
  <em>Generate Oríkì</em>.
</div>
            """,
            height=240,
        )
        return

    safe_text = _html.escape(text)
    data_url = ''
    if audio_bytes:
        mime = 'audio/wav' if audio_bytes[:4] == b'RIFF' else 'audio/mpeg'
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
const text = `{SAFE_TEXT}`;
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
    html = html.replace('{DATA_URL}', data_url).replace('{SAFE_TEXT}', safe_text)
    components.html(html, height=460)
```

Remove the old `render_oriki_component` definition and its standalone call (now invoked from the stage column in Task 4).

- [ ] **Step 2: Manual check** — empty state shows before generating; after generating, poem renders in Gentium Plus on a paper card; playing audio sweeps a terracotta underline word-by-word; diacritics render correctly.

- [ ] **Step 3: Commit**

```bash
git add app/main.py
git commit -m "feat: editorial stage with underline karaoke + empty state"
```

---

### Task 6: Restyled Word Breakdown (divide-y list, skeleton, inline states)

**Files:**
- Modify: `app/main.py` (the `st.expander` breakdown block → `render_breakdown`)

**Interfaces:**
- Consumes: `text`, `language`, `api_langs`; `build_glossary(text, language, nla_client)` → `{rows, truncated, total_words}`; each row `{word, status, matches:[{kind, gloss, dialect_name, pos, headword}]}`.
- Produces: `render_breakdown(text, language, api_langs) -> None`.

- [ ] **Step 1: Replace the expander block with `render_breakdown` + call**

```python
def _gloss_row_html(row):
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
            ) + '</div>', unsafe_allow_html=True)
        glossary = build_glossary(text, language, nla_client)
        rows = glossary["rows"]
        html_rows = "".join(_gloss_row_html(r) for r in rows)
        slot.markdown(f'<div class="gloss-list">{html_rows}</div>', unsafe_allow_html=True)
        if glossary["truncated"]:
            st.caption(f"Showing the first {len(rows)} of {glossary['total_words']} words.")
        st.caption("Word data provided by the Nigerian Languages API (dara-ze5e.onrender.com).")


render_breakdown(st.session_state.get('last_result', ''), st.session_state.get('language', 'yoruba'), _api_languages)
```

Delete the old `if text_to_display:` expander block.

- [ ] **Step 2: Manual check** — breakdown shows a shimmer, then a hairline-divided list (no boxes); API-unavailable message inline; truncation caption when applicable.

- [ ] **Step 3: Commit**

```bash
git add app/main.py
git commit -m "feat: divide-y Word Breakdown with skeleton loader"
```

---

### Task 7: Final verification

**Files:** none (verification only)

- [ ] **Step 1: Run full test suite** — `pytest -q` → all pass.
- [ ] **Step 2: Manual end-to-end** — `streamlit run app/main.py`; generate for each of yoruba/igbo/hausa, play audio, open breakdown; confirm empty/loading/error states; confirm no emojis anywhere; confirm single-column collapse on narrow width.
- [ ] **Step 3: Commit any fixes** found during verification.

---

## Self-Review

- **Spec coverage:** masthead/status (T3), asymmetric columns (T4), Gentium display + underline karaoke + empty state (T5), divide-y breakdown + skeleton + inline error (T6), theme/fonts/palette/motion (T2), Streamlit theme (T1), states covered (T5 empty, T6 loading/error), pytest gate (T7). ✅
- **Placeholder scan:** all steps contain real code/commands. ✅
- **Type consistency:** `render_stage`, `render_masthead`, `render_composer`, `render_breakdown`, `_gloss_row_html` used consistently; session keys `last_result`/`last_audio`/`language`/`voice` preserved. ✅
