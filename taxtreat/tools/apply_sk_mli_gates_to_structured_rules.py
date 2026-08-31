from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data/legal_reviews/sk_outbound"
RULE_DIR = ROOT / "data/legal_rules_sk"
MLI = BASE / "mli_bilateral_adjudication_2026.json"

ARTICLE_GATES = {
    "3": (
        "mli_article_3_transparent_entity_entitlement_passed",
        "MLI Article 3 transparent-entity entitlement",
    ),
    "4": (
        "mli_article_4_dual_resident_entitlement_passed",
        "MLI Article 4 dual-resident entity entitlement",
    ),
    "7": (
        "treaty_ppt_passed",
        "MLI Article 7 principal purpose test",
    ),
    "10": (
        "mli_article_10_third_jurisdiction_pe_test_passed",
        "MLI Article 10 third-jurisdiction PE anti-abuse test",
    ),
    "12": (
        "mli_article_12_dependent_agent_pe_status_resolved",
        "MLI Article 12 dependent-agent PE modification",
    ),
    "13": (
        "mli_article_13_specific_activity_pe_status_resolved",
        "MLI Article 13 specific-activity PE modification",
    ),
    "14": (
        "mli_article_14_contract_splitting_pe_status_resolved",
        "MLI Article 14 contract-splitting PE modification",
    ),
    "15": (
        "mli_article_15_closely_related_enterprise_status_resolved",
        "MLI Article 15 closely-related-enterprise definition",
    ),
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def notice_url(notice: str) -> str:
    number, year = notice.split("/", 1)
    return f"https://static.slov-lex.sk/static/SK/ZZ/{year}/{number}/vyhlasene_znenie.html"


def main() -> int:
    mli = load(MLI)
    rel_by_country = {
        row["recipient_country"]: row
        for row in mli["relationships"]
    }
    assert len(rel_by_country) == 46
    assert mli["status"] == "ADJUDICATED"
    assert mli["relationship_count"] == 46

    gate_count = 0
    gated_scopes = set()
    for path in sorted(RULE_DIR.glob("*.json")):
        payload = load(path)
        country = payload["country_pair"]["recipient_country"]
        relationship = rel_by_country.get(country)
        base_rules = [
            row for row in payload["rules"]
            if row.get("legal_layer") == "treaty" and row.get("effect") == "rate"
        ]

        # Rebuild gates deterministically.
        payload["rules"] = [
            row for row in payload["rules"]
            if not str(row.get("rule_id", "")).startswith(f"SK-{country}-MLI-GATE-")
        ]

        if relationship is None:
            path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            continue

        effective_dates = relationship.get("wht_effective_dates") or []
        if not effective_dates:
            raise RuntimeError(f"{country}: MLI relationship has no WHT effective date")
        effective_from = min(effective_dates)
        result_articles = {
            str(value) for value in relationship.get("result_changing_articles", [])
        }
        notice = relationship["slovak_notice"]
        source_url = notice_url(notice)
        source_text = (
            f"Slovak bilateral MLI adjudication for SK-{country}: notice {notice}; "
            f"result-changing articles {sorted(result_articles)}; "
            f"WHT effective date(s) {effective_dates}."
        )
        source_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()

        for treaty_rule in base_rules:
            income = treaty_rule["income_type"]
            for article in sorted(result_articles, key=lambda x: int(x)):
                if article == "8":
                    # Article 8 modifies qualifying dividend ownership branches.
                    # Those branches are deliberately excluded from Stage 1 simple rules.
                    continue
                gate_spec = ARTICLE_GATES.get(article)
                if gate_spec is None:
                    continue
                fact, label = gate_spec
                rule = {
                    "rule_id": f"SK-{country}-MLI-GATE-{income.upper()}-A{article}",
                    "income_type": income,
                    "source_country": "SK",
                    "recipient_country": country,
                    "legal_instrument": "mli",
                    "legal_layer": "mli",
                    "article": article,
                    "paragraph": None,
                    "rate": None,
                    "priority": 50 + int(article),
                    "conditions": [{
                        "fact": fact,
                        "fact_source": "determination",
                        "operator": "==",
                        "value": True,
                    }],
                    "effect": "eligibility_gate",
                    "applies_to_layers": ["treaty", "protocol", "mli"],
                    "effective_from": effective_from,
                    "verification_status": "verified",
                    "source_text": source_text + f" Gate: {label}.",
                    "source_id": f"SK-MLI-{notice.replace('/', '-')}",
                    "source_url": source_url,
                    "source_excerpt_hash": hashlib.sha256(
                        (source_text + f" Gate: {label}.").encode("utf-8")
                    ).hexdigest(),
                    "verification_authority": "sk_mli_bilateral_adjudication_and_reconfirmation",
                    "reviewer_id": "sk_mli_final_reconfirmation",
                    "reviewed_at": "2026-08-21",
                    "approved_by": "mli_bilateral_adjudication_2026",
                    "approved_at": "2026-08-21",
                    "approval_dataset_release": mli["dataset_release"],
                    "approval_created_at": "2026-08-21",
                    "dataset_release": treaty_rule["dataset_release"],
                    "evidence_source_ids": [f"SK-MLI-{notice.replace('/', '-')}"],
                }
                payload["rules"].append(rule)
                gate_count += 1
                gated_scopes.add((country, income))

        payload["rules"].sort(
            key=lambda row: (
                row["income_type"],
                0 if row["effect"] == "eligibility_gate" else 1,
                row["priority"],
                row["rule_id"],
            )
        )
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    print(f"SK MLI gates materialized: {gate_count}")
    print(f"gated Stage 1 scopes: {len(gated_scopes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
