from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from taxtreat.consolidation.country_qa import (
    CountryRisk,
    apply_country_qa_event,
    classify_country_risk,
    select_independent_sample,
    selected_for_independent_sample,
)
from taxtreat.engine.ppt_representation import (
    PPTRepresentation,
    assess_ppt_representation,
)


ROOT = Path(__file__).parents[1]
BASE = ROOT / "data/legal_reviews/global_cz_outbound"
BUILDER = ROOT / "scripts/build_cz_country_qa_queue.py"
QUEUE = BASE / "cz_country_qa_queue.json"
MLI_SCOPE = BASE / "cz_wht_mli_product_scope.json"
GOVERNANCE = BASE / "cz_scalable_release_governance.json"
FINAL23_AGGREGATE_SHA256 = "3140c31835596f00686f9ad99fc2cddaf43c185ab94a73c94bccf993fe159486"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def module():
    spec = importlib.util.spec_from_file_location("cz_country_qa_builder", BUILDER)
    value = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(value)
    return value


def test_country_queue_is_reproducible_and_reconciles_to_100_and_300():
    queue = load(QUEUE)
    assert queue == module().build_queue()
    assert queue["summary"] == {
        "country_count": 100,
        "pending_country_qa": 100,
        "production_releasable_scope_count": 0,
        "risk_counts": {"ELEVATED": 20, "EXCEPTION": 0, "STANDARD": 80},
        "scope_count": 300,
        "verified_scope_count": 0,
        "previously_elevated_solely_for_clean_ppt_mli_path": 51,
    }
    assert len(queue["packages"]) == 100
    assert len({row["treaty_pair_id"] for row in queue["packages"]}) == 100
    assert all(len(row["income_scopes"]) == 3 for row in queue["packages"])


def test_risk_classification_is_deterministic_and_reason_bound():
    queue = load(QUEUE)
    selected = select_independent_sample({
        package["treaty_pair_id"]: package["risk_category"]
        for package in queue["packages"]
    })
    for package in queue["packages"]:
        assert classify_country_risk(set(package["risk_reasons"])).value == package["risk_category"]
        assert package["human_qa"]["independent_sample_selected"] is (package["treaty_pair_id"] in selected)
    assert sum(row["risk_category"] == "STANDARD" for row in queue["packages"] if row["treaty_pair_id"] in selected) == 4
    assert sum(row["risk_category"] == "ELEVATED" for row in queue["packages"] if row["treaty_pair_id"] in selected) == 2
    by_country = {row["partner_country"]: row for row in queue["packages"]}
    assert by_country["AE"]["risk_reasons"] == ["multiple_historical_instruments", "unusual_treaty_numbering"]
    assert by_country["NG"]["risk_reasons"] == ["unusual_treaty_numbering"]
    assert "preserved_historical_source_hash_difference" in by_country["GR"]["risk_reasons"]
    assert "preserved_historical_source_hash_difference" in by_country["NL"]["risk_reasons"]
    assert by_country["AL"]["wht_relevant_mli"]["modification"] is not None
    assert by_country["AL"]["risk_category"] == "STANDARD"
    assert by_country["AL"]["risk_reasons"] == []


def test_risk_classifier_rejects_unknown_features_and_prioritises_exceptions():
    assert classify_country_risk(set()) is CountryRisk.STANDARD
    assert classify_country_risk({"material_protocol_overlay"}) is CountryRisk.ELEVATED
    assert classify_country_risk({"material_protocol_overlay", "effective_date_conflict"}) is CountryRisk.EXCEPTION
    with pytest.raises(ValueError, match="Unsupported"):
        classify_country_risk({"invented_feature"})


def test_clean_ppt_only_mli_path_is_not_an_elevated_feature():
    with pytest.raises(ValueError, match="Unsupported"):
        classify_country_risk({"wht_relevant_mli_modification"})
    queue = load(QUEUE)
    elevated = {row["partner_country"] for row in queue["packages"] if row["risk_category"] == "ELEVATED"}
    assert elevated == {
        "AE", "AT", "BE", "BY", "CH", "CL", "GB", "GH", "GR", "HR",
        "IT", "KZ", "MD", "NG", "NL", "RS", "RU", "SG", "UA", "UZ",
    }


def test_articles_are_treaty_specific_in_country_view():
    packages = {row["partner_country"]: row for row in load(QUEUE)["packages"]}
    assert [row["article_number"] for row in packages["AE"]["income_scopes"]] == [11, 12, 13]
    assert [row["article_number"] for row in packages["NG"]["income_scopes"]] == [9, 10, 11]
    assert [row["article_number"] for row in packages["AD"]["income_scopes"]] == [10, 11, 12]


