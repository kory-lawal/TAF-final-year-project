# Oríkì × Nigerian Languages API — Word Glossary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a live "Word Breakdown / Glossary" panel to the Streamlit Oríkì app that looks up each word of a generated Oríkì against the live Nigerian Languages API, proving the API works from a real consumer.

**Architecture:** Additive layer only. Local Oríkì generation and TTS are untouched. A resilient HTTP client (`nla_client.py`) talks to the deployed API; pure logic (`oriki_glossary.py`) turns an Oríkì string + client into displayable glossary rows; `main.py` renders the panel and a live-status indicator. All network failures degrade to friendly messages — never a traceback.

**Tech Stack:** Python 3.13, Streamlit, `requests`, `pytest` (new, dev-only).

## Global Constraints

- **Additive only:** do not modify `app/services/oriki_service.py`, `app/utils/*`, `app/services/tts.py`, `app/data/*.csv`, or the Nigerian Languages API repo. `main.py` is edited but its existing generate/audio flow must keep working unchanged.
- **Never raise to the UI:** every function in `nla_client.py` returns `[]` / `None` / `False` on any error (timeouts, connection errors, non-200, bad JSON). No exception propagates to Streamlit.
- **Default API base URL:** `https://dara-ze5e.onrender.com`, overridable via env var `NLA_API_URL`.
- **Timeouts:** connect default `10`s, read default `60`s (Render free-tier cold start can take 30–50s). Env-overridable.
- **Lookup cap:** at most `NLA_MAX_LOOKUPS` (default `12`) unique words looked up per Oríkì.
- **Language keys stay lowercase** (`yoruba`/`igbo`/`hausa`) everywhere downstream, matching existing CSV filenames and TTS keys.
- **`get_entry` budget:** a metadata follow-up (`GET /api/entries/:id`) happens only for the single top word-level match per word.
- **Classification signal is `pos`:** `pos == "sentence"` → corpus example; any other `pos` → word-level dictionary entry.
- **Do not commit** `.env` or secrets. No API keys are needed (all consumed endpoints are public GETs).

---

### Task 1: Project foundation — dev deps, config, pytest wiring

**Files:**
- Create: `requirements-dev.txt`
- Create: `conftest.py` (repo root)
- Modify: `app/config.py` (currently an empty stub)
- Test: `tests/test_config.py`
- Create: `tests/__init__.py` (empty)

**Interfaces:**
- Consumes: nothing (first task).
- Produces (imported by later tasks):
  - `app.config.NLA_API_URL: str` — base URL, no trailing slash.
  - `app.config.NLA_TIMEOUT_CONNECT: float`
  - `app.config.NLA_TIMEOUT_READ: float`
  - `app.config.NLA_MAX_LOOKUPS: int`

- [ ] **Step 1: Create dev requirements**

Create `requirements-dev.txt`:

```
pytest>=8.0
```

- [ ] **Step 2: Install pytest**

Run: `python -m pip install -r requirements-dev.txt`
Expected: pytest installs successfully.

- [ ] **Step 3: Create repo-root conftest so `import app...` works under pytest**

Create `conftest.py` at the repo root:

```python
import sys
import pathlib

# Ensure the repo root is importable so `import app...` resolves in tests,
# mirroring the sys.path tweak app/main.py does at runtime.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
```

- [ ] **Step 4: Create the tests package marker**

Create `tests/__init__.py` as an empty file.

- [ ] **Step 5: Write the failing config test**

Create `tests/test_config.py`:

```python
from app import config


def test_defaults_present_and_typed():
    assert config.NLA_API_URL == "https://dara-ze5e.onrender.com"
    assert isinstance(config.NLA_TIMEOUT_CONNECT, float)
    assert isinstance(config.NLA_TIMEOUT_READ, float)
    assert config.NLA_MAX_LOOKUPS == 12


def test_base_url_has_no_trailing_slash():
    assert not config.NLA_API_URL.endswith("/")


def test_env_override(monkeypatch):
    import importlib
    monkeypatch.setenv("NLA_API_URL", "http://localhost:3000/")
    importlib.reload(config)
    assert config.NLA_API_URL == "http://localhost:3000"  # slash stripped
    monkeypatch.delenv("NLA_API_URL")
    importlib.reload(config)
```

