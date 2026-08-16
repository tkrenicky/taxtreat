from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RULES_DIR = ROOT / "data" / "legal_rules_stage6"
CANONICAL_PATH = ROOT / "data" / "legal_texts" / "verified_provisions.json"
OUTPUT_PATH = ROOT / "reports" / "treaty_verbatim_registry.json"

EXPECTED_PROVISIONS = 302
EXPECTED_SOURCE_INSTRUMENTS = 101

SUSPECT_PATTERNS = (
    re.compile(r"\ufffd"),
    re.compile(r"\brozdili\b", re.IGNORECASE),
    re.compile(r"\bvyplacejici\b", re.IGNORECASE),
)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_records() -> dict[str, dict[str, Any]]:
    if not CANONICAL_PATH.exists():
        return {}
    payload = _load_json(CANONICAL_PATH)
    if not isinstance(payload, dict):
        raise ValueError("verified_provisions.json must contain an object")
    return payload


def _is_fully_verified(record: dict[str, Any]) -> bool:
    text = str(record.get("text") or "")
    expected_hash = record.get("verified_text_sha256")
    return bool(
        text
        and record.get("verification_status")
        == "verified_against_authoritative_pdf"
        and record.get("official_pdf_sha256")
        and expected_hash
        and expected_hash == _sha256_text(text)
    )


def build_registry() -> dict[str, Any]:
    canonical = _canonical_records()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    treaty_rule_records = 0
    for path in sorted(RULES_DIR.glob("*.json")):
        package = _load_json(path)
        for rule in package.get("rules", []):
            if rule.get("legal_layer") != "treaty":
                continue
            article = rule.get("article")
            source_url = rule.get("source_url")
            recipient = str(rule.get("recipient_country") or "").upper()
            if not recipient or article is None or not source_url:
                raise ValueError(f"Incomplete treaty citation in {path}: {rule.get('rule_id')}")
            treaty_rule_records += 1
            key = f"CZ-{recipient}|treaty|{article}"
            grouped[key].append(rule)

    provisions: list[dict[str, Any]] = []
    source_urls: set[str] = set()

    for key, rules in sorted(grouped.items()):
        source_urls_for_key = {str(rule["source_url"]) for rule in rules}
        source_ids = {str(rule.get("source_id") or "") for rule in rules}
        articles = {str(rule["article"]) for rule in rules}
        approved_hashes = {
            str(rule.get("approved_article_text_sha256") or "")
            for rule in rules
            if rule.get("approved_article_text_sha256")
        }
        if len(source_urls_for_key) != 1 or len(articles) != 1:
            raise ValueError(f"Conflicting source identity for {key}")
        if len(approved_hashes) > 1:
            raise ValueError(f"Conflicting approved article hashes for {key}")

        source_url = next(iter(source_urls_for_key))
        source_urls.add(source_url)
        raw_texts = [str(rule.get("source_text") or "") for rule in rules]
        representative_text = max(raw_texts, key=len, default="")
        suspect = sorted(
            {
                pattern.pattern
                for text in raw_texts
                for pattern in SUSPECT_PATTERNS
                if pattern.search(text)
            }
        )

        canonical_record = canonical.get(key) or {}
        canonical_text = str(canonical_record.get("text") or "")
        fully_verified = _is_fully_verified(canonical_record)
        if fully_verified:
            status = "verified_against_authoritative_pdf"
        elif canonical_text:
            status = "canonical_text_requires_pdf_provenance"
        else:
            status = "pending_authoritative_pdf_verification"

        first = rules[0]
        provisions.append(
            {
                "key": key,
                "recipient_country": first["recipient_country"],
                "article": first["article"],
                "income_types": sorted({str(rule["income_type"]) for rule in rules}),
                "rule_ids": sorted({str(rule["rule_id"]) for rule in rules}),
                "source_id": sorted(source_ids)[0] if source_ids else None,
                "source_url": source_url,
                "approved_article_text_sha256": (
                    sorted(approved_hashes)[0] if approved_hashes else None
                ),
                "stage6_source_text_sha256": (
                    _sha256_text(representative_text) if representative_text else None
                ),
                "stage6_source_text_suspect_patterns": suspect,
                "canonical_text_present": bool(canonical_text),
                "canonical_text_sha256": (
                    _sha256_text(canonical_text) if canonical_text else None
                ),
                "official_pdf_sha256": canonical_record.get("official_pdf_sha256"),
                "verification_method": canonical_record.get("verification_method"),
                "verification_status": status,
            }
        )

    verified = sum(
        item["verification_status"] == "verified_against_authoritative_pdf"
        for item in provisions
    )
    suspect = sum(bool(item["stage6_source_text_suspect_patterns"]) for item in provisions)
    canonical_present = sum(item["canonical_text_present"] for item in provisions)

    result = {
        "schema_version": 1,
        "purpose": (
            "Fail-closed inventory of every treaty article that can be emitted by "
            "the Czech outbound Stage 6 runtime. Governance approval of a rule is "
            "not treated as proof that its displayed article text is verbatim."
        ),
        "counts": {
            "treaty_rule_records": treaty_rule_records,
            "unique_used_treaty_provisions": len(provisions),
            "unique_official_source_instruments": len(source_urls),
            "canonical_text_present": canonical_present,
            "verified_against_authoritative_pdf": verified,
            "pending_or_provenance_incomplete": len(provisions) - verified,
            "stage6_text_with_known_suspect_pattern": suspect,
        },
        "release_gate": {
            "expected_provisions": EXPECTED_PROVISIONS,
            "expected_source_instruments": EXPECTED_SOURCE_INSTRUMENTS,
            "complete": (
                len(provisions) == EXPECTED_PROVISIONS
                and len(source_urls) == EXPECTED_SOURCE_INSTRUMENTS
                and verified == EXPECTED_PROVISIONS
            ),
        },
        "provisions": provisions,
    }
    return result


def main() -> None:
    result = build_registry()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    counts = result["counts"]
    print(
        "Treaty verbatim registry: "
        f"{counts['verified_against_authoritative_pdf']}/"
        f"{counts['unique_used_treaty_provisions']} fully verified; "
        f"{counts['unique_official_source_instruments']} official instruments."
    )
    if result["release_gate"]["complete"]:
        print("VERBATIM RELEASE GATE: PASS")
    else:
        print("VERBATIM RELEASE GATE: FAIL-CLOSED")


if __name__ == "__main__":
    main()
