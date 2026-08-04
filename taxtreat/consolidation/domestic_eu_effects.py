from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from taxtreat.registry.legal_scope import load_partner_registry


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = (
    ROOT
    / "data"
    / "legal_consolidation"
    / "cz_domestic_eu_candidates.json"
)

LEGAL_DATA_CUTOFF = "2026-08-04"
CZECH_LAW_EFFECTIVE_FROM = "2026-04-01"

EU_MEMBER_PARTNERS = {
    "AT", "BE", "BG", "CY", "DE", "DK", "EE", "ES", "FI", "FR",
    "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL",
    "PL", "PT", "RO", "SE", "SI", "SK",
}
SECTION_19_8_EXTENSION_PARTNERS = {"CH", "IS", "LI", "NO"}
RELIEF_ELIGIBLE_PARTNERS = (
    EU_MEMBER_PARTNERS | SECTION_19_8_EXTENSION_PARTNERS
)

SOURCES = [
    {
        "source_id": "CZ-ZDP-2026-04-01-OPEN-DATA",
        "title": "Act No. 586/1992 Coll., Income Taxes Act, consolidated text",
        "authority": "e-Sbírka open data, Ministry of the Interior of the Czech Republic",
        "authority_class": "official",
        "url": "https://opendata.eselpoint.gov.cz/esel-esb/eli/cz/sb/1992/586/2026-04-01",
        "effective_from": CZECH_LAW_EFFECTIVE_FROM,
        "retrieved_at": LEGAL_DATA_CUTOFF,
        "source_document_sha256": "fae29f32d63f9f8a7574e56a3cb441df49c904c60ff31495cf977eed8b66067e",
        "relevant_provisions": [
            "section 19(1)(ze), (zj), (zk), (3)-(8), (11)",
            "section 22(1)(g)(1)-(4)",
            "section 23(7)",
            "section 36(1)(a)-(c)",
            "section 38nb",
        ],
    },
    {
        "source_id": "EU-PSD-2011-96-CONSOLIDATED",
        "title": "Council Directive 2011/96/EU, consolidated text",
        "authority": "European Union, EUR-Lex",
        "authority_class": "official",
        "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02011L0096-20150217",
        "retrieved_at": LEGAL_DATA_CUTOFF,
        "source_document_sha256": "ca8cb52854e21e128395be2f84215ae74833d0f36e8e5325ac4c05cb002ac0d7",
        "relevant_provisions": ["Articles 1-3 and 5"],
    },
    {
        "source_id": "EU-IRD-2003-49-CONSOLIDATED",
        "title": "Council Directive 2003/49/EC, consolidated text",
        "authority": "European Union, EUR-Lex",
        "authority_class": "official",
        "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02003L0049-20130701",
        "retrieved_at": LEGAL_DATA_CUTOFF,
        "source_document_sha256": "e28224be32008bcc1d1052f9686c43977d30d32d33fb36011ee5f2637a1d57c2",
        "relevant_provisions": ["Articles 1-5"],
    },
    {
        "source_id": "EU-MEMBER-STATES-2026-08-04",
        "title": "EU countries",
        "authority": "European Union",
        "authority_class": "official",
        "url": "https://european-union.europa.eu/principles-countries-history/eu-countries_en",
        "retrieved_at": LEGAL_DATA_CUTOFF,
        "source_document_sha256": "816b46a2b0c5ec6140190399000081502ee0e855e559695b2bf71cd41c625555",
        "relevant_provisions": ["Current list of 27 EU Member States"],
    },
]


DOMESTIC_REFERENCES = {
    "dividend": {
        "standard_reference": "section 36(1)(b)(1), referring to section 22(1)(g)(3)",
        "income_scope_reference": "section 22(1)(g)(3)",
    },
    "interest": {
        "standard_reference": "section 36(1)(a)(1), referring to section 22(1)(g)(4)",
        "income_scope_reference": "section 22(1)(g)(4)",
    },
    "royalty": {
        "standard_reference": "section 36(1)(a)(1), referring to section 22(1)(g)(1)-(2)",
        "income_scope_reference": "section 22(1)(g)(1)-(2)",
    },
}


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _rate_candidate(income_type: str) -> dict[str, Any]:
    references = DOMESTIC_REFERENCES[income_type]
    return {
        "standard_rate": 15.0,
        "standard_reference": references["standard_reference"],
        "income_scope_reference": references["income_scope_reference"],
        "protective_rate": 35.0,
        "protective_rate_reference": "section 36(1)(c)",
        "protective_rate_condition": (
            "recipient is outside the EU/EEA and no qualifying treaty or "
            "tax-information-exchange instrument is applied"
        ),
        "source_id": "CZ-ZDP-2026-04-01-OPEN-DATA",
        "effective_from": CZECH_LAW_EFFECTIVE_FROM,
    }


def _holding_period_alternatives(months: int) -> list[dict[str, Any]]:
    return [
        {
            "fact": "holding_period_months",
            "operator": ">=",
            "value": months,
        },
        {
            "all_of": [
                {
                    "fact": "holding_period_will_reach_months",
                    "operator": ">=",
                    "value": months,
                },
                {
                    "fact": "statutory_clawback_acknowledged",
                    "operator": "==",
                    "value": True,
                },
            ]
        },
    ]


