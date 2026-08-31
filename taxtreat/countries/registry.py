from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from taxtreat.engine.legal_rule_engine import LegalDecisionResult
from taxtreat.countries.cz import apply_rule_overlays as apply_cz_rule_overlays
from taxtreat.countries.sk import evaluate_domestic_precedence as evaluate_sk_domestic_precedence


ROOT = Path(__file__).resolve().parents[2]


DomesticPrecedenceHandler = Callable[
    ...,
    LegalDecisionResult | None,
]

RuleOverlayHandler = Callable[..., list[Any]]


@dataclass(frozen=True)
class CountryConfig:
    code: str
    currency: str
    supported_income_types: tuple[str, ...]
    treaty_partner_registry: Path | None
    runtime_released: bool
    fx_provider: str | None
    domestic_legal_source_url: str | None
    domestic_law_label: str | None
    compliance_form_code: str | None = None
    compliance_legal_reference: str | None = None
    compliance_periodicity: str | None = None
    domestic_precedence_handler: DomesticPrecedenceHandler | None = None
    rule_overlay_handler: RuleOverlayHandler | None = None
    release_manifest_path: Path | None = None
    calculation_strategy: str = "czk_domestic"
    compliance_strategy: str = "cz"
    runtime_dataset_strategy: str = "canonical_stage6"
    release_gate_strategy: str = "canonical_stage6"
    report_calculation_strategy: str = "czk"
    html_localization_strategy: str = "identity"
    legacy_canonical_fallback_allowed: bool = False
    rule_directory: Path | None = None


_COUNTRIES: dict[str, CountryConfig] = {
    "CZ": CountryConfig(
        code="CZ",
        currency="CZK",
        supported_income_types=("dividend", "interest", "royalty"),
        treaty_partner_registry=ROOT / "data" / "cz_treaty_partners.json",
        runtime_released=True,
        fx_provider="CNB",
        domestic_legal_source_url="https://e-sbirka.gov.cz/sb/1992/586",
        domestic_law_label="ZDP",
        rule_overlay_handler=apply_cz_rule_overlays,
        html_localization_strategy="cz",
        legacy_canonical_fallback_allowed=True,
    ),
    "SK": CountryConfig(
        code="SK",
        currency="EUR",
        supported_income_types=("dividend", "interest", "royalty"),
        treaty_partner_registry=ROOT / "data" / "sk_treaty_partners.json",
        runtime_released=True,
        fx_provider="ECB/NBS",
        domestic_legal_source_url=(
            "https://static.slov-lex.sk/static/SK/ZZ/2003/595/20260101.print.html"
        ),
        domestic_law_label="zákon č. 595/2003 Z. z.",
        compliance_form_code="OZN4311v26",
        compliance_legal_reference="§ 43 ods. 11",
        compliance_periodicity="monthly",
        domestic_precedence_handler=evaluate_sk_domestic_precedence,
        release_manifest_path=(
            ROOT
            / "data"
            / "legal_reviews"
            / "sk_outbound"
            / "source_country_release_manifest.json"
        ),
        calculation_strategy="payment_currency_then_eur",
        compliance_strategy="sk_monthly_section_43_11",
        runtime_dataset_strategy="source_country_manifest",
        release_gate_strategy="source_country_manifest",
        report_calculation_strategy="payment_currency_eur",
        html_localization_strategy="sk",
        rule_directory=ROOT / "data" / "legal_rules_sk",
    ),
}


def get_country_config(code: str) -> CountryConfig:
    normalized = str(code or "").upper()
    try:
        return _COUNTRIES[normalized]
    except KeyError as exc:
        raise KeyError(f"Unsupported source country: {normalized}") from exc


def supported_source_countries() -> tuple[str, ...]:
    return tuple(sorted(_COUNTRIES))
