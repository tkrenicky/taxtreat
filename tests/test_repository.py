import sqlite3
from pathlib import Path

import pytest

from taxtreat.db.repository import (
    AmbiguousArticleError,
    TreatyRepository,
    connect_db,
    get_article_paragraph_texts,
    get_repo_root,
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
    assert repository.conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1

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
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
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


def test_repository_never_mixes_same_numbered_articles_between_treaties(tmp_path):
    db_path = tmp_path / "multiple-treaties.db"
    create_test_database(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO articles (id, treaty_version_id, article_number, title) "
        "VALUES (3, 200, 10, 'Dividends other treaty')"
    )
    conn.execute(
        "INSERT INTO paragraphs (id, article_id, paragraph_number, text) "
        "VALUES (4, 3, '1', 'OTHER TREATY')"
    )
    conn.commit()
    conn.close()

    repository = TreatyRepository(db_path)
    with pytest.raises(AmbiguousArticleError):
        repository.get_full_article_text(10)

    assert repository.get_full_article_text(
        10,
        treaty_version_id=100,
    ) == "First dividend paragraph\nSecond dividend paragraph"
    assert repository.get_full_article_text(article_id=3) == "OTHER TREATY"
    repository.close()


def test_repository_lookup_boundaries_and_id_access(tmp_path):
    db_path = tmp_path / "lookup-boundaries.db"
    create_test_database(db_path)
    repository = TreatyRepository(db_path)

    repo_root = get_repo_root()
    assert (repo_root / "taxtreat").is_dir()
    assert (repo_root / "tests").is_dir()
    assert repository.get_article_by_id(1) == {
        "id": 1,
        "treaty_version_id": 100,
        "article_number": 10,
        "title": "Dividends",
    }
    assert repository.get_article_by_id(999) is None
    assert repository.get_article_paragraphs(article_id=999) == []
    assert repository.get_article_paragraphs(999) == []
    with pytest.raises(ValueError, match="article_id or article_number is required"):
        repository.get_article_paragraphs()

    repository.close()


def test_paragraph_text_lookup_can_scope_ambiguous_article_numbers(tmp_path):
    db_path = tmp_path / "paragraph-scope.db"
    create_test_database(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO articles (id, treaty_version_id, article_number, title) "
        "VALUES (3, 200, 10, 'Dividends other treaty')"
    )
    conn.execute(
        "INSERT INTO paragraphs (id, article_id, paragraph_number, text) "
        "VALUES (4, 3, '1', 'OTHER TREATY')"
    )
    conn.commit()

    with pytest.raises(AmbiguousArticleError):
        get_article_paragraph_texts(conn, 10)
    assert get_article_paragraph_texts(conn, 10, treaty_version_id=100) == [
        "First dividend paragraph",
        "Second dividend paragraph",
    ]
    assert get_article_paragraph_texts(conn, 10, treaty_version_id=200) == [
        "OTHER TREATY"
    ]

    conn.close()
