import sqlite3
from pathlib import Path

import pytest


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "taxtreat" / "schema.sql"


@pytest.fixture
def seeded_treaty_db(tmp_path):
    db_path = tmp_path / "taxtreat.db"
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    connection.executemany(
        "INSERT INTO countries (id, iso2, iso3, name_en, name_local) VALUES (?, ?, ?, ?, ?)",
        [
            (1, "CZ", "CZE", "Czech Republic", "Česká republika"),
            (2, "CH", "CHE", "Switzerland", "Švýcarsko"),
        ],
    )
    connection.execute(
        "INSERT INTO treaties (id, country_a_id, country_b_id, treaty_type, status) VALUES (?, ?, ?, ?, ?)",
        (1, 1, 2, "DTT", "active"),
    )
    connection.execute(
        "INSERT INTO treaty_versions (id, treaty_id, language, source_file, is_authentic) VALUES (?, ?, ?, ?, ?)",
        (1, 1, "en", "test-fixture", 1),
    )
    connection.execute(
        "INSERT INTO articles (id, treaty_version_id, article_number, title) VALUES (?, ?, ?, ?)",
        (1, 1, 10, "Dividendy"),
    )
    connection.execute(
        "INSERT INTO paragraphs (id, article_id, paragraph_number, text) VALUES (?, ?, ?, ?)",
        (
            1,
            1,
            "2",
            "2. If the beneficial owner of the dividends is a resident of the other Contracting State, the tax shall not exceed:\n"
            "a) 5 percent of the gross amount of the dividends if the beneficial owner is a company which directly owns at least 25 percent of the capital of the company paying the dividends;\n"
            "b) 15 percent of the gross amount of the dividends in all other cases.",
        ),
    )
    connection.commit()
    connection.close()
    return db_path
