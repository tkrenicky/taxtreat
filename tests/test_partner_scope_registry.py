import json
from pathlib import Path

import pytest

from taxtreat.registry.legal_scope import (
    expected_legal_scopes,
    load_partner_registry,
    supported_scope_keys,
)


ROOT = Path(__file__).parents[1]


def test_registry_covers_every_parsed_treaty_once():
    partners = load_partner_registry()
    parsed_files = {path.name for path in (ROOT / "data" / "parsed").glob("*.json")}

    assert len(partners) == 100
    assert {partner["parsed_file"] for partner in partners} == parsed_files
    assert len({partner["iso2"] for partner in partners}) == 100
    assert {"AT", "CH", "DE", "US", "GB", "KR"}.issubset(
        {partner["iso2"] for partner in partners}
    )


def test_registry_expands_to_exactly_three_hundred_scopes():
    scopes = expected_legal_scopes()
    keys = supported_scope_keys()

    assert len(scopes) == 300
    assert len(keys) == 300
    assert {scope["income_type"] for scope in scopes} == {
        "dividend",
        "interest",
        "royalty",
    }


@pytest.mark.parametrize(
    "payload, message",
    [
        ({}, "JSON list"),
        ([{"country": "Test", "iso2": "T", "parsed_file": "x.json"}], "ISO-like"),
        ([{"country": "Test", "iso2": "TT", "parsed_file": "../x.json"}], "filename"),
        (
            [
                {"country": "One", "iso2": "TT", "parsed_file": "one.json"},
                {"country": "Two", "iso2": "TT", "parsed_file": "two.json"},
            ],
            "Duplicate",
        ),
    ],
)
def test_registry_validation_fails_closed(tmp_path, payload, message):
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_partner_registry(path)