def test_mli_product_scope_filters_unrelated_provisions_from_wht_output():
    scope = load(MLI_SCOPE)
    assert scope == module().build_mli_product_scope()
    assert [row["article"] for row in scope["output_influencing_provisions"]] == ["Article 7(1)"]
    assert scope["expressly_non_applicable_under_czech_position"] == [{
        "adds_365_day_dividend_holding_period": False,
        "article": "Article 8",
        "reason": "Czechia reserves the right for the entirety of Article 8 not to apply to its Covered Tax Agreements",
    }]
    assert scope["wht_effective_date_mechanics"]["pair_specific_candidate_effect_count"] == 64
    outside = " ".join(scope["outside_tax_treat_product_output"])
    assert "permanent-establishment" in outside
    assert "mutual agreement" in outside
    for package in load(QUEUE)["packages"]:
        assert package["wht_relevant_mli"]["article_8_modification"] is None
        assert package["wht_relevant_mli"]["unrelated_mli_provisions_considered_in_wht_output"] == []


def test_ppt_representation_also_covers_official_bilateral_anti_abuse_candidates():
    packages = {row["partner_country"]: row for row in load(QUEUE)["packages"]}
    assert packages["KW"]["wht_relevant_mli"]["modification"] is None
    assert packages["KW"]["ppt_treatment"]["relevant"] is True
    assert packages["KW"]["ppt_treatment"]["relevance_basis"]["bilateral_ppt_or_equivalent_candidate"]["official_czech_mli_position_notifies_existing_article_7_2_provision"] is True
    assert packages["AD"]["ppt_treatment"]["relevance_basis"]["bilateral_ppt_or_equivalent_candidate"]["official_base_treaty_text_match"] is True
    assert packages["US"]["ppt_treatment"]["relevant"] is False


@pytest.mark.parametrize("response", [PPTRepresentation.NOT_CONFIRMED, PPTRepresentation.UNKNOWN, None])
def test_unconfirmed_or_unknown_ppt_retains_research_but_never_asserts_relief(response):
    result = assess_ppt_representation(ppt_relevant=True, representation=response)
    assert result.research_may_proceed is True
    assert result.separate_anti_abuse_assessment_required is True
    assert result.tax_treat_determined_ppt_satisfied is False
    assert "subject_to_separate_ppt_assessment" in result.treaty_benefit_treatment


def test_confirmed_ppt_is_only_a_user_research_basis():
    result = assess_ppt_representation(
        ppt_relevant=True,
        representation=PPTRepresentation.CONFIRMED,
    )
    assert result.research_basis == "user_representation_confirmed"
    assert result.separate_anti_abuse_assessment_required is False
    assert result.tax_treat_determined_ppt_satisfied is False
    with pytest.raises(ValueError, match="irrelevant"):
        assess_ppt_representation(ppt_relevant=False, representation="confirmed")


def test_irrelevant_and_invalid_ppt_responses_are_deterministic():
    irrelevant = assess_ppt_representation(ppt_relevant=False)
    assert irrelevant.as_dict()["representation_requested"] is False
    assert irrelevant.treaty_benefit_treatment == "subject_to_other_treaty_and_domestic_conditions"
    with pytest.raises(ValueError, match="Unsupported"):
        assess_ppt_representation(ppt_relevant=True, representation="maybe")


def test_no_machine_generated_human_approval_or_scope_verification():
    queue = load(QUEUE)
    for package in queue["packages"]:
        qa = package["human_qa"]
        assert qa["status"] == "pending"
        for field in (
            "reviewer_id", "reviewed_at", "outcome", "independent_reviewer_id",
            "independently_reviewed_at", "independent_outcome",
        ):
            assert qa[field] is None
        assert package["release_state"] == {
            "fail_closed": True,
            "needs_review_scope_count": 3,
            "production_releasable": False,
            "scope_count": 3,
            "verified_scope_count": 0,
        }


def test_country_qa_event_never_auto_promotes_scopes_or_production():
    package = {
        "treaty_pair_id": "CZ-XX",
        "risk_category": CountryRisk.EXCEPTION.value,
        "package_sha256": "a" * 64,
    }
    pending = apply_country_qa_event(package, None)
    assert pending.production_release_allowed is False
    event = {
        "package_sha256": "a" * 64,
        "reviewer_id": "human-primary",
        "reviewed_at": "2026-08-10T10:00:00Z",
        "outcome": "accepted",
        "independent_reviewer_id": "human-independent",
        "independently_reviewed_at": "2026-08-10T11:00:00Z",
        "independent_outcome": "accepted",
    }
    completed = apply_country_qa_event(package, event)
    assert completed.country_qa_complete is True
    assert completed.independent_review_complete is True
    assert completed.scopes_marked_verified == 0
    assert completed.production_release_allowed is False
    event["independent_reviewer_id"] = "human-primary"
    with pytest.raises(ValueError, match="must differ"):
        apply_country_qa_event(package, event)


