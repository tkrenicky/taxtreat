import json
import sys
from pathlib import Path

from taxtreat.tools import audit_at_royalty_categories as audit


def test_at_royalty_audit_cli_writes_fail_closed_output(monkeypatch, tmp_path: Path):
    partners = []
    for index in range(89):
        article = tmp_path / f"article-{index}.txt"
        article.write_text(
            "Artikel 12 Lizenzgebühren. Lizenzgebühren dürfen nur im anderen Staat besteuert werden.",
            encoding="utf-8",
        )
        partners.append(
            {
                "partner_label": f"Partner {index}",
                "sources": [
                    {
                        "article_candidates": [
                            {
                                "article_number": 12,
                                "substantive_article_candidate": True,
                                "artifact_path": f"artifacts/at/{article.name}",
                            }
                        ]
                    }
                ],
            }
        )

    source = tmp_path / "inventory.json"
    output = tmp_path / "audit.json"
    source.write_text(
        json.dumps(
            {
                "source_country": "AT",
                "partner_count": 89,
                "partners": partners,
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "audit_at_royalty_categories",
            "--input",
            str(source),
            "--artifact-root",
            str(tmp_path),
            "--output",
            str(output),
        ],
    )
    audit.main()

    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["schema_version"] == 4
    assert result["partner_count"] == 89
    assert result["status"] == "royalty_category_machine_risk_queue_not_released"
    assert result["risk_partner_count"] == 0
    assert all(row["projection_released"] is False for row in result["partners"])
