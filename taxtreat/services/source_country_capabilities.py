from __future__ import annotations

from typing import Any

from taxtreat.countries.registry import (
    get_country_config,
    supported_source_countries,
)


def source_country_capability(code: str) -> dict[str, Any]:
    config = get_country_config(code)
    return {
        "code": config.code,
        "currency": config.currency,
        "supported_income_types": list(config.supported_income_types),
        "runtime_released": config.runtime_released,
        "availability": "released" if config.runtime_released else "pre_release",
        "fx_provider": config.fx_provider,
        "domestic_legal_source_url": config.domestic_legal_source_url,
        "domestic_law_label": config.domestic_law_label,
        "compliance": {
            "form_code": config.compliance_form_code,
            "legal_reference": config.compliance_legal_reference,
            "periodicity": config.compliance_periodicity,
        },
        "policy": {
            "country_specific_domestic_logic_required": True,
            "country_specific_compliance_required": True,
            "czech_fallback_allowed": (
                config.legacy_canonical_fallback_allowed
            ),
            "final_analysis_allowed": config.runtime_released,
        },
    }


def source_country_capabilities() -> dict[str, Any]:
    countries = [
        source_country_capability(code)
        for code in supported_source_countries()
    ]
    return {
        "schema_version": 1,
        "countries": countries,
        "released_source_countries": [
            row["code"] for row in countries if row["runtime_released"]
        ],
        "pre_release_source_countries": [
            row["code"] for row in countries if not row["runtime_released"]
        ],
    }
