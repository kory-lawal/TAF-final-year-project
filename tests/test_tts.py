import importlib
import sys
import types


def test_tts_reads_api_key_from_streamlit_secrets(monkeypatch):
    fake_streamlit = types.ModuleType("streamlit")
    fake_streamlit.secrets = {"YARNGPT_API_KEY": "from-secrets"}
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.delenv("YARNGPT_API_KEY", raising=False)

    import app.services.tts as tts
    importlib.reload(tts)

    assert tts.API_KEY == "from-secrets"
