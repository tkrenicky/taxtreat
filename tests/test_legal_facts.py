import hashlib
import json
from datetime import date

import pytest

from taxtreat.engine.legal_facts import (
    load_legal_facts,
    resolve_legal_facts,
)


def write_facts(path, facts):
    path.write_text(
        json.dumps({"schema_version": 1, "facts": facts}),
        encoding="utf-8",
    )


def approved_fact(**overrides):
    payload = {
        "fact_id": "CH-FACT-1",
        "country": "CH",
        "name": "royalty_wht",
        "value": False,
        "effective_from": "2020-01-01",
        "verification_status": "verified",
        "source_id": "SRC-1",
        "source_url": "https://example.test/source",
        "source_excerpt_hash": hashlib.sha256(b"excerpt").hexdigest(),
        "reviewer_id": "reviewer-1",
        "reviewed_at": "2026-08-01",
        "approved_by": "approver-2",
        "approved_at": "2026-08-02",
        "dataset_release": "2026.08.1",
    }
    payload.update(overrides)
    return payload


def test_only_approved_effective_legal_fact_is_resolved(tmp_path):
    path = tmp_path / "facts.json"
    write_facts(path, [approved_fact()])

    resolved, unresolved = resolve_legal_facts(
        load_legal_facts(path),
        country="CH",
        as_of=date(2026, 8, 3),
    )

    assert resolved == {"royalty_wht": False}
    assert unresolved == []


def test_unapproved_or_conflicting_legal_facts_fail_closed(tmp_path):
    path = tmp_path / "facts.json"
    write_facts(
        path,
        [
            approved_fact(verification_status="needs_review"),
            approved_fact(fact_id="CH-FACT-2", value=True),
            approved_fact(fact_id="CH-FACT-3", value=False),
        ],
    )
    resolved, unresolved = resolve_legal_facts(
        load_legal_facts(path),
        country="CH",
        as_of=date(2026, 8, 3),
    )

    assert resolved == {}
    assert unresolved == ["royalty_wht"]


def test_legal_fact_loader_rejects_invalid_data(tmp_path):
    missing = tmp_path / "missing.json"
    missing.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="facts"):
        load_legal_facts(missing)

    duplicate = tmp_path / "duplicate.json"
    write_facts(duplicate, [approved_fact(), approved_fact()])
    with pytest.raises(ValueError, match="Duplicate"):
        load_legal_facts(duplicate)

    missing_date = tmp_path / "missing-date.json"
    write_facts(
        missing_date,
        [approved_fact(effective_from=None)],
    )
    with pytest.raises(ValueError, match="effective_from is required"):
        load_legal_facts(missing_date)

    interval = tmp_path / "interval.json"
    write_facts(
        interval,
        [approved_fact(effective_to="2019-12-31")],
    )
    with pytest.raises(ValueError, match="invalid date interval"):
        load_legal_facts(interval)
