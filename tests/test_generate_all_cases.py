import sqlite3
from pathlib import Path

from taxtreat.generator.generate_all_cases import (
    generate,
    load_partners,
    load_registry_partners,
)


def create_registry_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE country_documents (
                id INTEGER PRIMARY KEY,
                country_cs TEXT NOT NULL,
                document_id INTEGER NOT NULL,
                relation TEXT
            );

            INSERT INTO country_documents
                (country_cs, document_id, relation)
            VALUES
                ('Německo', 1, 'treaty'),
                ('Německo', 2, 'financial_bulletin'),
                ('Švýcarsko', 3, 'treaty'),
                ('Švýcarsko', 4, 'protocol');
            """
        )


def test_load_partners_uses_treaty_relations(tmp_path):
    db_path = tmp_path / "registry.sqlite"
    create_registry_database(db_path)

    assert load_partners(db_path) == ["Německo", "Švýcarsko"]


def test_generate_creates_three_cases_per_partner(tmp_path):
    db_path = tmp_path / "registry.sqlite"
    create_registry_database(db_path)

    rows = generate(db_path)

    assert len(rows) == 6
    assert {row["payer"] for row in rows} == {"CZ"}
    assert {row["income_type"] for row in rows} == {
        "dividend",
        "interest",
        "royalty",
    }
    assert {row["recipient_country_cs"] for row in rows} == {
        "Německo",
        "Švýcarsko",
    }
    assert all(row["manual_review"] is True for row in rows)


def test_canonical_registry_generates_all_scopes_with_codes():
    partners = load_registry_partners()
    rows = generate()

    assert len(partners) == 100
    assert len(rows) == 300
    assert len({row["recipient_iso2"] for row in rows}) == 100
    assert all(row["recipient_iso2"] for row in rows)
    assert {row["status"] for row in rows} == {"PENDING_CONSOLIDATION"}
