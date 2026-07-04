import os


def _get_setting(name, default=None):
    """Return a value from Streamlit secrets, then environment variables, then a default."""
    try:
        import streamlit as st
    except Exception:
        st = None

    if st is not None:
        try:
            secrets = getattr(st, "secrets", None)
            if secrets:
                value = secrets.get(name)
                if value not in (None, ""):
                    return value
        except Exception:
            pass

    value = os.environ.get(name)
    if value not in (None, ""):
        return value
    return default


# Base URL of the deployed Nigerian Languages API (Render). Env-overridable.
NLA_API_URL = _get_setting(
    "NLA_API_URL", "https://dara-ze5e.onrender.com"
).rstrip("/")

# Timeouts (seconds). Read timeout is generous because Render free-tier
# cold start can take 30-50s on the first request after idle.
NLA_TIMEOUT_CONNECT = float(_get_setting("NLA_TIMEOUT_CONNECT", "10"))
NLA_TIMEOUT_READ = float(_get_setting("NLA_TIMEOUT_READ", "60"))

# Cap unique-word lookups per Oríkì so we never hammer the API.
NLA_MAX_LOOKUPS = int(_get_setting("NLA_MAX_LOOKUPS", "12"))
