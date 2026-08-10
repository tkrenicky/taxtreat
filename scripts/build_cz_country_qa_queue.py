from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
BASE = ROOT / "data/legal_reviews/global_cz_outbound"
STAGE5 = BASE / "stage5_human_review_package"
OUTPUT = BASE / "cz_country_qa_queue.json"
MLI_SCOPE_OUTPUT = BASE / "cz_wht_mli_product_scope.json"
GOVERNANCE_OUTPUT = BASE / "cz_scalable_release_governance.json"
REVIEW_DIR = BASE / "cz_country_qa_review_batches"
MANIFEST = ROOT / "data/manifests/source_manifest.json"
BASE_CANDIDATES = ROOT / "data/legal_consolidation/remaining_294_base_candidates.json"
MLI_EFFECTS = ROOT / "data/legal_consolidation/mli_wht_effects.json"
BLOCKER_RESOLUTIONS = ROOT / "data/legal_consolidation/blocker_resolutions.json"
HUMAN_CONDITION_CORRECTIONS = ROOT / "data/legal_consolidation/human_condition_corrections.json"
TAIWAN_SPECIAL = ROOT / "data/legal_special_jurisdictions/taiwan_45_2020.json"
AT_CH_RULES = {
    "AT": ROOT / "data/legal_rules/rakousko.json",
    "CH": ROOT / "data/legal_rules/svycarsko.json",
}
INCOMES = ("dividend", "interest", "royalty")
ARTICLE7_EXISTING_PROVISION_COUNTRIES = {
    "AM", "AZ", "BH", "BB", "CL", "CN", "CO", "CY", "ET", "IL", "JO",
    "KW", "LI", "LU", "PK", "PA", "PH", "SA", "SG", "CH", "SY", "UA", "UZ",
}
PPT_TEXT_PATTERN = re.compile(
    r"principal purpose|hlavn.{0,4} účel|jedn.{0,3} z hlavních|účelem.{0,80}výhod",
    re.IGNORECASE,
)


