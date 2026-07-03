"""Import Yoruba lineage Oríkì from the compiled .docx into app/data/yoruba.csv.

The source document (`app/data/sources/Yoruba_States_Oriki_Idile_Compilation.docx`)
groups Yoruba family lineages (Oríkì Ìdílé) by state:

    Heading 2  -> State  (Oyo, Ogun, Osun, ...)
    Heading 3  -> Lineage / family name  ("Adeyemi", "Egba – Lisabi", ...)
    Normal     -> "Oríkì (representative): <verse> ... Meaning: <english>"

Each lineage is mapped onto the existing 8-column CSV schema:

    id, name, gender, language, praise_text, meaning, category, keywords

- name      : the family token (last segment after an en-dash/hyphen).
- gender    : "all"  (lineage oríkì are not person/gender specific).
- language  : "yoruba".
- praise_text: the Yoruba verse (newlines flattened to spaces).
- meaning   : the English "Meaning:" line from the document.
- category  : "oriki_idile"  (used to make re-runs idempotent).
- keywords  : "<state>;<subgroup?>;lineage".

The importer is idempotent: it drops any existing rows whose category is
"oriki_idile" before appending, so hand-authored rows (royalty, honor, ...)
are preserved and re-running never duplicates lineage rows.

Usage:
    python scripts/import_oriki_docx.py            # uses the bundled source doc
    python scripts/import_oriki_docx.py <path.docx>
"""

import re
import sys
from pathlib import Path

import pandas as pd

try:
    import docx  # python-docx
except ImportError:
    sys.exit("python-docx is required: pip install python-docx")

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCX = REPO_ROOT / "app" / "data" / "sources" / "Yoruba_States_Oriki_Idile_Compilation.docx"
CSV_PATH = REPO_ROOT / "app" / "data" / "yoruba.csv"
CATEGORY = "oriki_idile"
COLUMNS = ["id", "name", "gender", "language", "praise_text", "meaning", "category", "keywords"]

_SPLIT_NAME = re.compile(r"\s*[–—-]\s*")  # en-dash, em-dash, hyphen


def parse_docx(path: Path):
    """Yield dicts of {state, subgroup, name, praise_text, meaning} per lineage."""
    document = docx.Document(str(path))
    state = None
    lineage = None
    entries = []
    for para in document.paragraphs:
        style = para.style.name
        text = para.text.strip()
        if not text:
            continue
        if style == "Heading 2":
            state = text
        elif style == "Heading 3":
            lineage = text
        elif style == "Normal" and lineage:
            body = text.replace("Oríkì (representative):", "").strip()
            if "Meaning:" in body:
                verse, meaning = body.split("Meaning:", 1)
            else:
                verse, meaning = body, ""
            praise_text = " ".join(verse.split())  # flatten newlines/space runs
            meaning = " ".join(meaning.split())

            parts = _SPLIT_NAME.split(lineage)
            name = parts[-1].strip()
            subgroup = parts[0].strip() if len(parts) > 1 else ""

            entries.append({
                "state": (state or "").strip(),
                "subgroup": subgroup,
                "name": name,
                "praise_text": praise_text,
                "meaning": meaning,
            })
            lineage = None
    return entries


def build_rows(entries, start_id):
    rows = []
    next_id = start_id
    for e in entries:
        kw = [e["state"].lower()] + ([e["subgroup"].lower()] if e["subgroup"] else []) + ["lineage"]
        rows.append({
            "id": next_id,
            "name": e["name"],
            "gender": "all",
            "language": "yoruba",
            "praise_text": e["praise_text"],
            "meaning": e["meaning"],
            "category": CATEGORY,
            "keywords": ";".join(kw),
        })
        next_id += 1
    return rows


def main():
    docx_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DOCX
    if not docx_path.exists():
        sys.exit(f"Source doc not found: {docx_path}")

    existing = pd.read_csv(CSV_PATH, dtype=str, encoding="utf-8")
    # Idempotent: drop previously-imported lineage rows, keep everything else.
    kept = existing[existing["category"] != CATEGORY].copy()

    entries = parse_docx(docx_path)
    max_id = pd.to_numeric(kept["id"], errors="coerce").max()
    start_id = (int(max_id) if pd.notna(max_id) else 0) + 1
    new_rows = build_rows(entries, start_id)

    combined = pd.concat([kept, pd.DataFrame(new_rows, columns=COLUMNS)], ignore_index=True)
    combined = combined[COLUMNS]
    combined.to_csv(CSV_PATH, index=False, encoding="utf-8")

    states = sorted({e["state"] for e in entries})
    print(f"Source: {docx_path.name}")
    print(f"Kept {len(kept)} existing rows; imported {len(new_rows)} lineage rows.")
    print(f"States: {', '.join(states)}")
    print(f"Total rows now: {len(combined)}  ->  {CSV_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
