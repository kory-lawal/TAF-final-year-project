import random

from app.utils.loader import load_data
from app.utils.generator import generate_oriki
from app.services import nla_client


def _extract(entry):
    """Pull the oríkì text and its meaning out of an /api/praise row."""
    meta = entry.get("metadata") or {}
    text = meta.get("praise_text") or entry.get("headword") or ""
    return text, meta.get("meaning")


def get_oriki_result(language, name=None):
    """Fetch an oríkì, preferring the Nigerian Languages API.

    Returns a dict: {status, text, meaning, name, source} where status is:
      - 'found'       an oríkì was returned (from /api/praise, else local CSV)
      - 'not_found'   the API is reachable but has no oríkì for this name
      - 'unavailable' the API is down and no local oríkì could be produced

    The API (/api/praise) is the source of truth. The bundled local CSV is
    used only as a fallback when the API is unreachable, so that a network
    outage degrades gracefully instead of erroring.
    """
    if nla_client.is_api_available():
        matches = nla_client.get_praise(name=name, language=language)
        chosen = _choose(matches, name)
        if chosen is not None:
            text, meaning = _extract(chosen)
            if text:
                return {"status": "found", "text": text, "meaning": meaning,
                        "name": name, "source": "api"}
        # API reachable, but no oríkì matched — this is the "we don't have
        # an oríkì for this name" state the UI surfaces to the user.
        return {"status": "not_found", "text": None, "meaning": None,
                "name": name, "source": "api"}

    # API unreachable → fall back to the bundled local data.
    text = _local_oriki(language, name)
    if text:
        return {"status": "found", "text": text, "meaning": None,
                "name": name, "source": "local"}
    return {"status": "unavailable", "text": None, "meaning": None,
            "name": name, "source": "local"}


def _choose(matches, name):
    """Pick the best oríkì from API matches: exact name first, else the first."""
    if not matches:
        return None
    if name:
        lname = name.strip().lower()
        for m in matches:
            if str(m.get("headword") or "").strip().lower() == lname:
                return m
    return matches[0]


def _local_oriki(language, name=None):
    """Local-CSV fallback. Returns the praise text, or None if not present."""
    try:
        df = load_data(language)
    except Exception:
        return None
    if name:
        result = df[df["name"].str.lower() == name.lower()]
        return result.iloc[0]["praise_text"] if not result.empty else None
    texts = df["praise_text"].tolist()
    return random.choice(texts) if texts else None


# --- Backward-compatible local-only helpers (kept for any existing callers) ---
def get_oriki(language, name=None):
    return _local_oriki(language, name) or ""


def generate_smart_oriki(language):
    try:
        df = load_data(language)
    except Exception:
        return ""
    return generate_oriki(df["praise_text"].tolist())
