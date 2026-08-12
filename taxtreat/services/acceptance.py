from __future__ import annotations

import hashlib
import json
from html import escape
from pathlib import Path
from typing import Any, Callable, Mapping


Executor = Callable[[Mapping[str, Any]], tuple[int, Mapping[str, Any]]]


def load_acceptance_fixture(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))

    if payload.get("schema_version") != 1:
        raise ValueError("Stage 7A acceptance fixture requires schema version 1.")
    if len(payload.get("cases", [])) != 17:
        raise ValueError("Stage 7A acceptance fixture must contain 17 cases.")
    if payload.get("semantics", {}).get(
        "discovery_is_not_legal_approval"
    ) is not True:
        raise ValueError("Discovery fixtures must not claim legal approval.")

    return payload


def _official_citation_errors(
    citations: list[Mapping[str, Any]],
) -> list[str]:
    errors = []
    for citation in citations:
        url = citation.get("source_url")
        excerpt_hash = citation.get("excerpt_sha256")
        if not isinstance(url, str) or not url.startswith("https://"):
            errors.append("citation source_url is not official HTTPS")
        if not isinstance(excerpt_hash, str) or len(excerpt_hash) != 64:
            errors.append("citation excerpt hash is not SHA-256")
    return errors


def validate_case_result(
    case: Mapping[str, Any],
    http_status: int,
    body: Mapping[str, Any],
    *,
    legal_dataset_release: str,
    source_release: str,
) -> list[str]:
    expected = case["expected"]
    errors = []

    if http_status != expected["http_status"]:
        errors.append(
            f"http_status expected {expected['http_status']}, got {http_status}"
        )

    if http_status != 200:
        detail = body.get("detail", body)
        if detail.get("code") != expected.get("error_code"):
            errors.append("error code mismatch")
        if detail.get("release_status") != expected.get("release_status"):
            errors.append("release status mismatch")
        if detail.get("release_blockers") != expected.get(
            "release_blockers"
        ):
            errors.append("release blockers mismatch")
        return errors

    for field in ("status", "rate", "requires_review"):
        if body.get(field) != expected.get(field):
            errors.append(
                f"{field} expected {expected.get(field)!r}, "
                f"got {body.get(field)!r}"
            )

    if expected.get("missing_facts_nonempty") and not body.get(
        "missing_facts"
    ):
        errors.append("missing facts unexpectedly empty")

    citations = body.get("citations", [])
    minimum = expected.get("minimum_official_citations", 0)
    if len(citations) < minimum:
        errors.append(
            f"expected at least {minimum} citations, got {len(citations)}"
        )
    errors.extend(_official_citation_errors(citations))

    if case["kind"] == "released_empty_fact_discovery":
        if body.get("legal_dataset_release") != legal_dataset_release:
            errors.append("legal dataset release mismatch")
        if body.get("dataset_version") != source_release:
            errors.append("source release mismatch")
        if body.get("selected_rule_id") is not None:
            errors.append("empty-fact discovery selected a final rule")

    return errors


def run_acceptance_suite(
    fixture: Mapping[str, Any],
    executor: Executor,
) -> dict[str, Any]:
    results = []

    for case in fixture["cases"]:
        http_status, body = executor(case["request"])
        errors = validate_case_result(
            case,
            http_status,
            body,
            legal_dataset_release=fixture["legal_dataset_release"],
            source_release=fixture["source_release"],
        )
        results.append(
            {
                "case_id": case["case_id"],
                "kind": case["kind"],
                "passed": not errors,
                "errors": errors,
                "http_status": http_status,
                "status": body.get("status"),
                "rate": body.get("rate"),
                "candidate_rate": body.get("candidate_rate"),
                "missing_facts": body.get("missing_facts", []),
                "citation_count": len(body.get("citations", [])),
            }
        )

    canonical = json.dumps(
        results,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    passed = sum(result["passed"] for result in results)

    return {
        "schema_version": 1,
        "dataset_release": fixture["dataset_release"],
        "legal_dataset_release": fixture["legal_dataset_release"],
        "source_release": fixture["source_release"],
        "legal_data_cutoff": fixture["legal_data_cutoff"],
        "case_count": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "acceptance_sha256": hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest(),
        "results": results,
    }


def render_acceptance_html(summary: Mapping[str, Any]) -> str:
    rows = []
    for result in summary["results"]:
        outcome = "PASS" if result["passed"] else "FAIL"
        rows.append(
            "<tr>"
            f"<td>{escape(str(result['case_id']))}</td>"
            f"<td>{escape(outcome)}</td>"
            f"<td>{escape(str(result['http_status']))}</td>"
            f"<td>{escape(str(result.get('status') or 'HTTP_ERROR'))}</td>"
            f"<td>{escape(', '.join(result['errors']) or '—')}</td>"
            "</tr>"
        )

    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Stage 7A acceptance</title></head>
<body>
<h1>Stage 7A end-to-end acceptance</h1>
<p>Dataset: <code>{escape(str(summary['dataset_release']))}</code><br>
Cases: {summary['passed']}/{summary['case_count']} passed<br>
Acceptance SHA-256: <code>{escape(str(summary['acceptance_sha256']))}</code></p>
<table>
<thead><tr><th>Case</th><th>Result</th><th>HTTP</th><th>Status</th><th>Errors</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
<p>Discovery cases validate fail-closed behavior and report plumbing. They do
not constitute new legal review or approval.</p>
</body>
</html>
"""
