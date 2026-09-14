from pathlib import Path

from taxtreat.tools.audit_at_royalty_categories import build_audit


def _inventory(tmp_path: Path, special_text: str):
    partners = []
    for index in range(89):
        path = tmp_path / f"article-{index}.txt"
        text = special_text if index == 0 else "Artikel 12 Lizenzgebühren. Die Lizenzgebühren dürfen nur im anderen Staat besteuert werden."
        path.write_text(text, encoding="utf-8")
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


def _row(tmp_path: Path, text: str):
    return build_audit(_inventory(tmp_path, text), artifact_root=tmp_path)["partners"][0]


def test_canada_like_general_cap_plus_selective_residence_only_branch_is_category_scoped(tmp_path: Path):
    row = _row(
        tmp_path,
        "Artikel 12 Lizenzgebühren. Diese Lizenzgebühren dürfen jedoch auch in dem Vertragsstaat, aus dem sie stammen, "
        "besteuert werden; die Steuer darf 10 vom Hundert des Bruttobetrags der Lizenzgebühren nicht übersteigen. "
        "Ungeachtet des Absatzes 2 dürfen Lizenzgebühren für Urheberrechte an literarischen und musikalischen Werken "
        "sowie Lizenzgebühren für Software, Patente und gewerbliche Erfahrungen nur im anderen Staat besteuert werden.",
    )
    assert row["rate_candidates_machine"] == [10.0]
    assert row["within_candidate_multi_rate_machine"] is False
    assert row["category_scoped_source_tax_right_machine"] is True
    assert "category_scoped_source_tax_right_language" in row["machine_risk_reasons"]


def test_czech_like_rate_cap_limited_to_article_subcategory_is_category_scoped(tmp_path: Path):
    row = _row(
        tmp_path,
        "Artikel 12 Lizenzgebühren. Die in Absatz 3 lit. a angeführten Lizenzgebühren dürfen auch im Quellenstaat "
        "besteuert werden, aber die Steuer darf 5 vom Hundert des Bruttobetrags der Lizenzgebühren nicht übersteigen. "
        "Absatz 3 lit. a umfasst Patente, Marken, Software und Ausrüstungen; lit. b umfasst Urheberrechte an "
        "literarischen, künstlerischen oder wissenschaftlichen Werken einschließlich Filmen und Rundfunkmaterial.",
    )
    assert row["rate_candidates_machine"] == [5.0]
    assert row["category_scoped_source_tax_right_machine"] is True
    assert "category_scoped_source_tax_right_language" in row["machine_risk_reasons"]


def test_treaty_wide_residence_only_royalty_rule_does_not_create_category_scoped_signal(tmp_path: Path):
    row = _row(
        tmp_path,
        "Artikel 12 Lizenzgebühren. Lizenzgebühren, deren Nutzungsberechtigter im anderen Vertragsstaat ansässig ist, "
        "dürfen nur im anderen Staat besteuert werden. Der Ausdruck Lizenzgebühren umfasst Urheberrechte, Patente, "
        "Marken, Muster, Modelle und gewerbliche Erfahrungen.",
    )
    assert row["rate_candidates_machine"] == []
    assert row["category_scoped_source_tax_right_machine"] is False
    assert "category_scoped_source_tax_right_language" not in row["machine_risk_reasons"]


def test_policy_treats_non_numeric_category_source_right_as_branch_signal(tmp_path: Path):
    audit = build_audit(_inventory(tmp_path, "Artikel 12 Lizenzgebühren. Nur im anderen Staat besteuerbar."), artifact_root=tmp_path)
    assert audit["policy"]["category_scoped_source_tax_rights_are_branch_signals_even_without_second_numeric_rate"] is True
