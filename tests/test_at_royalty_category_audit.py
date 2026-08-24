from pathlib import Path

from taxtreat.tools.audit_at_royalty_categories import BASE_CATEGORIES, build_audit


def _inventory(tmp_path: Path):
    partners = []
    for index in range(89):
        path = tmp_path / f"article-{index}.txt"
        if index == 0:
            text = (
                "Artikel 12 Lizenzgebühren. Die Steuer darf 5 vom Hundert für Ausrüstungen "
                "und 10 vom Hundert in allen anderen Fällen nicht übersteigen."
            )
        elif index == 1:
            text = (
                "Artikel 12 Lizenzgebühren und Vergütungen für technische Dienstleistungen. "
                "Lizenzgebühren 10 vom Hundert; technische Dienstleistungen 7,5 vom Hundert."
            )
        elif index == 2:
            text = (
                "Artikel 12. Lizenzgebühren 10 vom Hundert, wenn eine Beteiligung am Kapital "
                "von mehr als 50 vom Hundert besteht; sonst 5 vom Hundert."
            )
        else:
            text = "Artikel 12 Lizenzgebühren. Nur im anderen Staat besteuerbar."
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
    return {
        "source_country": "AT",
        "partner_count": 89,
        "partners": partners,
    }


def test_at_royalty_audit_is_fail_closed_and_preserves_89_partner_population(tmp_path: Path):
    audit = build_audit(_inventory(tmp_path), artifact_root=tmp_path)
    assert audit["partner_count"] == 89
    assert len(BASE_CATEGORIES) == 7
    assert audit["status"] == "royalty_category_machine_risk_queue_not_released"
    assert all(row["projection_released"] is False for row in audit["partners"])
    assert all(row["legal_review_completed"] is False for row in audit["partners"])


def test_at_audit_flags_multiple_rate_category_split(tmp_path: Path):
    audit = build_audit(_inventory(tmp_path), artifact_root=tmp_path)
    row = audit["partners"][0]
    assert row["rate_candidates_machine"] == [5.0, 10.0]
    assert "multiple_rate_candidates_after_condition_filter" in row["machine_risk_reasons"]


def test_at_audit_separates_technical_service_rate_from_royalty_category(tmp_path: Path):
    audit = build_audit(_inventory(tmp_path), artifact_root=tmp_path)
    row = audit["partners"][1]
    assert row["keyword_flags"]["technical_services"] is True
    assert "technical_services_or_assistance_language" in row["machine_risk_reasons"]


def test_at_audit_excludes_ownership_threshold_from_rate_candidates():
    # Unit-level regression for the same class of defect found in the SK/BR audit.
    # The actual royalty rates are 10 and 5; 50 is only the ownership threshold.
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        audit = build_audit(_inventory(tmp_path), artifact_root=tmp_path)
        row = audit["partners"][2]
        assert row["percentage_tokens_raw"] == [5.0, 10.0, 50.0]
        assert row["ownership_threshold_tokens_machine"] == [50.0]
        assert row["rate_candidates_machine"] == [5.0, 10.0]
        assert row["non_rate_percentage_tokens"] == [50.0]
        assert "ownership_percentage_condition_present" in row["machine_risk_reasons"]


def test_at_audit_never_assumes_seven_categories_are_exhaustive(tmp_path: Path):
    audit = build_audit(_inventory(tmp_path), artifact_root=tmp_path)
    assert audit["policy"]["seven_base_categories_are_not_assumed_to_be_legally_exhaustive"] is True
    assert audit["policy"]["treaty_specific_discriminators_may_be_required"] is True
    assert audit["policy"]["raw_percentage_tokens_are_not_rate_candidates"] is True
    assert audit["policy"]["ownership_threshold_percentages_cannot_create_rate_branches"] is True
    assert audit["policy"]["multiple_applicable_branches_with_different_results_must_fail_closed"] is True
