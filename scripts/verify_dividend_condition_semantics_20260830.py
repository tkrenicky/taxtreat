from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "data" / "legal_rules_stage6"

VOTING_MARKERS = (
    "hlasovac",
    "voting",
)
DIRECT_MARKERS = (
    "přímo",
    "primo",
    "directly",
    "direct ",
)
COMPANY_MARKERS = (
    "příjemce je společnost",
    "prijemce je spolecnost",
    "skutečným vlastníkem je společnost",
    "skutecnym vlastnikem je spolecnost",
    "beneficial owner is a company",
    "recipient is a company",
)

VOTING_FACTS = {
    "voting_ownership",
    "voting_power_control",
    "direct_or_indirect_voting_ownership",
}


def _facts(rule: dict) -> set[str]:
    return {str(c.get("fact") or "") for c in rule.get("conditions", [])}


def _normalized_source(rule: dict) -> str:
    text = str(rule.get("source_text") or "").lower()
    return re.sub(r"\s+", " ", text)


def main() -> int:
    failures: list[str] = []

    for path in sorted(RULE_DIR.glob("*.json")):
        package = json.loads(path.read_text(encoding="utf-8"))
        country = package.get("country_pair", {}).get("recipient_country")

        for rule in package.get("rules", []):
            if rule.get("legal_layer") not in {"treaty", "protocol", "mli"}:
                continue
            if rule.get("effect") != "rate" or rule.get("income_type") != "dividend":
                continue

            facts = _facts(rule)
            source = _normalized_source(rule)

            if "ownership_percent" not in facts and not (facts & VOTING_FACTS):
                continue

            source_mentions_voting = any(marker in source for marker in VOTING_MARKERS)
            source_mentions_direct = any(marker in source for marker in DIRECT_MARKERS)
            source_mentions_company = any(marker in source for marker in COMPANY_MARKERS)

            if source_mentions_voting and not (facts & VOTING_FACTS):
                failures.append(
                    f"{country} {rule.get('rule_id')}: source text uses voting rights/power "
                    "but rule has no voting-specific fact"
                )

            if source_mentions_direct and "direct_ownership" not in facts and (
                "ownership_percent" in facts or "voting_ownership" in facts
            ):
                # direct_or_indirect_voting_ownership is deliberately not accepted here:
                # a treaty branch that explicitly requires direct ownership must not be
                # satisfied by an indirect voting-rights aggregate.
                failures.append(
                    f"{country} {rule.get('rule_id')}: source text expressly requires direct "
                    "ownership but rule has no direct_ownership condition"
                )

            if source_mentions_company and "recipient_entity_type" not in facts:
                failures.append(
                    f"{country} {rule.get('rule_id')}: source text limits the reduced dividend "
                    "branch to a company but rule has no recipient_entity_type condition"
                )

    if failures:
        raise AssertionError(
            "Dividend condition semantic failures:\n" + "\n".join(sorted(set(failures)))
        )

    print("Dividend condition semantics: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