- [ ] **Step 6: Run the test to verify it fails**

Run: `python -m pytest tests/test_config.py -v`
Expected: FAIL (config attributes do not exist — `AttributeError`).

- [ ] **Step 7: Implement `app/config.py`**

Replace the empty `app/config.py` with:

```python
import os

# Base URL of the deployed Nigerian Languages API (Render). Env-overridable.
NLA_API_URL = os.environ.get(
    "NLA_API_URL", "https://dara-ze5e.onrender.com"
).rstrip("/")

# Timeouts (seconds). Read timeout is generous because Render free-tier
# cold start can take 30-50s on the first request after idle.
NLA_TIMEOUT_CONNECT = float(os.environ.get("NLA_TIMEOUT_CONNECT", "10"))
NLA_TIMEOUT_READ = float(os.environ.get("NLA_TIMEOUT_READ", "60"))

# Cap unique-word lookups per Oríkì so we never hammer the API.
NLA_MAX_LOOKUPS = int(os.environ.get("NLA_MAX_LOOKUPS", "12"))
```

- [ ] **Step 8: Run the test to verify it passes**

Run: `python -m pytest tests/test_config.py -v`
Expected: PASS (3 tests).

- [ ] **Step 9: Commit**

```bash
git add requirements-dev.txt conftest.py tests/__init__.py tests/test_config.py app/config.py
git commit -m "feat: add NLA config + pytest foundation"
```

---

### Task 2: Resilient API client (`nla_client.py`)

**Files:**
- Create: `app/services/nla_client.py`
- Test: `tests/test_nla_client.py`

**Interfaces:**
- Consumes: `app.config.NLA_API_URL`, `NLA_TIMEOUT_CONNECT`, `NLA_TIMEOUT_READ`.
- Produces (used by Task 3 and Task 4):
  - `get_languages() -> list[dict]` — `[]` on failure.
  - `search(q: str, language: str | None = None) -> list[dict]` — `[]` on failure/empty `q`; filters by `language_name` (case-insensitive) client-side when `language` given.
  - `get_entry(entry_id) -> dict | None` — `None` on failure.
  - `is_api_available() -> bool`.
  - `clear_cache() -> None` — resets the in-memory cache (used by tests).
  - Module attribute `_session` (a `requests.Session`) — monkeypatched by tests.

- [ ] **Step 1: Write the failing client tests**

Create `tests/test_nla_client.py`:

```python
import requests
import pytest

from app.services import nla_client


class FakeResp:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json = json_data

    def json(self):
        if isinstance(self._json, Exception):
            raise self._json
        return self._json


class FakeSession:
    """Returns queued responses, or raises a queued exception, per .get call."""
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params, timeout))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


@pytest.fixture(autouse=True)
def _clear():
    nla_client.clear_cache()
    yield
    nla_client.clear_cache()


def _install(monkeypatch, outcomes):
    session = FakeSession(outcomes)
    monkeypatch.setattr(nla_client, "_session", session)
    return session


def test_get_languages_success(monkeypatch):
    _install(monkeypatch, [FakeResp(200, [{"name": "Yoruba"}])])
    assert nla_client.get_languages() == [{"name": "Yoruba"}]


def test_get_languages_connection_error_returns_empty(monkeypatch):
    _install(monkeypatch, [requests.RequestException("boom")])
    assert nla_client.get_languages() == []


def test_get_languages_non_200_returns_empty(monkeypatch):
    _install(monkeypatch, [FakeResp(500, {"error": "db"})])
    assert nla_client.get_languages() == []


def test_get_languages_bad_json_returns_empty(monkeypatch):
    _install(monkeypatch, [FakeResp(200, ValueError("not json"))])
    assert nla_client.get_languages() == []


def test_search_empty_query_short_circuits(monkeypatch):
    session = _install(monkeypatch, [])
    assert nla_client.search("") == []
    assert session.calls == []  # no network call


def test_search_filters_by_language(monkeypatch):
    rows = [
        {"headword": "a", "language_name": "Igbo"},
        {"headword": "b", "language_name": "Yoruba"},
    ]
    _install(monkeypatch, [FakeResp(200, rows)])
    out = nla_client.search("x", language="igbo")
    assert out == [{"headword": "a", "language_name": "Igbo"}]


def test_search_caches_by_query(monkeypatch):
    session = _install(monkeypatch, [FakeResp(200, [{"language_name": "Igbo"}])])
    nla_client.search("akwa")
    nla_client.search("akwa")
    assert len(session.calls) == 1  # second call served from cache


def test_get_entry_success_and_failure(monkeypatch):
    _install(monkeypatch, [FakeResp(200, {"entry_id": 5, "metadata": {}})])
    assert nla_client.get_entry(5)["entry_id"] == 5
    nla_client.clear_cache()
    _install(monkeypatch, [FakeResp(404, {"error": "nope"})])
    assert nla_client.get_entry(999) is None


def test_is_api_available(monkeypatch):
    _install(monkeypatch, [FakeResp(200, [{"name": "Yoruba"}])])
    assert nla_client.is_api_available() is True
    nla_client.clear_cache()
    _install(monkeypatch, [requests.RequestException("down")])
    assert nla_client.is_api_available() is False
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_nla_client.py -v`
Expected: FAIL (module `app.services.nla_client` does not exist — `ModuleNotFoundError`).

