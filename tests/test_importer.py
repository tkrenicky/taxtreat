import json
from pathlib import Path

from taxtreat.db.repository import connect_db
from taxtreat.services.importer import import_treaty_json


def test_import_treaty_json(tmp_path):
    db_path = tmp_path / "test.db"

    # vytvoří schéma databáze
    conn = connect_db(db_path)
    conn.executescript(Path("taxtreat/schema.sql").read_text(encoding="utf-8"))
    conn.commit()
    conn.close()

    treaty = {
        "articles": [
            {
                "number": 10,
                "title": "Dividends",
                "paragraphs": [
                    {"text": "Paragraph 1"},
                    {"text": "Paragraph 2"},
                    "Paragraph 3",
                ],
            },
            {
                "number": 11,
                "title": "Interest",
                "paragraphs": [],
            },
        ]
    }

    json_file = tmp_path / "treaty.json"
    json_file.write_text(json.dumps(treaty), encoding="utf-8")

    import_treaty_json(json_file, db_path)

    conn = connect_db(db_path)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM countries")
    assert cur.fetchone()[0] == 2

    cur.execute("SELECT COUNT(*) FROM treaties")
    assert cur.fetchone()[0] == 1

    cur.execute("SELECT COUNT(*) FROM treaty_versions")
    assert cur.fetchone()[0] == 1

    cur.execute("SELECT COUNT(*) FROM articles")
    assert cur.fetchone()[0] == 2

    cur.execute("SELECT COUNT(*) FROM paragraphs")
    assert cur.fetchone()[0] == 3

    cur.execute(
        """
        SELECT article_number, title
        FROM articles
        ORDER BY article_number
        """
    )
    assert cur.fetchall() == [
        (10, "Dividends"),
        (11, "Interest"),
    ]

    cur.execute(
        """
        SELECT paragraph_number, text
        FROM paragraphs
        ORDER BY paragraph_number
        """
    )
    assert cur.fetchall() == [
        ("1", "Paragraph 1"),
        ("2", "Paragraph 2"),
        ("3", "Paragraph 3"),
    ]

    conn.close()

