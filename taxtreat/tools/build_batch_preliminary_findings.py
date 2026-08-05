from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

BELGIUM = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_belgium_preliminary_findings.json"
)

DOSSIERS = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_country_dossiers.json"
)

OUTPUT = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_preliminary_findings.json"
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_findings() -> dict[str, Any]:
    belgium = read_json(BELGIUM)
    dossiers = read_json(DOSSIERS)

    findings = list(belgium["findings"])

    nl = next(
        country
        for country in dossiers["countries"]
        if country["recipient_country"] == "NL"
    )

    nl_interest = next(
        scope
        for scope in nl["scopes"]
        if scope["income_type"] == "interest"
    )

    findings.append(
        {
            "packet_id": nl_interest["packet_id"],
            "recipient_country": "NL",
            "income_type": "interest",
            "treaty_findings": {
                "source_state_rate": 0.0,
                "taxing_right": (
                    "Interest arising in one contracting state and paid "
                    "to a resident of the other contracting state is "
                    "taxable only in the recipient state."
                ),
                "rate_scope": "general",
                "conditions": [
                    (
                        "recipient is resident in the other contracting "
                        "state"
                    ),
                    (
                        "the debt claim is not effectively connected with "
                        "a permanent establishment in the source state"
                    ),
                ],
                "pe_exception_applies": True,
            },
            "protocol_preliminary_finding": {
                "effect": "definition_change_only",
                "rate_effect": "none identified",
                "source_ids": [
                    "CZ-MF-NL-45D279EE7770",
                    "CZ-MF-NL-7CAD483C3F1A",
                ],
            },
            "mli_preliminary_finding": {
                "effect": "Article 7(1) PPT",
                "effective_from": "2021-01-01",
                "source_id": "CZ-MF-NL-0210508FF125",
            },
            "data_quality_issues": [
                {
                    "code": "article_text_truncated",
                    "severity": "medium",
                    "detail": (
                        "Stored Article 11 paragraph 3 ends after "
                        "'V takovém případě se použije'. The complete "
                        "cross-reference must be checked against the "
                        "official instrument before final approval."
                    ),
                    "affects_general_rate_conclusion": False,
                }
            ],
            "domestic_and_eu_review_required": True,
            "human_confirmation_required": True,
            "review_outcome": None,
            "status": "preliminary_findings_only",
        }
    )

    findings.extend(
        [
            {
                "packet_id": "CZ-DK-DIV-LEGAL-REVIEW",
                "recipient_country": "DK",
                "income_type": "dividend",
                "treaty_findings": {
                    "rates": [
                        {
                            "rate": 0.0,
                            "conditions": [
                                "recipient is the beneficial owner",
                                (
                                    "recipient is a company other than a "
                                    "partnership"
                                ),
                                (
                                    "recipient directly holds at least 10% "
                                    "of the capital of the paying company"
                                ),
                            ],
                        },
                        {
                            "rate": 0.0,
                            "conditions": [
                                "recipient is the beneficial owner",
                                (
                                    "recipient is a qualifying pension fund "
                                    "or similar institution"
                                ),
                                (
                                    "the pension plan is recognized for tax "
                                    "purposes in the recipient state under "
                                    "Article 17(2)"
                                ),
                            ],
                        },
                        {
                            "rate": 15.0,
                            "conditions": [
                                "recipient is the beneficial owner",
                                "all other cases",
                            ],
                        },
                    ],
                    "pe_exception_applies": True,
                },
                "protocol_preliminary_finding": {
                    "effect": "no_protocol_effect_recorded",
                },
                "mli_preliminary_finding": {
                    "effect": "Article 7(1) PPT",
                    "effective_from": "2021-01-01",
                    "source_id": "CZ-MF-DK-6D5DDFC81601",
                },
                "data_quality_issues": [
                    {
                        "code": "article_cross_reference_split",
                        "severity": "low",
                        "detail": (
                            "The Article 7 cross-reference is split into a "
                            "separate parsed paragraph."
                        ),
                        "affects_rate_conclusion": False,
                    }
                ],
                "domestic_and_eu_review_required": True,
                "human_confirmation_required": True,
                "review_outcome": None,
                "status": "preliminary_findings_only",
            },
            {
                "packet_id": "CZ-IT-ROY-LEGAL-REVIEW",
                "recipient_country": "IT",
                "income_type": "royalty",
                "treaty_findings": {
                    "rates": [
                        {
                            "rate": 0.0,
                            "categories": [
                                (
                                    "copyright in literary, artistic or "
                                    "scientific works"
                                ),
                                "cinematographic and television films",
                            ],
                            "conditions": [
                                "recipient is the beneficial owner",
                            ],
                        },
                        {
                            "rate": 5.0,
                            "categories": [
                                "patents",
                                "trademarks",
                                "designs or models",
                                "plans",
                                "secret formulas or processes",
                                (
                                    "industrial, commercial or scientific "
                                    "equipment"
                                ),
                                "industrial, commercial or scientific know-how",
                            ],
                            "conditions": [
                                "recipient is the beneficial owner",
                            ],
                        },
                    ],
                    "pe_exception_applies": True,
                    "excess_payment_limitation": True,
                },
                "protocol_preliminary_finding": {
                    "effect": "no_protocol_effect_recorded",
                },
                "mli_preliminary_finding": {
                    "effect": "no_mli_effect_recorded",
                    "requires_separate_verification": True,
                },
                "data_quality_issues": [],
                "domestic_and_eu_review_required": True,
                "human_confirmation_required": True,
                "review_outcome": None,
                "status": "preliminary_findings_only",
            },
            {
                "packet_id": "CZ-SE-ROY-LEGAL-REVIEW",
                "recipient_country": "SE",
                "income_type": "royalty",
                "treaty_findings": {
                    "rates": [
                        {
                            "rate": 0.0,
                            "categories": [
                                (
                                    "copyright in literary, artistic or "
                                    "scientific works"
                                ),
                            ],
                            "conditions": [
                                (
                                    "recipient is resident in the other "
                                    "contracting state"
                                ),
                            ],
                        },
                        {
                            "rate": 5.0,
                            "categories": [
                                "patents",
                                "trademarks",
                                "designs or models",
                                "plans",
                                "secret formulas or processes",
                                (
                                    "industrial, commercial or scientific "
                                    "equipment"
                                ),
                                "industrial, commercial or scientific know-how",
                                (
                                    "copyright categories not falling within "
                                    "the specific source-state exemption"
                                ),
                            ],
                            "conditions": [],
                        },
                    ],
                    "pe_exception_applies": True,
                    "excess_payment_limitation": True,
                },
                "protocol_preliminary_finding": {
                    "effect": "no_protocol_effect_recorded",
                },
                "mli_preliminary_finding": {
                    "effect": "no_mli_effect_recorded",
                    "requires_separate_verification": True,
                },
                "data_quality_issues": [
                    {
                        "code": "beneficial_owner_wording_not_explicit",
                        "severity": "medium",
                        "detail": (
                            "The extracted treaty text does not expressly "
                            "state a beneficial-owner condition in Article 12; "
                            "this must not be added automatically."
                        ),
                        "affects_rate_conclusion": False,
                    }
                ],
                "domestic_and_eu_review_required": True,
                "human_confirmation_required": True,
                "review_outcome": None,
                "status": "preliminary_findings_only",
            },
        ]
    )


    findings.extend(
        [
            {
                "packet_id": "CZ-DE-DIV-LEGAL-REVIEW",
                "recipient_country": "DE",
                "income_type": "dividend",
                "treaty_findings": {
                    "rates": [
                        {
                            "rate": 5.0,
                            "conditions": [
                                (
                                    "recipient is a company directly holding "
                                    "at least 25% of the capital of the paying "
                                    "company"
                                ),
                            ],
                        },
                        {
                            "rate": 15.0,
                            "conditions": [
                                "all other cases",
                            ],
                        },
                        {
                            "rate": 25.0,
                            "conditions": [
                                (
                                    "the corporate income tax rate in the "
                                    "source state is lower for distributed "
                                    "profits than for undistributed profits"
                                ),
                                (
                                    "the difference between those rates is "
                                    "at least 20 percentage points"
                                ),
                                (
                                    "the recipient company, alone or together "
                                    "with associated persons, directly or "
                                    "indirectly holds at least 25% of the "
                                    "voting interests in the paying company"
                                ),
                            ],
                            "special_historical_rule": True,
                            "current_applicability_requires_confirmation": True,
                        },
                    ],
                    "pe_exception_applies": True,
                },
                "candidate_extraction_correction": {
                    "incorrect_extracted_rate": 20.0,
                    "correct_source_text_rate": 25.0,
                    "reason": (
                        "The value 20% is the minimum tax-rate differential "
                        "condition, not the withholding-tax ceiling."
                    ),
                    "base_candidate_must_not_be_promoted": True,
                },
                "protocol_preliminary_finding": {
                    "effect": "no_protocol_effect_recorded",
                },
                "mli_preliminary_finding": {
                    "effect": "Article 7(1) PPT",
                    "effective_from": "2026-01-01",
                    "source_id": "CZ-MF-DE-B5236226B2AF",
                },
                "data_quality_issues": [
                    {
                        "code": "rate_condition_misclassified_as_rate",
                        "severity": "critical",
                        "detail": (
                            "The extractor stored 20% as a dividend rate, "
                            "although Article 10(3) states a 25% ceiling and "
                            "uses 20% only as a tax-rate differential trigger."
                        ),
                        "affects_rate_conclusion": True,
                    },
                    {
                        "code": "article_cross_reference_split",
                        "severity": "low",
                        "detail": (
                            "The Article 7 cross-reference is split into a "
                            "separate parsed paragraph."
                        ),
                        "affects_rate_conclusion": False,
                    },
                ],
                "domestic_and_eu_review_required": True,
                "human_confirmation_required": True,
                "review_outcome": None,
                "status": "preliminary_findings_only",
            },
            {
                "packet_id": "CZ-DE-INT-LEGAL-REVIEW",
                "recipient_country": "DE",
                "income_type": "interest",
                "treaty_findings": {
                    "source_state_rate": 0.0,
                    "taxing_right": (
                        "Interest arising in one contracting state and paid "
                        "to a resident of the other contracting state is "
                        "taxable only in the recipient state."
                    ),
                    "rate_scope": "general",
                    "conditions": [
                        (
                            "recipient has residence or registered office in "
                            "the other contracting state"
                        ),
                        (
                            "the debt claim is not effectively connected with "
                            "a permanent establishment in the source state"
                        ),
                    ],
                    "pe_exception_applies": True,
                    "excess_payment_limitation": True,
                },
                "protocol_preliminary_finding": {
                    "effect": "no_protocol_effect_recorded",
                },
                "mli_preliminary_finding": {
                    "effect": "Article 7(1) PPT",
                    "effective_from": "2026-01-01",
                    "source_id": "CZ-MF-DE-B5236226B2AF",
                },
                "data_quality_issues": [
                    {
                        "code": "article_cross_reference_split",
                        "severity": "low",
                        "detail": (
                            "The Article 7 cross-reference is split into a "
                            "separate parsed paragraph."
                        ),
                        "affects_rate_conclusion": False,
                    }
                ],
                "domestic_and_eu_review_required": True,
                "human_confirmation_required": True,
                "review_outcome": None,
                "status": "preliminary_findings_only",
            },
            {
                "packet_id": "CZ-FR-INT-LEGAL-REVIEW",
                "recipient_country": "FR",
                "income_type": "interest",
                "treaty_findings": {
                    "source_state_rate": 0.0,
                    "taxing_right": (
                        "Interest arising in one contracting state and "
                        "beneficially owned by a resident of the other "
                        "contracting state is taxable only in that other "
                        "state."
                    ),
                    "rate_scope": "general",
                    "conditions": [
                        "recipient is resident in the other contracting state",
                        "recipient is the beneficial owner of the interest",
                        (
                            "the debt claim is not effectively connected with "
                            "a permanent establishment or fixed base in the "
                            "source state"
                        ),
                    ],
                    "beneficial_owner_required": True,
                    "pe_exception_applies": True,
                    "excess_payment_limitation": True,
                },
                "protocol_preliminary_finding": {
                    "effect": "no_protocol_effect_recorded",
                },
                "mli_preliminary_finding": {
                    "effect": "Article 7(1) PPT",
                    "effective_from": "2021-01-01",
                    "source_id": "CZ-MF-FR-F51BC9297EF7",
                },
                "data_quality_issues": [
                    {
                        "code": "article_10_cross_reference_split",
                        "severity": "low",
                        "detail": (
                            "The Article 10 cross-reference in the interest "
                            "definition is split across parsed paragraphs."
                        ),
                        "affects_rate_conclusion": False,
                    }
                ],
                "domestic_and_eu_review_required": True,
                "human_confirmation_required": True,
                "review_outcome": None,
                "status": "preliminary_findings_only",
            },
        ]
    )


    findings.extend(
        [
            {
                "packet_id": "CZ-DK-INT-LEGAL-REVIEW",
                "recipient_country": "DK",
                "income_type": "interest",
                "treaty_findings": {
                    "source_state_rate": 0.0,
                    "taxing_right": (
                        "Interest arising in one contracting state and "
                        "beneficially owned by a resident of the other "
                        "contracting state is taxable only in that other "
                        "state."
                    ),
                    "rate_scope": "general",
                    "conditions": [
                        "recipient is resident in the other contracting state",
                        "recipient is the beneficial owner of the interest",
                        (
                            "the debt claim is not effectively connected "
                            "with a permanent establishment in the source "
                            "state"
                        ),
                    ],
                    "beneficial_owner_required": True,
                    "pe_exception_applies": True,
                    "excess_payment_limitation": True,
                },
                "protocol_preliminary_finding": {
                    "effect": "no_protocol_effect_recorded",
                },
                "mli_preliminary_finding": {
                    "effect": "Article 7(1) PPT",
                    "effective_from": "2021-01-01",
                    "source_id": "CZ-MF-DK-6D5DDFC81601",
                },
                "data_quality_issues": [
                    {
                        "code": "article_cross_references_split",
                        "severity": "low",
                        "detail": (
                            "References to Article 10(3) and Article 7 are "
                            "split across parsed paragraphs."
                        ),
                        "affects_rate_conclusion": False,
                    }
                ],
                "domestic_and_eu_review_required": True,
                "human_confirmation_required": True,
                "review_outcome": None,
                "status": "preliminary_findings_only",
            },
            {
                "packet_id": "CZ-ES-ROY-LEGAL-REVIEW",
                "recipient_country": "ES",
                "income_type": "royalty",
                "treaty_findings": {
                    "rates": [
                        {
                            "rate": 5.0,
                            "categories": [
                                (
                                    "royalties generally falling within "
                                    "Article 12"
                                ),
                            ],
                            "conditions": [
                                (
                                    "royalties are subject to tax in the "
                                    "recipient state"
                                ),
                            ],
                        },
                        {
                            "rate": 0.0,
                            "categories": [
                                (
                                    "copyright royalties and similar "
                                    "payments for the performance or "
                                    "reproduction of literary, dramatic, "
                                    "musical or artistic works"
                                ),
                            ],
                            "excluded_categories": [
                                "cinematographic films",
                                (
                                    "works recorded on film or television "
                                    "tape for television broadcasting"
                                ),
                            ],
                            "conditions": [
                                (
                                    "recipient is subject to tax on the "
                                    "royalties in the recipient state"
                                ),
                            ],
                        },
                    ],
                    "beneficial_owner_wording_explicit": False,
                    "pe_or_fixed_base_exception_applies": True,
                    "excess_payment_limitation": True,
                },
                "protocol_preliminary_finding": {
                    "effect": "no_protocol_effect_recorded",
                },
                "mli_preliminary_finding": {
                    "effect": "Article 7(1) PPT",
                    "effective_from": "2023-01-01",
                    "source_id": "CZ-MF-ES-ED9522D43DFC",
                },
                "data_quality_issues": [
                    {
                        "code": "zero_rate_category_requires_narrow_mapping",
                        "severity": "high",
                        "detail": (
                            "The 0% rule is limited to specified copyright "
                            "works and expressly excludes films and certain "
                            "television recordings."
                        ),
                        "affects_rate_conclusion": True,
                    },
                    {
                        "code": "subject_to_tax_condition_required",
                        "severity": "high",
                        "detail": (
                            "Both the general 5% ceiling and the specific "
                            "0% copyright rule depend on taxation in the "
                            "recipient state."
                        ),
                        "affects_rate_conclusion": True,
                    },
                    {
                        "code": "beneficial_owner_wording_not_explicit",
                        "severity": "medium",
                        "detail": (
                            "The extracted Article 12 text does not expressly "
                            "state a beneficial-owner condition."
                        ),
                        "affects_rate_conclusion": False,
                    },
                ],
                "domestic_and_eu_review_required": True,
                "human_confirmation_required": True,
                "review_outcome": None,
                "status": "preliminary_findings_only",
            },
            {
                "packet_id": "CZ-IT-INT-LEGAL-REVIEW",
                "recipient_country": "IT",
                "income_type": "interest",
                "treaty_findings": {
                    "source_state_rate": 0.0,
                    "taxing_right": (
                        "Interest arising in one contracting state and paid "
                        "to a resident of the other contracting state is "
                        "taxable only in that other state where the recipient "
                        "is the beneficial owner."
                    ),
                    "rate_scope": "general",
                    "conditions": [
                        "recipient is resident in the other contracting state",
                        "recipient is the beneficial owner of the interest",
                        (
                            "the debt claim is not effectively connected "
                            "with a permanent establishment or fixed base "
                            "in the source state"
                        ),
                    ],
                    "beneficial_owner_required": True,
                    "pe_or_fixed_base_exception_applies": True,
                    "excess_payment_limitation": True,
                },
                "protocol_preliminary_finding": {
                    "effect": "no_protocol_effect_recorded",
                },
                "mli_preliminary_finding": {
                    "effect": "no_mli_effect_recorded",
                    "requires_separate_verification": True,
                },
                "data_quality_issues": [],
                "domestic_and_eu_review_required": True,
                "human_confirmation_required": True,
                "review_outcome": None,
                "status": "preliminary_findings_only",
            },
        ]
    )


    findings.extend(
        [
            {
                "packet_id": "CZ-ES-INT-LEGAL-REVIEW",
                "recipient_country": "ES",
                "income_type": "interest",
                "treaty_findings": {
                    "source_state_rate": 0.0,
                    "taxing_right": (
                        "Interest arising in one contracting state and paid "
                        "to a resident of the other contracting state is "
                        "taxable only in that other state."
                    ),
                    "rate_scope": "general",
                    "conditions": [
                        "recipient is resident in the other contracting state",
                        (
                            "the debt claim is not effectively connected "
                            "with a permanent establishment or fixed base "
                            "in the source state"
                        ),
                    ],
                    "beneficial_owner_wording_explicit": False,
                    "pe_or_fixed_base_exception_applies": True,
                    "excess_payment_limitation": True,
                },
                "protocol_preliminary_finding": {
                    "effect": "no_protocol_effect_recorded",
                },
                "mli_preliminary_finding": {
                    "effect": "Article 7(1) PPT",
                    "effective_from": "2023-01-01",
                    "source_id": "CZ-MF-ES-ED9522D43DFC",
                },
                "data_quality_issues": [
                    {
                        "code": "beneficial_owner_wording_not_explicit",
                        "severity": "medium",
                        "detail": (
                            "Article 11 does not expressly state a "
                            "beneficial-owner condition; it must not be "
                            "added automatically."
                        ),
                        "affects_rate_conclusion": False,
                    }
                ],
                "domestic_and_eu_review_required": True,
                "human_confirmation_required": True,
                "review_outcome": None,
                "status": "preliminary_findings_only",
            },
            {
                "packet_id": "CZ-FR-ROY-LEGAL-REVIEW",
                "recipient_country": "FR",
                "income_type": "royalty",
                "treaty_findings": {
                    "rates": [
                        {
                            "rate": 0.0,
                            "categories": [
                                (
                                    "copyright in literary, artistic or "
                                    "scientific works"
                                ),
                                "cinematographic films",
                                (
                                    "films or recordings for television "
                                    "or radio broadcasting"
                                ),
                            ],
                            "excluded_categories": [
                                "computer software",
                            ],
                            "conditions": [
                                "recipient is resident in the other state",
                            ],
                        },
                        {
                            "rate": 5.0,
                            "categories": [
                                (
                                    "industrial, commercial or scientific "
                                    "equipment"
                                ),
                            ],
                            "conditions": [
                                "recipient is the beneficial owner",
                            ],
                        },
                        {
                            "rate": 10.0,
                            "categories": [
                                "patents",
                                "trademarks",
                                "designs or models",
                                "plans",
                                "secret formulas or processes",
                                "computer software",
                                (
                                    "industrial, commercial or scientific "
                                    "know-how"
                                ),
                            ],
                            "conditions": [
                                "recipient is the beneficial owner",
                            ],
                        },
                    ],
                    "pe_or_fixed_base_exception_applies": True,
                    "excess_payment_limitation": True,
                },
                "protocol_preliminary_finding": {
                    "effect": "no_protocol_effect_recorded",
                },
                "mli_preliminary_finding": {
                    "effect": "Article 7(1) PPT",
                    "effective_from": "2021-01-01",
                    "source_id": "CZ-MF-FR-F51BC9297EF7",
                },
                "data_quality_issues": [
                    {
                        "code": "zero_rate_not_extracted",
                        "severity": "high",
                        "detail": (
                            "The candidate extractor returned only 5% and "
                            "10%, although Article 12 excludes paragraph "
                            "3(a) copyright payments from source-state "
                            "taxation."
                        ),
                        "affects_rate_conclusion": True,
                    },
                    {
                        "code": "article_cross_reference_split",
                        "severity": "low",
                        "detail": (
                            "The reference to paragraph 3 is split into "
                            "a separate parsed paragraph."
                        ),
                        "affects_rate_conclusion": False,
                    },
                ],
                "domestic_and_eu_review_required": True,
                "human_confirmation_required": True,
                "review_outcome": None,
                "status": "preliminary_findings_only",
            },
            {
                "packet_id": "CZ-SK-INT-LEGAL-REVIEW",
                "recipient_country": "SK",
                "income_type": "interest",
                "treaty_findings": {
                    "source_state_rate": 0.0,
                    "taxing_right": (
                        "Interest arising in one contracting state and "
                        "beneficially owned by a resident of the other "
                        "contracting state is taxable only in that other "
                        "state."
                    ),
                    "rate_scope": "general",
                    "conditions": [
                        "recipient is resident in the other contracting state",
                        "recipient is the beneficial owner of the interest",
                        (
                            "the debt claim is not effectively connected "
                            "with a permanent establishment in the source "
                            "state"
                        ),
                    ],
                    "beneficial_owner_required": True,
                    "pe_exception_applies": True,
                    "excess_payment_limitation": True,
                },
                "protocol_preliminary_finding": {
                    "effect": "no_protocol_effect_recorded",
                },
                "mli_preliminary_finding": {
                    "effect": "Article 7(1) PPT",
                    "effective_from": "2021-01-01",
                    "source_id": "CZ-MF-SK-0054E687E82B",
                },
                "data_quality_issues": [
                    {
                        "code": "article_cross_references_split",
                        "severity": "low",
                        "detail": (
                            "References to Article 10 and Article 7 are "
                            "split across parsed paragraphs."
                        ),
                        "affects_rate_conclusion": False,
                    }
                ],
                "domestic_and_eu_review_required": True,
                "human_confirmation_required": True,
                "review_outcome": None,
                "status": "preliminary_findings_only",
            },
        ]
    )


    findings.extend(
        [
            {
                "packet_id": "CZ-NL-DIV-LEGAL-REVIEW",
                "recipient_country": "NL",
                "income_type": "dividend",
                "treaty_findings": {
                    "rates": [
                        {
                            "rate": 0.0,
                            "conditions": [
                                (
                                    "recipient is a company whose capital is "
                                    "wholly or partly divided into shares"
                                ),
                                (
                                    "recipient directly holds at least 25% "
                                    "of the capital of the paying company"
                                ),
                            ],
                        },
                        {
                            "rate": 10.0,
                            "conditions": [
                                "all other cases",
                            ],
                        },
                    ],
                    "pe_exception_applies": True,
                },
                "candidate_extraction_correction": {
                    "missing_rate": 0.0,
                    "reason": (
                        "Article 10(3) exempts qualifying direct "
                        "participation dividends from source-state tax."
                    ),
                    "base_candidate_must_not_be_promoted_without_correction": (
                        True
                    ),
                },
                "protocol_preliminary_finding": {
                    "effect": "no_article_10_change",
                    "source_ids": [
                        "CZ-MF-NL-45D279EE7770",
                        "CZ-MF-NL-7CAD483C3F1A",
                    ],
                },
                "mli_preliminary_finding": {
                    "effect": "Article 7(1) PPT",
                    "effective_from": "2021-01-01",
                    "source_id": "CZ-MF-NL-0210508FF125",
                },
                "data_quality_issues": [
                    {
                        "code": "participation_exemption_not_extracted",
                        "severity": "critical",
                        "detail": (
                            "The extractor returned only the 10% residual "
                            "rate and omitted the 0% direct-participation "
                            "rule in Article 10(3)."
                        ),
                        "affects_rate_conclusion": True,
                    },
                    {
                        "code": "article_cross_references_split",
                        "severity": "low",
                        "detail": (
                            "References to paragraph 3 and Article 7 are "
                            "split across parsed paragraphs."
                        ),
                        "affects_rate_conclusion": False,
                    },
                ],
                "domestic_and_eu_review_required": True,
                "human_confirmation_required": True,
                "review_outcome": None,
                "status": "preliminary_findings_only",
            },
            {
                "packet_id": "CZ-PL-INT-LEGAL-REVIEW",
                "recipient_country": "PL",
                "income_type": "interest",
                "treaty_findings": {
                    "rates": [
                        {
                            "rate": 5.0,
                            "conditions": [
                                "recipient is the beneficial owner",
                                "general residual treaty rate",
                            ],
                        },
                        {
                            "rate": 0.0,
                            "categories": [
                                "loans or credits granted by a bank",
                                (
                                    "interest paid to the other contracting "
                                    "state, its subdivisions, local "
                                    "authorities or central bank"
                                ),
                                (
                                    "interest paid to a financial institution "
                                    "owned or controlled by that government"
                                ),
                                (
                                    "loans or credits guaranteed by those "
                                    "governmental or public institutions"
                                ),
                            ],
                            "conditions": [
                                "recipient is the beneficial owner",
                            ],
                        },
                    ],
                    "pe_exception_applies": True,
                    "excess_payment_limitation": True,
                },
                "protocol_preliminary_finding": {
                    "effect": "no_protocol_effect_recorded",
                },
                "mli_preliminary_finding": {
                    "effect": "Article 7(1) PPT",
                    "effective_from": "2021-01-01",
                    "source_id": "CZ-MF-PL-B4A96328539C",
                },
                "data_quality_issues": [
                    {
                        "code": "zero_rate_requires_category_mapping",
                        "severity": "high",
                        "detail": (
                            "The 0% rate applies only to the categories "
                            "enumerated in Article 11(3)."
                        ),
                        "affects_rate_conclusion": True,
                    },
                    {
                        "code": "article_cross_references_split",
                        "severity": "low",
                        "detail": (
                            "References to Article 10(3) and Article 7 are "
                            "split across parsed paragraphs."
                        ),
                        "affects_rate_conclusion": False,
                    },
                ],
                "domestic_and_eu_review_required": True,
                "human_confirmation_required": True,
                "review_outcome": None,
                "status": "preliminary_findings_only",
            },
            {
                "packet_id": "CZ-SE-INT-LEGAL-REVIEW",
                "recipient_country": "SE",
                "income_type": "interest",
                "treaty_findings": {
                    "source_state_rate": 0.0,
                    "taxing_right": (
                        "Interest arising in one contracting state and paid "
                        "to a resident of the other contracting state is "
                        "taxable only in that other state."
                    ),
                    "rate_scope": "general",
                    "conditions": [
                        "recipient is resident in the other contracting state",
                        (
                            "the debt claim is not effectively connected "
                            "with a permanent establishment or fixed base "
                            "in the source state"
                        ),
                    ],
                    "beneficial_owner_wording_explicit": False,
                    "pe_or_fixed_base_exception_applies": True,
                    "excess_payment_limitation": True,
                },
                "protocol_preliminary_finding": {
                    "effect": "no_protocol_effect_recorded",
                },
                "mli_preliminary_finding": {
                    "effect": "no_mli_effect_recorded",
                    "requires_separate_verification": True,
                },
                "data_quality_issues": [
                    {
                        "code": "beneficial_owner_wording_not_explicit",
                        "severity": "medium",
                        "detail": (
                            "Article 11 does not expressly state a "
                            "beneficial-owner condition."
                        ),
                        "affects_rate_conclusion": False,
                    }
                ],
                "domestic_and_eu_review_required": True,
                "human_confirmation_required": True,
                "review_outcome": None,
                "status": "preliminary_findings_only",
            },
        ]
    )


    payload = {
        "schema_version": 1,
        "dataset_release": (
            "legal-review-batch-01-preliminary-findings-"
            "2026-08-05.1"
        ),
        "policy": {
            "source_derived_preliminary_findings": True,
            "not_a_completed_legal_review": True,
            "independent_approval_required": True,
            "fail_closed": True,
        },
        "summary": {
            "total_scopes": 30,
            "preliminary_findings_completed": len(findings),
            "preliminary_completion_percent": round(
                len(findings) / 30 * 100,
                1,
            ),
            "completed_primary_reviews": 0,
            "approved_scopes": 0,
        },
        "findings": findings,
    }

    OUTPUT.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return payload


def main() -> None:
    payload = build_findings()

    print("Batch preliminary findings created.")
    print(
        "Preliminary findings:",
        payload["summary"]["preliminary_findings_completed"],
        "/",
        payload["summary"]["total_scopes"],
    )
    print(
        "Content progress:",
        f'{payload["summary"]["preliminary_completion_percent"]}%',
    )
    print("Output:", OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
