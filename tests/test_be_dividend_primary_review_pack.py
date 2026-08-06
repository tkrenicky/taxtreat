from taxtreat.tools.build_be_dividend_primary_review_pack import (
    build_markdown,
    build_review_pack,
)


def test_review_pack_targets_be_dividend_scope():
    payload = build_review_pack()

    assert payload["packet_id"] == (
        "CZ-BE-DIV-LEGAL-REVIEW"
    )
    assert payload["recipient_country"] == "BE"
    assert payload["income_type"] == "dividend"
    assert len(payload["review_row_sha256"]) == 64


def test_review_pack_contains_all_legal_layers():
    payload = build_review_pack()

    assert payload["treaty"]["rate_candidates"]
    assert payload["domestic_and_eu"][
        "domestic_rate_candidate"
    ]
    assert payload["domestic_and_eu"]["relief_candidate"]
    assert "protocols" in payload
    assert "mli_effects" in payload


def test_review_pack_remains_fail_closed():
    payload = build_review_pack()

    assert payload["status"] == "awaiting_primary_review"
    assert payload["promotable_to_active_rules"] is False
    assert payload["review_fields"]["review_outcome"] is None
    assert payload["policy"]["fail_closed"] is True


def test_markdown_contains_required_review_sections():
    markdown = build_markdown(build_review_pack())

    assert "# Primary legal review – CZ → BE / dividendy" in markdown
    assert "## 1. Základní smlouva" in markdown
    assert "## 3. EU osvobození" in markdown
    assert "## 5. MLI" in markdown
    assert "## 6. Otázky pro primary review" in markdown
    assert "## 7. Výsledek primary review" in markdown
