from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from taxtreat.pipeline.release import (
    LEGAL_REGISTRY,
    RELEASE_MANIFEST,
    build_legal_registry,
    validate_release,
)
from taxtreat.engine.source_release_gate import (
    SourceNotReleasedError,
    get_source_release,
)
from taxtreat.registry.legal_scope import load_partner_registry
from taxtreat.services.decision import (
    CanonicalAnalysisRequest,
    analyze_transaction,
)


ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="TaxTreat", version="0.2.0")


class AnalysisPayload(BaseModel):
    source_country: str = Field(min_length=2, max_length=2)
    recipient_country: str = Field(min_length=2, max_length=2)
    income_type: str
    transaction_date: date
    facts: dict[str, Any] = Field(default_factory=dict)
    determinations: dict[str, Any] = Field(default_factory=dict)


def get_db_connection() -> sqlite3.Connection:
    db_path = ROOT / "taxtreat.db"
    if not db_path.is_file():
        raise FileNotFoundError("The treaty database has not been built.")
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/")
def read_root():
    return {"name": "TaxTreat", "version": app.version}


@app.get("/health/live")
def liveness():
    return {"status": "ok"}


@app.get("/health/ready")
def readiness():
    try:
        validate_release(production=True)
    except (OSError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "ready"}


@app.get("/health")
def health_check():
    """Backward-compatible liveness alias."""
    return liveness()


@app.get("/jurisdictions")
def list_jurisdictions():
    registry = (
        json.loads(LEGAL_REGISTRY.read_text(encoding="utf-8"))
        if LEGAL_REGISTRY.exists()
        else build_legal_registry()
    )
    review_ready = {
        (scope["recipient_country"], scope["income_type"])
        for scope in registry["scopes"]
        if scope["review_ready"]
    }
    base_candidate = {
        (scope["recipient_country"], scope["income_type"])
        for scope in registry["scopes"]
        if scope["base_candidate_status"]
        == "base_rate_candidate_extracted"
    }
    protocol_candidate = {
        (scope["recipient_country"], scope["income_type"])
        for scope in registry["scopes"]
        if scope["protocol_candidate_status"]
        == "protocol_effect_candidate_consolidated"
    }
    domestic_candidate = {
        (scope["recipient_country"], scope["income_type"])
        for scope in registry["scopes"]
        if scope["domestic_candidate_status"]
        == "domestic_and_relief_candidate_consolidated"
    }
    eu_relief_candidate = {
        (scope["recipient_country"], scope["income_type"])
        for scope in registry["scopes"]
        if scope["eu_relief_candidate_status"]
        == "relief_candidate_consolidated"
    }
    manual_rate_extraction = {
        (scope["recipient_country"], scope["income_type"])
        for scope in registry["scopes"]
        if scope["base_candidate_status"]
        == "manual_rate_extraction_required"
    }
    candidate_chain_assembled = {
        (scope["recipient_country"], scope["income_type"])
        for scope in registry["scopes"]
        if scope["candidate_chain_status"]
        in {"candidate_chain_assembled", "pilot_consolidated"}
    }
    candidate_chain_blocked = {
        (scope["recipient_country"], scope["income_type"])
        for scope in registry["scopes"]
        if scope["candidate_chain_status"] == "candidate_chain_blocked"
    }
    candidate_review_queued = {
        (scope["recipient_country"], scope["income_type"])
        for scope in registry["scopes"]
        if scope["candidate_review_packet_id"] is not None
    }
    candidate_review_approved = {
        (scope["recipient_country"], scope["income_type"])
        for scope in registry["scopes"]
        if scope["candidate_review_promotable"]
    }
    jurisdictions = []
    for partner in load_partner_registry():
        jurisdictions.append(
            {
                "country": partner["country"],
                "iso2": partner["iso2"],
                "income_types": ["dividend", "interest", "royalty"],
                "review_ready_income_types": [
                    income_type
                    for income_type in ("dividend", "interest", "royalty")
                    if (partner["iso2"], income_type) in review_ready
                ],
                "base_candidate_income_types": [
                    income_type
                    for income_type in ("dividend", "interest", "royalty")
                    if (partner["iso2"], income_type) in base_candidate
                ],
                "protocol_candidate_income_types": [
                    income_type
                    for income_type in ("dividend", "interest", "royalty")
                    if (partner["iso2"], income_type) in protocol_candidate
                ],
                "domestic_candidate_income_types": [
                    income_type
                    for income_type in ("dividend", "interest", "royalty")
                    if (partner["iso2"], income_type) in domestic_candidate
                ],
                "eu_relief_candidate_income_types": [
                    income_type
                    for income_type in ("dividend", "interest", "royalty")
                    if (partner["iso2"], income_type) in eu_relief_candidate
                ],
                "manual_rate_extraction_income_types": [
                    income_type
                    for income_type in ("dividend", "interest", "royalty")
                    if (partner["iso2"], income_type)
                    in manual_rate_extraction
                ],
                "candidate_chain_assembled_income_types": [
                    income_type
                    for income_type in ("dividend", "interest", "royalty")
                    if (partner["iso2"], income_type)
                    in candidate_chain_assembled
                ],
                "candidate_chain_blocked_income_types": [
                    income_type
                    for income_type in ("dividend", "interest", "royalty")
                    if (partner["iso2"], income_type)
                    in candidate_chain_blocked
                ],
                "candidate_review_queued_income_types": [
                    income_type
                    for income_type in ("dividend", "interest", "royalty")
                    if (partner["iso2"], income_type)
                    in candidate_review_queued
                ],
                "candidate_review_approved_income_types": [
                    income_type
                    for income_type in ("dividend", "interest", "royalty")
                    if (partner["iso2"], income_type)
                    in candidate_review_approved
                ],
            }
        )
    return {"total": len(jurisdictions), "jurisdictions": jurisdictions}


