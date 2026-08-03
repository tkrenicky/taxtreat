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
