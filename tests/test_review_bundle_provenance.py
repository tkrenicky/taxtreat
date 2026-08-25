from __future__ import annotations

import pytest

from taxtreat.tools.review_bundle_provenance import (
    build_review_bundle_provenance,
    payload_sha256,
)


def _queue() -> dict:
    return {
        "source_country": "AT",
        "status": "review_queue_not_released",
        "scopes": [
            {"partner_label": "A", "income_type": income}
            for income in ("dividend", "interest", "royalty")
        ] + [
            {"partner_label": "B", "income_type": income}
            for income in ("dividend", "interest", "royalty")
        ],
    }


def _articles() -> dict:
    return {
        "source_country": "AT",
        "status": "article_text_candidates_not_reviewed",
        "partners": [
            {"partner_label": "A", "sources": []},
            {"partner_label": "B", "sources": []},
        ],
    }


def test_payload_digest_is_independent_of_dictionary_key_order():
    assert payload_sha256({"a": 1, "b": 2}) == payload_sha256({"b": 2, "a": 1})


def test_review_bundle_id_changes_when_any_bound_input_changes():
    first = build_review_bundle_provenance(review_queue=_queue(), article_inventory=_articles())
    changed = _articles()
    changed["partners"][0]["new_machine_fact"] = True
    second = build_review_bundle_provenance(review_queue=_queue(), article_inventory=changed)
    assert first["review_bundle_id"].startswith("sha256:")
    assert first["review_bundle_id"] != second["review_bundle_id"]
    assert first["input_digests"]["article_inventory"] != second["input_digests"]["article_inventory"]


def test_review_bundle_binds_optional_inputs_too():
    royalty = {
        "source_country": "AT",
        "partners": [{"partner_label": "A"}, {"partner_label": "B"}],
    }
    base = build_review_bundle_provenance(
        review_queue=_queue(),
        article_inventory=_articles(),
        royalty_audit=royalty,
    )
    royalty["partners"][0]["machine_risk_reasons"] = ["category_sensitive"]
    changed = build_review_bundle_provenance(
        review_queue=_queue(),
        article_inventory=_articles(),
        royalty_audit=royalty,
    )
    assert "royalty_audit" in base["input_digests"]
    assert base["review_bundle_id"] != changed["review_bundle_id"]


def test_review_bundle_rejects_country_or_partner_universe_mixing():
    articles = _articles()
    articles["source_country"] = "SK"
    with pytest.raises(ValueError, match="source-country mismatch"):
        build_review_bundle_provenance(review_queue=_queue(), article_inventory=articles)

    articles = _articles()
    articles["partners"].pop()
    with pytest.raises(ValueError, match="treaty-partner universe mismatch"):
        build_review_bundle_provenance(review_queue=_queue(), article_inventory=articles)

    language = {
        "source_country": "AT",
        "partners": [{"partner_label": "A"}],
    }
    with pytest.raises(ValueError, match="language_evidence treaty-partner universe mismatch"):
        build_review_bundle_provenance(
            review_queue=_queue(),
            article_inventory=_articles(),
            language_evidence=language,
        )
