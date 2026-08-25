from pathlib import Path

from taxtreat.tools.audit_at_royalty_categories import build_audit


def _inventory(tmp_path: Path, text: str):
    partners = []
    for index in range(89):
        path = tmp_path / f"article-{index}.txt"
        path.write_text(
            text if index == 0 else "Artikel 12 Lizenzgebühren. Nur im anderen Staat besteuerbar.",
            encoding="utf-8",
        )
        partners.append({
            "partner_label": f"Partner {index}",
            "sources": [{
                "article_candidates": [{
                    "article_number": 12,
                    "substantive_article_candidate": True,
                    "artifact_path": f"artifacts/at/{path.name}",
                }]
            }],
        })
    return {"source_country": "AT", "partner_count": 89, "partners": partners}


def test_legacy_v_h_ownership_threshold_is_not_a_royalty_rate(tmp_path: Path):
    text = (
        "Artikel 12 Lizenzgebühren. Hält der Empfänger mehr als 50 v. H. am Grund- oder Stamm- kapital "
        "der zahlenden Gesellschaft, darf die Steuer 10 v. H. des Rohbetrags der Lizenzgebühren nicht übersteigen."
    )
    row = build_audit(_inventory(tmp_path, text), artifact_root=tmp_path)["partners"][0]
    assert row["percentage_tokens_raw"] == [10.0, 50.0]
    assert row["ownership_threshold_tokens_machine"] == [50.0]
    assert row["rate_candidates_machine"] == [10.0]
    assert row["within_candidate_multi_rate_machine"] is False


def test_intervening_indirect_wording_still_marks_ownership_threshold(tmp_path: Path):
    text = (
        "Artikel 12 Lizenzgebühren. Ist der Empfänger zu mehr als 50 vom Hundert mittelbar oder unmittelbar am Kapital "
        "der zahlenden Gesellschaft beteiligt, darf die Steuer 10 vom Hundert des Bruttobetrags der Lizenzgebühren nicht übersteigen."
    )
    row = build_audit(_inventory(tmp_path, text), artifact_root=tmp_path)["partners"][0]
    assert row["percentage_tokens_raw"] == [10.0, 50.0]
    assert row["ownership_threshold_tokens_machine"] == [50.0]
    assert row["rate_candidates_machine"] == [10.0]
    assert row["within_candidate_multi_rate_machine"] is False
