from __future__ import annotations

import csv
import json
import re
import sqlite3
import subprocess
import sys
import unicodedata
from pathlib import Path

from taxtreat.engine.extractors import dividend_rule

DB = Path("data/processed/taxtreat_cz.sqlite")
PARSED_DIR = Path("data/parsed")
REPORT = Path("reports/treaty_extraction_benchmark.csv")


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", ascii_value.lower()).strip("_")


def load_treaties() -> list[sqlite3.Row]:
    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        """
        SELECT
            cd.country_cs,
            d.title,
            d.local_path
        FROM country_documents cd
        JOIN documents d ON d.id = cd.document_id
        WHERE cd.relation = 'treaty'
          AND d.status = 'downloaded'
          AND d.local_path IS NOT NULL
        ORDER BY cd.country_cs
        """
    ).fetchall()

    connection.close()
    return rows


def parse_treaty(country: str, title: str, pdf: Path, output: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "parse_treaty.py",
            str(pdf),
            "--country",
            country,
            "--title",
            title or "",
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"""
STDOUT
------
{result.stdout}

STDERR
------
{result.stderr}
"""
        )

def benchmark(parsed_path: Path) -> dict[str, object]:
    data = json.loads(parsed_path.read_text(encoding="utf-8"))
    articles = {
        article.get("number"): article
        for article in data.get("articles", [])
    }

    result: dict[str, object] = {
        "articles_detected": len(articles),
        "article_10": 10 in articles,
        "article_11": 11 in articles,
        "article_12": 12 in articles,
        "dividend_status": "",
        "dividend_rates": "",
        "dividend_conditions": "",
    }

    if 10 in articles:
        rule = dividend_rule(articles[10].get("text", ""))

        result["dividend_status"] = rule.extraction_status
        result["dividend_rates"] = "|".join(
            str(rate.rate) for rate in rule.rates
        )
        result["dividend_conditions"] = "|".join(
            f"{condition.condition_type.value}:{condition.value}"
            for rate in rule.rates
            for condition in rate.conditions
        )

    return result


def main() -> None:
    PARSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []

    for treaty in load_treaties():
        country = treaty["country_cs"]
        title = treaty["title"] or ""
        pdf = Path(treaty["local_path"])
        parsed_path = PARSED_DIR / f"{slugify(country)}.json"

        row: dict[str, object] = {
            "country": country,
            "title": title,
            "pdf": str(pdf),
            "parsed_file": str(parsed_path),
            "parse_status": "pending",
            "error": "",
        }

        try:
            if not parsed_path.exists():
                parse_treaty(country, title, pdf, parsed_path)

            row["parse_status"] = "ok"
            row.update(benchmark(parsed_path))

        except Exception as exc:
            row["parse_status"] = "failed"
            row["error"] = str(exc)

        rows.append(row)

        print(
            f"{row['parse_status'].upper():6} "
            f"{country} "
            f"A10={row.get('article_10', '')} "
            f"rates={row.get('dividend_rates', '')}"
        )

    fieldnames = [
        "country",
        "title",
        "pdf",
        "parsed_file",
        "parse_status",
        "articles_detected",
        "article_10",
        "article_11",
        "article_12",
        "dividend_status",
        "dividend_rates",
        "dividend_conditions",
        "error",
    ]

    with REPORT.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    successful = sum(row["parse_status"] == "ok" for row in rows)
    failed = len(rows) - successful

    print()
    print(f"Treaties: {len(rows)}")
    print(f"Parsed successfully: {successful}")
    print(f"Failed: {failed}")
    print(f"Report: {REPORT}")


if __name__ == "__main__":
    main()
