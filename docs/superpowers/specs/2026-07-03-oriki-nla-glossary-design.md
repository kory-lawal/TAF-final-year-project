# Oríkì App × Nigerian Languages API — Word Glossary Integration

**Date:** 2026-07-03
**Status:** Approved for implementation planning
**Repo:** `TAF-final-year-project` (the AI Indigenous Oríkì Generator — Streamlit app)

## 1. Goal

Connect the Oríkì generator (a Streamlit app that currently reads only
local CSVs) to the **Nigerian Languages API** — a separately-owned
final-year project — so that generating an Oríkì makes live calls to
that API. This serves two purposes:

1. **Completes the Oríkì app** by giving it a real linguistic data
   layer instead of dead local CSVs.
2. **Proves the Nigerian Languages API works** end-to-end from a real
   consumer application.

The centerpiece is a **Word Breakdown / Glossary** panel: after an
Oríkì is generated, each meaningful word is looked up in the live API
and shown with its dialect, part of speech, and definition / corpus
usage.

**Non-goal for this phase:** translation between languages. See §8.

## 2. The two systems

### 2.1 Oríkì app (this repo — the consumer)

- **Streamlit** app: `app/main.py`. Select language (Yoruba / Igbo /
  Hausa), optionally enter a name, generate a praise poem, play audio.
- Data source today: **local CSVs** in `app/data/*.csv` with columns
  `id, name, gender, language, praise_text, meaning, category, keywords`.
- Generation: `app/services/oriki_service.py` (name lookup or random
  stitch via `app/utils/generator.py`).
- Audio: `app/services/tts.py` (YarnGPT TTS, gTTS fallback).
- The UI already tokenizes the Oríkì into words for the audio-highlight
  feature — a natural hook for per-word lookups.
- `app/config.py` and `app/services/translation.py` are currently
  **empty stub files**.

### 2.2 Nigerian Languages API (external — the provider)

- **Node/Express + PostgreSQL** (DB on Railway; API server deployed on
  **Render**). Swagger UI at `/api-docs`.
- **Deployed base URL (verified live):** `https://dara-ze5e.onrender.com`
- Data model: `languages → dialects → entries → metadata(jsonb)`,
  ~4,500 real entries.
- Endpoints consumed by this integration (all GET, no auth required):
  - `GET /api/languages` → `[{language_id, name, iso_code}]`
    (Yoruba/`yor`, Igbo/`ibo`, Hausa/`hau`).
  - `GET /api/search?q=<substring>` → array of entries, each
    `{entry_id, headword, pos, dialect_id, dialect_name, language_name}`.
    Case-insensitive substring (`ILIKE '%q%'`) match on `headword`.
  - `GET /api/entries/:id` → single entry **with** `metadata` (jsonb),
    e.g. `{... , metadata: {source, definitions:[...], examples:[...],
    english_translation, dialect_variants:[...]}}`.
- Write endpoints (`POST/PATCH/DELETE`) exist but are **out of scope**
  (this integration is read-only).

### 2.3 Data reality that shapes the design

- **Igbo** entries (source `IgboAPI`) are **word-level** with English
  `definitions` in metadata — true dictionary glosses.
- **Yoruba** entries (source `YorùLect`) are **sentence-level** with an
  `english_translation` in metadata.
- **Hausa** entries (sources `VOA Hausa`, `NaijaSenti`) are
  **sentence/tweet-level** with no translation metadata.
- Because `search` is a substring match, a single Yoruba/Hausa word
  typically matches **whole sentences containing it** — authentic
  corpus usage rather than a one-word definition. The UI must present
  this honestly (see §5.3).

## 3. Design principles

- **Additive only.** Local Oríkì generation and TTS are not modified.
  The API layer is added alongside; if the API is unreachable, the app
  behaves exactly as it does today.
- **Never crash on the network.** Every API call is wrapped so failures
  degrade to a friendly message, never a Streamlit traceback.
- **Cold-start aware.** Render free tier spins down after inactivity;
  the first request can take 30–50s. The client uses a generous timeout
  and the UI shows a loading state.
- **Visible proof.** A "Powered by the Nigerian Languages API" credit
  and a live reachability indicator make the connection demonstrable.

## 4. Components

### 4.1 `app/config.py` (fill the empty stub)

Central configuration read from environment with safe defaults:

