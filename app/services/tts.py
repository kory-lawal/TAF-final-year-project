import os
import requests
from pathlib import Path

# Load .env during development so local API key is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv not installed or .env not present; environment variables may be set elsewhere
    pass

# Use environment variable for API key so secrets are not in source
API_KEY = os.environ.get('YARNGPT_API_KEY')
# Allow overriding the TTS endpoint (tools use YARNGPT_TTS_URL)
API_URL = os.environ.get('YARNGPT_TTS_URL', 'https://yarngpt.ai/api/v1/tts')

# Top-level voice candidates and language codes (editable)
VOICE_CANDIDATES = {
    'yoruba': ['Idera', 'Iya', 'Yoruba'],
    'igbo': ['Ijeoma', 'Chinedu', 'Igbo'],
    'hausa': ['Hauwa', 'Hausa']
}

# language code hints (ISO-ish)
LANG_CODES = {
    'yoruba': 'yo',
    'igbo': 'ig',
    'hausa': 'ha'
}

def _yarngpt_tts(text, language, voice=None):
    """Call YarnGPT TTS endpoint. Returns bytes on success, else None."""
    diagnostics_path = Path(__file__).resolve().parents[1] / 'last_tts_payload.json'

    # If no API key, write diagnostic and bail so callers can fallback.
    if not API_KEY:
        try:
            import json
            diagnostics_path.write_text(json.dumps({
                'error': 'missing_api_key',
                'attempted_text': text,
                'language': language,
                'voice': voice
            }))
        except Exception:
            pass
        return None

    url = API_URL

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/octet-stream",
    }




    # Build attempt payloads prioritizing explicit voice if provided,
    # then voice candidates, then language codes.
    attempts = []

    # If an explicit voice is provided, try multiple common payload keys
    # (some TTS APIs expect 'speaker' or 'voice_name' etc.). Also try
    # combining voice fields with language variants ('language','lang','locale').
    alt_voice_keys = ["voice", "speaker", "voice_name", "speaker_id"]
    alt_lang_keys = ["language", "lang", "locale"]

    def add_payload(text, voice_val=None, lang_val=None):
        p = {"text": text}
        if voice_val:
            # add one of the voice keys at a time to form distinct payloads
            for k in alt_voice_keys:
                payload = p.copy()
                payload[k] = voice_val
                if lang_val:
                    payload.update(lang_val)
                attempts.append(payload)
        else:
            payload = p.copy()
            if lang_val:
                payload.update(lang_val)
            attempts.append(payload)

    # try explicit voice first (use the passed voice as-is)
    if voice:
        code = LANG_CODES.get(language.lower())
        lang_variants = []
        if code:
            for lk in alt_lang_keys:
                lang_variants.append({lk: code})
        # also include language name variants
        for lk in alt_lang_keys:
            lang_variants.append({lk: language})

        # add payloads for explicit voice + each language variant (and voice-only)
        add_payload(text, voice_val=voice, lang_val=None)
        for lv in lang_variants:
            add_payload(text, voice_val=voice, lang_val=lv)

    # voice candidates from top-level mapping
    for v in VOICE_CANDIDATES.get(language.lower(), [language.title()]):
        add_payload(text, voice_val=v, lang_val=None)
        code = LANG_CODES.get(language.lower())
        if code:
            for lk in alt_lang_keys:
                add_payload(text, voice_val=v, lang_val={lk: code})

    # lastly, try language codes and language name without voice
    code = LANG_CODES.get(language.lower())
    if code:
        for lk in alt_lang_keys:
            add_payload(text, voice_val=None, lang_val={lk: code})
    for lk in alt_lang_keys:
        add_payload(text, voice_val=None, lang_val={lk: language})

    # Deduplicate while preserving order
    seen = set()
    unique_attempts = []
    for p in attempts:
        key = tuple(sorted(p.items()))
        if key in seen:
            continue
        seen.add(key)
        unique_attempts.append(p)

    diagnostics_path = Path(__file__).resolve().parents[1] / 'last_tts_payload.json'

    import base64
    import json

    attempts_info = []
    for payload in unique_attempts:
        info = {'payload': payload}
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            info['status_code'] = resp.status_code
            ct = resp.headers.get('Content-Type', '')
            info['content_type'] = ct

            # If response is raw audio or octet-stream, return bytes
            if ct.startswith('audio') or ct == 'application/octet-stream':
                data = resp.content
            else:
                # Try parse JSON and extract base64 audio
                try:
                    j = resp.json()
                    b64 = j.get('audio') or j.get('audio_base64') or j.get('audioB64')
                    if b64:
                        data = base64.b64decode(b64)
                    else:
                        data = b''
                        info['json'] = j
                except Exception as e:
                    data = b''
                    info['error'] = str(e)

            attempts_info.append(info)

            # persist diagnostic snapshot after each attempt (helpful during debugging)
            try:
                diagnostics_path.write_text(json.dumps({
                    'attempts': attempts_info,
                    'last_attempt': info,
                }))
            except Exception:
                pass

            if data:
                # write diagnostics of successful payload (final)
                try:
                    diagnostics_path.write_text(json.dumps({
                        'attempts': attempts_info,
                        'used_payload': payload,
                        'status_code': resp.status_code,
                        'content_type': ct
                    }))
                except Exception:
                    pass
                return data
        except Exception as e:
            info['exception'] = str(e)
            attempts_info.append(info)
            try:
                diagnostics_path.write_text(json.dumps({'attempts': attempts_info}))
            except Exception:
                pass
            continue

    # no successful audio
    try:
        diagnostics_path.write_text(json.dumps({'attempts': attempts_info}))
    except Exception:
        pass
    return None


def _gtts_fallback(text, language):
    """Fallback to gTTS if available. Returns bytes or None."""
    try:
        from gtts import gTTS
    except Exception:
        return None

    lang_code = _map_language_for_gtts(language)
    try:
        tts = gTTS(text=text, lang=lang_code)
    except ValueError:
        # gTTS may not support the mapped language; fall back to English
        try:
            tts = gTTS(text=text, lang='en')
        except Exception:
            return None

    # write to a temporary file safely
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            tmp_path = Path(f.name)
        tts.save(str(tmp_path))
        data = tmp_path.read_bytes()
        try:
            tmp_path.unlink()
        except Exception:
            pass
        return data
    except Exception:
        return None


def _map_language_for_gtts(lang):
    # Map project language to gTTS-supported codes. gTTS may not support
    # regional languages; default to English when uncertain.
    mapping = {
        'yoruba': 'en',
        'hausa': 'en',
        'igbo': 'en'
    }
    return mapping.get(lang, 'en')


def get_voice_candidates(language):
    return VOICE_CANDIDATES.get(language.lower(), [])


def is_yarngpt_api_available():
    return bool(API_KEY)


def text_to_speech(text, language, voice=None):
    # Try YarnGPT first
    data = _yarngpt_tts(text, language, voice)
    if data:
        return data

    # Fallback to gTTS
    data = _gtts_fallback(text, language)
    if data:
        return data

    # As last resort return empty bytes so Streamlit doesn't crash
    return b""