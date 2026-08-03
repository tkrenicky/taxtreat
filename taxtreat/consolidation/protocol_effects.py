from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INVENTORY = ROOT / "data" / "legal_consolidation" / "mf_inventory.json"
DEFAULT_BASE_CANDIDATES = (
    ROOT / "data" / "legal_consolidation" / "remaining_294_base_candidates.json"
)
DEFAULT_OUTPUT = (
    ROOT / "data" / "legal_consolidation" / "protocol_effect_candidates.json"
)


PROTOCOL_DOCUMENTS: dict[str, list[dict[str, str]]] = {
    "BE": [{
        "source_id": "CZ-MF-BE-D0E145875613",
        "entry_into_force": "2015-01-13",
        "candidate_effective_from": "2016-01-01",
        "source_document_sha256": "732c539fe77e9a29bcae92344a8a8bf81c31f6e4cff5d5c0238fae2f2155eeac",
    }],
    "BY": [{
        "source_id": "CZ-MF-BY-9FB15934EDD7",
        "entry_into_force": "2011-05-31",
        "candidate_effective_from": "2012-01-01",
        "source_document_sha256": "39e56e09142fef6cd8240ddeaa1dcf2f131500c26bcb9048357dd1e0ae666963",
    }],
    "HR": [{
        "source_id": "CZ-MF-HR-FF7645967F85",
        "entry_into_force": "2012-07-30",
        "candidate_effective_from": "2013-01-01",
        "source_document_sha256": "87fde5d9e8aeb1353059fc68a58dc68620c1d1ac12c522dd735d1677fec968bc",
    }],
    "KZ": [{
        "source_id": "CZ-MF-KZ-1510692CA08E",
        "entry_into_force": "2016-06-28",
        "candidate_effective_from": "2017-01-01",
        "source_document_sha256": "8b1d1d9f5222317e50d4fec103173d02e0f2a883c358bc743a08537bcb4a31ee",
    }],
    "MD": [{
        "source_id": "CZ-MF-MD-4CDF66434EF2",
        "entry_into_force": "2005-07-13",
        "candidate_effective_from": "2006-01-01",
        "source_document_sha256": "e5c2ae2a3a370e4ac4baf1b5da31325305f37cf77174806ec0613bddb002d6ee",
    }],
    "NL": [
        {
            "source_id": "CZ-MF-NL-45D279EE7770",
            "entry_into_force": "1997-04-11",
            "candidate_effective_from": "1998-01-01",
            "source_document_sha256": "46302e1d53791277d487b197fa8924a6cf7a52381e524bb84c58969f84356017",
        },
        {
            "source_id": "CZ-MF-NL-7CAD483C3F1A",
            "entry_into_force": "2013-05-31",
            "candidate_effective_from": "2014-01-01",
            "source_document_sha256": "d1cad7bfa1f4854fdddd36bdbc5585b2d25c3aa8fa15594063b2a5f0ee1e6595",
        },
    ],
    "RS": [{
        "source_id": "CZ-MF-RS-7987A53E3798",
        "entry_into_force": "2011-02-28",
        "candidate_effective_from": "2012-01-01",
        "source_document_sha256": "93a287fdcf0b097714c3348798c05a7b1464c6000738720211f6fe8cfb838d2a",
    }],
    "RU": [{
        "source_id": "CZ-MF-RU-2647E9E83753",
        "entry_into_force": "2009-04-17",
        "candidate_effective_from": "2010-01-01",
        "source_document_sha256": "30ce8f0520aea9e7076870c54f9253efc242b3eed69862ea9ecc1b7ca3e8a307",
    }],
    "SG": [{
        "source_id": "CZ-MF-SG-D1E21A71E463",
        "entry_into_force": "2014-09-12",
        "candidate_effective_from": "2015-01-01",
        "source_document_sha256": "826cea30f4213c69c1102c6dc19e4c4ff6650ad03ce00b9b883ceb9602b12612",
    }],
    "UA": [{
        "source_id": "CZ-MF-UA-5F98838DA169",
        "entry_into_force": "2015-12-09",
        "candidate_effective_from": "2016-01-01",
        "source_document_sha256": "083f60f62a4a2c09586f1d6ca6e5a87569ede388f522ba10e5f7f77b80f1202a",
    }],
    "UZ": [{
        "source_id": "CZ-MF-UZ-91E56630154D",
        "entry_into_force": "2012-06-15",
        "candidate_effective_from": "2013-01-01",
        "source_document_sha256": "86bff9645370f35e14fea7aa347887f389150636dd417d58fd01f2678bf645a8",
    }],
}