from taxtreat.consolidation.country_qa import (  # noqa: E402
    METHODOLOGY_VERSION,
    CountryRisk,
    classify_country_risk,
    select_independent_sample,
)
from taxtreat.engine.ppt_representation import PPT_REPRESENTATION_TEXT  # noqa: E402


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def render(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def stage5_scopes() -> list[dict[str, Any]]:
    index = load(STAGE5 / "index.json")
    rows = [
        row
        for node in index["batch_files"]
        for row in load(ROOT / node["path"])["scopes"]
    ]
    if len(rows) != 300 or len({row["recipient_country"] for row in rows}) != 100:
        raise RuntimeError("Stage 5 source package does not reconcile to 100/300.")
    return rows


def rate_candidates() -> dict[tuple[str, str], list[dict[str, Any]]]:
    result = {
        (row["recipient_country"], row["income_type"]): row["rate_candidates"]
        for row in load(BASE_CANDIDATES)["scopes"]
    }
    for country, path in AT_CH_RULES.items():
        rules = load(path)["rules"]
        for income in INCOMES:
            candidates = []
            for rule in rules:
                if (
                    rule["income_type"] == income
                    and rule["legal_layer"] in {"treaty", "protocol"}
                    and rule.get("effect", "rate") == "rate"
                    and rule.get("rate") is not None
                ):
                    candidates.append({
                        "rate": rule["rate"],
                        "legal_basis": f"Article {rule['article']}",
                        "conditions": rule.get("conditions", []),
                        "source_text": rule.get("source_text"),
                        "source_text_sha256": rule.get("source_excerpt_hash"),
                        "candidate_rule_id": rule["rule_id"],
                    })
            result[(country, income)] = candidates

    corrections = load(HUMAN_CONDITION_CORRECTIONS)["corrections"]
    for correction in corrections:
        key = (correction["country"], correction["income_type"])
        originals = result.get(key)
        if not originals:
            raise RuntimeError(f"Human correction target missing: {key}")
        template = originals[0]
        rebuilt = []
        for desired in correction["rate_candidates"]:
            source = next((row for row in originals if row.get("rate") == desired["rate"]), template)
            row = dict(source)
            row["rate"] = desired["rate"]
            row["conditions"] = desired["conditions"]
            row["candidate_rule_id"] = f"HUMAN-CORR-{key[0]}-{key[1]}-{str(desired['rate']).replace('.', '_')}"
            rebuilt.append(row)
        result[key] = rebuilt

    if len(result) != 300:
        raise RuntimeError(f"Expected 300 rate-candidate scopes, found {len(result)}.")
    return result


def language_summary(layer: dict[str, Any]) -> dict[str, Any]:
    evidence = layer.get("evidence") or {}
    interpretation = evidence.get("candidate_interpretation") or {}
    languages = interpretation.get("authentic_languages", evidence.get("authentic_languages"))
    prevailing = interpretation.get("prevailing_language_rule", evidence.get("prevailing_language_rule"))
    official = evidence.get("official_source") or evidence.get("evidence_source") or {}
    signature = evidence.get("signature_clause_candidate") or evidence.get("signature_clause_evidence") or {}
    if not signature and evidence.get("candidates"):
        signature = evidence["candidates"][0]
    return {
        "authentic_languages_candidate": languages,
        "prevailing_text_candidate": prevailing,
        "evidence_class": layer["evidence_class"],
        "signature_clause_excerpt": signature.get("exact_excerpt") or signature.get("machine_transcription"),
        "official_source_url": official.get("url"),
        "current_official_sha256": official.get("current_download_sha256"),
        "archived_manifest_sha256": official.get("archived_manifest_sha256"),
        "hash_relation": official.get("hash_relation"),
        "verification_status": evidence.get("verification_status", "needs_review"),
    }


def risk_features(country_rows: list[dict[str, Any]]) -> set[str]:
    features: set[str] = set()
    sequence = tuple(
        next(row for row in country_rows if row["income_type"] == income)["treaty_article"]["article_number"]
        for income in INCOMES
    )
    if sequence != (10, 11, 12):
        features.add("unusual_treaty_numbering")
    if any(row["protocol_overlays"]["inventory_protocol_listed"] for row in country_rows):
        features.add("material_protocol_overlay")
    related = country_rows[0]["protocol_overlays"]["inventory_related_instruments"]
    bilateral_history = [
        node for node in related
        if not str(node.get("source_type", "")).startswith("mli_")
    ]
    status = country_rows[0]["treaty_status_instruments"]
    if len(bilateral_history) > 1 or status.get("candidate_status") != "not_listed":
        features.add("multiple_historical_instruments")
    language = language_summary(country_rows[0]["language_authority_evidence"])
    if language["prevailing_text_candidate"] in {
        "french_prevails_in_dispute",
        "both_texts_authentic_no_prevailing_clause_stated",
    }:
        features.add("unusual_language_or_prevailing_text")
    if language["hash_relation"] == "current_official_bytes_differ_from_archived_manifest_preserved":
        original = country_rows[0]["language_authority_evidence"].get("evidence") or {}
        if original.get("former_gap_class") == "source_hash_conflict":
            features.add("preserved_historical_source_hash_difference")
    if any(row["blocker_partition"] == "genuine_legal_ambiguity_requires_human_determination" for row in country_rows):
        features.add("unresolved_legal_effect")
    if any(row["source_remediation_blockers"] for row in country_rows):
        features.add("conflicting_primary_evidence")
    return features


def source_references(
    country_rows: list[dict[str, Any]],
    manifest: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    first = country_rows[0]
    refs = [{
        "role": "base_treaty",
        "source_id": first["canonical_treaty"]["source_id"],
        "title": first["canonical_treaty"]["title"],
        "official_urls": first["canonical_treaty"]["official_urls"],
        "archived_sha256": first["canonical_treaty"]["archived_manifest_sha256"],
        "parsed_sha256": first["canonical_treaty"]["parsed_sha256"],
    }]
    ids: set[str] = set()
    for row in country_rows:
        ids.update(row["protocol_overlays"]["candidate_effect"].get("source_ids", []))
        ids.update(row["mli_evidence"]["candidate_effect"].get("resolution_source_ids", []))
        source_id = row["treaty_status_instruments"].get("source_id")
        if source_id:
            ids.add(source_id)
    for source_id in sorted(ids):
        source = manifest.get(source_id)
        refs.append({
            "role": "related_instrument_or_status_evidence",
            "source_id": source_id,
            "title": None if source is None else source.get("source_title"),
            "official_urls": [] if source is None else source.get("official_urls", []),
            "archived_sha256": None if source is None else source.get("sha256"),
        })
    return refs


def bilateral_anti_abuse_candidate(
    country: str,
    first: dict[str, Any],
) -> dict[str, Any]:
    parsed_path = ROOT / first["canonical_treaty"]["parsed_path"]
    parsed = load(parsed_path)
    matched_excerpt = None
    matched_article = None
    for article in parsed.get("articles", []):
        text = article.get("text", "")
        match = PPT_TEXT_PATTERN.search(text)
        if match:
            start = max(0, match.start() - 180)
            matched_excerpt = text[start:match.end() + 420]
            matched_article = article.get("number")
            break
    notified = country in ARTICLE7_EXISTING_PROVISION_COUNTRIES
    return {
        "relevant_candidate": notified or matched_excerpt is not None,
        "official_czech_mli_position_notifies_existing_article_7_2_provision": notified,
        "official_base_treaty_text_match": matched_excerpt is not None,
        "matched_article": matched_article,
        "candidate_excerpt": matched_excerpt,
        "parsed_path": str(parsed_path.relative_to(ROOT)),
        "parsed_sha256": digest(parsed_path),
        "verification_status": "needs_review",
    }


def build_mli_product_scope() -> dict[str, Any]:
    position_pdf = ROOT / "data/legal_sources/czech_mli_position/czech_republic_mli_position.pdf"
    position_text = ROOT / "data/legal_sources/czech_mli_position/czech_republic_mli_position.txt"
    effects = load(MLI_EFFECTS)["effects"]
    supplemental_effects = [
        row for row in load(BLOCKER_RESOLUTIONS)["mli_resolutions"]
        if row.get("effect_id")
    ]
    return {
        "schema_version": 1,
        "dataset_release": "cz-wht-mli-product-scope-2026-08-10.1",
        "product_scope": ["Czech-source dividends", "Czech-source interest", "Czech-source royalties"],
        "official_source_conclusion_status": "machine_consolidated_candidate_needs_human_qa",
        "wht_output_architecture": [
            "covered_tax_agreement_and_matching_status",
            "wht_relevant_mli_modification",
            "ppt_applicability",
            "pair_specific_wht_effective_date",
        ],
        "output_influencing_provisions": [{
            "article": "Article 7(1)",
            "role": "PPT may deny an otherwise available treaty benefit for any of the three income types",
            "automation_boundary": "TaxTreat asks for a user representation and never determines PPT satisfaction",
        }],
        "interpretive_support_only": [{
            "article": "Article 6",
            "role": "minimum-standard treaty purpose/preamble context supporting Article 7; no numeric WHT rate modification",
        }],
        "expressly_non_applicable_under_czech_position": [{
            "article": "Article 8",
            "reason": "Czechia reserves the right for the entirety of Article 8 not to apply to its Covered Tax Agreements",
            "adds_365_day_dividend_holding_period": False,
        }],
        "outside_tax_treat_product_output": [
            "Article 9 capital gains",
            "Articles 10 and 12-15 permanent-establishment provisions",
            "Article 16 mutual agreement procedure",
            "Article 17 corresponding adjustments",
            "Parts V-VI arbitration and administrative provisions",
        ],
        "wht_effective_date_mechanics": {
            "method": "Use the pair-specific official Czech MF MLI notice/effect record after CTA matching; do not substitute a generic date.",
            "article_35_role": "The Convention distinguishes taxes withheld at source and applies the matched modification from the applicable Article 35 entry-into-effect boundary.",
            "pair_specific_candidate_effect_count": len(effects) + len(supplemental_effects),
            "verification_status": "needs_review",
        },
        "official_primary_sources": [
            {
                "authority": "OECD Depositary",
                "title": "Czech Republic — Status of List of Reservations and Notifications",
                "url": "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/beps-mli/beps-mli-position-czech-republic.pdf",
                "pdf_path": str(position_pdf.relative_to(ROOT)),
                "pdf_sha256": digest(position_pdf),
                "text_path": str(position_text.relative_to(ROOT)),
                "text_sha256": digest(position_text),
                "article_8_excerpt": "Pursuant to Article 8(3)(a) of the Convention, the Czech Republic reserves the right for the entirety of Article 8 not to apply to its Covered Tax Agreements.",
                "article_7_excerpt": "Pursuant to Article 7(17)(b) of the Convention, the Czech Republic hereby chooses to apply Article 7(4).",
            },
            {
                "authority": "Ministry of the Interior of the Czech Republic",
                "title": "Multilateral Convention, Collection of International Treaties No. 32/2020",
                "url": "https://aplikace.mvcr.cz/sbirka-zakonu/ViewFile.aspx?type=c&id=38919",
                "source_id": "CZ-MLI-32-2020",
            },
            {
                "authority": "Ministry of Finance of the Czech Republic",
                "title": "Pair-specific Financial Gazette MLI notices",
                "artifact": str(MLI_EFFECTS.relative_to(ROOT)),
                "artifact_sha256": digest(MLI_EFFECTS),
                "supplemental_resolution_artifact": str(BLOCKER_RESOLUTIONS.relative_to(ROOT)),
                "supplemental_resolution_sha256": digest(BLOCKER_RESOLUTIONS),
            },
        ],
        "safety_boundary": {
            "candidate_evidence_is_not_legal_verification": True,
            "article_7_ppt_is_not_automatically_decided": True,
            "all_country_packages_remain_fail_closed": True,
        },
    }



def build_taiwan_package(sampled_pairs: set[str]) -> dict[str, Any]:
    source = load(TAIWAN_SPECIAL)
    domestic = load(OUTPUT)["packages"][0]["czech_domestic_wht"] if OUTPUT.exists() else {
        "effective_from": "2026-04-01",
        "standard_rate": 15.0,
        "protective_rate": 35.0,
        "source_id": "CZ-ZDP-2026-04-01-OPEN-DATA",
        "income_scope_reference": "section 22(1)(g)(3)",
        "standard_reference": "section 36(1)(b)(1), referring to section 22(1)(g)(3)",
        "protective_rate_reference": "section 36(1)(c)",
        "protective_rate_condition": "recipient is outside the EU/EEA and no qualifying treaty or tax-information-exchange instrument is applied",
    }
    excerpts = {
        "dividend": "Article 10(2): source-territory tax does not exceed 10% of the gross dividend where the beneficial owner is resident in the other territory.",
        "interest": "Article 11(2): 10% general ceiling for beneficial-owner interest; Article 11(3) provides source exemption for specified qualifying cases.",
        "royalty": "Article 12(2): 5% for industrial, commercial or scientific equipment; 10% in all other cases, subject to beneficial ownership.",
    }
    scopes = []
    for income in INCOMES:
        node = source["income_scopes"][income]
        conditions = []
        for rate in node["rates"]:
            if income == "interest" and rate == 0.0:
                cs = [
                    {"condition_type": "special_article_11_3_exemption", "operator": "==", "value": "true", "unit": None},
                    {"condition_type": "beneficial_owner", "operator": "==", "value": "true", "unit": None},
                ]
            elif income == "royalty" and rate == 5.0:
                cs = [
                    {"condition_type": "royalty_category", "operator": "==", "value": "industrial_commercial_scientific_equipment", "unit": None},
                    {"condition_type": "beneficial_owner", "operator": "==", "value": "true", "unit": None},
                ]
            elif income == "royalty" and rate == 10.0:
                cs = [
                    {"condition_type": "royalty_category", "operator": "==", "value": "other", "unit": None},
                    {"condition_type": "beneficial_owner", "operator": "==", "value": "true", "unit": None},
                ]
            else:
                cs = [{"condition_type": "beneficial_owner", "operator": "==", "value": "true", "unit": None}]
            conditions.append({"rate": rate, "conditions": cs})
        excerpt = excerpts[income]
        scopes.append({
            "income_type": income,
            "article_number": node["article"],
            "article_heading": {"dividend":"Dividendy","interest":"Úroky","royalty":"Licenční poplatky"}[income],
            "candidate_rates": node["rates"],
            "material_conditions": conditions,
            "candidate_excerpt": excerpt,
            "article_text_sha256": hashlib.sha256(excerpt.encode()).hexdigest(),
            "candidate_status": {"verification_status":"needs_review","stage5_terminal_status":"pending","fail_closed":True,"production_releasable":False},
        })
    package = {
        "treaty_pair_id": "CZ-TW",
        "partner_country": "TW",
        "partner_country_name": "Tchaj-wan",
        "risk_category": CountryRisk.ELEVATED.value,
        "risk_reasons": ["special_statutory_double_taxation_arrangement"],
        "review_focus": ["special_statutory_double_taxation_arrangement", "effective_notice_309_2020"],
        "base_treaty": {
            "identity": "zákon č. 45/2020 Sb. (příloha – Ustanovení ve vztahu k Tchaj-wanu)",
            "source_id": "CZ-TW-LAW-45-2020",
            "official_urls": ["https://e-sbirka.gov.cz/sb/2020/45"],
        },
        "current_instrument_chain": {
            "protocol": {
                "inventory_protocol_listed": False,
                "inventory_related_instruments": [{"authority":"Ministerstvo financí ČR / Sbírka zákonů","label":"Sdělení č. 309/2020 Sb.","source_id":"CZ-TW-NOTICE-309-2020","source_type":"effective_notice","url":"https://e-sbirka.gov.cz/sb/2020/309"}],
                "candidate_effect": {"required":True,"candidate_status":"official_effective_notice_identified_needs_human_review","candidate_effective_from":"2021-01-01","effect_kind":"wht_rules_start_using","candidate_rates":[],"source_ids":["CZ-TW-NOTICE-309-2020"]},
            },
            "status_instrument": {"candidate_status":"in_force_use_start_confirmed_needs_human_review","effect_kind":"special_statutory_arrangement_in_use","effective_from":"2021-01-01","effective_to":None,"source_id":"CZ-TW-NOTICE-309-2020","suspended_articles":[]},
        },
        "income_scopes": scopes,
        "wht_relevant_mli": {"cta_or_listing_status":"not_applicable_special_statutory_arrangement","modification":None,"article":None,"wht_effective_from_candidate":None,"source_page_id":None,"source_excerpt_sha256":None,"article_8_modification":None,"unrelated_mli_provisions_considered_in_wht_output":[]},
        "language_and_prevailing_text": {"authentic_languages_candidate":["Czech statutory text"],"prevailing_text_candidate":"not_applicable_special_statutory_arrangement","evidence_class":"official_czech_statutory_text","signature_clause_excerpt":None,"official_source_url":"https://e-sbirka.gov.cz/sb/2020/45","current_official_sha256":None,"archived_manifest_sha256":None,"hash_relation":None,"verification_status":"needs_review"},
        "effective_date_evidence": {"interpretation_status":"official_notice_candidate_needs_human_review","inventory_entry_into_force_candidate":"2020-03-12","mli_candidate_effective_from":None,"protocol_candidate_effective_from":"2021-01-01","status_candidate_effective_from":"2021-01-01","status_candidate_effective_to":None},
        "czech_domestic_wht": domestic,
        "eu_directive_interaction": {income:{"candidate":None,"candidate_status":"not_applicable_by_recipient_jurisdiction","potentially_relevant_by_recipient_jurisdiction":False} for income in INCOMES},
        "ppt_treatment": {"relevant":True,"relevance_basis":{"wht_relevant_mli_article_7_effect":False,"bilateral_ppt_or_equivalent_candidate":{"relevant_candidate":True,"official_czech_mli_position_notifies_existing_article_7_2_provision":False,"official_base_treaty_text_match":True,"matched_article":26,"candidate_excerpt":"Article 26 permits denial of benefits where the competent authority considers granting them an abuse of the provisions.","parsed_path":None,"parsed_sha256":None,"verification_status":"needs_review"}},"user_representation_text":None,"tax_treat_determines_ppt_satisfaction":False,"unknown_or_not_confirmed_treatment":"retain research; do not assert unconditional relief; Article 26 anti-abuse requires separate assessment"},
        "official_source_references": [
            {"role":"special_statutory_arrangement","source_id":"CZ-TW-LAW-45-2020","title":"Zákon č. 45/2020 Sb., o zamezení dvojímu zdanění ve vztahu k Tchaj-wanu","official_urls":["https://e-sbirka.gov.cz/sb/2020/45"],"archived_sha256":None,"parsed_sha256":None},
            {"role":"effective_notice","source_id":"CZ-TW-NOTICE-309-2020","title":"Sdělení MF č. 309/2020 Sb.","official_urls":["https://e-sbirka.gov.cz/sb/2020/309"],"archived_sha256":None},
        ],
        "audit_provenance": {"stage5_scope_ids":["CZ-TW-dividend","CZ-TW-interest","CZ-TW-royalty"],"candidate_chain_sha256":[],"existing_review_pack_sha256":[]},
        "human_qa": {"status":"pending","reviewer_id":None,"reviewed_at":None,"outcome":None,"independent_review_required":"CZ-TW" in sampled_pairs,"independent_sample_selected":"CZ-TW" in sampled_pairs,"independent_reviewer_id":None,"independently_reviewed_at":None,"independent_outcome":None},
        "release_state": {"scope_count":3,"needs_review_scope_count":3,"verified_scope_count":0,"fail_closed":True,"production_releasable":False},
    }
    package["package_sha256"] = canonical_hash(package)
    return package


def build_queue() -> dict[str, Any]:
    rows = stage5_scopes()
    rates = rate_candidates()
    manifest = {row["source_id"]: row for row in load(MANIFEST)["sources"]}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["recipient_country"]].append(row)

    risks = {
        f"CZ-{country}": classify_country_risk(risk_features(country_rows))
        for country, country_rows in grouped.items()
    }
    risks["CZ-TW"] = CountryRisk.ELEVATED
    sampled_pairs = select_independent_sample(risks)

    packages = []
    for country, country_rows in sorted(grouped.items()):
        country_rows.sort(key=lambda row: INCOMES.index(row["income_type"]))
        features = risk_features(country_rows)
        risk = risks[f"CZ-{country}"]
        first = country_rows[0]
        mli = first["mli_evidence"]["candidate_effect"]
        bilateral_anti_abuse = bilateral_anti_abuse_candidate(country, first)
        ppt_relevant = bool(mli.get("effect_id")) or bilateral_anti_abuse["relevant_candidate"]
        income_summaries = []
        for row in country_rows:
            candidate_rates = rates[(country, row["income_type"])]
            income_summaries.append({
                "income_type": row["income_type"],
                "article_number": row["treaty_article"]["article_number"],
                "article_heading": row["treaty_article"]["heading"],
                "candidate_rates": sorted({node["rate"] for node in candidate_rates}),
                "material_conditions": [
                    {"rate": node["rate"], "conditions": node.get("conditions", [])}
                    for node in candidate_rates
                ],
                "candidate_excerpt": row["treaty_article"]["exact_candidate_excerpt"],
                "article_text_sha256": row["treaty_article"]["article_text_sha256"],
                "candidate_status": row["candidate_status"],
            })
        package = {
            "treaty_pair_id": f"CZ-{country}",
            "partner_country": country,
            "partner_country_name": first["recipient_country_name"],
            "risk_category": risk.value,
            "risk_reasons": sorted(features),
            "review_focus": sorted(features) or ["high_level_three_income_sanity_check"],
            "base_treaty": {
                "identity": first["canonical_treaty"]["title"],
                "source_id": first["canonical_treaty"]["source_id"],
                "official_urls": first["canonical_treaty"]["official_urls"],
            },
            "current_instrument_chain": {
                "protocol": first["protocol_overlays"],
                "status_instrument": first["treaty_status_instruments"],
            },
            "income_scopes": income_summaries,
            "wht_relevant_mli": {
                "cta_or_listing_status": mli["status"],
                "modification": mli.get("effect_id"),
                "article": "Article 7(1) PPT" if mli.get("effect_id") else None,
                "wht_effective_from_candidate": mli.get("effective_from"),
                "source_page_id": mli.get("source_page_id"),
                "source_excerpt_sha256": mli.get("source_excerpt_sha256"),
                "article_8_modification": None,
                "unrelated_mli_provisions_considered_in_wht_output": [],
            },
            "language_and_prevailing_text": language_summary(first["language_authority_evidence"]),
            "effective_date_evidence": first["effective_date_evidence"],
            "czech_domestic_wht": first["domestic_czech_wht_layer"],
            "eu_directive_interaction": {
                income["income_type"]: next(row for row in country_rows if row["income_type"] == income["income_type"])["eu_directive_layer"]
                for income in income_summaries
            },
            "ppt_treatment": {
                "relevant": ppt_relevant,
                "relevance_basis": {
                    "wht_relevant_mli_article_7_effect": bool(mli.get("effect_id")),
                    "bilateral_ppt_or_equivalent_candidate": bilateral_anti_abuse,
                },
                "user_representation_text": PPT_REPRESENTATION_TEXT if ppt_relevant else None,
                "tax_treat_determines_ppt_satisfaction": False,
                "unknown_or_not_confirmed_treatment": "retain research; do not assert unconditional treaty relief; require separate anti-abuse/PPT assessment",
            },
            "official_source_references": source_references(country_rows, manifest),
            "audit_provenance": {
                "stage5_scope_ids": [row["scope_id"] for row in country_rows],
                "candidate_chain_sha256": [row["provenance"]["candidate_chain_sha256"] for row in country_rows],
                "existing_review_pack_sha256": [row["provenance"]["existing_review_pack_sha256"] for row in country_rows],
            },
            "human_qa": {
                "status": "pending",
                "reviewer_id": None,
                "reviewed_at": None,
                "outcome": None,
                "independent_review_required": risk is CountryRisk.EXCEPTION or f"CZ-{country}" in sampled_pairs,
                "independent_sample_selected": risk is not CountryRisk.EXCEPTION and f"CZ-{country}" in sampled_pairs,
                "independent_reviewer_id": None,
                "independently_reviewed_at": None,
                "independent_outcome": None,
            },
            "release_state": {
                "scope_count": 3,
                "needs_review_scope_count": 3,
                "verified_scope_count": 0,
                "fail_closed": True,
                "production_releasable": False,
            },
        }
        package["package_sha256"] = canonical_hash(package)
        packages.append(package)

    packages.append(build_taiwan_package(sampled_pairs))
    packages.sort(key=lambda row: row["partner_country"])

    counts = Counter(row["risk_category"] for row in packages)
    for category in CountryRisk:
        counts.setdefault(category.value, 0)
    formerly_ppt_only = sum(
        row["risk_category"] == CountryRisk.STANDARD.value
        and row["wht_relevant_mli"]["modification"] is not None
        for row in packages
    )
    return {
        "schema_version": 1,
        "dataset_release": "cz-country-qa-queue-2026-08-10.2",
        "methodology_version": METHODOLOGY_VERSION,
        "purpose": "Machine-prepared country-level legal QA queue; no package has been human reviewed or approved.",
        "summary": {
            "country_count": len(packages),
            "scope_count": sum(row["release_state"]["scope_count"] for row in packages),
            "risk_counts": dict(sorted(counts.items())),
            "pending_country_qa": sum(row["human_qa"]["status"] == "pending" for row in packages),
            "verified_scope_count": 0,
            "production_releasable_scope_count": 0,
            "previously_elevated_solely_for_clean_ppt_mli_path": formerly_ppt_only,
        },
        "packages": packages,
    }


def build_governance(queue: dict[str, Any]) -> dict[str, Any]:
    sampled = [row["treaty_pair_id"] for row in queue["packages"] if row["human_qa"]["independent_sample_selected"]]
    return {
        "schema_version": 1,
        "dataset_release": "cz-scalable-release-governance-2026-08-10.1",
        "status": "proposed_and_machine_enforced_candidate_workflow_not_production_release",
        "country_qa": {
            "required_for_every_country_package": True,
            "three_income_scopes_reviewed_together": True,
            "standard_review_target_minutes": [3, 5],
            "elevated_review_target_minutes": [8, 15],
            "exception_review_target": "issue-driven detailed legal research; no artificial time floor",
        },
        "independent_review": {
            "required_for_all_exception_packages": True,
            "standard_sample_percent": 5,
            "elevated_sample_percent": 10,
            "selection_method": "exact stratified quota (ceiling of category rate), selected by deterministic SHA-256 rank bound to methodology version and treaty pair",
            "sampling_rationale": "A small methodology-control sample checks machine-prepared package quality without re-performing treaty research. Article 7 PPT plus a mechanically clean WHT effective date is a standard cross-cutting condition and is not an elevated feature.",
            "selected_sample_pairs": sampled,
            "same_person_forbidden": True,
        },
        "estimated_workload": {
            "primary_country_qa_minutes": [408, 715],
            "independent_sample_minutes": [36, 65],
            "combined_hours_rounded": [7, 13],
            "exception_effort_excluded_until_an_exception_exists": True,
            "planning_estimate_not_completed_review": True,
        },
        "release_prerequisites": [
            "country QA event bound to exact package hash",
            "required exception/sample independent review event with separate identity",
            "all flagged corrections resolved and package rebuilt",
            "canonical automated invariants and clean-clone checks green",
            "explicit hash-bound rule promotion action; country QA alone never marks a scope verified",
            "production source-release gate explicitly opened by a separate release action",
        ],
        "legacy_four_eyes_boundary": {
            "hard_coded_locations": [
                "taxtreat/consolidation/legal_review_queue.py::_apply_decision (294 per-scope packets)",
                "taxtreat/consolidation/batch_primary_review.py (batch per-scope decisions)",
                "taxtreat/tools/build_legal_review_batch.py and review dossier builders",
                "taxtreat/pipeline/release.py legal-review summary fields",
                "data/legal_reviews/remaining_294_review_queue.json policy metadata",
            ],
            "change_in_this_release": "Legacy per-scope promotion path remains fail-closed. The new country-level QA gate is additive and cannot promote rules. A later policy-approved migration may retire the legacy path only after real QA records and release integration exist.",
            "safety_controls_removed": [],
        },
        "no_machine_human_approval": True,
        "ppt_only_mli_risk_correction": {
            "former_elevated_country_count": queue["summary"]["previously_elevated_solely_for_clean_ppt_mli_path"],
            "classification": "STANDARD when Article 7 PPT and its pair-specific WHT effective-date evidence are mechanically clean and no other elevated or exception feature exists",
        },
        "all_current_country_events_pending": True,
        "production_release_created": False,
    }


def markdown_batch(packages: list[dict[str, Any]], batch_number: int) -> str:
    lines = [
        f"# CZ country legal-QA review batch {batch_number:02d}",
        "",
        "> Machine-prepared candidate evidence only. No country or scope in this file has been human reviewed, approved, verified, or released.",
        "",
    ]
    for package in packages:
        lines.extend([
            f"## {package['partner_country']} — {package['partner_country_name']} ({package['risk_category']})",
            "",
            f"Base treaty: **{package['base_treaty']['identity']}** (`{package['base_treaty']['source_id']}`).",
            "",
            "Risk focus: " + ", ".join(package["review_focus"]) + ".",
            "",
            "| Income | Article | Candidate rate(s) | Material candidate conditions |",
            "|---|---:|---:|---|",
        ])
        for income in package["income_scopes"]:
            conditions = "; ".join(
                f"{node['rate']}%: " + ", ".join(
                    f"{condition.get('condition_type', condition.get('fact'))} {condition.get('operator')} {condition.get('value')}"
                    for condition in node["conditions"]
                )
                for node in income["material_conditions"]
            ) or "No extracted rate condition"
            lines.append(
                f"| {income['income_type']} | {income['article_number']} | "
                f"{', '.join(str(rate) + '%' for rate in income['candidate_rates']) or 'none'} | {conditions} |"
            )
        protocol = package["current_instrument_chain"]["protocol"]
        mli = package["wht_relevant_mli"]
        language = package["language_and_prevailing_text"]
        lines.extend([
            "",
            f"Protocol/status: `{protocol['candidate_effect'].get('candidate_status')}` / `{package['current_instrument_chain']['status_instrument'].get('candidate_status')}`.",
            "",
            f"MLI (WHT only): `{mli['cta_or_listing_status']}`; modification `{mli['modification']}`; candidate WHT date `{mli['wht_effective_from_candidate']}`. Article 8 adds no overlay.",
            "",
            f"Language: authentic `{language['authentic_languages_candidate']}`; prevailing `{language['prevailing_text_candidate']}`; evidence `{language['evidence_class']}`; signature clause `{language['signature_clause_excerpt']}`.",
            "",
            f"Domestic/EU: Czech candidate standard/protective rates `{package['czech_domestic_wht'].get('standard_rate')}` / `{package['czech_domestic_wht'].get('protective_rate')}`; EU interaction is shown per income in the JSON audit package.",
            "",
            "PPT: " + (package["ppt_treatment"]["user_representation_text"] or "No current WHT-relevant MLI PPT effect record.") ,
            "",
            "Official sources: " + "; ".join(
                f"[{ref['source_id']}]({ref['official_urls'][0]})" if ref.get("official_urls") else f"`{ref['source_id']}`"
                for ref in package["official_source_references"]
            ) + ".",
            "",
            "Candidate excerpts:",
            "",
        ])
        for income in package["income_scopes"]:
            excerpt = " ".join(income["candidate_excerpt"].split())[:900]
            lines.append(f"- {income['income_type']} Article {income['article_number']}: {excerpt} …")
        lines.extend([
            "",
            f"Audit package hash: `{package['package_sha256']}`.",
            "",
            "Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def write_outputs() -> None:
    mli_scope = build_mli_product_scope()
    queue = build_queue()
    governance = build_governance(queue)
    MLI_SCOPE_OUTPUT.write_text(render(mli_scope), encoding="utf-8")
    OUTPUT.write_text(render(queue), encoding="utf-8")
    GOVERNANCE_OUTPUT.write_text(render(governance), encoding="utf-8")
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    batch_size = 10
    package_count = len(queue["packages"])
    batch_count = (package_count + batch_size - 1) // batch_size
    for index in range(batch_count):
        path = REVIEW_DIR / f"batch_{index + 1:02d}.md"
        path.write_text(
            markdown_batch(
                queue["packages"][index * batch_size:(index + 1) * batch_size],
                index + 1,
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    write_outputs()
