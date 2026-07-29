import sqlite3
from pathlib import Path

from fastapi import FastAPI

app = FastAPI(title="TaxTreat", version="0.1.0")


def get_db_connection() -> sqlite3.Connection:
    db_path = Path(__file__).resolve().parent.parent / "taxtreat.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/")
def read_root():
    return {"name": "TaxTreat", "version": "0.1.0"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/treaties")
def list_treaties():
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT id, country_a_id, country_b_id, treaty_type, signed_date, effective_from, effective_to, status FROM treaties"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
