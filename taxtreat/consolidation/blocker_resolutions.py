from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INVENTORY = ROOT / "data" / "legal_consolidation" / "mf_inventory.json"
DEFAULT_OUTPUT = (
    ROOT / "data" / "legal_consolidation" / "blocker_resolutions.json"
)

LEGAL_STATUS_AS_OF = "2026-08-04"
GREEK_DIVIDEND_ARTICLE_SHA256 = (
    "3999b70531b5111b4bb1440a925feeec26b9b55abf5df117f0d43a1633e9833b"
)

OECD_MLI_PARTIES_URL = (
    "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/"
    "beps-mli/beps-mli-signatories-and-parties.pdf"
)
OECD_CZECH_POSITION_URL = (
    "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/"
    "beps-mli/beps-mli-position-czech-republic-instrument-deposit.pdf"
)
OECD_ESTONIA_POSITION_URL = (
    "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/"
    "beps-mli/beps-mli-position-estonia-instrument-deposit.pdf"
)
OECD_SWEDEN_POSITION_URL = (
    "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/"
    "beps-mli/beps-mli-position-sweden.pdf"
)
OECD_MLI_TEXT_URL = (
    "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/"
    "beps-mli/multilateral-convention-to-implement-tax-treaty-related-"
    "measures-to-prevent-beps.pdf"
)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _evidence(value: str) -> dict[str, str]:
    return {"summary": value, "summary_sha256": _sha256(value)}


MLI_RESOLUTIONS: tuple[dict[str, Any], ...] = (
    {
        "recipient_country": "EE",
        "resolution_status": "wht_effect_candidate_available",
        "effect_id": "CZ-EE-MLI-WHT-PPT",
        "effective_from": "2025-01-01",
        "mli_article": "Article 7(1) PPT",
        "czech_treaty_listing": "added_by_notification",
        "czech_notification_communication_date": "2024-08-16",
        "counterparty_treaty_listing": "listed_agreement_12",
        "counterparty_mli_entry_into_force": "2021-05-01",
        "source_ids": [
            "CZ-MF-EE-420787A74132",
            "OECD-MLI-CZ-POSITION",
            "OECD-MLI-EE-POSITION",
            "OECD-MLI-ARTICLE-35",
            "OECD-MLI-PARTIES-2026-07",
        ],
        "evidence": _evidence(
            "Czechia added the Czech-Estonian agreement to its MLI list in "
            "the notification communicated on 16 August 2024; Estonia had "
            "already listed the same agreement and its MLI was in force. "
            "Article 35(5)(a) therefore gives Czech WHT effect from "
            "1 January 2025."
        ),
    },
    {
        "recipient_country": "SE",
        "resolution_status": "wht_effect_candidate_available",
        "effect_id": "CZ-SE-MLI-WHT-PPT",
        "effective_from": "2021-01-01",
        "mli_article": "Article 7(1) PPT",
        "czech_treaty_listing": "listed_agreement_49",
        "counterparty_treaty_listing": "listed_agreement_16",
        "counterparty_mli_entry_into_force": "2018-10-01",
        "czech_mli_entry_into_force": "2020-09-01",
        "source_ids": [
            "OECD-MLI-CZ-POSITION",
            "OECD-MLI-SE-POSITION",
            "OECD-MLI-ARTICLE-35",
            "OECD-MLI-PARTIES-2026-07",
        ],
        "evidence": _evidence(
            "Czechia and Sweden both listed their 1979 agreement and both "
            "MLI instruments were in force by 1 September 2020; Article "
            "35(1)(a) therefore gives Czech WHT effect from 1 January 2021."
        ),
    },
    *(
        {
            "recipient_country": code,
            "resolution_status": "signed_not_ratified_no_current_wht_effect",
            "effect_id": None,
            "effective_from": None,
            "mli_article": None,
            "signature_date": signature_date,
            "deposit_of_ratification": None,
            "checked_as_of": LEGAL_STATUS_AS_OF,
            "source_ids": [
                "OECD-MLI-CZ-POSITION",
                "OECD-MLI-PARTIES-2026-07",
            ],
            "evidence": _evidence(
                f"{name} had signed the MLI on {signature_date} but had not "
                f"deposited an instrument of ratification by "
                f"{LEGAL_STATUS_AS_OF}; no MLI WHT effect can therefore be "
                "applied to the Czech treaty on that date."
            ),
        }
        for code, name, signature_date in (
            ("CO", "Colombia", "2017-06-07"),
            ("IT", "Italy", "2017-06-07"),
            ("KW", "Kuwait", "2017-06-07"),
            ("MA", "Morocco", "2019-06-25"),
            ("MK", "North Macedonia", "2020-01-29"),
            ("NG", "Nigeria", "2017-08-17"),
            ("TR", "Türkiye", "2017-06-07"),
        )
    ),
)