- [ ] **Step 3: Implement `app/services/nla_client.py`**

Create `app/services/nla_client.py`:

```python
import requests

from app.config import NLA_API_URL, NLA_TIMEOUT_CONNECT, NLA_TIMEOUT_READ

# Module-level session (reused across calls) and a simple in-memory cache.
# Tests monkeypatch `_session`; do not inline requests.get elsewhere.
_session = requests.Session()
_cache = {}


def clear_cache():
    _cache.clear()


def _timeout():
    return (NLA_TIMEOUT_CONNECT, NLA_TIMEOUT_READ)


def _get_json(path, params=None):
    """GET NLA_API_URL+path, return parsed JSON or None. Never raises."""
    key = (path, tuple(sorted((params or {}).items())))
    if key in _cache:
        return _cache[key]
    try:
        resp = _session.get(
            f"{NLA_API_URL}{path}", params=params, timeout=_timeout()
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
    except (requests.RequestException, ValueError):
        return None
    _cache[key] = data  # cache only successful responses
    return data


def get_languages():
    data = _get_json("/api/languages")
    return data if isinstance(data, list) else []


def search(q, language=None):
    if not q:
        return []
    data = _get_json("/api/search", {"q": q})
    if not isinstance(data, list):
        return []
    if language:
        lang = language.lower()
        data = [
            r for r in data
            if str(r.get("language_name", "")).lower() == lang
        ]
    return data


def get_entry(entry_id):
    data = _get_json(f"/api/entries/{entry_id}")
    return data if isinstance(data, dict) else None


def is_api_available():
    return len(get_languages()) > 0
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_nla_client.py -v`
Expected: PASS (9 tests).

- [ ] **Step 5: Commit**

```bash
git add app/services/nla_client.py tests/test_nla_client.py
git commit -m "feat: add resilient Nigerian Languages API client"
```

---

### Task 3: Glossary logic (`oriki_glossary.py`)

**Files:**
- Create: `app/services/oriki_glossary.py`
- Test: `tests/test_oriki_glossary.py`

**Interfaces:**
- Consumes: `app.config.NLA_MAX_LOOKUPS`; a `client` object exposing `search(q, language)` and `get_entry(entry_id)` (satisfied by `nla_client` or a fake).
- Produces (used by Task 4):
  - `tokenize(text: str) -> list[str]` — whitespace split, strip surrounding punctuation, lowercase, drop empties, dedupe preserving order.
  - `build_glossary(text, language, client, max_lookups=None) -> dict` — returns `{"rows": list[dict], "truncated": bool, "total_words": int}`. Each row: `{"word": str, "status": "found"|"not_found", "matches": list[dict]}`. Each match: `{"headword", "pos", "dialect_name", "language_name", "kind": "definition"|"corpus_example", "gloss": str|None}`.
  - `language_options(api_languages: list[dict], fallback: list[str]) -> list[str]` — lowercased language names from the API, or `fallback` if none.

