import json
from pathlib import Path

import pytest

from taxtreat.tools.audit_at_royalty_categories import BASE_CATEGORIES, build_audit


SUMMARY_PATH = Path("data/legal_reviews/at_outbound/royalty_category_audit_summary_2026.json")


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


def test_at_audit_detects_post_percentage_ownership_wording_without_bleeding_into_rates(tmp_path: Path):
    inventory = _inventory(tmp_path)
    (tmp_path / "article-3.txt").write_text(
        "Artikel 12. Lizenzgebühren an eine Person, die zu mehr als 50 vom Hundert am Kapital "
        "der zahlenden Gesellschaft beteiligt ist, dürfen mit 10 vom Hundert des Bruttobetrages "
        "besteuert werden; in allen anderen Fällen 5 vom Hundert des Bruttobetrages.",
        encoding="utf-8",
    )
    row = build_audit(inventory, artifact_root=tmp_path)["partners"][3]
    assert row["percentage_tokens_raw"] == [5.0, 10.0, 50.0]
    assert row["ownership_threshold_tokens_machine"] == [50.0]
    assert row["rate_candidates_machine"] == [5.0, 10.0]


def test_at_audit_flags_lease_subcategory_language(tmp_path: Path):
    inventory = _inventory(tmp_path)
    (tmp_path / "article-4.txt").write_text(
        "Artikel 12. Finanzierungsleasing wird mit 5 Prozent der Bruttosumme besteuert; "
        "operatives Leasing mit 10 Prozent der Bruttosumme.",
        encoding="utf-8",
    )
    row = build_audit(inventory, artifact_root=tmp_path)["partners"][4]
    assert row["keyword_flags"]["financial_lease"] is True
    assert row["keyword_flags"]["operating_lease"] is True
    assert "lease_subcategory_language" in row["machine_risk_reasons"]


def test_at_audit_keeps_rejected_article_12_auditable_and_fails_closed(tmp_path: Path):
    inventory = _inventory(tmp_path)
    inventory["partners"][5]["sources"][0]["article_candidates"][0]["substantive_article_candidate"] = False
    row = build_audit(inventory, artifact_root=tmp_path)["partners"][5]
    assert row["candidate_text_count"] == 0
    assert row["rejected_candidate_count"] == 1
    assert "no_substantive_article_12_candidate" in row["machine_risk_reasons"]
    assert row["category_projection_review_required"] is True


def test_at_audit_rejects_wrong_country_or_incomplete_partner_universe(tmp_path: Path):
    wrong_country = _inventory(tmp_path)
    wrong_country["source_country"] = "SK"
    with pytest.raises(ValueError, match="Expected Austrian"):
        build_audit(wrong_country, artifact_root=tmp_path)

    incomplete = _inventory(tmp_path)
    incomplete["partner_count"] = 88
    with pytest.raises(ValueError, match="Expected 89"):
        build_audit(incomplete, artifact_root=tmp_path)


def test_at_audit_rejects_missing_substantive_article_artifact(tmp_path: Path):
    inventory = _inventory(tmp_path)
    inventory["partners"][6]["sources"][0]["article_candidates"][0]["artifact_path"] = "artifacts/at/missing.txt"
    with pytest.raises(ValueError, match="Missing AT article candidate text"):
        build_audit(inventory, artifact_root=tmp_path)


def test_at_audit_ignores_non_royalty_article_candidates_before_reading_artifacts(tmp_path: Path):
    inventory = _inventory(tmp_path)
    inventory["partners"][7]["sources"][0]["article_candidates"].insert(
        0,
        {
            "article_number": 11,
            "substantive_article_candidate": True,
            "artifact_path": "artifacts/at/nonexistent-article-11.txt",
        },
    )
    row = build_audit(inventory, artifact_root=tmp_path)["partners"][7]
    assert row["candidate_text_count"] == 1
    assert row["rejected_candidate_count"] == 0


def test_at_audit_accepts_candidate_path_relative_to_artifact_root(tmp_path: Path):
    inventory = _inventory(tmp_path)
    inventory["partners"][8]["sources"][0]["article_candidates"][0]["artifact_path"] = "article-8.txt"
    row = build_audit(inventory, artifact_root=tmp_path)["partners"][8]
    assert row["candidate_text_count"] == 1
    assert row["rate_candidates_machine"] == []


def test_at_audit_never_assumes_seven_categories_are_exhaustive(tmp_path: Path):
    audit = build_audit(_inventory(tmp_path), artifact_root=tmp_path)
    assert audit["policy"]["seven_base_categories_are_not_assumed_to_be_legally_exhaustive"] is True
    assert audit["policy"]["treaty_specific_discriminators_may_be_required"] is True
    assert audit["policy"]["raw_percentage_tokens_are_not_rate_candidates"] is True
    assert audit["policy"]["ownership_threshold_percentages_cannot_create_rate_branches"] is True
    assert audit["policy"]["multiple_applicable_branches_with_different_results_must_fail_closed"] is True


def test_static_at_audit_summary_matches_reconciled_machine_taxonomy():
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    counts = summary["risk_reason_counts"]

    assert summary["schema_version"] == 2
    assert summary["current_treaty_partner_count"] == 89
    assert summary["official_source_count"] == 281
    assert summary["royalty_machine_risk_partner_count"] == 50
    assert counts == {
        "no_substantive_article_12_candidate": 36,
        "multiple_rate_candidates_after_condition_filter": 10,
        "ownership_percentage_condition_present": 5,
        "technical_services_or_assistance_language": 1,
        "lease_subcategory_language": 0,
    }
    assert len(summary["multiple_rate_candidate_partners"]) == 10
    assert len(summary["ownership_condition_partners"]) == 5
    assert summary["technical_services_language_partners"] == ["Indien / India"]
    assert len(summary["no_substantive_article_12_candidate_partners"]) == 36
    assert set(summary["ownership_condition_partners"]) & set(summary["multiple_rate_candidate_partners"]) == {
        "Portugal / Portugal",
        "Slowenien / Slovenia",
    }
    assert summary["policy"]["ownership_threshold_percentages_cannot_create_rate_branches"] is True
    assert summary["policy"]["no_rate_projection_is_released_by_this_audit"] is True
