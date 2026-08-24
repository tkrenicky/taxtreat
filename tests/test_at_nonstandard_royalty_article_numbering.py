from pathlib import Path

from taxtreat.tools.audit_at_royalty_categories import build_audit
from taxtreat.tools.extract_at_treaty_article_candidates import extract_article_blocks


def test_extract_article_blocks_normalizes_roman_x_xi_xii():
    text = """
Artikel X
(1) Zinsen können besteuert werden. Diese Regel enthält ausreichend Text für die Extraktion.
(2) Weitere Bestimmungen über Zinsen folgen hier zur Qualitätssicherung.
Artikel XI
(1) Lizenzgebühren dürfen mit 10 v. H. besteuert werden. Lizenzgebühren umfassen Patente und Marken.
(2) Lizenzgebühren für Filme und Ausrüstungen fallen ebenfalls unter diese Bestimmung.
Artikel XII
(1) Öffentliche Vergütungen werden in diesem Artikel geregelt und sind keine Lizenzgebühren.
(2) Weitere Bestimmungen zu öffentlichen Vergütungen folgen hier.
"""
    blocks = extract_article_blocks(text)
    assert set(blocks) == {10, 11, 12}
    assert blocks[11].startswith("Artikel XI")
    assert "Lizenzgebühren" in blocks[11]


def test_royalty_audit_uses_semantic_fallback_but_keeps_nonstandard_numbering_fail_closed(tmp_path: Path):
    article_11 = tmp_path / "japan-article-11.txt"
    article_11.write_text(
        "Artikel XI\n(1) Der Satz der Steuer von Lizenzgebühren darf 10 vom Hundert nicht übersteigen. "
        "(2) Der Ausdruck Lizenzgebühren umfasst Urheberrechte, Patente, Marken und Ausrüstungen. "
        "(3) Weitere Lizenzgebühren fallen unter dieselbe Bestimmung.",
        encoding="utf-8",
    )
    partners = [{"partner_label": "Japan / Japan", "sources": [{"article_candidates": [{
        "article_number": 11,
        "substantive_article_candidate": True,
        "artifact_path": "japan-article-11.txt",
    }]}]}]
    for index in range(88):
        partners.append({"partner_label": f"Partner {index}", "sources": []})

    inventory = {"source_country": "AT", "partner_count": 89, "partners": partners}
    result = build_audit(inventory, artifact_root=tmp_path)
    japan = result["partners"][0]

    assert japan["royalty_article_numbers_machine"] == [11]
    assert japan["nonstandard_royalty_article_number_candidate"] is True
    assert japan["rate_candidates_machine"] == [10.0]
    assert "nonstandard_royalty_article_number_candidate" in japan["machine_risk_reasons"]
    assert "no_substantive_article_12_candidate" not in japan["machine_risk_reasons"]
    assert japan["category_projection_review_required"] is True
    assert japan["legal_review_completed"] is False
    assert japan["projection_released"] is False
    assert result["policy"]["article_number_alone_does_not_establish_income_type"] is True
    assert result["policy"]["nonstandard_royalty_article_number_requires_review"] is True
