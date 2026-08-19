from __future__ import annotations

from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from taxtreat.services.sk_prerelease_decision import (
    evaluate_sk_prerelease_candidate,
)
from taxtreat.services.source_country_release_gate import (
    SourceCountryNotReleasedError,
    require_source_country_analysis_release,
)


class SkPrereleaseAnalysisPayload(BaseModel):
    recipient_country: str = Field(min_length=2, max_length=2)
    income_type: str
    facts: dict[str, Any] = Field(default_factory=dict)

    @field_validator("recipient_country")
    @classmethod
    def normalize_recipient_country(cls, value: str) -> str:
        return value.upper()

    @field_validator("income_type")
    @classmethod
    def normalize_income_type(cls, value: str) -> str:
        return value.lower()


router = APIRouter(tags=["SK prerelease"])


@router.post("/analysis/pre-release/sk")
def analyze_sk_prerelease(payload: SkPrereleaseAnalysisPayload):
    result = evaluate_sk_prerelease_candidate(
        recipient_country=payload.recipient_country,
        income_type=payload.income_type,
        facts=payload.facts,
    )
    response = result.as_dict()
    response["api_contract"] = "candidate_evidence_only"
    response["production_endpoint"] = False
    return response


@router.get("/analysis/pre-release/sk/release-gate")
def sk_prerelease_release_gate():
    try:
        require_source_country_analysis_release("SK")
    except SourceCountryNotReleasedError as exc:
        decision = exc.decision
        return {
            "source_country": "SK",
            "allowed": False,
            "code": decision.code,
            "release_status": decision.release_status,
            "blockers": list(decision.blockers),
        }
    raise HTTPException(
        status_code=500,
        detail={
            "code": "SK_PRERELEASE_GATE_UNEXPECTEDLY_OPEN",
            "message": "SK prerelease gate must remain closed before legal release.",
        },
    )


# Standalone preview app for offline API verification. The production FastAPI
# application must include `router` only after the integration tests are green.
preview_app = FastAPI(title="TaxTreat SK prerelease preview", version="0.1")
preview_app.include_router(router)
