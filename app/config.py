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