def _rate(rate: float, condition: str) -> dict[str, Any]:
    return {"rate": rate, "condition_summary": condition}


PROTOCOL_EFFECTS: dict[str, dict[str, dict[str, Any]]] = {
    "BE": {
        income: {
            "effect_kind": "confirmed_no_article_10_12_change",
            "evidence_anchor": "Protocol Article I amends treaty Article 26 only",
        }
        for income in ("dividend", "interest", "royalty")
    },
    "BY": {
        "dividend": {
            "effect_kind": "replace_rates",
            "evidence_anchor": "Protocol Article V(1), treaty Article 10(2)",
            "rate_candidates": [
                _rate(5.0, "beneficial-owner company directly holds at least 25% of payer capital"),
                _rate(10.0, "all other cases"),
            ],
        },
        "interest": {
            "effect_kind": "add_conditional_exemptions",
            "evidence_anchor": "Protocol Article VI(1), treaty Article 11(3)",
            "rate_candidates": [
                _rate(0.0, "qualifying bank loan or credit"),
                _rate(0.0, "qualifying government, authority, central bank or listed public institution"),
            ],
        },
        "royalty": {
            "effect_kind": "replace_rates",
            "evidence_anchor": "Protocol Article VII(1), treaty Article 12(2)",
            "rate_candidates": [_rate(5.0, "all royalties within treaty Article 12")],
        },
    },
    "HR": {
        "dividend": {
            "effect_kind": "confirmed_no_article_10_change",
            "evidence_anchor": "Protocol contains no amendment to treaty Article 10",
        },
        "interest": {
            "effect_kind": "definition_change_only",
            "evidence_anchor": "Protocol Article 2, treaty Article 11(2)",
            "scope_summary": "Income treated as a dividend under Article 10(3) is excluded from interest.",
        },
        "royalty": {
            "effect_kind": "confirmed_no_article_12_change",
            "evidence_anchor": "Protocol contains no amendment to treaty Article 12",
        },
    },
    "KZ": {
        "dividend": {
            "effect_kind": "definition_change_only",
            "evidence_anchor": "Protocol Article 6, treaty Article 10(3)",
        },
        "interest": {
            "effect_kind": "add_conditional_exemptions",
            "evidence_anchor": "Protocol Article 7(1), treaty Article 11(3)",
            "rate_candidates": [
                _rate(0.0, "qualifying government, authority, central bank or government-owned export institution"),
                _rate(0.0, "loan or credit guaranteed by a qualifying public body or export institution"),
            ],
        },
        "royalty": {
            "effect_kind": "confirmed_no_article_12_change",
            "evidence_anchor": "Protocol contains no amendment to treaty Article 12",
        },
    },
    "MD": {
        income: {
            "effect_kind": "confirmed_no_article_10_12_change",
            "evidence_anchor": "Protocol Articles I-VI do not amend treaty Articles 10-12",
        }
        for income in ("dividend", "interest", "royalty")
    },
    "NL": {
        "dividend": {
            "effect_kind": "confirmed_no_article_10_change",
            "evidence_anchor": "1996 and 2012 Protocols contain no amendment to treaty Article 10",
        },
        "interest": {
            "effect_kind": "definition_change_only",
            "evidence_anchor": "1996 Protocol Article 3, treaty Article 11(2)",
        },
        "royalty": {
            "effect_kind": "confirmed_no_article_12_change",
            "evidence_anchor": "1996 and 2012 Protocols contain no amendment to treaty Article 12",
        },
    },
    "RS": {
        income: {
            "effect_kind": "confirmed_no_article_10_12_change",
            "evidence_anchor": "Protocol Articles 1-4 do not amend treaty Articles 10-12",
        }
        for income in ("dividend", "interest", "royalty")
    },
    "RU": {
        "dividend": {
            "effect_kind": "replace_rates",
            "evidence_anchor": "Protocol Article III(1), treaty Article 10(2)",
            "rate_candidates": [_rate(10.0, "all dividends within treaty Article 10")],
        },
        "interest": {
            "effect_kind": "replace_rates",
            "evidence_anchor": "Protocol Article IV(1), treaty Article 11(1)",
            "rate_candidates": [_rate(0.0, "beneficial owner is resident of the other contracting state")],
        },
        "royalty": {
            "effect_kind": "replace_rates",
            "evidence_anchor": "Protocol Article V, treaty Article 12(2)",
            "rate_candidates": [_rate(10.0, "all royalties within treaty Article 12")],
        },
    },
    "SG": {
        "dividend": {
            "effect_kind": "beneficial_owner_scope_change",
            "evidence_anchor": "Protocol Article 1(2), treaty Article 3(3)",
            "scope_summary": "A qualifying taxable trustee is deemed the beneficial owner.",
        },
        "interest": {
            "effect_kind": "scope_and_definition_changes",
            "evidence_anchor": "Protocol Articles 1(2), 3(4) and 5",
            "scope_summary": "Adds a trustee rule, an international-traffic rule and exclusions from interest.",
        },
        "royalty": {
            "effect_kind": "replace_rates_and_categories",
            "evidence_anchor": "Protocol Article 6, treaty Article 12(2)-(3)",
            "rate_candidates": [
                _rate(0.0, "copyright royalties excluding computer software"),
                _rate(5.0, "industrial, commercial or scientific equipment"),
                _rate(10.0, "patents, marks, designs, plans, formulae, processes, software or know-how"),
            ],
        },
    },
    "UA": {
        "dividend": {
            "effect_kind": "definition_change_only",
            "evidence_anchor": "Protocol Article 6, treaty Article 10(3)",
        },
        "interest": {
            "effect_kind": "add_conditional_exemptions",
            "evidence_anchor": "Protocol Article 7(1), treaty Article 11(3)",
            "rate_candidates": [
                _rate(0.0, "qualifying government, authority, central bank or government-owned/controlled institution"),
                _rate(0.0, "qualifying public loan or credit, including guaranteed or insured financing"),
            ],
        },
        "royalty": {
            "effect_kind": "definition_change_only",
            "evidence_anchor": "Protocol Article 8, treaty Article 12(3) and (6)",
        },
    },
    "UZ": {
        "dividend": {
            "effect_kind": "replace_rates",
            "evidence_anchor": "Protocol Article II(1), treaty Article 10(2)",
            "rate_candidates": [
                _rate(5.0, "beneficial-owner company directly holds at least 25% of payer capital"),
                _rate(10.0, "all other cases"),
            ],
        },
        "interest": {
            "effect_kind": "add_conditional_exemptions",
            "evidence_anchor": "Protocol Article III(1), treaty Article 11(3)(a)",
            "rate_candidates": [
                _rate(0.0, "qualifying government, authority, central bank or government-owned/controlled institution"),
                _rate(0.0, "loan or credit guaranteed or insured by a qualifying public body"),
            ],
        },
        "royalty": {
            "effect_kind": "definition_change_only",
            "evidence_anchor": "Protocol Article IV, treaty Article 12(3)",
        },
    },
}