def require_analysis_source_release(
    source_country: str,
    recipient_country: str,
):
    source = source_country.upper()
    recipient = recipient_country.upper()

    if source != "CZ":
        return None

    treaty_pair_id = f"{source}-{recipient}"

    try:
        release = get_source_release(treaty_pair_id)
    except SourceNotReleasedError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "SOURCE_NOT_RELEASED",
                "treaty_pair_id": treaty_pair_id,
                "message": str(exc),
                "release_status": "not_registered",
                "release_blockers": [
                    "production_source_release_missing"
                ],
            },
        ) from exc

    if not release.is_released:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "SOURCE_NOT_RELEASED",
                "treaty_pair_id": treaty_pair_id,
                "message": (
                    "The legal source package has not completed "
                    "the production release gate."
                ),
                "release_status": release.release_status,
                "release_blockers": list(
                    release.release_blockers
                ),
            },
        )

    return release


@app.post("/analysis")
def analyze(payload: AnalysisPayload):
    source_country = payload.source_country.upper()
    recipient_country = payload.recipient_country.upper()

    require_analysis_source_release(
        source_country,
        recipient_country,
    )

    result = analyze_transaction(
        CanonicalAnalysisRequest(
            source_country=source_country,
            recipient_country=recipient_country,
            income_type=payload.income_type,
            transaction_date=payload.transaction_date,
            facts=payload.facts,
            determinations=payload.determinations,
        )
    )
    dataset_version = "unreleased"
    if RELEASE_MANIFEST.exists():
        dataset_version = json.loads(
            RELEASE_MANIFEST.read_text(encoding="utf-8")
        ).get("dataset_version", dataset_version)
    return {
        "status": result.status.value,
        "rate": result.rate,
        "candidate_rate": result.candidate_rate,
        "eligible": result.eligible,
        "requires_review": result.requires_review,
        "selected_rule_id": result.selected_rule_id,
        "candidate_rule_id": result.candidate_rule_id,
        "applied_rule_ids": result.applied_rule_ids,
        "overridden_rule_id": result.overridden_rule_id,
        "missing_facts": result.missing_facts,
        "missing_legal_layers": result.missing_legal_layers,
        "failed_conditions": result.failed_conditions,
        "explanation": result.explanation,
        "citations": result.citations,
        "layer_results": result.layer_results,
        "legal_dataset_release": result.dataset_release,
        "dataset_version": dataset_version,
    }


@app.get("/treaties")
def list_treaties():
    try:
        conn = get_db_connection()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    try:
        rows = conn.execute(
            "SELECT id, country_a_id, country_b_id, treaty_type, signed_date, "
            "effective_from, effective_to, status FROM treaties"
        ).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=503,
            detail="The treaty database schema is not ready.",
        ) from exc
    finally:
        conn.close()