STATUS_INSTRUMENTS: tuple[dict[str, Any], ...] = (
    {
        "recipient_country": "BY",
        "source_id": "CZ-MF-BY-852FD44A9622",
        "notice_label": "Sdělení č. 115/2024 Sb.",
        "notice_date": "2024-03-21",
        "effective_from": "2024-06-01",
        "effective_to": "2026-12-31",
        "suspended_articles": [10, 11, 13],
        "effect_kind": "temporary_partial_suspension",
        "evidence": _evidence(
            "Belarus suspended Articles 10, 11 and 13 of the Czech-Belarus "
            "treaty, as amended, from 1 June 2024 through 31 December 2026."
        ),
    },
    {
        "recipient_country": "RU",
        "source_id": "CZ-MF-RU-4F72F907462B",
        "notice_label": "Sdělení č. 36/2023 Sb. m. s.",
        "notice_date": "2023-08-08",
        "effective_from": "2023-08-11",
        "effective_to": None,
        "suspended_articles": [*range(5, 23), 24],
        "effect_kind": "partial_suspension",
        "evidence": _evidence(
            "Russia suspended Articles 5 through 22 and Article 24 of the "
            "Czech-Russian treaty, as amended, with effect from "
            "11 August 2023."
        ),
    },
)


BASE_TREATY_RESOLUTIONS: tuple[dict[str, Any], ...] = (
    {
        "recipient_country": "GR",
        "income_type": "dividend",
        "article_number": 10,
        "article_text_sha256": GREEK_DIVIDEND_ARTICLE_SHA256,
        "resolution_status": "source_state_taxation_without_numeric_treaty_cap",
        "rate_cap_status": "no_numeric_cap",
        "source_state_taxation": "permitted_under_domestic_law",
        "source_id": "CZ-MF-GR-31B8B4B101BC",
        "evidence": _evidence(
            "Article 10(1) permits taxation of dividends in both Contracting "
            "States and contains no numeric ceiling on source-state tax."
        ),
    },
)


SOURCE_DOCUMENTS: tuple[dict[str, str], ...] = (
    {
        "source_id": "OECD-MLI-PARTIES-2026-07",
        "authority": "OECD MLI Depositary",
        "url": OECD_MLI_PARTIES_URL,
    },
    {
        "source_id": "OECD-MLI-CZ-POSITION",
        "authority": "OECD MLI Depositary",
        "url": OECD_CZECH_POSITION_URL,
    },
    {
        "source_id": "OECD-MLI-EE-POSITION",
        "authority": "OECD MLI Depositary",
        "url": OECD_ESTONIA_POSITION_URL,
    },
    {
        "source_id": "OECD-MLI-SE-POSITION",
        "authority": "OECD MLI Depositary",
        "url": OECD_SWEDEN_POSITION_URL,
    },
    {
        "source_id": "OECD-MLI-ARTICLE-35",
        "authority": "OECD MLI Depositary",
        "url": OECD_MLI_TEXT_URL,
    },
)


def build_blocker_resolutions(
    *, inventory_path: str | Path = DEFAULT_INVENTORY
) -> dict[str, Any]:
    inventory = json.loads(Path(inventory_path).read_text(encoding="utf-8"))
    partners = {row["iso2"]: row for row in inventory["partners"]}
    if len(partners) != 100:
        raise ValueError("Instrument inventory must cover 100 partners.")

    mli_codes = {row["recipient_country"] for row in MLI_RESOLUTIONS}
    if mli_codes != {"CO", "EE", "IT", "KW", "MA", "MK", "NG", "SE", "TR"}:
        raise ValueError("MLI blocker resolutions do not cover the expected queue.")
    if not all(partners[code]["mli_listed"] for code in mli_codes):
        raise ValueError("An MLI resolution targets a partner not listed for MLI.")

    for row in STATUS_INSTRUMENTS:
        source_ids = {
            source["source_id"]
            for source in partners[row["recipient_country"]][
                "related_instruments"
            ]
        }
        if row["source_id"] not in source_ids:
            raise ValueError(
                f"Missing status source {row['source_id']} in MF inventory."
            )

    return {
        "schema_version": 1,
        "dataset_release": "remaining-blocker-resolutions-2026-08-04.1",
        "legal_status_as_of": LEGAL_STATUS_AS_OF,
        "verification_status": "needs_review",
        "source_documents": sorted(
            SOURCE_DOCUMENTS, key=lambda row: row["source_id"]
        ),
        "mli_resolutions": sorted(
            MLI_RESOLUTIONS, key=lambda row: row["recipient_country"]
        ),
        "status_instruments": sorted(
            STATUS_INSTRUMENTS, key=lambda row: row["recipient_country"]
        ),
        "base_treaty_resolutions": list(BASE_TREATY_RESOLUTIONS),
        "summary": {
            "mli_effect_candidates": sum(
                row["resolution_status"] == "wht_effect_candidate_available"
                for row in MLI_RESOLUTIONS
            ),
            "mli_no_current_effect_determinations": sum(
                row["resolution_status"]
                == "signed_not_ratified_no_current_wht_effect"
                for row in MLI_RESOLUTIONS
            ),
            "status_instruments": len(STATUS_INSTRUMENTS),
            "base_treaty_semantic_resolutions": len(BASE_TREATY_RESOLUTIONS),
            "resolved_scopes": 34,
        },
    }


def write_blocker_resolutions(
    payload: dict[str, Any], path: str | Path = DEFAULT_OUTPUT
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
