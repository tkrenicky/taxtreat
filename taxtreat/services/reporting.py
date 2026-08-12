from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from html import escape
from typing import Any, Mapping


REPORT_SCHEMA_VERSION = 2
LEGAL_DATA_CUTOFF = "2026-08-12"
DISCLAIMER = (
    "TaxTreat is a deterministic legal-information and workflow tool. "
    "This report is not tax advice and does not replace review of the "
    "transaction, supporting documents, current law or official guidance "
    "by an appropriately qualified professional."
)


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def stable_report_id(
    request: Mapping[str, Any],
    analysis: Mapping[str, Any],
) -> str:
    fingerprint = {
        "request": dict(request),
        "result": {
            "status": analysis.get("status"),
            "rate": analysis.get("rate"),
            "candidate_rate": analysis.get("candidate_rate"),
            "selected_rule_id": analysis.get("selected_rule_id"),
            "candidate_rule_id": analysis.get("candidate_rule_id"),
            "missing_facts": analysis.get("missing_facts", []),
            "legal_dataset_release": analysis.get(
                "legal_dataset_release"
            ),
            "source_release": analysis.get("dataset_version"),
            "withholding_tax_calculation": analysis.get(
                "withholding_tax_calculation"
            ),
            "citation_hashes": sorted(
                citation.get("excerpt_sha256")
                for citation in analysis.get("citations", [])
                if citation.get("excerpt_sha256")
            ),
        },
    }
    digest = hashlib.sha256(
        _canonical_json(fingerprint).encode("utf-8")
    ).hexdigest()
    return f"TAXTREAT-{digest[:20].upper()}"


def build_professional_report(
    request: Mapping[str, Any],
    analysis: Mapping[str, Any],
    *,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(timezone.utc)
    status = str(analysis.get("status"))

    if status == "FINAL":
        risk = "Automated result available from the released rule catalog."
    elif status == "OUT_OF_SCOPE":
        risk = "The requested transaction is outside the supported scope."
    else:
        risk = (
            "Professional review is required before relying on a rate or "
            "relief outcome."
        )

    citations = [
        {
            "rule_id": citation.get("rule_id"),
            "source_id": citation.get("source_id"),
            "source_url": citation.get("source_url"),
            "article": citation.get("article"),
            "paragraph": citation.get("paragraph"),
            "excerpt": citation.get("excerpt"),
            "excerpt_sha256": citation.get("excerpt_sha256"),
        }
        for citation in analysis.get("citations", [])
    ]

    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report_id": stable_report_id(request, analysis),
        "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
        "legal_data_cutoff": LEGAL_DATA_CUTOFF,
        "legal_dataset_release": analysis.get("legal_dataset_release"),
        "source_release": analysis.get("dataset_version"),
        "scope": {
            "source_country": request.get("source_country"),
            "recipient_country": request.get("recipient_country"),
            "income_type": request.get("income_type"),
            "transaction_date": request.get("transaction_date"),
            "transaction_amount": request.get("transaction_amount"),
        },
        "result": {
            "status": analysis.get("status"),
            "rate": analysis.get("rate"),
            "candidate_rate": analysis.get("candidate_rate"),
            "eligible": analysis.get("eligible"),
            "requires_review": analysis.get("requires_review"),
            "selected_rule_id": analysis.get("selected_rule_id"),
            "candidate_rule_id": analysis.get("candidate_rule_id"),
            "applied_rule_ids": analysis.get("applied_rule_ids", []),
            "withholding_tax_calculation": analysis.get(
                "withholding_tax_calculation"
            ),
        },
        "assumptions": {
            "transaction_facts": request.get("facts", {}),
            "user_determinations": request.get("determinations", {}),
        },
        "missing_facts": analysis.get("missing_facts", []),
        "missing_legal_layers": analysis.get("missing_legal_layers", []),
        "failed_conditions": analysis.get("failed_conditions", []),
        "decision_path": analysis.get("layer_results", []),
        "explanation": analysis.get("explanation", []),
        "official_sources": citations,
        "risk_assessment": risk,
        "required_documentation": [
            "Transaction agreement and payment documentation",
            "Tax residence and beneficial-owner evidence",
            "Evidence supporting every supplied fact and determination",
            "Any required Czech exemption or administrative decision",
        ],
        "disclaimer": DISCLAIMER,
    }
    return report