```python
import os

NLA_API_URL = os.environ.get(
    "NLA_API_URL", "https://dara-ze5e.onrender.com"
).rstrip("/")

# Generous because Render free-tier cold start can take ~30-50s.
NLA_TIMEOUT_CONNECT = float(os.environ.get("NLA_TIMEOUT_CONNECT", "10"))
NLA_TIMEOUT_READ = float(os.environ.get("NLA_TIMEOUT_READ", "60"))

# Cap lookups per Oríkì so we never hammer the API.
NLA_MAX_LOOKUPS = int(os.environ.get("NLA_MAX_LOOKUPS", "12"))
```

### 4.2 `app/services/nla_client.py` (new)

A thin, dependency-light (`requests`) HTTP client. **Public surface:**

- `get_languages() -> list[dict]`
  Calls `GET /api/languages`. On any failure returns `[]`.
- `search(q: str, language: str | None = None) -> list[dict]`
  Calls `GET /api/search?q=<q>`. Because the API's `/search` has no
  server-side language filter, when `language` is given the client
  filters the returned rows by `language_name` (case-insensitive)
  client-side. On any failure returns `[]`.
- `get_entry(entry_id: int) -> dict | None`
  Calls `GET /api/entries/:id` (used to fetch `metadata`). On failure
  returns `None`.
- `is_api_available() -> bool`
  Lightweight reachability check (a cached `get_languages()` truthiness)
  used to drive the status indicator.

**Behavior:**

- Uses a module-level `requests.Session`.
- Timeouts: `(NLA_TIMEOUT_CONNECT, NLA_TIMEOUT_READ)` tuple on every
  call.
- **Caching:** in-memory dict cache keyed by the request (languages
  cached once; each `search(q, language)` and `get_entry(id)` cached by
  argument) so repeated words / re-renders don't re-hit the API within a
  session. A Streamlit `@st.cache_data` wrapper is acceptable as long as
  the underlying function still swallows errors.
- **Error posture:** catches `requests.RequestException` (timeouts,
  connection errors) and non-2xx responses; logs to Streamlit only via
  return values, never raises.

### 4.3 `app/services/oriki_glossary.py` (new)

Pure logic that turns an Oríkì string into a list of glossary rows,
independent of Streamlit so it is unit-testable.

- `tokenize(text: str) -> list[str]`
  Splits on whitespace, strips punctuation, lowercases, drops empties
  and pure-punctuation tokens, de-duplicates preserving order.
- `build_glossary(text, language, client, max_lookups) -> list[dict]`
  For up to `max_lookups` unique tokens, calls `client.search(word,
  language)`. For each token produces a row:
  ```python
  {
    "word": "omo",
    "status": "found" | "not_found",
    "matches": [
      {
        "headword": ...,
        "pos": ...,
        "dialect_name": ...,
        "language_name": ...,
        "kind": "definition" | "corpus_example",
        "gloss": <definition string or the matching sentence>,
      },
      ...
    ],
  }
  ```
  - **Classification signal is `pos`:** a match with `pos == "sentence"`
    is a corpus example; any other `pos` (e.g. `noun`, `NNC`, `DEM`) is
    a word-level dictionary entry. This is known from the `search`
    response alone — no extra call needed to decide.
  - "definition" `kind` for word-level matches (`pos != "sentence"`):
    read the metadata `definitions` array via a `get_entry` follow-up.
    Done only for the top word-level match per word, to bound calls. If
    metadata has no usable `definitions`, fall back to showing headword
    + pos with no gloss.
  - "corpus_example" `kind` when the match is a sentence
    (`pos == "sentence"`) containing the word (Yoruba/Hausa case):
    `gloss` is the matched `headword` (sentence), truncated for display.
    No `get_entry` follow-up.
  - Keep at most the top few matches per word (e.g. 3) to keep the panel
    readable.

**Call-budget rule:** `search` is one call per unique word (capped by
`NLA_MAX_LOOKUPS`). A `get_entry` metadata follow-up happens only for
the single best match of each *word-level* hit, so total calls per Oríkì
stay bounded and predictable.

### 4.4 `app/main.py` (edit — local flow untouched)

Additions, in order:

