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
    assert audit["schema_version"] == 6
    assert len(BASE_CATEGORIES) == 7
    assert audit["status"] == "royalty_category_machine_risk_queue_not_released"
    assert all(row["projection_released"] is False for row in audit["partners"])
    assert all(row["legal_review_completed"] is False for row in audit["partners"])


def test_at_audit_flags_multiple_rate_category_split(tmp_path: Path):
    audit = build_audit(_inventory(tmp_path), artifact_root=tmp_path)
    row = audit["partners"][0]
    assert row["rate_candidates_machine"] == [5.0, 10.0]
    assert row["within_candidate_multi_rate_machine"] is True
    assert row["cross_instrument_rate_variance_machine"] is False
    assert "multiple_rate_candidates_after_condition_filter" in row["machine_risk_reasons"]


def test_at_audit_separates_technical_service_rate_from_royalty_category(tmp_path: Path):
    audit = build_audit(_inventory(tmp_path), artifact_root=tmp_path)
    row = audit["partners"][1]
    assert row["keyword_flags"]["technical_services"] is True
    assert "technical_services_or_assistance_language" in row["machine_risk_reasons"]


def test_at_audit_excludes_ownership_threshold_from_rate_candidates():
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
        "Artikel 12. Lizenzgebühren aus Finanzierungsleasing werden mit 5 Prozent der Bruttosumme besteuert; "
        "Lizenzgebühren aus operativem Leasing mit 10 Prozent der Bruttosumme.",
        encoding="utf-8",
    )
    row = build_audit(inventory, artifact_root=tmp_path)["partners"][4]
    assert row["keyword_flags"]["financial_lease"] is True
    assert row["keyword_flags"]["operating_lease"] is True
    assert "lease_subcategory_language" in row["machine_risk_reasons"]


def test_at_audit_detects_royalty_source_exemption_branch_without_synthetic_zero_rate(tmp_path: Path):
    inventory = _inventory(tmp_path)
    (tmp_path / "article-11.txt").write_text(
        "Artikel 12 Lizenzgebühren. Die Steuer im Quellenstaat darf 5 vom Hundert des Bruttobetrags "
        "der Lizenzgebühren nicht übersteigen. Ungeachtet dessen sind Lizenzgebühren für Urheberrechte "
        "eines Autors für literarische, dramatische, musikalische oder künstlerische Arbeiten im Quellenstaat "
        "von der Besteuerung ausgenommen.",
        encoding="utf-8",
    )
    row = build_audit(inventory, artifact_root=tmp_path)["partners"][11]
    assert row["rate_candidates_machine"] == [5.0]
    assert row["royalty_source_exemption_branch_machine"] is True
    assert row["within_candidate_multi_rate_machine"] is False
    assert "royalty_source_exemption_branch_language" in row["machine_risk_reasons"]


def test_at_audit_single_rate_without_exemption_does_not_create_branch_signal(tmp_path: Path):
    inventory = _inventory(tmp_path)
    (tmp_path / "article-12.txt").write_text(
        "Artikel 12 Lizenzgebühren. Die Steuer darf 10 vom Hundert des Bruttobetrags der Lizenzgebühren "
        "nicht übersteigen. Der Ausdruck Lizenzgebühren umfasst Urheberrechte, Patente und Marken.",
        encoding="utf-8",
    )
    row = build_audit(inventory, artifact_root=tmp_path)["partners"][12]
    assert row["rate_candidates_machine"] == [10.0]
    assert row["royalty_source_exemption_branch_machine"] is False
    assert "royalty_source_exemption_branch_language" not in row["machine_risk_reasons"]


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


def test_at_audit_semantically_ignores_non_royalty_article_11_when_article_12_exists(tmp_path: Path):
    inventory = _inventory(tmp_path)
    article_11 = tmp_path / "article-11-nonroyalty.txt"
    article_11.write_text(
        "Artikel 11. Zinsen aus einem Vertragsstaat können im anderen Staat besteuert werden. "
        "Der Ausdruck Zinsen bezeichnet Einkünfte aus Forderungen jeder Art. Weitere Regeln "
        "betreffen ausschließlich Zinsen und enthalten keine Regel zu anderen Einkunftsarten.",
        encoding="utf-8",
    )
    inventory["partners"][7]["sources"][0]["article_candidates"].insert(
        0,
        {
            "article_number": 11,
            "substantive_article_candidate": True,
            "artifact_path": "artifacts/at/article-11-nonroyalty.txt",
        },
    )
    row = build_audit(inventory, artifact_root=tmp_path)["partners"][7]
    assert row["candidate_text_count"] == 1
    assert row["royalty_article_numbers_machine"] == [12]
    assert row["nonstandard_royalty_article_number_candidate"] is False
    assert row["rejected_candidate_count"] == 0


