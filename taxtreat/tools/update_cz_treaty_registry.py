from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB = Path("data/processed/taxtreat_cz.sqlite")
OUT = Path("data/registries/cz_registry.json")

OUT.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

rows = conn.execute("""
SELECT DISTINCT
    partner_iso2,
    partner_name
FROM treaty_registry
WHERE status='ACTIVE'
ORDER BY partner_name
""").fetchall()

partners = [
    {
        "iso2": r["partner_iso2"],
        "country": r["partner_name"],
    }
    for r in rows
]

OUT.write_text(
    json.dumps(partners, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print(f"Exported {len(partners)} treaty partners.")