1. **Live language dropdown.** On load, call
   `nla_client.get_languages()`. If non-empty, build the selectbox from
   the returned language names (lowercased to match existing CSV/TTS
   keys `yoruba/igbo/hausa`). If empty (API down), fall back to the
   current hardcoded `["yoruba", "igbo", "hausa"]`. The rest of the app
   keeps using the lowercased language string exactly as today, so
   `oriki_service` and `tts` are unaffected.
2. **Reachability indicator.** A small caption near the top:
   `🟢 Connected to Nigerian Languages API` /
   `🔴 Nigerian Languages API unavailable — using local data only`.
3. **Word Breakdown panel.** Rendered under the generated Oríkì
   (after `st.session_state['last_result']` is set). Behind an
   expander titled **"Word breakdown (powered by the Nigerian Languages
   API)"**. Shows a spinner while building (cold-start friendly). For
   each glossary row: the word, and its matches as
   dialect · POS · gloss. Words with no match show "no dictionary/corpus
   match". If the API is unreachable, the expander body shows a friendly
   notice instead of erroring.
4. **Data-source credit** in the panel footer:
   *"Word data provided by the Nigerian Languages API
   (dara-ze5e.onrender.com)."*

### 4.5 `app/services/translation.py`

Left as an **empty stub** with a docstring noting cross-lingual word
rendering is a deferred Phase 2 (see §8). No behavior this phase.

## 5. Error handling & edge cases

1. **API cold start / timeout.** Generous read timeout (60s) + spinner.
   If it still times out, the panel shows "the language API is waking
   up or unreachable — try again in a moment," app stays usable.
2. **API returns empty for a word.** Row marked `not_found`; displayed
   as "no dictionary/corpus match."
3. **API entirely down at page load.** Language dropdown falls back to
   hardcoded list; status shows red; breakdown expander explains the
   feature needs the API. Generation + audio still work.
4. **Very long Oríkì / many words.** Bounded by `NLA_MAX_LOOKUPS`; panel
   notes when it truncated ("showing first N words").
5. **Punctuation / tonal marks.** Tokenizer strips surrounding
   punctuation but preserves in-word diacritics (Yoruba/Igbo tone
   marks) since the API stores and matches them.
6. **Substring false positives** (Yoruba/Hausa word matching unrelated
   sentences). Accepted and labeled as "corpus example," not
   "definition," so it's never presented as an authoritative gloss.

## 6. Testing

- **Unit (no network):** `tokenize` (punctuation, dedup, diacritics),
  and `build_glossary` against a **fake client** returning canned
  responses — asserts row shapes, `definition` vs `corpus_example`
  classification, and the call-budget cap.
- **Client resilience:** `nla_client` functions return `[]`/`None` (not
  raise) when the session raises `RequestException` or returns non-2xx
  (simulate with a monkeypatched session).
- **Live smoke (manual, documented):** with the real deployed URL,
  `get_languages()` returns 3 languages; `search("akwa","igbo")` returns
  Igbo rows; an Igbo word resolves to a `definition` gloss. Recorded in
  the plan as a manual verification step (not a CI test, to avoid
  depending on Render uptime).

## 7. Out of scope (this phase)

- Any write to the API (`POST/PATCH/DELETE`).
- Changes to the Nigerian Languages API repo itself.
- Changes to local Oríkì generation, the CSV data, or TTS.
- Translation / cross-lingual Oríkì rendering (§8).
- Browsing the full corpus (dialects browser, full-repository search).

## 8. Deferred: Phase 2 — cross-lingual word rendering

Recorded so the empty `translation.py` has a clear future. The API is a
dictionary/corpus, not a translator, so a future "render this Oríkì in
another language" feature would be an **English-pivot dictionary gloss**:
take the Oríkì's English `meaning` (already in the local CSV) → extract
keywords → look them up in the API's target-language entries (strongest
for Igbo word-level definitions) → assemble a labeled word-level
rendering. Explicitly **not** fluent machine translation. Out of scope
until the glossary phase ships and is validated.

## 9. Success criteria

- Selecting a language and generating an Oríkì shows a Word Breakdown
  panel populated from live calls to `https://dara-ze5e.onrender.com`.
- Igbo words display real dictionary definitions; Yoruba/Hausa words
  display authentic corpus examples, clearly labeled.
- With the API unreachable, the app still generates Oríkì and plays
  audio; the panel and status degrade gracefully with no traceback.
- The connection is visible to a demo observer (status indicator + data
  credit), providing the proof that the Nigerian Languages API works
  from a real consumer app.
