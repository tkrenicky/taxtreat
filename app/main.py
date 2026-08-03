from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from taxtreat.pipeline.release import RELEASE_MANIFEST, validate_release
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


@app.post("/analysis")
def analyze(payload: AnalysisPayload):
    result = analyze_transaction(
        CanonicalAnalysisRequest(
            source_country=payload.source_country.upper(),
            recipient_country=payload.recipient_country.upper(),
            income_type=payload.income_type,
            transaction_date=payload.transaction_date,
            facts=payload.facts,
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
        "eligible": result.eligible,
        "requires_review": result.requires_review,
        "selected_rule_id": result.selected_rule_id,
        "overridden_rule_id": result.overridden_rule_id,
        "missing_facts": result.missing_facts,
        "failed_conditions": result.failed_conditions,
        "explanation": result.explanation,
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
