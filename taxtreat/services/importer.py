import json
from pathlib import Path
from typing import Any

from taxtreat.db.repository import connect_db


def import_treaty_json(json_file: str | Path, db_path: str | Path | None = None) -> None:
    conn = connect_db(db_path)
    cur = conn.cursor()

    with open(json_file, encoding="utf-8") as f:
        treaty = json.load(f)

    cur.execute(
        "INSERT OR IGNORE INTO countries (iso2, name_en) VALUES (?, ?)",
        ("CZ", "Czech Republic"),
    )
    cur.execute(
        "INSERT OR IGNORE INTO countries (iso2, name_en) VALUES (?, ?)",
        ("CH", "Switzerland"),
    )

    cur.execute("SELECT id FROM countries WHERE iso2='CZ'")
    cz_id = cur.fetchone()[0]

    cur.execute("SELECT id FROM countries WHERE iso2='CH'")
    ch_id = cur.fetchone()[0]

    cur.execute(
        "INSERT INTO treaties (country_a_id, country_b_id) VALUES (?, ?)",
        (cz_id, ch_id),
    )
    treaty_id = cur.lastrowid

    cur.execute(
        """INSERT INTO treaty_versions
        (treaty_id, language, source_file, is_authentic)
        VALUES (?, ?, ?, ?)""",
        (treaty_id, "cs", str(json_file), 0),
    )

    version_id = cur.lastrowid

    for article in treaty["articles"]:
        cur.execute(
            """INSERT INTO articles
            (treaty_version_id, article_number, title)
            VALUES (?, ?, ?)""",
            (version_id, article["number"], article["title"]),
        )
        article_id = cur.lastrowid

        for paragraph_number, paragraph in enumerate(article.get("paragraphs", []), start=1):
            paragraph_text = paragraph["text"] if isinstance(paragraph, dict) else paragraph
            cur.execute(
                """INSERT INTO paragraphs
                (article_id, paragraph_number, text)
                VALUES (?, ?, ?)""",
                (article_id, paragraph_number, paragraph_text),
            )

    conn.commit()
    conn.close()
