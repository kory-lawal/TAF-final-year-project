import copy
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
    """GET NLA_API_URL+path, return parsed JSON (a fresh copy) or None. Never raises."""
    key = (path, tuple(sorted((params or {}).items())))
    if key in _cache:
        return copy.deepcopy(_cache[key])
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
    return copy.deepcopy(data)


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
