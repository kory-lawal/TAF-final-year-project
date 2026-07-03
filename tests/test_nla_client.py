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
