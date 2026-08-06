import json
from pathlib import Path


ROOT = Path(__file__).parents[1]

PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "remaining_zero_rate_scope_verification.json"
)


def load():
    return json.loads(
        PATH.read_text(encoding="utf-8")
    )


def test_all_zero_rate_scopes_are_verified():
    payload = load()

    assert payload["treaty_partner_count"] == 6
    assert payload["zero_rate_scope_count"] == 12

    assert payload[
        "verification_summary"
    ]["completed_article_scopes_total"] == 39

    assert payload[
        "verification_summary"
    ]["remaining_primary_rate_scopes"] == 0


def test_each_scope_has_a_legal_basis():
    payload = load()

    scope_count = 0

    for record in payload["records"]:
        for scope in record[
            "verified_zero_rate_scopes"
        ].values():
            scope_count += 1

            assert scope["rate_percent"] == 0
            assert scope["legal_basis"]
            assert scope["basis_type"]

            assert scope[
                "primary_article_identity_verified"
            ] is True

            assert scope[
                "zero_rate_legal_basis_verified"
            ] is True

            assert scope[
                "verification_status"
            ] == "zero_rate_scope_verified"

    assert scope_count == 12


def test_primary_rates_complete_but_not_production_ready():
    payload = load()

    assert payload["semantics"][
        "primary_rate_comparison_completed"
    ] is True

    assert payload["semantics"][
        "effective_date_review_completed"
    ] is False

    assert payload["semantics"][
        "protocol_review_completed"
    ] is False

    assert payload["semantics"][
        "mli_review_completed"
    ] is False

    assert payload[
        "legal_verification_completed"
    ] is False

    assert payload["production_ready"] is False
    assert payload["fail_closed"] is True

    assert payload[
        "promotable_to_active_rules"
    ] is False