LATER_STATUS_INSTRUMENTS = {
    "BY": "CZ-MF-BY-852FD44A9622",
    "RU": "CZ-MF-RU-4F72F907462B",
}


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_protocol_effects(
    *,
    inventory_path: str | Path = DEFAULT_INVENTORY,
    base_candidates_path: str | Path = DEFAULT_BASE_CANDIDATES,
) -> dict[str, Any]:
    inventory = json.loads(Path(inventory_path).read_text(encoding="utf-8"))
    base_payload = json.loads(
        Path(base_candidates_path).read_text(encoding="utf-8")
    )
    inventory_by_code = {row["iso2"]: row for row in inventory["partners"]}
    base_by_scope = {
        (row["recipient_country"], row["income_type"]): row
        for row in base_payload["scopes"]
    }

    expected_codes = {
        row["iso2"]
        for row in inventory["partners"]
        if row["protocol_listed"] and row["iso2"] not in {"AT", "CH"}
    }
    if expected_codes != set(PROTOCOL_DOCUMENTS) or expected_codes != set(PROTOCOL_EFFECTS):
        raise ValueError("Curated protocol coverage must match all non-pilot protocol partners.")

    documents: list[dict[str, Any]] = []
    scopes: list[dict[str, Any]] = []
    for country in sorted(expected_codes):
        inventory_row = inventory_by_code[country]
        official_protocols = {
            row["source_id"]: row
            for row in inventory_row["related_instruments"]
            if row["source_type"] == "protocol"
        }
        curated_documents = PROTOCOL_DOCUMENTS[country]
        if set(official_protocols) != {
            row["source_id"] for row in curated_documents
        }:
            raise ValueError(f"Protocol source mismatch for {country}.")
        for document in curated_documents:
            source = official_protocols[document["source_id"]]
            documents.append({
                "recipient_country": country,
                "source_id": document["source_id"],
                "label": source["label"],
                "url": source["url"],
                "authority": source["authority"],
                **{key: value for key, value in document.items() if key != "source_id"},
                "verification_status": "needs_review",
            })

        for income_type in ("dividend", "interest", "royalty"):
            effect = deepcopy(PROTOCOL_EFFECTS[country][income_type])
            base = base_by_scope[(country, income_type)]
            protocol_rates = effect.pop("rate_candidates", [])
            later_status_source = LATER_STATUS_INSTRUMENTS.get(country)
            blockers = [
                "independent_legal_review",
                "protocol_effect_candidate_review",
            ]
            if inventory_row["mli_listed"]:
                blockers.append("mli_effect_candidate_review")
            if later_status_source:
                blockers.append("post_protocol_status_instrument_consolidation")
            blockers.append(
                "domestic_and_parent_subsidiary_relief_consolidation"
                if income_type == "dividend"
                else "domestic_and_eu_relief_consolidation"
            )
            scope = {
                "source_country": "CZ",
                "recipient_country": country,
                "income_type": income_type,
                "protocol_source_ids": [row["source_id"] for row in curated_documents],
                "protocol_candidate_effective_from": max(
                    row["candidate_effective_from"] for row in curated_documents
                ),
                "base_rate_candidates": [
                    {
                        "rate": row["rate"],
                        "conditions": row["conditions"],
                    }
                    for row in base["rate_candidates"]
                ],
                "protocol_rate_candidates": protocol_rates,
                "later_status_source_id": later_status_source,
                "consolidation_blockers": sorted(blockers),
                "candidate_status": "protocol_effect_candidate_consolidated",
                "verification_status": "needs_review",
                **effect,
            }
            scope["candidate_sha256"] = _sha256_text(
                json.dumps(scope, ensure_ascii=False, sort_keys=True)
            )
            scopes.append(scope)

    if len(documents) != 12 or len(scopes) != 33:
        raise ValueError("Expected 12 protocol instruments and 33 protocol scopes.")
    return {
        "schema_version": 1,
        "dataset_release": "remaining-294-protocol-effects-2026-08-03.1",
        "legal_data_cutoff": inventory["source_page"]["legal_data_cutoff"],
        "scope_exclusions": {
            "AT": "covered by the AT/CH pilot",
            "CH": "covered by the AT/CH pilot",
        },
        "documents": documents,
        "scopes": sorted(
            scopes,
            key=lambda row: (row["recipient_country"], row["income_type"]),
        ),
    }


def write_protocol_effects(
    payload: dict[str, Any],
    path: str | Path = DEFAULT_OUTPUT,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
