from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/legal_reviews/global_cz_outbound"
INVENTORY = ROOT / "data/legal_consolidation/mf_inventory.json"
MANIFEST = ROOT / "data/manifests/source_manifest.json"
AT_CH_EXISTING = BASE / "at_ch_existing_source_evidence.json"
MLI_EFFECTS = ROOT / "data/legal_consolidation/mli_wht_effects.json"
OUTPUT = BASE / "stage5_final10_source_remediation.json"


LANGUAGE_CASES: dict[str, dict[str, Any]] = {
    "AT": {"source_id": "SRC-142E073CB800ACCE", "page": 37, "hash": "08dffc8820e7ed4f344a5b9eb004772ee2f341ee2d4c2890386456ef7f161bbd", "languages": ["English"], "rule": "sole_english", "excerpt": "Dáno v Praze dne 8. cervna 2006 ve dvou puvodnõch vyhotovenõch v anglickém jazyce.", "method": "official_pdf_text_layer"},
    "BH": {"source_id": "SRC-023262E3EBEE0E28", "page": 21, "hash": "c14188c1722ddd018fa6d53a33f4a78ff09ad86984409530fd6ef7294b4c17fc", "languages": ["Czech", "Arabic", "English"], "rule": "english_prevails_all_text_divergences", "excerpt": "Dano v Praze dne 24. kvétna 2011 ve dvou ptivodnich vyhotovenich, v éeském, arabském a anglickém jazyce, pYitemZ vSechny tii texty jsou autentické. V pripadé jakéhokoliv rozdilu bude rozhodujicim anglicky text.", "method": "tesseract_5.3.4_eng_not_human_verified"},
    "CH": {"source_id": "SRC-773D5F8BD93AE73A", "page": 14, "hash": "f5c19b46bb6e3c4af8537ca8e3369e5948f96611c9fe51fcfdbd246560af619f", "languages": ["Czech", "German", "English"], "rule": "english_prevails_czech_german_interpretive_divergence", "excerpt": "Dáno v Praze ve dvojõm vyhotovenõ dne 4. prosince 1995 v ceském, nemeckém a anglickém jazyce, pricemz vsechny texty jsou autentické. V prõpade jakýchkoliv rozdõlnostõ výkladu mezi ceským a nemeckým textem bude rozhodujõcõ anglický text.", "method": "official_pdf_text_layer"},
    "CL": {"source_id": "SRC-CE747E586B47529F", "page": 25, "hash": "03a3e05c8232f71585b6aac9833f279a0eba4623e0dbbac2350ce27b9c33c7b0", "languages": ["Czech", "Spanish", "English"], "rule": "english_prevails_all_text_divergences", "excerpt": "Dano v Santiagu de Chile dne 2. prosince 2015 ve dvou piivodnich vyhotovenich, v éeském, Spanélském a anglickém jazyce, priéemZ vSechny texty jsou autentické. V pripadé jakéhokoliv rozdilu bude rozhodujicim anglicky text.", "method": "tesseract_5.3.4_eng_not_human_verified"},
    "CO": {"source_id": "SRC-C8C9A9DAD91A0DEF", "page": 22, "hash": "0f1b515e56e9a4b695dcf02e6c8757ac4a16bd3621f55d61861f5a14f4652a9c", "languages": ["Czech", "Spanish", "English"], "rule": "english_prevails_all_text_divergences", "excerpt": "Dano v Bogoté D.C. dne 22. brezna 2012 ve dvou ptivodnich vyhotovenich, v éeském, Spanélském a anglickém jazyce, pri¢emZ vSechny texty jsou autentické. V pripadé jakéhokoliv rozdilu bude rozhodujicim anglicky text.", "method": "tesseract_5.3.4_eng_not_human_verified"},
    "GH": {"source_id": "SRC-0CAA69D6B9F619E5", "page": 23, "hash": "ccac4155518ad15429205c394979994da76f4627ed57dba659d6d098c09d078a", "languages": ["Czech", "English"], "rule": "both_texts_authentic_no_prevailing_clause_stated", "excerpt": "Dano v Akk#e dne 11. dubna 2017 ve dvou piivodnich vyhotovenich, v éeském a anglickém jazyce, pri¢emZ oba texty jsou autentické.", "method": "tesseract_5.3.4_eng_not_human_verified"},
    "JP": {"source_id": "SRC-DAF33E409B334A94", "page": 11, "hash": "06a55be51d08a7a17aed0a4b8e78a53d2576defae8554d5dcff36bcadc9ba1ef", "languages": ["English"], "rule": "sole_english", "excerpt": "Dano ve dvojim vyhotoveni v Praze dne 11. fijna 1977 v anglickém jazyce.", "method": "tesseract_5.3.4_eng_not_human_verified"},
    "LU": {"source_id": "SRC-D1DA8B0150E7B80D", "page": 23, "hash": "2cd3329aeba24c790698b291c9f0d5a708682a79db5d2981b92a2e76fe4b1766", "languages": ["English"], "rule": "sole_english", "excerpt": "DONE in duplicate at Brussels this 5™ day of March 2013 in the English language.", "method": "tesseract_5.3.4_eng_not_human_verified"},
    "PA": {"source_id": "SRC-82F15B2AF261EB4D", "page": 23, "hash": "31b79092e4ceff2ff389749014940544fe7ce3d02c5282a70a062663d4706376", "languages": ["Czech", "Spanish", "English"], "rule": "english_prevails_all_text_divergences", "excerpt": "Dano v Panamé dne 4. éervence 2012 ve dvou pivodnich vyhotovenich, v Ceském, Spanélském a anglickém jazyce, pritemzZ vsechny texty jsou autentické. V pripadé jakéhokoliv rozdilu bude rozhodujicim anglicky text.", "method": "tesseract_5.3.4_eng_not_human_verified"},
    "PL": {"source_id": "SRC-6449FD410AC2BC33", "page": 21, "hash": "1cc8fe31e7c5bef399d49e993791e2ddeae2f55f6c6d76eb436d4e95f0bcd9c6", "languages": ["Czech", "Polish", "English"], "rule": "english_prevails_all_text_divergences", "excerpt": "Dano ve VarSavé dne 13. zA¥i 2011 ve dvou ptivodnich vyhotovenich, v éeském, polském a anglickém jazyce, priéemz vSechny texty jsou autentické. V pripadé jakéhokoliv rozdilu bude rozhodujicim anglicky text.", "method": "tesseract_5.3.4_eng_not_human_verified"},
}