def test_at_audit_semantically_rejects_protocol_article_xii_that_changes_other_article(tmp_path: Path):
    inventory = _inventory(tmp_path)
    protocol = tmp_path / "protocol-article-xii.txt"
    protocol.write_text(
        "Article XII The following new paragraph 5 shall be added to Article 24 Mutual Agreement Procedure. "
        "Where 60 per cent of the cases are unresolved after 15 per cent of the period has elapsed, "
        "the competent authorities shall continue consultations under Article 24.",
        encoding="utf-8",
    )
    inventory["partners"][8]["sources"].append({
        "article_candidates": [{
            "article_number": 12,
            "substantive_article_candidate": True,
            "artifact_path": "artifacts/at/protocol-article-xii.txt",
        }]
    })
    row = build_audit(inventory, artifact_root=tmp_path)["partners"][8]
    assert row["candidate_text_count"] == 1
    assert row["semantic_rejected_article_12_count"] == 1
    assert row["rate_candidates_machine"] == []
    assert "multiple_rate_candidates_after_condition_filter" not in row["machine_risk_reasons"]


def test_at_audit_separates_cross_instrument_rate_variance_from_within_text_multi_rate(tmp_path: Path):
    inventory = _inventory(tmp_path)
    first = tmp_path / "variant-one.txt"
    second = tmp_path / "variant-two.txt"
    first.write_text(
        "Artikel 12 Lizenzgebühren. Lizenzgebühren dürfen mit 10 Prozent des Bruttobetrags besteuert werden.",
        encoding="utf-8",
    )
    second.write_text(
        "Artikel 12 Lizenzgebühren. Lizenzgebühren dürfen mit 5 Prozent des Bruttobetrags besteuert werden.",
        encoding="utf-8",
    )
    inventory["partners"][9]["sources"] = [
        {"article_candidates": [{"article_number": 12, "substantive_article_candidate": True, "artifact_path": "artifacts/at/variant-one.txt"}]},
        {"article_candidates": [{"article_number": 12, "substantive_article_candidate": True, "artifact_path": "artifacts/at/variant-two.txt"}]},
    ]
    row = build_audit(inventory, artifact_root=tmp_path)["partners"][9]
    assert row["rate_candidates_machine"] == [5.0, 10.0]
    assert row["rate_candidates_by_text_machine"] == [[10.0], [5.0]]
    assert row["within_candidate_multi_rate_machine"] is False
    assert row["cross_instrument_rate_variance_machine"] is True
    assert "multiple_rate_candidates_after_condition_filter" not in row["machine_risk_reasons"]
    assert "cross_instrument_rate_variance" in row["machine_risk_reasons"]


def test_at_audit_accepts_candidate_path_relative_to_artifact_root(tmp_path: Path):
    inventory = _inventory(tmp_path)
    inventory["partners"][10]["sources"][0]["article_candidates"][0]["artifact_path"] = "article-10.txt"
    row = build_audit(inventory, artifact_root=tmp_path)["partners"][10]
    assert row["candidate_text_count"] == 1
    assert row["rate_candidates_machine"] == []


def test_at_audit_never_assumes_seven_categories_are_exhaustive(tmp_path: Path):
    audit = build_audit(_inventory(tmp_path), artifact_root=tmp_path)
    assert audit["policy"]["seven_base_categories_are_not_assumed_to_be_legally_exhaustive"] is True
    assert audit["policy"]["treaty_specific_discriminators_may_be_required"] is True
    assert audit["policy"]["raw_percentage_tokens_are_not_rate_candidates"] is True
    assert audit["policy"]["ownership_threshold_percentages_cannot_create_rate_branches"] is True
    assert audit["policy"]["source_exemption_language_is_a_branch_signal_not_a_synthetic_zero_rate"] is True
    assert audit["policy"]["royalty_semantics_required_for_article_candidate"] is True
    assert audit["policy"]["cross_instrument_rate_variance_is_not_a_category_split"] is True
    assert audit["policy"]["multiple_applicable_branches_with_different_results_must_fail_closed"] is True


def test_static_at_audit_summary_matches_reconciled_machine_taxonomy():
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    counts = summary["risk_reason_counts"]
    reconciliation = summary["preliminary_multi_rate_reconciliation"]

    assert summary["schema_version"] == 3
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
    assert len(reconciliation["category_split_partners"]) == 5
    assert len(reconciliation["non_category_condition_partners"]) == 4
    assert reconciliation["instrument_variant_chronology_partners"] == ["Slowenien / Slovenia"]
    assert len(reconciliation["rows"]) == 10
    assert {row["partner_label"] for row in reconciliation["rows"]} == set(summary["multiple_rate_candidate_partners"])
    assert all(row["legal_review_completed"] is False for row in reconciliation["rows"])
    assert all(row["projection_released"] is False for row in reconciliation["rows"])
    assert summary["policy"]["ownership_threshold_percentages_cannot_create_rate_branches"] is True
    assert summary["policy"]["preliminary_reconciliation_does_not_select_controlling_text"] is True
    assert summary["policy"]["no_rate_projection_is_released_by_this_audit"] is True
