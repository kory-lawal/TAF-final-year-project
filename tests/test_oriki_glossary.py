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
