import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


class TreatyRepository:
    def __init__(self, db_path: str | Path = "taxtreat.db"):
        base_path = Path(db_path)
        if not base_path.is_absolute():
            base_path = get_repo_root() / base_path
        self.db_path = base_path
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

    def get_article(self, article_number: int) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            """
            SELECT id, treaty_version_id, article_number, title
            FROM articles
            WHERE article_number = ?
            LIMIT 1
            """,
            (article_number,),
        ).fetchone()
        if row is None:
            return None
        return dict(row)

    def get_article_paragraphs(self, article_number: int) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT p.id, p.article_id, p.paragraph_number, p.text
            FROM paragraphs p
            JOIN articles a ON a.id = p.article_id
            WHERE a.article_number = ?
            ORDER BY p.paragraph_number
            """,
            (article_number,),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_full_article_text(self, article_number: int) -> str:
        paragraphs = self.get_article_paragraphs(article_number)
        return "\n".join(paragraph["text"] for paragraph in paragraphs)


def connect_db(db_path: str | Path | None = None) -> sqlite3.Connection:
    if db_path is None:
        db_path = get_repo_root() / "taxtreat.db"
    return sqlite3.connect(str(db_path))


def get_article_paragraph_texts(conn: sqlite3.Connection, article_number: int) -> List[str]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT p.text
        FROM paragraphs p
        JOIN articles a ON a.id = p.article_id
        WHERE a.article_number = ?
        ORDER BY p.paragraph_number
        """,
        (article_number,),
    )
    return [row[0] for row in cur.fetchall()]