def test_country_qa_event_validation_and_non_sample_path():
    pair_id = next(
        f"CZ-{first}{second}"
        for first in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for second in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if not selected_for_independent_sample(f"CZ-{first}{second}", CountryRisk.STANDARD)
    )
    package = {
        "treaty_pair_id": pair_id,
        "risk_category": "STANDARD",
        "package_sha256": "b" * 64,
    }
    accepted = {
        "package_sha256": "b" * 64,
        "reviewer_id": "human-primary",
        "reviewed_at": "2026-08-10T10:00:00Z",
        "outcome": "accepted",
    }
    outcome = apply_country_qa_event(package, accepted)
    assert outcome.country_qa_complete is True
    assert outcome.independent_review_required is False
    assert outcome.independent_review_complete is False

    returned = {**accepted, "outcome": "returned_for_correction"}
    assert apply_country_qa_event(package, returned).package_status == "returned_for_correction"

    for replacement, message in (
        ({"package_sha256": "c" * 64}, "stale"),
        ({"reviewer_id": None}, "reviewer_id"),
        ({"reviewed_at": "not-a-date"}, "invalid reviewed_at"),
        ({"outcome": "invented"}, "invalid outcome"),
    ):
        with pytest.raises(ValueError, match=message):
            apply_country_qa_event(package, {**accepted, **replacement})


def test_required_independent_event_fields_are_strict():
    package = {
        "treaty_pair_id": "CZ-XX",
        "risk_category": "EXCEPTION",
        "package_sha256": "d" * 64,
    }
    base = {
        "package_sha256": "d" * 64,
        "reviewer_id": "human-primary",
        "reviewed_at": "2026-08-10T10:00:00Z",
        "outcome": "accepted",
    }
    cases = (
        ({}, "independent_reviewer_id"),
        ({"independent_reviewer_id": "human-independent"}, "independently_reviewed_at"),
        ({"independent_reviewer_id": "human-independent", "independently_reviewed_at": "bad"}, "invalid independently_reviewed_at"),
        ({"independent_reviewer_id": "human-independent", "independently_reviewed_at": "2026-08-10T11:00:00Z", "independent_outcome": "rejected"}, "must be accepted"),
    )
    for additions, message in cases:
        with pytest.raises(ValueError, match=message):
            apply_country_qa_event(package, {**base, **additions})


def test_governance_is_additive_and_does_not_weaken_live_gate():
    policy = load(GOVERNANCE)
    assert policy == module().build_governance(load(QUEUE))
    assert policy["no_machine_human_approval"] is True
    assert policy["all_current_country_events_pending"] is True
    assert policy["production_release_created"] is False
    assert policy["legacy_four_eyes_boundary"]["safety_controls_removed"] == []
    assert "remains fail-closed" in policy["legacy_four_eyes_boundary"]["change_in_this_release"]
    assert policy["independent_review"]["standard_sample_percent"] == 5
    assert policy["independent_review"]["elevated_sample_percent"] == 10
    assert policy["ppt_only_mli_risk_correction"]["former_elevated_country_count"] == 51
    assert policy["estimated_workload"]["combined_hours_rounded"] == [7, 13]
    assert policy["estimated_workload"]["planning_estimate_not_completed_review"] is True


def test_package_hashes_and_protected_candidate_hashes_are_unchanged():
    for package in load(QUEUE)["packages"]:
        expected = package.pop("package_sha256")
        actual = hashlib.sha256(
            json.dumps(package, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        assert actual == expected
    execution = load(ROOT / "data/legal_consolidation/stage5_execution_manifest.json")
    for relative, expected in execution["frozen_remaining_294_hashes"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
    digest = hashlib.sha256()
    for path in sorted((ROOT / "data/legal_rule_candidates/final23").glob("*.json")):
        digest.update(str(path.relative_to(ROOT)).encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
    assert digest.hexdigest() == FINAL23_AGGREGATE_SHA256


def test_review_views_are_complete_and_do_not_depend_on_ignored_raw_artifacts():
    files = sorted((BASE / "cz_country_qa_review_batches").glob("batch_*.md"))
    assert len(files) == 10
    assert sum(path.read_text(encoding="utf-8").count("Human QA: **PENDING**") for path in files) == 100
    assert "data/raw" not in BUILDER.read_text(encoding="utf-8")