AT_CH_INSTRUMENTS = {
    "AT": {"protocol_current_sha256": "7bae18b222475981a570be470b6d5a7dee05707efa7d64e2f56420db8c79b83c", "protocol_archived_sha256": "366757d295d0d6fab635857b3be44fc5f616e0d697af42395d725cefc8e7d972", "protocol_notice_excerpt": "Protokol mezi Českou republikou a Rakouskou republikou, který upravuje Smlouvu ... podepsané dne 8. června 2006 v Praze. Protokol vstoupil v platnost na základě svého článku IV dne 26. listopadu 2012 a jeho ustanovení se budou provádět v souladu se zněním tohoto článku.", "protocol_notice_page": 1, "mli_notice_sha256": "c9819441da103851a07bc1da9a9d0544258ab1fd266fe1a712cb3db0168e3b4c"},
    "CH": {"protocol_current_sha256": "704f5deea8db74ae126781b177310a1ec94b7c0f7bef0ee6f4eabb2aa1ed4998", "protocol_archived_sha256": "a82e4b44856a2dd18723f6a3dca28e8229bd7e4193f3f2ef711cd6a1e0f5a130", "protocol_notice_excerpt": "Protokol mezi vládou České republiky a Švýcarskou spolkovou radou, který upravuje Smlouvu ... podepsané v Praze dne 4. prosince 1995. Protokol vstoupil v platnost na základě svého článku XII dne 11. října 2013 a jeho ustanovení se budou provádět v souladu se zněním tohoto článku.", "protocol_notice_page": 1, "mli_notice_sha256": "2a4aafcff0330eb2cb94fa0ca684b5e0e8ca3ca30c6f3b8f7e6f00017c0979c3"},
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build() -> dict[str, Any]:
    inventory = {row["iso2"]: row for row in load(INVENTORY)["partners"]}
    manifest = {row["source_id"]: row for row in load(MANIFEST)["sources"]}
    historic = load(AT_CH_EXISTING)["countries"]
    mli = {row["recipient_country"]: row for row in load(MLI_EFFECTS)["effects"] if row["recipient_country"] in AT_CH_INSTRUMENTS}
    language = []
    for country, case in sorted(LANGUAGE_CASES.items()):
        source = manifest[case["source_id"]]
        base = inventory[country]["base_instruments"][0]
        language.append({
            "country": country,
            "treaty_pair_id": f"CZ-{country}",
            "official_source": {"inventory_source_id": base["source_id"], "manifest_source_id": source["source_id"], "title": source["source_title"], "url": base["url"], "pdf_page": case["page"], "current_download_sha256": case["hash"], "archived_manifest_sha256": source["sha256"], "hash_relation": "current_official_bytes_bound_archived_hash_preserved"},
            "signature_clause_candidate": {"machine_transcription": case["excerpt"], "transcription_sha256": sha(case["excerpt"]), "method": case["method"]},
            "candidate_interpretation": {"authentic_languages": case["languages"], "prevailing_language_rule": case["rule"]},
            "evidence_status": "official_primary_candidate_needs_human_review", "verification_status": "needs_review", "human_primary_review_complete": False, "independent_approval_complete": False, "production_releasable": False, "fail_closed": True,
        })

    chains = []
    for country, case in sorted(AT_CH_INSTRUMENTS.items()):
        partner = inventory[country]
        protocol = next(row for row in partner["related_instruments"] if row["source_type"] == "protocol")
        correction = next(row for row in partner["related_instruments"] if row["source_type"] == "correction")
        mli_notice = next(row for row in partner["related_instruments"] if row["source_type"] == "mli_synthesised_notice")
        base = next(row for row in language if row["country"] == country)
        chain = {
            "country": country,
            "base_treaty": base["official_source"],
            "base_entry_into_force_inventory_candidate": partner["entry_into_force"],
            "correction_status_instrument": correction,
            "protocol": {"inventory": protocol, "current_official_download_sha256": case["protocol_current_sha256"], "archived_sha256": case["protocol_archived_sha256"], "hash_relation": "current_official_bytes_bound_archived_hash_preserved", "official_notice_page": case["protocol_notice_page"], "relationship_and_entry_into_force_excerpt": case["protocol_notice_excerpt"], "excerpt_sha256": sha(case["protocol_notice_excerpt"]), "effect_interpretation_status": "not_assessed_needs_human_review"},
            "mli": {"inventory": mli_notice, "current_official_notice_sha256": case["mli_notice_sha256"], "candidate_effect_record": mli[country], "matching_and_effect_interpretation_status": "candidate_only_needs_human_review"},
            "chain_status": "official_primary_instrument_chain_candidate_assembled",
            "verification_status": "needs_review", "human_primary_review_complete": False, "independent_approval_complete": False, "production_releasable": False, "fail_closed": True,
        }
        chain["candidate_sha256"] = sha(json.dumps(chain, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        chains.append(chain)
    return {"schema_version": 1, "dataset_release": "stage5-final10-source-remediation-2026-08-10.1", "purpose": "Official-primary candidate evidence closing machine-locatable language and AT/CH instrument-chain source slots without legal verification.", "safety_boundary": {"candidate_evidence_is_not_verification": True, "historic_hashes_preserved": True, "automatic_promotion_forbidden": True}, "summary": {"language_country_count": 10, "language_candidate_resolved_count": 10, "language_ambiguous_count": 0, "language_blocked_count": 0, "instrument_chain_country_count": 2, "instrument_chain_candidate_assembled_count": 2, "human_verified_count": 0, "production_releasable_count": 0}, "language_authority_entries": language, "instrument_chain_entries": chains}


def main() -> None:
    OUTPUT.write_text(json.dumps(build(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
