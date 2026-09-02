from __future__ import annotations

import json
import sqlite3
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from taxtreat.pipeline.release import (
    LEGAL_REGISTRY,
    RELEASE_MANIFEST,
    build_legal_registry,
    validate_release,
)
from taxtreat.engine.source_release_gate_v2 import (
    CanonicalSourceNotReleasedError,
    get_canonical_source_release,
    load_canonical_source_release_gate,
)
from taxtreat.registry.legal_scope import load_partner_registry
from taxtreat.services.calculation import (
    build_withholding_compliance_schedule,
    build_withholding_tax_calculation,
)
from taxtreat.services.source_country_calculation import (
    build_source_country_withholding_compliance_schedule,
    build_source_country_withholding_tax_calculation,
)
from taxtreat.services.source_country_runtime_metadata import (
    source_country_runtime_dataset_version,
)
from taxtreat.services.decision import (
    CanonicalAnalysisRequest,
    analyze_transaction,
)
from taxtreat.services.intake import build_intake_plan
from taxtreat.services.legal_sources import build_legal_path
from taxtreat.services.exchange_rates import (
    CnbRateUnavailableError,
    fetch_cnb_exchange_rate,
)
from taxtreat.services.reporting import (
    build_professional_report,
    render_report_html,
)
from taxtreat.services.web_locale_engine import (
    localize_intake_response,
    render_workspace_asset,
    render_workspace_document,
)
from taxtreat.services.source_country_release_gate import (
    SourceCountryNotReleasedError,
    UnsupportedSourceCountryError,
    require_source_country_analysis_release,
)
from app.sk_prerelease import router as sk_prerelease_router


ROOT = Path(__file__).resolve().parent.parent
WEB_ROOT = ROOT / "app" / "web"
STAGE6_SOURCE_RELEASE = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "stage6_source_release.json"
)
app = FastAPI(title="TaxTreat", version="0.2.0")
app.mount(
    "/ui-assets",
    StaticFiles(directory=WEB_ROOT),
    name="ui-assets",
)
app.include_router(sk_prerelease_router)


class CnbExchangeRate(BaseModel):
    source: str = Field(pattern=r"^(?i:CNB)$")
    currency: str = Field(pattern=r"^[A-Za-z]{3}$")
    czk_per_unit: Decimal = Field(
        gt=0,
        max_digits=30,
        decimal_places=12,
    )
    effective_date: date
    source_url: str = Field(pattern=r"^https://")
    entry_method: Literal["automatic", "manual_override"] = "automatic"
    cnb_reference_czk_per_unit: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=30,
        decimal_places=12,
    )

    @field_validator("source", "currency")
    @classmethod
    def normalize_codes(cls, value: str) -> str:
        return value.upper()


class SkExchangeRate(BaseModel):
    source: str = Field(pattern=r"^(?i:ECB|NBS)$")
    currency: str = Field(pattern=r"^[A-Za-z]{3}$")
    foreign_units_per_eur: Decimal = Field(
        gt=0,
        max_digits=30,
        decimal_places=12,
    )
    effective_date: date
    source_url: str = Field(pattern=r"^https://")
    entry_method: Literal["automatic", "manual_override"] = "automatic"

    @field_validator("source", "currency")
    @classmethod
    def normalize_codes(cls, value: str) -> str:
        return value.upper()


class TransactionAmount(BaseModel):
    amount: Decimal = Field(
        gt=0,
        max_digits=30,
        decimal_places=8,
    )
    currency: str = Field(
        min_length=3,
        max_length=3,
        pattern=r"^[A-Za-z]{3}$",
    )
    payment_date: date | None = None
    accounting_date: date | None = None
    exchange_rate: CnbExchangeRate | SkExchangeRate | None = None
    prior_same_type_monthly_amount_czk: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=30,
        decimal_places=2,
    )

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class AnalysisPayload(BaseModel):
    source_country: str = Field(min_length=2, max_length=2)
    recipient_country: str = Field(min_length=2, max_length=2)
    income_type: str
    transaction_date: date
    facts: dict[str, Any] = Field(default_factory=dict)
    determinations: dict[str, Any] = Field(default_factory=dict)
    transaction_amount: TransactionAmount | None = None


