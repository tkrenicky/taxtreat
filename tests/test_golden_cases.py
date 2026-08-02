import json
from pathlib import Path

GOLDEN_CASES = Path("data/golden_cases")


def load_cases():
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(GOLDEN_CASES.glob("*.json"))
    ]


def test_golden_cases_have_valid_structure():
    cases = load_cases()
    assert cases

    ids = []
    for case in cases:
        assert case["schema_version"] == 1
        assert case["verification"]["status"] == "verified"
        assert case["transaction"]["payer_country"]
        assert case["transaction"]["recipient_country"]
        assert case["transaction"]["transaction_type"] in {
            "dividends",
            "interest",
            "royalties",
        }

        expected = case["expected"]
        assert 0 <= expected["applicable_rate"] <= 100
        assert expected["article"] in {10, 11, 12}
        assert case["sources"]

        ids.append(case["case_id"])

    assert len(ids) == len(set(ids))


def test_cz_ch_royalties_protocol_rate():
    case = next(
        case
        for case in load_cases()
        if case["case_id"] == "CZ-CH-ROYALTIES-001"
    )

    assert case["facts"]["beneficial_owner"] is True
    assert case["facts"]["permanent_establishment_connection"] is False
    assert (
        case["facts"][
            "switzerland_imposes_source_wht_on_royalties_paid_to_nonresidents"
        ]
        is False
    )
    assert case["expected"]["treaty_article_rate"] == 10.0
    assert case["expected"]["applicable_rate"] == 5.0
    assert case["expected"]["protocol_reference"] == (
        "Protocol, point 2 to Article 12"
    )
