from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path


def build(root: Path):
    db = root / "data" / "processed" / "taxtreat_cz.sqlite"
    if db.exists():
        db.unlink()

    con = sqlite3.connect(db)
    con.executescript(
        """
        CREATE TABLE treaty_registry(
          id INTEGER PRIMARY KEY,
          country_cs TEXT NOT NULL UNIQUE,
          effective_from TEXT NOT NULL,
          source_status_date TEXT NOT NULL
        );
        CREATE TABLE documents(
          id INTEGER PRIMARY KEY,
          url TEXT NOT NULL,
          source_page TEXT,
          title TEXT,
          kind TEXT,
          mime_type TEXT,
          sha256 TEXT,
          local_path TEXT,
          downloaded_at TEXT,
          status TEXT,
          error TEXT,
          UNIQUE(url, title)
        );
        CREATE TABLE country_documents(
          id INTEGER PRIMARY KEY,
          country_cs TEXT NOT NULL,
          document_id INTEGER NOT NULL,
          relation TEXT,
          effective_from TEXT,
          UNIQUE(country_cs, document_id, relation),
          FOREIGN KEY(document_id) REFERENCES documents(id)
        );
        CREATE INDEX idx_documents_kind ON documents(kind);
        CREATE INDEX idx_documents_status ON documents(status);
        CREATE INDEX idx_country_documents_country ON country_documents(country_cs);
        """
    )

    seed = root / "data" / "processed" / "cz_treaty_registry_seed.csv"
    if seed.exists():
        with seed.open(encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
        con.executemany(
            "INSERT INTO treaty_registry(country_cs,effective_from,source_status_date) "
            "VALUES(:country_cs,:effective_from,:source_status_date)",
            rows,
        )

    manifest = root / "data" / "processed" / "document_manifest.json"
    if manifest.exists():
        records = json.loads(manifest.read_text(encoding="utf-8"))
        documents_by_key: dict[tuple[str, str], dict] = {}
        for record in records:
            document_key = (record["url"], record.get("title") or "")
            documents_by_key.setdefault(document_key, record)

        con.executemany(
            """
            INSERT INTO documents(url,source_page,title,kind,mime_type,sha256,local_path,downloaded_at,status,error)
            VALUES(:url,:source_page,:title,:kind,:mime_type,:sha256,:local_path,:downloaded_at,:status,:error)
            """,
            documents_by_key.values(),
        )
        document_ids = {
            (url, title or ""): document_id
            for url, title, document_id in con.execute(
                "SELECT url,title,id FROM documents"
            )
        }

        associations = []
        seen = set()
        for record in records:
            country = record.get("country_cs")
            if not country:
                continue
            document_key = (record["url"], record.get("title") or "")
            key = (
                country,
                document_ids[document_key],
                record.get("relation"),
            )
            if key in seen:
                continue
            seen.add(key)
            associations.append(
                {
                    "country_cs": country,
                    "document_id": document_ids[document_key],
                    "relation": record.get("relation"),
                    "effective_from": record.get("effective_from"),
                }
            )
        con.executemany(
            """
            INSERT INTO country_documents(country_cs,document_id,relation,effective_from)
            VALUES(:country_cs,:document_id,:relation,:effective_from)
            """,
            associations,
        )

    con.commit()
    con.close()
    print(db)


if __name__ == "__main__":
    build(Path(__file__).resolve().parents[2])