@app.get("/exchange-rates/cnb")
def cnb_exchange_rate(currency: str, date: date):
    try:
        return fetch_cnb_exchange_rate(currency, date)
    except CnbRateUnavailableError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "CNB_RATE_UNAVAILABLE",
                "message": str(exc),
            },
        ) from exc


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


@app.get("/ui", include_in_schema=False)
def guided_intake_ui(lang: Literal["cs", "en"] = "cs"):
    return HTMLResponse(
        render_workspace_document(WEB_ROOT, lang),
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


@app.get("/ui/{lang}", include_in_schema=False)
def guided_intake_ui_locale(lang: Literal["cs", "en"]):
    return HTMLResponse(
        render_workspace_document(WEB_ROOT, lang),
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


@app.get("/ui-engine/{lang}/{asset_path:path}", include_in_schema=False)
def guided_intake_ui_engine(lang: Literal["cs", "en"], asset_path: str):
    try:
        content = render_workspace_asset(WEB_ROOT, asset_path, lang)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Unknown UI engine asset") from exc
    return Response(
        content=content,
        media_type="application/javascript",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


@app.get("/workspace-demo", include_in_schema=False)
def workspace_demo_ui():
    return FileResponse(
        WEB_ROOT / "workspace.html",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/design-lab/{design}", include_in_schema=False)
def workspace_design_ui(design: str):
    if design not in {"editorial", "atlas", "civic"}:
        raise HTTPException(status_code=404, detail="Unknown design")
    return FileResponse(
        WEB_ROOT / "workspace.html",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/design-lab", include_in_schema=False)
def design_lab_ui():
    return FileResponse(
        WEB_ROOT / "design-lab.html",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/health/live")
def liveness():
    return {"status": "ok"}


def load_stage6_source_release() -> dict[str, Any]:
    if not STAGE6_SOURCE_RELEASE.is_file():
        raise RuntimeError(
            "Stage 6 source-release manifest is missing."
        )

    payload = json.loads(
        STAGE6_SOURCE_RELEASE.read_text(encoding="utf-8")
    )
    counts = payload.get("counts", {})

    if counts.get("released_packages") != 101:
        raise RuntimeError(
            "Stage 6 source release must contain 101 packages."
        )
    if counts.get("released_scopes") != 303:
        raise RuntimeError(
            "Stage 6 source release must contain 303 scopes."
        )
    if not payload.get("dataset_release"):
        raise RuntimeError(
            "Stage 6 source release has no dataset identifier."
        )

    return payload


def validate_stage6_runtime_release() -> dict[str, Any]:
    source_release = load_stage6_source_release()
    gate = load_canonical_source_release_gate()

    if len(gate) != 101 or not all(
        release.is_released for release in gate.values()
    ):
        raise RuntimeError(
            "Canonical Stage 6 runtime release is incomplete."
        )

    return {
        "dataset_release": source_release["dataset_release"],
        "released_packages": 101,
        "released_scopes": 303,
    }


@app.get("/health/ready")
def readiness():
    try:
        release = validate_stage6_runtime_release()
    except (OSError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "ready", "release": release}


@app.get("/health")
def health_check():
    """Backward-compatible liveness alias."""
    return liveness()


def _normalize_ares_subject(payload: dict[str, Any]) -> dict[str, Any]:
    sidlo = payload.get("sidlo") or {}
    data_boxes = payload.get("datoveSchranky") or []
    data_box = ""
    if isinstance(data_boxes, list) and data_boxes:
        first = data_boxes[0]
        if isinstance(first, dict):
            data_box = str(first.get("datovaSchranka") or first.get("idDatoveSchranky") or "")
        elif first:
            data_box = str(first)

    address = str(sidlo.get("textovaAdresa") or "").strip()
    if not address:
        street = str(sidlo.get("nazevUlice") or sidlo.get("nazevCastiObce") or "").strip()
        house = str(sidlo.get("cisloDomovni") or "").strip()
        orientation = str(sidlo.get("cisloOrientacni") or "").strip()
        number = house + (f"/{orientation}" if orientation else "")
        municipality = str(sidlo.get("nazevObce") or "").strip()
        psc = str(sidlo.get("psc") or "").strip()
        address = " ".join(part for part in (street, number) if part).strip()
        locality = " ".join(part for part in (psc, municipality) if part).strip()
        address = ", ".join(part for part in (address, locality) if part)

    return {
        "source": "ARES",
        "source_url": f"https://ares.gov.cz/ekonomicke-subjekty?ico={payload.get('ico', '')}",
        "ico": str(payload.get("ico") or ""),
        "name": str(payload.get("obchodniJmeno") or ""),
        "vat_id": str(payload.get("dic") or ""),
        "address": address,
        "legal_form": str(payload.get("pravniForma") or ""),
        "data_box": data_box,
        "established_at": str(payload.get("datumVzniku") or ""),
    }


@app.get("/company-registry/ares/{ico}")
def company_registry_ares(ico: str):
    normalized_ico = "".join(character for character in ico if character.isdigit())
    if len(normalized_ico) != 8:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_ICO", "message": "IČO musí obsahovat 8 číslic."},
        )

    url = (
        "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/"
        f"ekonomicke-subjekty/{normalized_ico}"
    )
    request = Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "TaxTreat/0.2 (+https://taxtreat.vercel.app)"},
    )
    try:
        with urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            raise HTTPException(
                status_code=404,
                detail={"code": "ARES_NOT_FOUND", "message": "Subjekt s tímto IČO nebyl v ARES nalezen."},
            ) from exc
        raise HTTPException(
            status_code=502,
            detail={"code": "ARES_UNAVAILABLE", "message": "ARES nyní není dostupný."},
        ) from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=502,
            detail={"code": "ARES_UNAVAILABLE", "message": "ARES nyní není dostupný."},
        ) from exc

    if not isinstance(payload, dict) or not payload.get("ico"):
        raise HTTPException(
            status_code=502,
            detail={"code": "ARES_INVALID_RESPONSE", "message": "ARES vrátil neočekávanou odpověď."},
        )
    return _normalize_ares_subject(payload)


@app.get("/jurisdictions")
def list_jurisdictions(source_country: str = "CZ"):
    source = str(source_country or "CZ").upper()
    if source == "SK":
        jurisdictions = [
            {
                "country": partner["country"],
                "iso2": partner["iso2"],
                "income_types": ["dividend", "interest", "royalty"],
                "review_ready_income_types": ["dividend", "interest", "royalty"],
                "base_candidate_income_types": [],
                "protocol_candidate_income_types": [],
                "domestic_candidate_income_types": ["dividend", "interest", "royalty"],
                "eu_relief_candidate_income_types": [],
                "manual_rate_extraction_income_types": [],
                "candidate_chain_assembled_income_types": ["dividend", "interest", "royalty"],
                "candidate_chain_blocked_income_types": [],
                "candidate_review_queued_income_types": [],
                "candidate_review_approved_income_types": [],
            }
            for partner in load_partner_registry(source_country="SK")
        ]
        return {"total": len(jurisdictions), "jurisdictions": jurisdictions}
    if source != "CZ":
        raise HTTPException(
            status_code=400,
            detail={"code": "UNSUPPORTED_SOURCE_COUNTRY", "source_country": source},
        )

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
    # Taiwan is supported by the production runtime through Czech domestic
    # withholding-tax rules even though it is not a Czech treaty partner.
    # `/jurisdictions` is a product-support catalog, not merely a treaty list.
    jurisdictions.append(
        {
            "country": "Tchaj-wan",
            "iso2": "TW",
            "income_types": ["dividend", "interest", "royalty"],
            "review_ready_income_types": [],
            "base_candidate_income_types": [],
            "protocol_candidate_income_types": [],
            "domestic_candidate_income_types": ["dividend", "interest", "royalty"],
            "eu_relief_candidate_income_types": [],
            "manual_rate_extraction_income_types": [],
            "candidate_chain_assembled_income_types": [],
            "candidate_chain_blocked_income_types": [],
            "candidate_review_queued_income_types": [],
            "candidate_review_approved_income_types": [],
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
        try:
            return require_source_country_analysis_release(source)
        except UnsupportedSourceCountryError:
            # Source-country release gating applies only to countries
            # onboarded into the source-country registry. Other source
            # directions retain the established downstream out-of-scope
            # handling rather than becoming a new API validation error.
            return None
        except SourceCountryNotReleasedError as exc:
            decision = exc.decision
            raise HTTPException(
                status_code=409,
                detail={
                    "code": decision.code,
                    "source_country": source,
                    "release_status": decision.release_status,
                    "release_blockers": list(decision.blockers),
                },
            ) from exc

    treaty_pair_id = f"{source}-{recipient}"

    try:
        release = get_canonical_source_release(
            treaty_pair_id
        )
    except CanonicalSourceNotReleasedError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "SOURCE_NOT_RELEASED",
                "treaty_pair_id": treaty_pair_id,
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
                "release_status":
                    release.release_status,
                "release_blockers":
                    list(release.release_blockers),
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
    dataset_version = source_country_runtime_dataset_version(
        source_country,
        cz_release_loader=load_stage6_source_release,
    )
    analysis = {
        "status": result.status.value,
        "rate": result.rate,
        "candidate_rate": result.candidate_rate,
        "tax_treatment": (
            result.tax_treatment.value
            if getattr(result, "tax_treatment", None) is not None
            else None
        ),
        "candidate_tax_treatment": (
            result.candidate_tax_treatment.value
            if getattr(result, "candidate_tax_treatment", None) is not None
            else None
        ),
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
    analysis["legal_path"] = build_legal_path(
        result.citations,
        source_country=source_country,
        recipient_country=recipient_country,
        selected_rule_id=(
            result.selected_rule_id or result.candidate_rule_id
        ),
        income_type=payload.income_type,
    )
    amount = (
        payload.transaction_amount.model_dump(mode="json")
        if payload.transaction_amount is not None
        else None
    )
    calculation = build_source_country_withholding_tax_calculation(
        source_country,
        amount,
        decision_status=result.status.value,
        rate_percent=result.rate,
        tax_treatment=(
            result.tax_treatment.value
            if getattr(result, "tax_treatment", None) is not None
            else None
        ),
    )
    analysis["withholding_tax_calculation"] = calculation
    analysis["withholding_compliance_schedule"] = (
        build_source_country_withholding_compliance_schedule(
            source_country,
            payload.transaction_date,
            income_type=payload.income_type,
            decision_status=result.status.value,
            rate_percent=result.rate,
            tax_treatment=(
                result.tax_treatment.value
                if getattr(result, "tax_treatment", None) is not None
                else None
            ),
            gross_amount_czk=(
                calculation.get("gross_amount_czk")
                if calculation is not None
                and calculation.get("status") == "CALCULATED"
                else None
            ),
            prior_same_type_monthly_amount_czk=(
                amount.get("prior_same_type_monthly_amount_czk")
                if amount is not None
                else None
            ),
        )
    )
    return analysis


@app.post("/analysis/intake")
def analysis_intake(payload: AnalysisPayload, lang: Literal["cs", "en"] = "cs"):
    analysis = analyze(payload)
    request = payload.model_dump(mode="json")
    response = {
        "analysis": analysis,
        "intake": build_intake_plan(request, analysis),
    }
    return localize_intake_response(response, WEB_ROOT, lang)


@app.post("/analysis/report")
def analysis_report(payload: AnalysisPayload):
    analysis = analyze(payload)
    request = payload.model_dump(mode="json")
    facts = request.get("facts")
    report_language = "cs"
    if isinstance(facts, dict):
        report_language = "en" if str(facts.pop("__report_language", "cs")).lower() == "en" else "cs"
    report = build_professional_report(
        request,
        analysis,
        language=report_language,
    )
    return {
        "report": report,
        "html": render_report_html(report),
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