- [ ] **Step 1: Write the failing glossary tests**

Create `tests/test_oriki_glossary.py`:

```python
from app.services import oriki_glossary as og


class FakeClient:
    def __init__(self, search_map, entry_map=None):
        self.search_map = search_map
        self.entry_map = entry_map or {}
        self.search_calls = []
        self.entry_calls = []

    def search(self, q, language=None):
        self.search_calls.append((q, language))
        return self.search_map.get(q, [])

    def get_entry(self, entry_id):
        self.entry_calls.append(entry_id)
        return self.entry_map.get(entry_id)


def test_tokenize_strips_punctuation_lowercases_dedupes():
    assert og.tokenize("Ọmọ, ọmọ! akin.") == ["ọmọ", "akin"]


def test_tokenize_handles_empty():
    assert og.tokenize("") == []
    assert og.tokenize("   ") == []


def test_language_options_from_api():
    api = [{"name": "Yoruba"}, {"name": "Igbo"}, {"name": "Hausa"}]
    assert og.language_options(api, ["x"]) == ["yoruba", "igbo", "hausa"]


def test_language_options_fallback_when_empty():
    assert og.language_options([], ["yoruba", "igbo"]) == ["yoruba", "igbo"]


def test_word_level_match_produces_definition():
    client = FakeClient(
        search_map={"akwa": [
            {"entry_id": 5, "headword": "akwa", "pos": "noun",
             "dialect_name": "Central Igbo", "language_name": "Igbo"}
        ]},
        entry_map={5: {"metadata": {"definitions": ["cloth", "egg"]}}},
    )
    result = og.build_glossary("akwa", "igbo", client)
    row = result["rows"][0]
    assert row["status"] == "found"
    match = row["matches"][0]
    assert match["kind"] == "definition"
    assert match["gloss"] == "cloth; egg"
    assert client.entry_calls == [5]  # one metadata follow-up


def test_sentence_match_produces_corpus_example_without_get_entry():
    client = FakeClient(
        search_map={"omo": [
            {"entry_id": 9, "headword": "aase baba mi omo iya mi",
             "pos": "sentence", "dialect_name": "Standard Yoruba",
             "language_name": "Yoruba"}
        ]},
    )
    result = og.build_glossary("omo", "yoruba", client)
    match = result["rows"][0]["matches"][0]
    assert match["kind"] == "corpus_example"
    assert "aase baba mi" in match["gloss"]
    assert client.entry_calls == []  # sentences never trigger get_entry


def test_not_found_word():
    client = FakeClient(search_map={})
    result = og.build_glossary("zzz", "igbo", client)
    assert result["rows"][0]["status"] == "not_found"
    assert result["rows"][0]["matches"] == []


def test_only_one_get_entry_per_word():
    client = FakeClient(
        search_map={"x": [
            {"entry_id": 1, "headword": "x", "pos": "noun",
             "dialect_name": "d", "language_name": "Igbo"},
            {"entry_id": 2, "headword": "x", "pos": "verb",
             "dialect_name": "d", "language_name": "Igbo"},
        ]},
        entry_map={1: {"metadata": {"definitions": ["one"]}},
                   2: {"metadata": {"definitions": ["two"]}}},
    )
    result = og.build_glossary("x", "igbo", client)
    assert client.entry_calls == [1]  # only the top word-level match
    glosses = [m["gloss"] for m in result["rows"][0]["matches"]]
    assert glosses[0] == "one"
    assert glosses[1] is None


def test_respects_max_lookups_and_flags_truncation():
    client = FakeClient(search_map={})
    text = "a b c d e"
    result = og.build_glossary(text, "igbo", client, max_lookups=2)
    assert len(result["rows"]) == 2
    assert result["truncated"] is True
    assert result["total_words"] == 5
    assert client.search_calls == [("a", "igbo"), ("b", "igbo")]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_oriki_glossary.py -v`
Expected: FAIL (module `app.services.oriki_glossary` does not exist).

