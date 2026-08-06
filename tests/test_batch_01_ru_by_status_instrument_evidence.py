from __future__ import annotations

import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).parents[1]

EVIDENCE_PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "batch_01_ru_by"
    / "status_instrument_evidence.json"
)


def _payload():
    return json.loads(
        EVIDENCE_PATH.read_text(
            encoding="utf-8"
        )
    )


def test_batch_identity_and_fail_closed_status():
    payload = _payload()

    assert (
        payload["batch_id"]
        == "GLOBAL-CZ-OUTBOUND-BATCH-01"
    )
    assert payload["fail_closed"] is True
    assert payload["approval_eligible"] is False
    assert (
        payload["promotable_to_active_rules"]
        is False
    )


def test_russia_status_instrument_scope():
    ru = _payload()["countries"]["RU"]

    assert (
        ru["status_instrument"]["publication"]
        == "36/2023 Sb. m. s."
    )
    assert (
        ru["status_instrument"]["effective_from"]
        == "2023-08-11"
    )

    affected = set(
        ru["status_instrument"][
            "affected_articles"
        ]
    )

    assert {"10", "11", "12"} <= affected

    for income_type in (
        "dividend",
        "interest",
        "royalty",
    ):
        effect = ru[
            "preliminary_scope_effects"
        ][income_type]

        assert (
            effect["article_application_status"]
            == "suspended"
        )
        assert (
            effect[
                "requires_domestic_fallback_review"
            ]
            is True
        )


def test_belarus_status_instrument_scope():
    by = _payload()["countries"]["BY"]

    assert (
        by["status_instrument"]["publication"]
        == "115/2024 Sb."
    )
    assert (
        by["status_instrument"]["effective_from"]
        == "2024-06-01"
    )
    assert (
        by["status_instrument"]["effective_to"]
        == "2026-12-31"
    )

    affected = set(
        by["status_instrument"][
            "affected_articles"
        ]
    )

    assert affected == {"10", "11", "13"}

    assert (
        by["preliminary_scope_effects"]
        ["dividend"]
        ["article_application_status"]
        == "suspended"
    )
    assert (
        by["preliminary_scope_effects"]
        ["interest"]
        ["article_application_status"]
        == "suspended"
    )
    assert (
        by["preliminary_scope_effects"]
        ["royalty"]
        ["article_application_status"]
        == "not_listed_as_suspended"
    )


def test_belarus_suspension_is_current_on_release_date():
    by = _payload()["countries"]["BY"]
    instrument = by["status_instrument"]

    release_date = date(2026, 8, 6)

    assert (
        date.fromisoformat(
            instrument["effective_from"]
        )
        <= release_date
        <= date.fromisoformat(
            instrument["effective_to"]
        )
    )


def test_all_sources_are_identified():
    for country in (
        _payload()["countries"].values()
    ):
        assert country[
            "base_treaty"
        ]["official_reference"]

        assert country[
            "protocol"
        ]["official_reference"]

        assert country[
            "status_instrument"
        ]["official_reference"]
