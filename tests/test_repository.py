import sqlite3
from pathlib import Path

from taxtreat.db.repository import (
    TreatyRepository,
    connect_db,
    get_article_paragraph_texts,
)


def create_test_database(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE articles (
            id INTEGER PRIMARY KEY,
            treaty_version_id INTEGER NOT NULL,
            article_number INTEGER NOT NULL,
            title TEXT
        );

        CREATE TABLE paragraphs (
            id INTEGER PRIMARY KEY,
            article_id INTEGER NOT NULL,
            paragraph_number TEXT,
            text TEXT NOT NULL
        );

        INSERT INTO articles (
            id,
            treaty_version_id,
            article_number,
            title
        )
        VALUES
            (1, 100, 10, 'Dividends'),
            (2, 100, 11, 'Interest');

        INSERT INTO paragraphs (
            id,
            article_id,
            paragraph_number,
            text
        )
        VALUES
            (1, 1, '1', 'First dividend paragraph'),
            (2, 1, '2', 'Second dividend paragraph'),
            (3, 2, '1', 'Interest paragraph');
        """
    )
    conn.commit()
    conn.close()


def test_repository_reads_article_and_paragraphs(tmp_path):
    db_path = tmp_path / "repository.db"
    create_test_database(db_path)

    repository = TreatyRepository(db_path)

    article = repository.get_article(10)
    paragraphs = repository.get_article_paragraphs(10)
    full_text = repository.get_full_article_text(10)

    assert article == {
        "id": 1,
        "treaty_version_id": 100,
        "article_number": 10,
        "title": "Dividends",
    }

    assert paragraphs == [
        {
            "id": 1,
            "article_id": 1,
            "paragraph_number": "1",
            "text": "First dividend paragraph",
        },
        {
            "id": 2,
            "article_id": 1,
            "paragraph_number": "2",
            "text": "Second dividend paragraph",
        },
    ]

    assert full_text == (
        "First dividend paragraph\n"
        "Second dividend paragraph"
    )

    repository.conn.close()


def test_get_article_returns_none_when_article_does_not_exist(tmp_path):
    db_path = tmp_path / "repository.db"
    create_test_database(db_path)

    repository = TreatyRepository(db_path)

    assert repository.get_article(99) is None

    repository.conn.close()


def test_repository_resolves_relative_database_path(monkeypatch, tmp_path):
    db_path = tmp_path / "relative.db"
    create_test_database(db_path)

    monkeypatch.setattr(
        "taxtreat.db.repository.get_repo_root",
        lambda: tmp_path,
    )

    repository = TreatyRepository("relative.db")

    assert repository.db_path == db_path
    assert repository.get_article(10)["title"] == "Dividends"

    repository.conn.close()


def test_connect_db_with_explicit_path(tmp_path):
    db_path = tmp_path / "explicit.db"

    conn = connect_db(db_path)
    conn.execute("CREATE TABLE example (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

    assert db_path.exists()


def test_connect_db_uses_default_repository_database(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "taxtreat.db.repository.get_repo_root",
        lambda: tmp_path,
    )

    conn = connect_db()
    conn.execute("CREATE TABLE example (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

    assert (tmp_path / "taxtreat.db").exists()


def test_get_article_paragraph_texts(tmp_path):
    db_path = tmp_path / "paragraphs.db"
    create_test_database(db_path)

    conn = sqlite3.connect(db_path)

    result = get_article_paragraph_texts(conn, 10)

    assert result == [
        "First dividend paragraph",
        "Second dividend paragraph",
    ]

    assert get_article_paragraph_texts(conn, 99) == []

    conn.close()