- [ ] **Step 3: Implement `app/services/oriki_glossary.py`**

Create `app/services/oriki_glossary.py`:

```python
import re

from app.config import NLA_MAX_LOOKUPS

# Strip leading/trailing non-word characters. Unicode-aware, so Yoruba/Igbo
# tone-marked letters inside a word are preserved.
_EDGE_PUNCT = re.compile(r"^\W+|\W+$", re.UNICODE)

_GLOSS_MAX_CHARS = 160
_MAX_MATCHES_PER_WORD = 3


def tokenize(text):
    tokens = []
    seen = set()
    for raw in (text or "").split():
        word = _EDGE_PUNCT.sub("", raw).lower()
        if not word or word in seen:
            continue
        seen.add(word)
        tokens.append(word)
    return tokens


def language_options(api_languages, fallback):
    names = [
        str(lang.get("name", "")).lower()
        for lang in api_languages
        if lang.get("name")
    ]
    names = [n for n in names if n]
    return names or list(fallback)


def _truncate(text):
    text = str(text or "")
    if len(text) <= _GLOSS_MAX_CHARS:
        return text
    return text[:_GLOSS_MAX_CHARS].rstrip() + "…"


def _extract_definition(entry):
    if not entry:
        return None
    meta = entry.get("metadata") or {}
    definitions = meta.get("definitions") or []
    if definitions:
        return "; ".join(str(d) for d in definitions)
    english = meta.get("english_translation")
    return str(english) if english else None


def _classify(matches, client):
    out = []
    definition_fetched = False
    for match in matches[:_MAX_MATCHES_PER_WORD]:
        pos = str(match.get("pos", ""))
        row = {
            "headword": match.get("headword"),
            "pos": pos,
            "dialect_name": match.get("dialect_name"),
            "language_name": match.get("language_name"),
        }
        if pos == "sentence":
            row["kind"] = "corpus_example"
            row["gloss"] = _truncate(match.get("headword", ""))
        else:
            row["kind"] = "definition"
            gloss = None
            if not definition_fetched:
                entry = client.get_entry(match.get("entry_id"))
                gloss = _extract_definition(entry)
                definition_fetched = True
            row["gloss"] = gloss
        out.append(row)
    return out


def build_glossary(text, language, client, max_lookups=None):
    if max_lookups is None:
        max_lookups = NLA_MAX_LOOKUPS
    words = tokenize(text)
    truncated = len(words) > max_lookups
    selected = words[:max_lookups]
    rows = []
    for word in selected:
        matches = client.search(word, language)
        if matches:
            rows.append({
                "word": word,
                "status": "found",
                "matches": _classify(matches, client),
            })
        else:
            rows.append({"word": word, "status": "not_found", "matches": []})
    return {"rows": rows, "truncated": truncated, "total_words": len(words)}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_oriki_glossary.py -v`
Expected: PASS (9 tests).

- [ ] **Step 5: Run the whole suite**

Run: `python -m pytest -v`
Expected: PASS (all tests from Tasks 1–3).

- [ ] **Step 6: Commit**

```bash
git add app/services/oriki_glossary.py tests/test_oriki_glossary.py
git commit -m "feat: add Oríkì glossary logic (tokenize + build_glossary)"
```

---

### Task 4: Wire the glossary into the Streamlit UI (`main.py`)

**Files:**
- Modify: `app/main.py`
- Test: manual (Streamlit UI) + a syntax-check command.

**Interfaces:**
- Consumes: `app.services.nla_client` (`get_languages`, `search`, `get_entry`, `is_api_available`), `app.services.oriki_glossary` (`build_glossary`, `language_options`).
- Produces: no new importable API (UI only).

- [ ] **Step 1: Add the new imports**

In `app/main.py`, just below the existing import block (after the line
`from app.services.tts import text_to_speech, get_voice_candidates, is_yarngpt_api_available`),
add:

```python
from app.services import nla_client
from app.services.oriki_glossary import build_glossary, language_options
```

- [ ] **Step 2: Add the live-status indicator and drive the language dropdown from the API**

In `app/main.py`, replace this existing block:

