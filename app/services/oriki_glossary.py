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
