import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


class AmbiguousArticleError(LookupError):
    """Raised when an article lookup is not scoped to one treaty version."""


def get_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


class TreatyRepository:
    def __init__(self, db_path: str | Path = "taxtreat.db"):
        base_path = Path(db_path)
        if not base_path.is_absolute():
            base_path = get_repo_root() / base_path
        self.db_path = base_path
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row

    def close(self) -> None:
        self.conn.close()

    def get_article(
        self,
        article_number: int,
        *,
        treaty_version_id: int | None = None,
    ) -> Optional[Dict[str, Any]]:
        query = """
            SELECT id, treaty_version_id, article_number, title
            FROM articles
            WHERE article_number = ?
        """
        parameters: list[Any] = [article_number]
        if treaty_version_id is not None:
            query += " AND treaty_version_id = ?"
            parameters.append(treaty_version_id)
        query += " ORDER BY id LIMIT 2"

        rows = self.conn.execute(query, parameters).fetchall()
        if not rows:
            return None
        if len(rows) > 1:
            raise AmbiguousArticleError(
                "Article lookup matched multiple treaty versions; "
                "supply treaty_version_id or use article_id."
            )
        return dict(rows[0])

    def get_article_by_id(self, article_id: int) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            """
            SELECT id, treaty_version_id, article_number, title
            FROM articles
            WHERE id = ?
            """,
            (article_id,),
        ).fetchone()
        if row is None:
            return None
        return dict(row)

    def get_article_paragraphs(
        self,
        article_number: int | None = None,
        *,
        treaty_version_id: int | None = None,
        article_id: int | None = None,
    ) -> List[Dict[str, Any]]:
        if article_id is None:
            if article_number is None:
                raise ValueError("article_id or article_number is required")
            article = self.get_article(
                article_number,
                treaty_version_id=treaty_version_id,
            )
            if article is None:
                return []
            article_id = int(article["id"])

        rows = self.conn.execute(
            """
            SELECT p.id, p.article_id, p.paragraph_number, p.text
            FROM paragraphs p
            WHERE p.article_id = ?
            ORDER BY CAST(p.paragraph_number AS INTEGER), p.paragraph_number, p.id
            """,
            (article_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_full_article_text(
        self,
        article_number: int | None = None,
        *,
        treaty_version_id: int | None = None,
        article_id: int | None = None,
    ) -> str:
        paragraphs = self.get_article_paragraphs(
            article_number,
            treaty_version_id=treaty_version_id,
            article_id=article_id,
        )
        return "\n".join(paragraph["text"] for paragraph in paragraphs)


def connect_db(db_path: str | Path | None = None) -> sqlite3.Connection:
    if db_path is None:
        db_path = get_repo_root() / "taxtreat.db"
    connection = sqlite3.connect(str(db_path))
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def get_article_paragraph_texts(
    conn: sqlite3.Connection,
    article_number: int,
    *,
    treaty_version_id: int | None = None,
) -> List[str]:
    query = """
        SELECT a.id
        FROM articles a
        WHERE a.article_number = ?
    """
    parameters: list[Any] = [article_number]
    if treaty_version_id is not None:
        query += " AND a.treaty_version_id = ?"
        parameters.append(treaty_version_id)
    query += " ORDER BY a.id LIMIT 2"

    article_rows = conn.execute(query, parameters).fetchall()
    if not article_rows:
        return []
    if len(article_rows) > 1:
        raise AmbiguousArticleError(
            "Article lookup matched multiple treaty versions; "
            "supply treaty_version_id."
        )

    cur = conn.cursor()
    cur.execute(
        """
        SELECT p.text
        FROM paragraphs p
        WHERE p.article_id = ?
        ORDER BY CAST(p.paragraph_number AS INTEGER), p.paragraph_number, p.id
        """,
        (article_rows[0][0],),
    )
    return [row[0] for row in cur.fetchall()]