```python
# Short sample phrases per language used for accent/voice preview
language = st.selectbox("Select Language", ["yoruba", "igbo", "hausa"], key='language')
```

with:

```python
# Live connection status to the Nigerian Languages API (visible proof).
_api_languages = nla_client.get_languages()
if _api_languages:
    st.caption("🟢 Connected to the Nigerian Languages API")
else:
    st.caption("🔴 Nigerian Languages API unavailable — using local data only")

# Language dropdown driven live from the API, with a local fallback.
_lang_choices = language_options(_api_languages, ["yoruba", "igbo", "hausa"])
language = st.selectbox("Select Language", _lang_choices, key='language')
```

- [ ] **Step 3: Add the Word Breakdown panel**

In `app/main.py`, immediately **after** this existing line near the end:

```python
render_oriki_component(text_to_display, audio_bytes)
```

add:

```python
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
```

- [ ] **Step 4: Syntax-check the edited file**

Run: `python -c "import ast; ast.parse(open('app/main.py', encoding='utf-8').read()); print('OK')"`
Expected: prints `OK` (no SyntaxError).

- [ ] **Step 5: Confirm the full test suite still passes**

Run: `python -m pytest -v`
Expected: PASS (all Task 1–3 tests; Task 4 has no unit tests).

- [ ] **Step 6: Manual UI verification**

Run: `python -m streamlit run app/main.py`
Then in the browser:
1. Confirm the top shows **🟢 Connected to the Nigerian Languages API**
   (first load may take up to ~60s while Render cold-starts).
2. Select **igbo**, leave name blank, click **Generate Oríkì**.
3. Open **Word breakdown** — confirm at least one word shows a
   _definition_ line with dialect/pos and a gloss.
4. Select **yoruba**, generate again — confirm words show _corpus example_
   lines (real sentences), clearly labeled.
5. Confirm audio still plays (existing flow unaffected).

- [ ] **Step 7: Offline-degradation verification**

Run: `NLA_API_URL=http://127.0.0.1:9 python -m streamlit run app/main.py`
(An unreachable URL simulates the API being down.)
Confirm:
1. Top shows **🔴 Nigerian Languages API unavailable**.
2. Language dropdown still lists yoruba/igbo/hausa (fallback).
3. Generating an Oríkì still works; the Word breakdown expander shows the
   friendly "unavailable" notice — **no traceback anywhere**.

- [ ] **Step 8: Commit**

```bash
git add app/main.py
git commit -m "feat: add live Word Breakdown panel + API status to Oríkì UI"
```

---

## Manual live-API smoke reference (not a CI test)

Depends on Render uptime, so run by hand when validating end-to-end:

```bash
curl -s "https://dara-ze5e.onrender.com/api/languages"
curl -s "https://dara-ze5e.onrender.com/api/search?q=akwa"
```

Expected: 3 languages; a JSON array of entries. (First call may be slow
due to cold start.)

## Self-Review

- **Spec coverage:**
  - §4.1 config → Task 1. §4.2 client → Task 2. §4.3 glossary logic → Task 3. §4.4 UI (live dropdown, status, breakdown panel, credit) → Task 4. §4.5 translation stub left empty → untouched (Global Constraints forbid modifying it; no task needed).
  - §5 error handling → Task 2 (client resilience tests), Task 4 Step 7 (degradation), edge case truncation → Task 3 `truncated` flag + Task 4 Step 3 caption.
  - §6 testing → Tasks 2–3 unit tests + Task 4 manual steps + live-smoke reference.
  - §8 deferred translation → out of scope, `translation.py` untouched.
  - §9 success criteria → Task 4 Steps 6–7.
- **Placeholder scan:** no TBD/TODO/"handle edge cases"; every code step has full code.
- **Type consistency:** `build_glossary` returns `{"rows","truncated","total_words"}` in Task 3 and is consumed with those exact keys in Task 4 Step 3. `language_options(api, fallback)` signature matches between Task 3 def and Task 4 Step 2 call. `nla_client` function names (`get_languages`/`search`/`get_entry`/`is_api_available`) consistent across Tasks 2 and 4.
