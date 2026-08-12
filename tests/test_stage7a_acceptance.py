from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Mapping

from fastapi import HTTPException

from app.main import AnalysisPayload, analyze
from taxtreat.services.acceptance import (
    load_acceptance_fixture,
    render_acceptance_html,
    run_acceptance_suite,
    validate_case_result,
)


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "data/acceptance/stage7a_pilot.json"


def execute(request: Mapping[str, Any]) -> tuple[int, Mapping[str, Any]]:
    try:
        return 200, analyze(AnalysisPayload(**request))
    except HTTPException as exc:
        return exc.status_code, {"detail": exc.detail}


def test_stage7a_fixture_has_exact_pilot_matrix():
    fixture = load_acceptance_fixture(FIXTURE)
    cases = fixture["cases"]

    discovery = [
        case
        for case in cases
        if case["kind"] == "released_empty_fact_discovery"
    ]

    assert len(cases) == 17
    assert len(discovery) == 15
    assert {
        case["request"]["recipient_country"]
        for case in discovery
    } == {"AT", "CH", "DE", "SG", "TW"}
    assert {
        case["request"]["income_type"]
        for case in discovery
    } == {"dividend", "interest", "royalty"}
    assert fixture["semantics"][
        "discovery_is_not_legal_approval"
    ] is True


def test_stage7a_acceptance_matrix_passes_end_to_end():
    fixture = load_acceptance_fixture(FIXTURE)
    summary = run_acceptance_suite(fixture, execute)

    assert summary["case_count"] == 17
    assert summary["passed"] == 17
    assert summary["failed"] == 0
    assert len(summary["acceptance_sha256"]) == 64

    discovery = [
        result
        for result in summary["results"]
        if result["kind"] == "released_empty_fact_discovery"
    ]
    assert len(discovery) == 15
    assert all(
        result["status"] == "REVIEW_REQUIRED"
        for result in discovery
    )
    assert all(
        result["rate"] is None
        for result in discovery
    )
    assert all(
        result["missing_facts"]
        for result in discovery
    )
    assert all(
        result["citation_count"] >= 1
        for result in discovery
    )


def test_stage7a_acceptance_is_deterministic():
    fixture = load_acceptance_fixture(FIXTURE)

    first = run_acceptance_suite(fixture, execute)
    second = run_acceptance_suite(fixture, execute)

    assert first == second


def test_acceptance_html_contains_summary_and_escapes():
    fixture = load_acceptance_fixture(FIXTURE)
    summary = run_acceptance_suite(fixture, execute)
    hostile = copy.deepcopy(summary)
    hostile["results"][0]["case_id"] = "<script>alert(1)</script>"

    html = render_acceptance_html(hostile)
    normalized_html = " ".join(html.split())

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert summary["acceptance_sha256"] in html
    assert "17/17 passed" in html
    assert "do not constitute new legal review" in normalized_html


def test_invalid_fixture_semantics_fail_closed(tmp_path):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    invalid = [
        {**fixture, "schema_version": 2},
        {**fixture, "cases": fixture["cases"][:-1]},
        {
            **fixture,
            "semantics": {
                **fixture["semantics"],
                "discovery_is_not_legal_approval": False,
            },
        },
    ]

    for index, payload in enumerate(invalid):
        path = tmp_path / f"invalid-{index}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")

        try:
            load_acceptance_fixture(path)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid fixture must fail closed.")


def test_validator_reports_mismatches_and_bad_citations():
    fixture = load_acceptance_fixture(FIXTURE)
    case = copy.deepcopy(fixture["cases"][0])
    case["expected"]["minimum_official_citations"] = 2

    errors = validate_case_result(
        case,
        200,
        {
            "status": "FINAL",
            "rate": 10.0,
            "requires_review": False,
            "missing_facts": [],
            "citations": [
                {
                    "source_url": "http://invalid.example",
                    "excerpt_sha256": "short",
                }
            ],
            "legal_dataset_release": "wrong",
            "dataset_version": "wrong",
            "selected_rule_id": "invented",
        },
        legal_dataset_release=fixture["legal_dataset_release"],
        source_release=fixture["source_release"],
    )

    assert "status expected" in errors[0]
    assert any("missing facts" in error for error in errors)
    assert any("expected at least 2 citations" in error for error in errors)
    assert any("HTTPS" in error for error in errors)
    assert any("SHA-256" in error for error in errors)
    assert "legal dataset release mismatch" in errors
    assert "source release mismatch" in errors
    assert "empty-fact discovery selected a final rule" in errors


def test_validator_reports_fail_closed_error_mismatch():
    fixture = load_acceptance_fixture(FIXTURE)
    case = fixture["cases"][-2]

    errors = validate_case_result(
        case,
        500,
        {
            "detail": {
                "code": "WRONG",
                "release_status": "wrong",
                "release_blockers": [],
            }
        },
        legal_dataset_release=fixture["legal_dataset_release"],
        source_release=fixture["source_release"],
    )

    assert "http_status expected 409, got 500" in errors
    assert "error code mismatch" in errors
    assert "release status mismatch" in errors
    assert "release blockers mismatch" in errors
