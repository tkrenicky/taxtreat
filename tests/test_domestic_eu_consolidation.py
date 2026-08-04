from __future__ import annotations

import hashlib
import json
from pathlib import Path

from taxtreat.consolidation.domestic_eu_effects import (
    EU_MEMBER_PARTNERS,
    RELIEF_ELIGIBLE_PARTNERS,
    SECTION_19_8_EXTENSION_PARTNERS,
    build_domestic_eu_candidates,
)


ROOT = Path(__file__).parents[1]
DATASET = (
    ROOT / "data" / "legal_consolidation" / "cz_domestic_eu_candidates.json"
)


def _payload():
    return json.loads(DATASET.read_text(encoding="utf-8"))


def _scope(country: str, income_type: str):
    return next(
        row
        for row in _payload()["scopes"]
        if row["recipient_country"] == country
        and row["income_type"] == income_type
    )


def test_domestic_dataset_covers_all_registered_scopes_fail_closed():
    payload = _payload()

    assert len(payload["scopes"]) == 300
    assert len({row["recipient_country"] for row in payload["scopes"]}) == 100
    assert sum(
        row["recipient_country"] not in {"AT", "CH"}
        for row in payload["scopes"]
    ) == 294
    assert all(
        row["verification_status"] == "needs_review"
        and "independent_legal_review" in row["consolidation_blockers"]
        for row in payload["scopes"]
    )


def test_standard_and_protective_domestic_rates_are_not_conflated():
    for scope in _payload()["scopes"]:
        candidate = scope["domestic_rate_candidate"]
        assert candidate["standard_rate"] == 15.0
        assert candidate["protective_rate"] == 35.0
        assert candidate["effective_from"] == "2026-04-01"

    assert "36(1)(b)(1)" in _scope("DE", "dividend")[
        "domestic_rate_candidate"
    ]["standard_reference"]
    assert "36(1)(a)(1)" in _scope("DE", "interest")[
        "domestic_rate_candidate"
    ]["standard_reference"]
    assert "36(1)(a)(1)" in _scope("DE", "royalty")[
        "domestic_rate_candidate"
    ]["standard_reference"]


def test_section_19_relief_jurisdiction_coverage_is_explicit():
    payload = _payload()
    assert len(EU_MEMBER_PARTNERS) == 26
    assert SECTION_19_8_EXTENSION_PARTNERS == {"CH", "IS", "LI", "NO"}
    assert len(RELIEF_ELIGIBLE_PARTNERS) == 30
    assert sum(row["relief_candidate"] is not None for row in payload["scopes"]) == 90
    assert sum(
        row["relief_candidate"] is not None
        and row["recipient_country"] not in {"AT", "CH"}
        for row in payload["scopes"]
    ) == 84
    assert _scope("DE", "dividend")["relief_candidate"]["regime"] == (
        "eu_directive_domestic_implementation"
    )
    assert _scope("NO", "interest")["relief_candidate"]["regime"] == (
        "section_19_8_extension"
    )
    assert _scope("GB", "dividend")["relief_candidate"] is None


def test_relief_timing_and_association_alternatives_are_preserved():
    dividend = _scope("DE", "dividend")["relief_candidate"]
    assert dividend["rate"] == 0.0
    assert dividend["holding_period_one_of"][0]["value"] == 12
    assert dividend["holding_period_one_of"][1]["all_of"][0]["value"] == 12

    interest = _scope("DE", "interest")["relief_candidate"]
    royalty = _scope("CH", "royalty")["relief_candidate"]
    assert all(row["fact"] != "beneficial_owner" for row in dividend["all_of"])
    assert len(interest["association_one_of"]) == 3
    assert interest["association_period_one_of"][0]["value"] == 24
    assert royalty["association_period_one_of"][1]["all_of"][0]["value"] == 24
    assert any(
        row["fact"] == "section_38nb_decision_effective"
        for row in interest["all_of"]
    )
    assert any(row["fact"] == "beneficial_owner" for row in interest["all_of"])


def test_source_and_candidate_hashes_are_stable():
    payload = _payload()
    assert len(payload["sources"]) == 4
    assert all(
        source["authority_class"] == "official"
        and source["url"].startswith("https://")
        and len(source["source_document_sha256"]) == 64
        for source in payload["sources"]
    )
    for scope in payload["scopes"]:
        expected = scope.pop("candidate_sha256")
        actual = hashlib.sha256(
            json.dumps(scope, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        assert actual == expected


def test_domestic_generation_is_deterministic():
    assert build_domestic_eu_candidates() == _payload()


def test_pilot_domestic_anchors_match_current_official_version():
    for filename in ("rakousko.json", "svycarsko.json"):
        payload = json.loads(
            (ROOT / "data" / "legal_rules" / filename).read_text(
                encoding="utf-8"
            )
        )
        domestic = [
            row
            for row in payload["rules"]
            if row["rule_id"].endswith("DOMESTIC-15")
        ]
        assert {row["effective_from"] for row in domestic} == {"2026-04-01"}
        by_income = {row["income_type"]: row for row in domestic}
        assert by_income["dividend"]["paragraph"] == "1(b)(1)"
        assert by_income["interest"]["paragraph"] == "1(a)(1)"
        assert by_income["royalty"]["paragraph"] == "1(a)(1)"
