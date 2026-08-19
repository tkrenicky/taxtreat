from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


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
    ),
    "SK": CountryConfig(
        code="SK",
        currency="EUR",
        supported_income_types=("dividend", "interest", "royalty"),
        treaty_partner_registry=ROOT / "data" / "sk_treaty_partners.json",
        runtime_released=False,
        fx_provider=None,
        domestic_legal_source_url=(
            "https://static.slov-lex.sk/static/SK/ZZ/2003/595/20260101.print.html"
        ),
        domestic_law_label="zákon č. 595/2003 Z. z.",
        compliance_form_code="OZN4311v26",
        compliance_legal_reference="§ 43 ods. 11",
        compliance_periodicity="monthly",
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
