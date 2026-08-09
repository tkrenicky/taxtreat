from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_stage5_remaining80_batch01_intake import resolve_source_manifest_row  # noqa: E402
BASE = ROOT / "data/legal_reviews/global_cz_outbound"
INVENTORY = ROOT / "data/legal_consolidation/mf_inventory.json"
MANIFEST = ROOT / "data/manifests/source_manifest.json"
OUTPUT = BASE / "stage5_language_authority_remediation.json"


# These are transcriptions of the identified signature clauses in the cited current
# official Collection PDFs.  They remain machine evidence and are never legal review.
CASES: dict[str, dict[str, Any]] = {
    "GR": {"page": 30, "hash": "048e09d7b8de0968c00247786189b7b51d3ee71b3d0c6565bac9f4969732615f", "languages": ["English"], "rule": "sole_english", "excerpt": "Dano ve dvojim vyhotoveni v Athénéch dne 23, Fijna 1986 v anglickém jazyce.", "former": "source_hash_conflict"},
    "NL": {"page": 9, "hash": "840a0f370477b4129ba5f52c8335adcb5d9a5895d106ff2e6406b90f6b634151", "languages": ["Czech", "Dutch", "English"], "rule": "english_prevails_czech_dutch_divergence", "excerpt": "Dano v Praze dne 4, brezna 1974 ve dvou slejnopisech, Kazdy v cCeském, nizozemském a anglickém jazyce, pfi€emz vSechna tH znéni majf stejnon platnost. Dojde-li k odligsnému vkladu Ceského a nizozemskéhto textu, bude rozhodujic! text anglicky.", "former": "source_hash_conflict"},
    "FI": {"page": 20, "hash": "f569ce5416d296d70834e03e6d202eee66303033b29310446d8ce8c6c3f4034e", "languages": ["English"], "rule": "sole_english", "excerpt": "Dano ve dvojim vyhotoveni v Praze dne 2. prosince 1994 v anglickém jazyce.", "former": "ambiguous_multiple_candidates"},
    "HU": {"page": 22, "hash": "b56fdab54bb69c0ec6209714f59c041d7dd584293ebac5bd60f3ca1d68d823da", "languages": ["English"], "rule": "sole_english", "excerpt": "Dano ve dvojim vyhotovenf v Praze dne 14. ledna 1993 v anglickém jazyce.", "former": "ambiguous_multiple_candidates"},
    "IT": {"page": 10, "hash": "3456c81327d3f7ab7f5ddefc5b9010d69c7f31e90e23e098c5ec1f1f7d21cc64", "languages": ["Czech", "Italian", "French"], "rule": "french_prevails_in_dispute", "excerpt": "Dano v Praze dne 5. kvétna 1981 ve dvou vyhotovenich, kazdé v jazyce teském, italském a francouzském, pritemz vyhotovent v jazyce francouzskéi bude rozhodujici v piipad’ sporu.", "former": "ambiguous_multiple_candidates"},
    "SG": {"page": 16, "hash": "5bdb2d4412907a927d8357c10ce72f991c7aa903b50f1606133a2fe3336c75a8", "languages": ["English"], "rule": "sole_english", "excerpt": "Dano v Singapuru dne 21. listopadu 1997 ve dvou pivodnich vyhotovenich v anglickém jazyce.", "former": "ambiguous_multiple_candidates"},
    "UZ": {"page": 76, "hash": "01716bbfb5bf29becfcc64cdc913a9139827968f086797923acccbb80fa9a11c", "languages": ["Czech", "Uzbek", "English"], "rule": "english_prevails_all_text_divergences", "excerpt": "Dáno v Praze dne 2. brezna roku 2000 ve dvou puvodnõch vyhotovenõch, kazdé v jazyce ceském, uzbeckém a anglickém, pricemz vsechny texty jsou autentické. V prõpade jakéhokoliv rozdõlu bude rozhodujõcõm anglický text.", "former": "ambiguous_multiple_candidates"},
    "BD": {"page": 25, "hash": "17b339e9f63735f98507beec07041888755cfe30d089468e299dba16f64a70f5", "languages": ["English"], "rule": "sole_english", "excerpt": "DONE in duplicate at Prague this an day of December 2019 in the English language.", "former": "unresolved"},
    "CN": {"page": 22, "hash": "f793ea9c9dea9ecd4cba8fc6b052449386fc1f2e82b69fe31b9e2571e0ee4c1c", "languages": ["Czech", "Chinese", "English"], "rule": "english_prevails_interpretive_divergence", "excerpt": "Dano v Pekingu dne 28. srpna 2009 ve dvou pivodnich vyhotovenich, kazdé v jazyce eském, cinském a anglickém, prigem% vSechny texty jsou autentické. V pripadé jakéhokoliv rozdilu ve vykladu bude rozhodujicim anglicky text.", "former": "unresolved"},
    "DK": {"page": 24, "hash": "44c30a11a9349f030d2e2196179b9da2b436b1d6d686a25529928dd03d48eda7", "languages": ["English"], "rule": "sole_english", "excerpt": "Done in duplicate at Prague this 25\" day of August 2011, in the English language.", "former": "unresolved"},
    "ES": {"page": 14, "hash": "580a7fffb9d58d866912471986c5fe52559fd6b76377634d5ee356e187668730", "languages": ["Czech", "Spanish"], "rule": "equal_authority", "excerpt": "Déno ve dvojim vytiotovent v Madrid dne 8. kvétna 1980 v Ceském a Spanélském jazyku, piiGemz ob& znSai maji stejnou platnost.", "former": "unresolved"},
    "IR": {"page": 23, "hash": "cb9e073717d6c043d31aa57291f0f05d86e114c8e22edfc27dcd6f034877bd0d", "languages": ["Czech", "Persian", "English"], "rule": "english_prevails_czech_persian_divergence", "excerpt": "Dano v Praze dne 30. dubna 2015, coz odpovida 1394/02/10 Solar Hijra, ve dvou plivodnich vyhotevenich, v Seském, perském a anglickém jazyce, pritemzZ vSechny texty jsou autentické. V p¥ipadé jakéhokoliv rozdilu mezi teskym a perskym textem bude rozhodujicim anglicky text.", "former": "unresolved"},
    "JO": {"page": 22, "hash": "ac9ed3260d96902b71b59b163bc5ef486d2b54edd39f9c1a4d71d36a17729000", "languages": ["Czech", "Arabic", "English"], "rule": "english_prevails_all_text_divergences", "excerpt": "Dano v wee AMMANU dne dulce 2006 ve dvou ptivodnich vyhotovenich, kazdé v jazyce éeském, arabském a anglickém. VSechny texty jsou autentické. V pripadé jakéhokoliv rozdilu bude rozhodujicim anglicky text.", "former": "unresolved"},
    "KG": {"page": 35, "hash": "24434a1249142b46b2d30a8e0b27173aef4852b70b5adab1c243208b503351b7", "languages": ["Czech", "Kyrgyz", "Russian", "English"], "rule": "english_prevails_all_text_divergences", "excerpt": "DONE in duplicate at Bishkek this 9 day of April 2019, in the Czech, Kyrgyz, Russian and English languages, all texts being equally authentic. In the case of any divergence, the English text shall prevail.", "former": "unresolved"},
    "LI": {"page": 22, "hash": "ec1b0e07f2fbbc2d02c02098663871400e42eea75fca3bcf4afb449f229a92bd", "languages": ["English"], "rule": "sole_english", "excerpt": "DONE in duplicate at Prague this 25\" day of September 2014 in the English language.", "former": "unresolved"},
    "PK": {"page": 25, "hash": "646751f8e2cfae01054ca23f502e67f5a7163e413d5959e897633bdde0d89ec8", "languages": ["English"], "rule": "sole_english", "excerpt": "DONE in duplicate at Prague this 2\" day of May 2014 in the English language.", "former": "unresolved"},
    "SA": {"page": 23, "hash": "d2dfb6e98cb30f4252b9f9eaf8d82f03e48ed6fb9a19d64fbd68940d551d4a4f", "languages": ["Czech", "Arabic", "English"], "rule": "english_prevails_all_text_divergences", "excerpt": "Dano v Praze dne 25. dubna 2012 ve dvou piivodnich yyhotovenich, v €eském, arabském a anglickém jazyce, prigemz vSechny texty jsou autentické. V pripadé jakéhokoliv rozdilu bude rozhodujicim anglicky text.", "former": "unresolved"},
    "SE": {"page": 11, "hash": "9ae779b7181557636297287002324bc5659fcfb772976336b8e78dee19effdc5", "languages": ["English"], "rule": "sole_english", "excerpt": "Dano v Prave dne 38. inora 1979 ve dvojim vyhotoven’, v anghckem jaayka.", "former": "unresolved"},
    "SM": {"page": 24, "hash": "d76afd391e4a8506796c283cefd7cc1ac70c856cb8be8009b90e91ccc6a9f985", "languages": ["English"], "rule": "sole_english", "excerpt": "DONE in duplicate at Rome this 27\" day of January 2021 in the English language.", "former": "unresolved"},
    "SN": {"page": 22, "hash": "aa0b3da5a8f5dde6d976e95890e6afbcb0d9c7e377a660fb29a94e07e4dcd085", "languages": ["Czech", "French", "English"], "rule": "english_prevails_all_text_divergences", "excerpt": "Dano v Dakaru dne 22. ledna 2020 ve dvou piivodnich vyhotovenich, kazZdé v jazyce éeském, francouzském a anglickém, pritemz vSechny tii texty jsou autentické. V pripadé jakéhokoliv rozdilu bude rozhodujicim anglicky text.", "former": "unresolved"},
    "TJ": {"page": 65, "hash": "ac9ed3260d96902b71b59b163bc5ef486d2b54edd39f9c1a4d71d36a17729000", "languages": ["Czech", "Tajik", "Russian", "English"], "rule": "english_prevails_all_text_divergences", "excerpt": "Dano v DuSanbe dne 7. listopadu 2006 ve dvou pivodnich vyhotovenich, kazdé v jazyce éeském, tadZickém, ruském a anglickém, pritemZ vSechny texty jsou autentické. V p¥ipadé jakéhokoliv rozdilu mezi texty bude rozhodujicim anglicky text.", "former": "unresolved"},
    "TM": {"page": 24, "hash": "4f9321b6b39052ddd395ce84989ae57a55618e553c0f72d5b3b8d7147fd0c60b", "languages": ["Czech", "Turkmen", "English"], "rule": "english_prevails_all_text_divergences", "excerpt": "Dano v ASchabadu dne 18. b¥ezna 2016 ve dvou pivodnich vyhotovenich, kazdé v jazyce éeském, turkmenském a anglickém, pritemz vsechny texty jsou autentické. V pripadé jakéhokoliv rozdilu mezi texty bude rozhodujicim anglicky text.", "former": "unresolved"},
    "XK": {"page": 25, "hash": "b8005bc12c060290c3cf3800c5d6f883f4db21fe5c0eeacc671349fffca1cb87", "languages": ["English"], "rule": "sole_english", "excerpt": "DONE in duplicate at Pristina this 26 day of November 2013 in the English language.", "former": "unresolved"},
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build() -> dict[str, Any]:
    partners = {row["iso2"]: row for row in load(INVENTORY)["partners"]}
    sources = load(MANIFEST)["sources"]
    rows = []
    for country, case in sorted(CASES.items()):
        partner = partners[country]
        base = partner["base_instruments"][0]
        source, _ = resolve_source_manifest_row(partner, sources)
        rows.append({
            "country": country,
            "treaty_pair_id": f"CZ-{country}",
            "former_gap_class": case["former"],
            "remediation_status": "official_signature_clause_located_candidate_only",
            "instrument_identity": {"inventory_source_id": base["source_id"], "label": base["label"], "manifest_source_id": source["source_id"]},
            "official_source": {"url": base["url"], "current_download_sha256": case["hash"], "archived_manifest_sha256": source["sha256"], "hash_relation": "matches_archived_manifest" if case["hash"] == source["sha256"] else "current_official_bytes_differ_from_archived_manifest_preserved", "pdf_page": case["page"]},
            "signature_clause_candidate": {"machine_transcription": case["excerpt"], "transcription_sha256": sha256_text(case["excerpt"]), "method": "tesseract_5.3.4_eng_or_hash_bound_repository_parse_not_human_verified"},
            "candidate_interpretation": {"authentic_languages": case["languages"], "prevailing_language_rule": case["rule"]},
            "verification_status": "needs_review",
            "human_primary_review_complete": False,
            "independent_approval_complete": False,
            "production_releasable": False,
            "fail_closed": True,
        })
    former = {kind: sum(r["former_gap_class"] == kind for r in rows) for kind in ("source_hash_conflict", "ambiguous_multiple_candidates", "unresolved")}
    return {"schema_version": 1, "dataset_release": "stage5-language-authority-remediation-2026-08-09.1", "purpose": "Official-source signature-clause candidates that remediate machine-locatable evidence gaps without performing legal verification.", "safety_boundary": {"machine_transcription_is_candidate_evidence_only": True, "historic_manifest_hashes_are_preserved": True, "automatic_verification_forbidden": True}, "summary": {"country_count": len(rows), "resolved_candidate_evidence_count": len(rows), "ambiguous_count": 0, "blocked_count": 0, "former_gap_counts": former, "current_official_hash_differs_from_archived_manifest_count": sum(r["official_source"]["hash_relation"] != "matches_archived_manifest" for r in rows)}, "entries": rows}


def main() -> None:
    OUTPUT.write_text(json.dumps(build(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
