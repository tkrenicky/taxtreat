import json
from pathlib import Path

ROOT = (
    Path(__file__).parents[1]
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)


def load():
    return json.loads(
        (
            ROOT
            / "at_ch_existing_source_evidence.json"
        ).read_text(encoding="utf-8")
    )


def test_exact_country_sources_are_selected():
    payload = load()

    assert payload["schema_version"] == 3
    assert set(payload["countries"]) == {
        "AT",
        "CH",
    }

    assert payload["countries"]["AT"][
        "base_treaty"
    ]["source_title"] == "31/2007 Sb.m.s."

    assert payload["countries"]["CH"][
        "base_treaty"
    ]["source_title"] == "281/1996 Sb."


def test_base_artifacts_exist_and_match_hashes():
    payload = load()

    for country in ("AT", "CH"):
        base = payload["countries"][country][
            "base_treaty"
        ]

        assert base["artifact_exists"] is True
        assert base["hash_matches"] is True
        assert (
            payload["countries"][country][
                "base_source_identity_confirmed"
            ]
            is True
        )


def test_hashes_do_not_promote_legal_rules():
    payload = load()

    semantics = payload["evidence_semantics"]

    assert semantics[
        "hash_match_confirms_file_identity_only"
    ] is True

    assert semantics[
        "hash_match_confirms_legal_correctness"
    ] is False

    assert semantics[
        "external_official_source_verification_required"
    ] is True


def test_sources_remain_fail_closed():
    payload = load()

    assert payload["legal_verification_completed"] is False
    assert payload["clean_source_confirmed"] is False
    assert payload["fail_closed"] is True
    assert payload["promotable_to_active_rules"] is False

    for country in ("AT", "CH"):
        entry = payload["countries"][country]

        assert entry["production_ready"] is False
        assert entry["fail_closed"] is True
        assert (
            entry["promotable_to_active_rules"]
            is False
        )
