import json
from pathlib import Path

import pytest

from taxtreat.engine.source_release_gate import (
    SourceGateConfigurationError,
    SourceNotReleasedError,
    get_source_release,
    load_source_release_gate,
    require_released_source,
    source_is_released,
)

ROOT = Path(__file__).parents[1]

GATE_PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "production_source_release_gate.json"
)


def write_gate(tmp_path, treaty_entry, **overrides):
    payload = {
        "treaty_partner_count": 1,
        "treaty_partners": [treaty_entry],
        "fail_closed": True,
    }
    payload.update(overrides)

    path = tmp_path / "gate.json"
    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    return path


def released_entry():
    return {
        "treaty_pair_id": "CZ-XX",
        "partner_country": "XX",
        "release_status": "released",
        "active_rule_allowed": True,
        "production_ready": True,
        "fail_closed": False,
        "release_blockers": [],
        "release_evidence": {
            "official_document_sha256": "abc",
        },
    }


def test_current_global_gate_loads_all_partners():
    load_source_release_gate.cache_clear()

    releases = load_source_release_gate(GATE_PATH)

    assert len(releases) == 98
    assert "CZ-AT" in releases
    assert "CZ-CH" in releases


def test_current_entries_are_blocked():
    load_source_release_gate.cache_clear()

    release = get_source_release(
        "CZ-AT",
        gate_path=GATE_PATH,
    )

    assert release.is_released is False
    assert release.fail_closed is True
    assert release.release_blockers

    with pytest.raises(SourceNotReleasedError):
        require_released_source(
            "CZ-AT",
            gate_path=GATE_PATH,
        )

    assert source_is_released(
        "CZ-AT",
        gate_path=GATE_PATH,
    ) is False


def test_unknown_pair_fails_closed():
    load_source_release_gate.cache_clear()

    with pytest.raises(SourceNotReleasedError):
        get_source_release(
            "CZ-ZZ",
            gate_path=GATE_PATH,
        )

    assert source_is_released(
        "CZ-ZZ",
        gate_path=GATE_PATH,
    ) is False


def test_fully_released_entry_is_allowed(tmp_path):
    gate_path = write_gate(
        tmp_path,
        released_entry(),
    )

    load_source_release_gate.cache_clear()

    release = require_released_source(
        "cz-xx",
        gate_path=gate_path,
    )

    assert release.is_released is True
    assert source_is_released(
        "CZ-XX",
        gate_path=gate_path,
    ) is True


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("release_status", "blocked"),
        ("active_rule_allowed", False),
        ("production_ready", False),
        ("fail_closed", True),
        ("release_blockers", ["missing_evidence"]),
    ],
)
def test_partial_release_is_never_allowed(
    tmp_path,
    field,
    value,
):
    entry = released_entry()
    entry[field] = value

    gate_path = write_gate(
        tmp_path,
        entry,
    )

    load_source_release_gate.cache_clear()

    with pytest.raises(SourceNotReleasedError):
        require_released_source(
            "CZ-XX",
            gate_path=gate_path,
        )


def test_missing_gate_file_fails_closed(tmp_path):
    load_source_release_gate.cache_clear()

    with pytest.raises(SourceGateConfigurationError):
        load_source_release_gate(
            tmp_path / "missing.json"
        )


def test_invalid_global_gate_is_rejected(tmp_path):
    gate_path = write_gate(
        tmp_path,
        released_entry(),
        fail_closed=False,
    )

    load_source_release_gate.cache_clear()

    with pytest.raises(SourceGateConfigurationError):
        load_source_release_gate(gate_path)


def test_duplicate_pair_is_rejected(tmp_path):
    entry = released_entry()

    payload = {
        "treaty_partner_count": 2,
        "treaty_partners": [entry, entry],
        "fail_closed": True,
    }

    gate_path = tmp_path / "gate.json"
    gate_path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    load_source_release_gate.cache_clear()

    with pytest.raises(SourceGateConfigurationError):
        load_source_release_gate(gate_path)