def _relief_candidate(country: str, income_type: str) -> dict[str, Any] | None:
    if country not in RELIEF_ELIGIBLE_PARTNERS:
        return None

    regime = (
        "eu_directive_domestic_implementation"
        if country in EU_MEMBER_PARTNERS
        else "section_19_8_extension"
    )
    common = [
        {
            "fact": "recipient_is_qualifying_company_form",
            "operator": "==",
            "value": True,
        },
        {
            "fact": "recipient_is_tax_resident_in_eligible_jurisdiction",
            "operator": "==",
            "value": True,
        },
        {
            "fact": "recipient_subject_to_qualifying_corporate_tax",
            "operator": "==",
            "value": True,
        },
        {
            "fact": "recipient_has_no_tax_exemption_or_zero_rate_option",
            "operator": "==",
            "value": True,
        },
    ]

    if income_type == "dividend":
        return {
            "rate": 0.0,
            "regime": regime,
            "legal_reference": "section 19(1)(ze), (3), (4), (6), (8) and (11)",
            "directive_source_id": (
                "EU-PSD-2011-96-CONSOLIDATED"
                if country in EU_MEMBER_PARTNERS
                else None
            ),
            "all_of": [
                *common,
                {
                    "fact": "ownership_percent",
                    "operator": ">=",
                    "value": 10,
                },
                {
                    "fact": "recipient_is_parent_company",
                    "operator": "==",
                    "value": True,
                },
            ],
            "holding_period_one_of": _holding_period_alternatives(12),
            "anti_abuse_review_required": True,
        }

    return {
        "rate": 0.0,
        "regime": regime,
        "legal_reference": (
            "section 19(1)(zj), (3), (5)-(8) and section 38nb"
            if income_type == "royalty"
            else "section 19(1)(zk), (3), (5), (6), (8) and section 38nb"
        ),
        "directive_source_id": (
            "EU-IRD-2003-49-CONSOLIDATED"
            if country in EU_MEMBER_PARTNERS
            else None
        ),
        "all_of": [
            *common,
            {
                "fact": "beneficial_owner",
                "operator": "==",
                "value": True,
            },
            {
                "fact": "payment_is_arm_length_amount",
                "operator": "==",
                "value": True,
            },
            {
                "fact": "section_38nb_decision_effective",
                "operator": "==",
                "value": True,
            },
            {
                "fact": "payment_not_attributable_to_disqualifying_pe",
                "operator": "==",
                "value": True,
            },
        ],
        "association_one_of": [
            "payer directly holds at least 25% of recipient capital or voting rights",
            "recipient directly holds at least 25% of payer capital or voting rights",
            "one person directly holds at least 25% of both payer and recipient capital or voting rights",
        ],
        "association_period_one_of": _holding_period_alternatives(24),
        "anti_abuse_review_required": True,
    }


def build_domestic_eu_candidates() -> dict[str, Any]:
    partners = load_partner_registry()
    partner_codes = {partner["iso2"] for partner in partners}
    unknown_relief_codes = RELIEF_ELIGIBLE_PARTNERS.difference(partner_codes)
    if unknown_relief_codes:
        raise ValueError(
            "Relief registry contains countries outside the treaty registry: "
            + ", ".join(sorted(unknown_relief_codes))
        )
    if len(EU_MEMBER_PARTNERS) != 26:
        raise ValueError("Expected 26 EU Member State partners other than Czechia.")
    if len(RELIEF_ELIGIBLE_PARTNERS) != 30:
        raise ValueError("Expected 30 section 19 relief-eligible treaty partners.")

    scopes: list[dict[str, Any]] = []
    for partner in partners:
        country = partner["iso2"]
        for income_type in ("dividend", "interest", "royalty"):
            relief = _relief_candidate(country, income_type)
            blockers = [
                "independent_legal_review",
                "domestic_rate_candidate_review",
            ]
            if relief is not None:
                blockers.extend(
                    [
                        "recipient_qualification_fact_review",
                        "anti_abuse_determination",
                        "relief_candidate_review",
                    ]
                )
            if country in {"BY", "RU"}:
                blockers.append("current_treaty_status_review")
            scope = {
                "source_country": "CZ",
                "recipient_country": country,
                "recipient_country_name": partner["country"],
                "income_type": income_type,
                "domestic_rate_candidate": _rate_candidate(income_type),
                "relief_eligible_by_jurisdiction": relief is not None,
                "relief_candidate": relief,
                "relief_candidate_status": (
                    "relief_candidate_consolidated"
                    if relief is not None
                    else "not_applicable_by_recipient_jurisdiction"
                ),
                "consolidation_blockers": sorted(set(blockers)),
                "candidate_status": "domestic_and_relief_candidate_consolidated",
                "verification_status": "needs_review",
            }
            scope["candidate_sha256"] = _sha256_text(
                json.dumps(scope, ensure_ascii=False, sort_keys=True)
            )
            scopes.append(scope)

    if len(scopes) != 300:
        raise ValueError(f"Expected 300 domestic-law scopes, found {len(scopes)}.")

    return {
        "schema_version": 1,
        "dataset_release": "cz-domestic-eu-candidates-2026-08-04.1",
        "legal_data_cutoff": LEGAL_DATA_CUTOFF,
        "czech_law_effective_from": CZECH_LAW_EFFECTIVE_FROM,
        "scope_note": (
            "Candidate layer only; no scope is activated before independent "
            "legal approval and completion of the full instrument chain."
        ),
        "sources": SOURCES,
        "jurisdiction_regimes": {
            "eu_member_partners": sorted(EU_MEMBER_PARTNERS),
            "section_19_8_extension_partners": sorted(
                SECTION_19_8_EXTENSION_PARTNERS
            ),
        },
        "scopes": sorted(
            scopes,
            key=lambda row: (row["recipient_country"], row["income_type"]),
        ),
    }


def write_domestic_eu_candidates(
    payload: dict[str, Any],
    path: str | Path = DEFAULT_OUTPUT,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
