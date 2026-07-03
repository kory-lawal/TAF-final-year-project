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
