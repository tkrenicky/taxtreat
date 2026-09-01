from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "data/legal_rules_sk"
SK_BASE = ROOT / "data/legal_reviews/sk_outbound"
RELEASE = SK_BASE / "source_country_release_manifest.json"
PROFILE = SK_BASE / "runtime_integration_profile.json"
COVERAGE = SK_BASE / "human_review_coverage.json"
MLI = SK_BASE / "mli_bilateral_adjudication_2026.json"

EXPECTED_INCOMES = {"dividend", "interest", "royalty"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    files = sorted(RULE_DIR.glob("*.json"))
    assert len(files) == 75, f"expected 75 SK treaty packages, got {len(files)}"

    package_countries = set()
    scope_keys = set()
    rate_rules = 0
    final_rate_allowed = 0
    cz_runtime_refs = []

    for path in files:
        payload = load(path)
        pair = payload.get("country_pair") or {}
        assert pair.get("source_country") == "SK", path.name
        country = str(pair.get("recipient_country") or "").upper()
        assert country == path.stem.upper(), path.name
        package_countries.add(country)

        rules = payload.get("rules") or []
        assert rules, f"{country}: no structured rules"
        incomes = {
            str(row.get("income_type") or "")
            for row in rules
            if row.get("income_type")
        }
        assert incomes == EXPECTED_INCOMES, f"{country}: income coverage {sorted(incomes)}"
        for income in EXPECTED_INCOMES:
            scope_keys.add(("SK", country, income))

        for row in rules:
            assert row.get("source_country") == "SK", row.get("rule_id")
            assert row.get("recipient_country") == country, row.get("rule_id")
            url = str(row.get("source_url") or "")
            if "e-sbirka.gov.cz" in url:
                cz_runtime_refs.append((country, row.get("rule_id"), url))
            if row.get("effect") == "rate":
                rate_rules += 1
                if row.get("final_rate_allowed") is True:
                    final_rate_allowed += 1
                # Treaty/protocol rate candidates may be materialized for runtime
                # discovery, but they cannot silently become final production law.
                if row.get("legal_layer") in {"treaty", "protocol"}:
                    assert row.get("automatic_production_approval_forbidden") is True
                    assert row.get("final_rate_allowed") is False
                    assert row.get("decision_status") == "REVIEW_REQUIRED"

    assert len(package_countries) == 75
    assert len(scope_keys) == 225
    assert cz_runtime_refs == [], f"CZ legal-source leakage: {cz_runtime_refs[:5]}"
    assert final_rate_allowed == 0

    release = load(RELEASE)
    assert release["source_country"] == "SK"
    assert release["release_status"] == "released"
    assert release["release_eligible"] is True
    assert release["expected_scope_count"] == 225
    assert release["legal_review_covered_scopes"] == 225
    assert release["human_reviewed_scopes"] == 24
    assert release["pattern_reconciled_scopes"] == 201
    assert release["blockers"] == []

    coverage = load(COVERAGE)
    assert coverage["coverage"]["expected_scope_count"] == 225
    assert coverage["coverage"]["legal_review_covered_scopes"] == 225
    assert coverage["coverage"]["uncovered_scopes"] == 0
    assert coverage["coverage"]["individually_reviewed_scopes"] == 24
    assert coverage["coverage"]["pattern_reconciled_scopes"] == 201
    assert coverage["mli_post_review_adjudication"]["relationship_count"] == 46
    assert coverage["mli_post_review_adjudication"]["machine_extraction_discrepancies"] == 0
    assert coverage["mli_post_review_adjudication"]["final_reviewer_reconfirmation_completed"] is True

    mli = load(MLI)
    assert len(mli.get("relationships") or []) == 46

    profile = load(PROFILE)
    assert profile["runtime_release"] is True
    assert profile["status"] == "source_country_released_rule_level_fail_closed"
    assert profile["production_released_scopes"] == 0
    assert profile["treaty_rule_release"]["expected_partner_packages"] == 75
    assert profile["treaty_rule_release"]["expected_scopes"] == 225
    assert profile["treaty_rule_release"]["final_rate_allowed_scopes"] == 0
    assert profile["treaty_rule_release"]["fail_closed_scopes"] == 225
    assert profile["treaty_rule_release"]["automatic_production_approval_forbidden"] is True
    assert profile["release_gates"]["czech_runtime_fallback_prohibited"] is True

    print("SK runtime closure verifier: PASS")
    print("partner_packages=75")
    print("income_scopes=225")
    print(f"structured_rate_rules={rate_rules}")
    print("source_country_gate=released")
    print("legal_review_covered_scopes=225")
    print("individual_reviewed_scopes=24")
    print("pattern_reconciled_scopes=201")
    print("mli_relationships=46")
    print("czech_runtime_fallback=0")
    print("final_rate_allowed_scopes=0")
    print("rule_level_mode=fail_closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
# closure rerun after explicit unresolved review-gate materialization
