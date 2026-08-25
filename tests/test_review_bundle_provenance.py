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


def _manifest() -> dict:
    return {
        "source_country": "AT",
        "attachment_acquisition_failure_count": 0,
        "partners": [
            {"partner_label": "A", "source_count": 1, "attachment_acquisition_complete": True},
            {"partner_label": "B", "source_count": 2, "attachment_acquisition_complete": True},
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


def test_review_bundle_binds_acquisition_manifest_and_optional_inputs():
    royalty = {
        "source_country": "AT",
        "partners": [{"partner_label": "A"}, {"partner_label": "B"}],
    }
    base = build_review_bundle_provenance(
        review_queue=_queue(),
        article_inventory=_articles(),
        acquisition_manifest=_manifest(),
        royalty_audit=royalty,
    )
    changed_manifest = _manifest()
    changed_manifest["partners"][0]["source_count"] = 3
    changed = build_review_bundle_provenance(
        review_queue=_queue(),
        article_inventory=_articles(),
        acquisition_manifest=changed_manifest,
        royalty_audit=royalty,
    )
    assert "acquisition_manifest" in base["input_digests"]
    assert "royalty_audit" in base["input_digests"]
    assert base["review_bundle_id"] != changed["review_bundle_id"]


def test_review_bundle_rejects_incomplete_acquisition_manifest():
    manifest = _manifest()
    manifest["attachment_acquisition_failure_count"] = 1
    manifest["partners"][0]["attachment_acquisition_complete"] = False
    with pytest.raises(ValueError, match="unresolved discovered attachments"):
        build_review_bundle_provenance(
            review_queue=_queue(),
            article_inventory=_articles(),
            acquisition_manifest=manifest,
        )

    manifest = _manifest()
    manifest["partners"][0]["source_count"] = 0
    with pytest.raises(ValueError, match="no archived official source"):
        build_review_bundle_provenance(
            review_queue=_queue(),
            article_inventory=_articles(),
            acquisition_manifest=manifest,
        )


def test_review_bundle_rejects_country_or_partner_universe_mixing():
    articles = _articles()
    articles["source_country"] = "SK"
    with pytest.raises(ValueError, match="source-country mismatch"):
        build_review_bundle_provenance(review_queue=_queue(), article_inventory=articles)

    articles = _articles()
    articles["partners"].pop()
    with pytest.raises(ValueError, match="treaty-partner universe mismatch"):
        build_review_bundle_provenance(review_queue=_queue(), article_inventory=articles)

    manifest = _manifest()
    manifest["partners"].pop()
    with pytest.raises(ValueError, match="acquisition_manifest treaty-partner universe mismatch"):
        build_review_bundle_provenance(
            review_queue=_queue(),
            article_inventory=_articles(),
            acquisition_manifest=manifest,
        )

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
