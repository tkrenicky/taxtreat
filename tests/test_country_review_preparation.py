from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import pytest

from taxtreat.tools.run_country_review_preparation import prepare_country_review
from taxtreat.tools.validate_review_bundle_submission import validate_review_bundle_submission


def _queue() -> dict:
    return {
        "source_country": "AT",
        "status": "review_queue_not_released",
        "scopes": [
            {
                "partner_label": "Partner A",
                "income_type": income,
                "machine_mli_flag": False,
                "machine_status_instrument_flag": False,
                "instrument_chain": {"official_links": ["https://ris.bka.gv.at/example"]},
            }
            for income in ("dividend", "interest", "royalty")
        ],
    }


def _inventory(tmp_path: Path) -> dict:
    article_texts = {
        "dividend": "Article 10 Dividends. Tax shall not exceed 5 percent of the gross amount if the beneficial owner is a company.",
        "interest": "Article 11 Interest. Tax shall not exceed 10 percent of the gross amount if the recipient is the beneficial owner.",
        "royalty": "Article 12 Royalties. Tax shall not exceed 5 percent of the gross amount if the recipient is the beneficial owner of software royalties.",
    }
    candidates = []
    for number, income in ((10, "dividend"), (11, "interest"), (12, "royalty")):
        text = article_texts[income]
        path = tmp_path / f"{income}.txt"
        path.write_text(text, encoding="utf-8")
        candidates.append({
            "article_number": number,
            "substantive_article_candidate": True,
            "semantic_income_detected": income,
            "artifact_path": str(path),
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        })
    return {
        "source_country": "AT",
        "status": "article_text_candidates_not_reviewed",
        "partners": [{
            "partner_label": "Partner A",
            "sources": [{
                "final_url": "https://ris.bka.gv.at/example",
                "role_candidate": "current_consolidated_view",
                "article_candidates": candidates,
            }],
        }],
    }


def test_prepare_country_review_binds_all_rows_to_one_machine_bundle(tmp_path: Path):
    scope_evidence, review_pack = prepare_country_review(
        review_queue=_queue(),
        article_inventory=_inventory(tmp_path),
        artifact_root=tmp_path,
    )
    bundle_id = review_pack["review_bundle_id"]
    assert bundle_id.startswith("sha256:")
    assert scope_evidence["review_bundle_id"] == bundle_id
    assert review_pack["review_bundle_provenance"]["review_bundle_id"] == bundle_id
    assert {row["review_bundle_id"] for row in review_pack["rows"]} == {bundle_id}
    assert review_pack["review_ready_scope_count"] == 3
    assert all(row["content_hashes_verified"] is True for row in scope_evidence["scopes"])


def test_machine_input_change_invalidates_old_human_review_bundle(tmp_path: Path):
    inventory = _inventory(tmp_path)
    _, first = prepare_country_review(
        review_queue=_queue(),
        article_inventory=inventory,
        artifact_root=tmp_path,
    )
    changed = copy.deepcopy(inventory)
    changed["partners"][0]["sources"][0]["role_candidate"] = "published_instrument_or_protocol"
    _, second = prepare_country_review(
        review_queue=_queue(),
        article_inventory=changed,
        artifact_root=tmp_path,
    )
    assert first["review_bundle_id"] != second["review_bundle_id"]
    with pytest.raises(ValueError, match="identity does not match"):
        validate_review_bundle_submission(
            first,
            expected_review_bundle_id=second["review_bundle_id"],
        )


def test_prepare_country_review_rejects_optional_cross_run_partner_universe(tmp_path: Path):
    language = {
        "source_country": "AT",
        "partners": [{"partner_label": "Other Partner"}],
    }
    with pytest.raises(ValueError, match="language_evidence treaty-partner universe mismatch"):
        prepare_country_review(
            review_queue=_queue(),
            article_inventory=_inventory(tmp_path),
            artifact_root=tmp_path,
            language_evidence=language,
        )


def test_prepare_country_review_rejects_tampered_article_artifact(tmp_path: Path):
    inventory = _inventory(tmp_path)
    candidate = inventory["partners"][0]["sources"][0]["article_candidates"][0]
    Path(candidate["artifact_path"]).write_text("tampered treaty text", encoding="utf-8")
    with pytest.raises(ValueError, match="evidence hash mismatch"):
        prepare_country_review(
            review_queue=_queue(),
            article_inventory=inventory,
            artifact_root=tmp_path,
        )


def test_prepare_country_review_rejects_missing_article_hash(tmp_path: Path):
    inventory = _inventory(tmp_path)
    inventory["partners"][0]["sources"][0]["article_candidates"][0]["text_sha256"] = None
    with pytest.raises(ValueError, match="missing a valid text_sha256"):
        prepare_country_review(
            review_queue=_queue(),
            article_inventory=inventory,
            artifact_root=tmp_path,
        )
