import hashlib
import json
from pathlib import Path

import pytest

from taxtreat.engine.legal_facts import (
    load_legal_facts,
    resolve_legal_fact_candidates,
)
from taxtreat.engine.legal_rule_loader import load_legal_rules
from taxtreat.engine.legal_sources import (
    load_legal_sources,
    validate_evidence_references,
)
from taxtreat.services.legal_sources import (
    build_legal_path,
    load_verified_provisions,
)


def test_pilot_rules_reference_only_registered_official_sources():
    sources = load_legal_sources("data/legal_sources/pilot_at_ch.json")
    assert len(sources) == 10

    for path in sorted(Path("data/legal_rules").glob("*.json")):
        for rule in load_legal_rules(path):
            assert not validate_evidence_references(
                [rule.source_id, *rule.evidence_source_ids], sources
            )
            assert rule.source_excerpt_hash == hashlib.sha256(
                rule.source_text.encode("utf-8")
            ).hexdigest()


def test_swiss_legal_fact_is_review_ready_but_not_verified():
    facts = load_legal_facts("data/legal_facts/svycarsko.json")
    assert len(facts) == 1
    assert facts[0].is_review_ready is True
    assert facts[0].is_verified is False

    values, unverified = resolve_legal_fact_candidates(
        facts,
        country="CH",
        as_of=facts[0].effective_from,
    )
    assert values == {
        "recipient_country_imposes_royalty_wht_on_nonresidents": False
    }
    assert unverified == [
        "recipient_country_imposes_royalty_wht_on_nonresidents"
    ]


def test_legal_source_loader_rejects_invalid_registries(tmp_path):
    def write(name, sources):
        path = tmp_path / name
        path.write_text(json.dumps({"sources": sources}), encoding="utf-8")
        return path

    source = {
        "source_id": "SOURCE",
        "title": "Title",
        "authority": "Authority",
        "authority_class": "official",
        "url": "https://example.test/source",
        "retrieved_at": "2026-08-03",
    }
    bad_shape = tmp_path / "shape.json"
    bad_shape.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="sources"):
        load_legal_sources(bad_shape)
    with pytest.raises(ValueError, match="Duplicate"):
        load_legal_sources(write("duplicate.json", [source, source]))
    with pytest.raises(ValueError, match="not an official"):
        load_legal_sources(
            write("mirror.json", [{**source, "authority_class": "mirror"}])
        )
    with pytest.raises(ValueError, match="HTTPS"):
        load_legal_sources(
            write("http.json", [{**source, "url": "http://example.test"}])
        )

    registered = load_legal_sources(write("valid.json", [source]))
    assert validate_evidence_references(
        [None, "SOURCE", "MISSING"], registered
    ) == ["MISSING"]


def test_verified_austrian_article_has_complete_czech_diacritics():
    provision = load_verified_provisions()["CZ-AT|treaty|10"]

    assert provision["text"].startswith("Článek 10\nDIVIDENDY\n")
    assert "skutečný vlastník" in provision["text"]
    assert "stálé provozovně" in provision["text"]
    assert "spolecnostõ" not in provision["text"]
    assert provision["source_url"].startswith("https://e-sbirka.gov.cz/")


def test_legal_path_keeps_domestic_start_before_selected_treaty():
    citations = [
        {
            "rule_id": "TREATY-10",
            "legal_layer": "treaty",
            "article": "10",
            "source_url": "https://example.test/treaty",
            "rate": 10.0,
        },
        {
            "rule_id": "DOMESTIC-15",
            "legal_layer": "domestic",
            "article": "36",
            "source_url": "https://example.test/domestic",
            "rate": 15.0,
        },
    ]

    path = build_legal_path(
        citations,
        source_country="CZ",
        recipient_country="AT",
        selected_rule_id="TREATY-10",
    )

    assert [item["rule_id"] for item in path] == [
        "DOMESTIC-15",
        "TREATY-10",
    ]
    assert "official_text" in path[1]


@pytest.mark.parametrize("income_type", ["dividend", "interest", "royalty"])
def test_legal_path_restores_missing_czech_domestic_starting_point(
    income_type: str,
):
    path = build_legal_path(
        [
            {
                "rule_id": "TREATY-10",
                "legal_layer": "treaty",
                "article": "10",
                "source_url": "https://example.test/treaty",
                "rate": 10.0,
            }
        ],
        source_country="CZ",
        recipient_country="AT",
        selected_rule_id="TREATY-10",
        income_type=income_type,
    )

    assert [(item["legal_layer"], item["rate"]) for item in path] == [
        ("domestic", 15.0),
        ("treaty", 10.0),
    ]
    assert path[0]["path_role"] == "domestic_starting_point"
    assert "zákona č. 586/1992 Sb." in path[0]["excerpt"]
