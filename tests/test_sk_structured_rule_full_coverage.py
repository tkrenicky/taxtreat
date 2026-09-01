from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
PARTNERS = ROOT / "data" / "sk_treaty_partners.json"
RULE_DIR = ROOT / "data" / "legal_rules_sk"
INCOMES = {"dividend", "interest", "royalty"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_sk_structured_rules_cover_exact_75_by_3_treaty_scope_universe():
    partners = load(PARTNERS)
    iso2 = {row["iso2"] for row in partners}

    assert len(partners) == 75
    assert len(iso2) == 75

    rule_files = {path.stem.upper(): path for path in RULE_DIR.glob("*.json")}
    assert set(rule_files) == iso2

    missing_scopes: list[str] = []
    empty_rules: list[str] = []
    source_country_errors: list[str] = []
    recipient_country_errors: list[str] = []

    for country in sorted(iso2):
        payload = load(rule_files[country])
        rules = payload.get("rules") or []
        if not rules:
            empty_rules.append(country)
            continue

        present = {str(rule.get("income_type")) for rule in rules}
        for income in sorted(INCOMES - present):
            missing_scopes.append(f"SK-{country}-{income}")

        for rule in rules:
            if rule.get("source_country") != "SK":
                source_country_errors.append(str(rule.get("rule_id")))
            if rule.get("recipient_country") != country:
                recipient_country_errors.append(str(rule.get("rule_id")))

    assert not empty_rules, f"SK structured rule files without rules: {empty_rules}"
    assert not source_country_errors, f"Wrong source country: {source_country_errors}"
    assert not recipient_country_errors, f"Wrong recipient country: {recipient_country_errors}"
    assert not missing_scopes, (
        f"SK structured production rules do not cover the full 225-scope universe; "
        f"missing {len(missing_scopes)} scopes: {missing_scopes}"
    )


def test_sk_release_manifest_cannot_claim_release_without_full_structured_rule_coverage():
    manifest = load(ROOT / "data/legal_reviews/sk_outbound/source_country_release_manifest.json")
    partners = load(PARTNERS)
    rule_files = {path.stem.upper(): path for path in RULE_DIR.glob("*.json")}

    covered = 0
    for row in partners:
        payload = load(rule_files[row["iso2"]])
        present = {str(rule.get("income_type")) for rule in payload.get("rules", [])}
        covered += len(INCOMES & present)

    if manifest.get("release_status") == "released":
        assert covered == 225, (
            "SK source-country release manifest is released while structured treaty "
            f"rule coverage is only {covered}/225 scopes."
        )
