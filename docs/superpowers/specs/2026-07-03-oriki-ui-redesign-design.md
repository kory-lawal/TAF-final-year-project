# Oríkì UI Redesign — Design Spec

**Date:** 2026-07-03
**Branch:** feature/nla-glossary-integration
**Status:** Awaiting user approval (defaults chosen while user was away — Palette A + Gentium Plus; user to confirm)

## Goal

Redesign the presentation layer of the AI Indigenous Oríkì Generator so it reads
as an intentional, premium, culturally-grounded product suitable for a final-year
project demo — without touching the working Python backend.

The concept is **"Editorial Heritage"**: treat an Oríkì as what it is — indigenous
praise *poetry* — and present it in an editorial, gallery-like frame rather than a
generic app form.

## Constraints & Findings

- **Stack is Streamlit** (Python), not React/Next.js. The `design-taste-frontend`
  directives are applied as *philosophy* through Streamlit-native levers, not React
  components. Motion is CSS-only (which is exactly the "Fluid CSS" tier for
  `MOTION_INTENSITY: 6`).
- **Design dials:** `DESIGN_VARIANCE: 8`, `MOTION_INTENSITY: 6`, `VISUAL_DENSITY: 4`.
- **Anti-emoji policy currently violated** — status dots (`🟢`/`🔴`) and
  `Play Audio 🔊`. Redesign replaces these with CSS indicator dots and clean glyphs.
- **Diacritics are a hard functional constraint.** Yoruba/Igbo/Hausa use tone marks
  and subdots (Oríkì, ẹ, ọ, ṣ, á, à). The display font MUST render these correctly.
- **No new dependencies.** Everything ships via `.streamlit/config.toml`, a CSS
  block injected with `st.markdown(unsafe_allow_html=True)`, and the existing
  `components.html` block. Fonts load from Google Fonts via `@import`/`<link>`.

## Design Decisions

### Layout (asymmetric — VARIANCE 8)

- **Masthead** (left-aligned, not centered): kicker `INDIGENOUS PRAISE POETRY` →
  large display word **Oríkì** → one-line description. Live API-status pill top-right.
- **Two-column asymmetric body** via `st.columns([5, 7])`:
  - **Left "composer" rail** — language, voice, name, Generate button. Grouped by
    negative space + hairline dividers, not boxed cards.
  - **Right "stage"** — the generated Oríkì on a warm paper surface (the single place
    a tinted-shadow elevated card is justified), with karaoke word-highlight.
- **Word Breakdown** full-width below — a `divide-y` glossary list, no heavy boxes
  (density 4). Each word shows its definition / corpus-example matches.
- Collapses to single column on narrow viewports (Streamlit default; to be verified).

### Typography

- **Oríkì display:** **Gentium Plus** — SIL serif built for African orthographies,
  excellent tone-mark/subdot rendering, editorial warmth. Both anti-slop and the
  correct engineering choice. (Alt: Charis SIL.)
- **UI chrome:** **Space Grotesk** for labels, buttons, controls. Serif is banned on
  UI chrome per the directives; serif is reserved exclusively for the poetry.

### Color — Palette A "Clay" (single accent, saturation < 80%)

| Token | Value | Use |
|---|---|---|
| `--bg` | `#faf8f5` | warm stone page background |
| `--surface` | `#ffffff` | the Oríkì paper stage |
| `--ink` | `#1c1a17` | primary text (off-black, never `#000`) |
| `--muted` | `#6b6459` | secondary text, meta |
| `--line` | `#e7e2da` | hairline dividers / borders |
| `--accent` | `#b5502e` | terracotta — single accent |
| `--accent-weak` | `#f0e0d8` | accent tint for highlights/hover |
| `--ok` | `#1f6f52` | status "connected" dot |
| `--warn` | `#b5502e` | status "unavailable" dot (reuses accent) |

Tinted shadow on the stage: `0 20px 40px -18px rgba(28,26,23,0.18)`.

### Motion (CSS, level 6)

- Staggered fade-up on load: masthead → rail → stage (`animation-delay` cascade).
- Button `:active` tactile push: `transform: translateY(1px)`.
- Status dot "breathing" pulse (infinite, `transform`/`opacity` only).
- **Karaoke highlight upgraded** from yellow highlighter block to a smooth accent
  **underline sweep** synced to audio `timeupdate` (transform/opacity only, no layout).
- All animation on `transform`/`opacity` only (hardware-accelerated).

## Components / Files

- `app/main.py` — restructure into: `inject_theme()` (CSS block), `render_masthead()`,
  `render_status_pill()`, `render_composer()` (left rail), `render_stage()`
  (`render_oriki_component`, restyled), `render_breakdown()`. Keeps all existing
  service calls and `st.session_state` keys intact.
- `.streamlit/config.toml` — new. Base theme (colors, font, radii) so Streamlit's own
  widgets inherit the palette instead of fighting the injected CSS.
- No changes to `app/services/*` or `app/utils/*`.

## Data Flow (unchanged)

`get_oriki` / `generate_smart_oriki` → `st.session_state['last_result']` → stage
component. `text_to_speech` → `last_audio` → audio element + karaoke sync.
`build_glossary(text, language, nla_client)` → breakdown list. `nla_client.get_languages()`
→ status pill + language options.

## States (Rule 5)

- **Empty:** stage shows a composed empty state ("Your Oríkì will appear here…") not a
  blank box; breakdown hidden until text exists.
- **Loading:** breakdown uses a skeletal shimmer matching row layout (not a spinner).
- **Error:** API-unavailable message inline in the breakdown; TTS failure inline near
  the stage, matching existing copy.

## Out of Scope (YAGNI)

- No React rewrite, no API extraction.
- No changes to TTS engine, NLA client logic, or glossary logic.
- No new backgrounds/grain, no WebGL — CSS motion only.

## Testing

- Existing pytest suite must still pass (no backend changes) — `pytest`.
- Manual: run `streamlit run app/main.py`; verify diacritics render in Gentium Plus,
  karaoke underline tracks audio, empty/loading/error states, single-column collapse.