def render_report_html(report: Mapping[str, Any]) -> str:
    scope = report["scope"]
    result = report["result"]
    sources = report.get("official_sources", [])
    calculation = result.get("withholding_tax_calculation")
    if calculation is None:
        calculation_html = "<p>No transaction amount was supplied.</p>"
    elif calculation["status"] == "CALCULATED":
        calculation_html = (
            "<p><strong>Gross amount:</strong> "
            f"{escape(str(calculation['gross_amount']))} "
            f"{escape(str(calculation['currency']))}<br>"
            "<strong>Estimated withholding tax:</strong> "
            f"{escape(str(calculation['estimated_tax_amount']))} "
            f"{escape(str(calculation['currency']))}<br>"
            "<strong>Estimated net amount:</strong> "
            f"{escape(str(calculation['estimated_net_amount']))} "
            f"{escape(str(calculation['currency']))}<br>"
            "<strong>Rounding:</strong> "
            f"{escape(str(calculation['rounding_policy']))}</p>"
        )
    else:
        calculation_html = (
            "<p>Amount supplied, but tax was not calculated because "
            "a final released rate is unavailable.</p>"
        )

    source_items = []
    for source in sources:
        url = escape(str(source.get("source_url") or ""), quote=True)
        label = escape(
            str(source.get("source_id") or source.get("rule_id") or "Source")
        )
        article = escape(str(source.get("article") or ""))
        source_items.append(
            f'<li><a href="{url}">{label}</a> — Article {article}</li>'
        )
    if not source_items:
        source_items.append("<li>No source citation was selected.</li>")

    missing = report.get("missing_facts", [])
    missing_items = "".join(
        f"<li>{escape(str(item))}</li>" for item in missing
    ) or "<li>None</li>"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>TaxTreat report {escape(str(report['report_id']))}</title>
  <style>
    body {{ font: 15px/1.5 system-ui, sans-serif; color: #18212b;
            max-width: 920px; margin: 40px auto; padding: 0 24px; }}
    header {{ border-bottom: 3px solid #163a5f; margin-bottom: 28px; }}
    h1, h2 {{ color: #163a5f; }}
    .meta {{ color: #536273; }}
    .result {{ background: #f3f7fa; border-left: 5px solid #163a5f;
               padding: 16px 20px; }}
    .warning {{ background: #fff7e6; padding: 14px 18px; }}
    code {{ overflow-wrap: anywhere; }}
  </style>
</head>
<body>
  <header>
    <h1>TaxTreat withholding-tax analysis</h1>
    <p class="meta">Report {escape(str(report['report_id']))}<br>
       Generated {escape(str(report['generated_at']))}<br>
       Legal-data cut-off {escape(str(report['legal_data_cutoff']))}</p>
  </header>
  <h2>Transaction scope</h2>
  <p>{escape(str(scope['source_country']))} →
     {escape(str(scope['recipient_country']))} ·
     {escape(str(scope['income_type']))} ·
     {escape(str(scope['transaction_date']))}</p>
  <section class="result">
    <h2>Result</h2>
    <p><strong>Status:</strong> {escape(str(result['status']))}<br>
       <strong>Rate:</strong> {escape(str(result['rate']))}<br>
       <strong>Candidate rate:</strong>
       {escape(str(result['candidate_rate']))}</p>
    <p>{escape(str(report['risk_assessment']))}</p>
  </section>
  <h2>Indicative amount calculation</h2>
  {calculation_html}
  <h2>Missing facts</h2><ul>{missing_items}</ul>
  <h2>Official sources</h2><ul>{''.join(source_items)}</ul>
  <h2>Release metadata</h2>
  <p>Legal rules: <code>{escape(str(report['legal_dataset_release']))}</code><br>
     Source release: <code>{escape(str(report['source_release']))}</code></p>
  <p class="warning">{escape(str(report['disclaimer']))}</p>
</body>
</html>
"""
