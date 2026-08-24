from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "data" / "legal_reviews" / "at_outbound" / "mli_discovery_profile_2026.json"


def _profile() -> dict:
    return json.loads(PROFILE.read_text(encoding="utf-8"))


def test_at_mli_profile_is_discovery_only_and_requires_bilateral_adjudication():
    data = _profile()

    assert data["source_country"] == "AT"
    assert data["status"] == "discovery_only_bilateral_adjudication_required"
    method = data["bilateral_adjudication_method"]
    assert any("partner jurisdiction" in step for step in method)
    assert any("Article 35" in step for step in method)
    assert any("2023" in step for step in method)


def test_at_mli_profile_preserves_both_austrian_notification_layers():
    data = _profile()
    layers = data["austrian_notification_layers"]

    assert [row["deposit_or_notification_date"] for row in layers] == [
        "2017-09-22",
        "2023-08-28",
    ]
    assert layers[1]["publication"] == "BGBl. III Nr. 145/2023"
    assert layers[1]["effective_under_depositary_notification"] == "2023-08-30"


def test_bmf_implementation_snapshot_is_context_not_release_inventory():
    data = _profile()
    snapshot = data["bmf_implementation_snapshot"]

    assert snapshot["snapshot_date"] == "2025-09-30"
    assert snapshot["first_notification_treaties"] == 38
    assert snapshot["first_notification_in_force"] == 35
    assert snapshot["second_notification_treaties"] == 34
    assert snapshot["second_notification_in_force"] == 17
    assert snapshot["status"] == "context_only_not_bilateral_release_evidence"


def test_at_mli_release_constraints_fail_closed_on_pair_and_wht_effective_date():
    data = _profile()
    constraints = "\n".join(data["release_constraints"])

    assert "not sufficient evidence of bilateral MLI effect" in constraints
    assert "bilateral matching" in constraints
    assert "Article 35 effective-date analysis" in constraints


def test_ppt_alone_is_not_an_elevated_review_trigger():
    data = _profile()
    ppt = data["wht_relevant_article_seed"]["article_7_ppt"]

    assert "does not create elevated review classification" in ppt
