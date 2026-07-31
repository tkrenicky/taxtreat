from __future__ import annotations

import json
from pathlib import Path

INPUT = Path("data/parsed")
OUTPUT = Path("data/extracted")
OUTPUT.mkdir(parents=True, exist_ok=True)

TARGETS = {10, 11, 12}


for file in INPUT.glob("*.json"):
    data = json.loads(file.read_text(encoding="utf-8"))

    extracted = {
        "country": data.get("country"),
        "articles": {}
    }

    for article in data.get("articles", []):
        number = article.get("number")

        if number in TARGETS:
            extracted["articles"][str(number)] = {
                "title": article.get("title"),
                "text": article.get("text"),
            }

    outfile = OUTPUT / file.name
    outfile.write_text(
        json.dumps(extracted, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Extracted {file.name}")
