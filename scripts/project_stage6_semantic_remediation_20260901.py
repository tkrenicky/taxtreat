from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data/legal_consolidation/semantic_remediation_condition_candidates_20260829.json"
QUEUE = ROOT / "data/legal_reviews/global_cz_outbound/cz_country_qa_queue.json"
RULES_DIR = ROOT / "data/legal_rules_stage6"
CANDIDATE_RELEASE = "stage6-semantic-remediation-candidate-2026-09-01.1"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _runtime_condition(row: dict[str, Any]) -> dict[str, Any]:
    operator = str(row.get("operator") or "")
    operator = {"not_in": "not in"}.get(operator, operator)
    return {
        "fact": str(row["condition_type"]),
        "fact_source": "transaction",
        "operator": operator,
        "value": str(row.get("value")),
    }


def _rate_key(value: Any) -> float:
    return float(value)


def _condition_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("fact") or ""),
        str(row.get("fact_source") or "transaction"),
        str(row.get("operator") or ""),
        repr(row.get("value")),
    )


def _common_conditions(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rules:
        return []
    common = {
        _condition_key(row): dict(row)
        for row in (rules[0].get("conditions") or [])
        if isinstance(row, dict)
    }
    for rule in rules[1:]:
        keys = {
            _condition_key(row)
            for row in (rule.get("conditions") or [])
            if isinstance(row, dict)
        }
        common = {key: row for key, row in common.items() if key in keys}
    return list(common.values())


def _merge_conditions(
    common: list[dict[str, Any]],
    remediation: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    remediation_facts = {str(row.get("fact") or "") for row in remediation}
    merged = [
        dict(row)
        for row in common
        if str(row.get("fact") or "") not in remediation_facts
    ]
    merged.extend(remediation)
    return merged


def _new_branch_priority(
    scope_rules: list[dict[str, Any]],
    fallback_rule: dict[str, Any],
) -> int:
    fallback_priority = int(fallback_rule["priority"])
    used = {
        int(rule["priority"])
        for rule in scope_rules
        if isinstance(rule.get("priority"), int)
    }
    specific_priorities = [value for value in used if value < fallback_priority]
    floor = max(specific_priorities) if specific_priorities else -1
    for priority in range(fallback_priority - 1, floor, -1):
        if priority not in used:
            return priority
    raise ValueError(
        "No safe priority slot exists immediately before the fallback rule"
    )


def project_country(country: str, *, write: bool = True) -> dict[str, Any]:
    code = str(country).upper()
    registry = load(REGISTRY)
    queue = load(QUEUE)
    corrections = [
        row
        for row in registry["corrections"]
        if str(row["country"]).upper() == code
    ]
    if not corrections:
        raise ValueError(f"{code}: no semantic remediation correction registered")

    package = next(
        row for row in queue["packages"]
        if str(row["partner_country"]).upper() == code
    )
    package_hash = str(package["package_sha256"])

    path = RULES_DIR / f"{code.lower()}.json"
    payload = load(path)
    changed_rule_ids: list[str] = []

    for correction in corrections:
        income = str(correction["income_type"])
        source_id = str(correction["evidence_source_id"])
        candidates = [
            rule
            for rule in payload.get("rules", [])
            if isinstance(rule, dict)
            and str(rule.get("income_type")) == income
            and str(rule.get("source_id")) == source_id
            and str(rule.get("legal_layer")) in {"treaty", "protocol"}
            and str(rule.get("effect") or "rate") == "rate"
            and rule.get("rate") is not None
        ]
        if not candidates:
            raise ValueError(f"{code}:{income}: no source-backed Stage 6 rules found")

        common_conditions = _common_conditions(candidates)
        by_rate: dict[float, list[dict[str, Any]]] = {}
        for rule in candidates:
            by_rate.setdefault(_rate_key(rule["rate"]), []).append(rule)

        # The most general existing rule is the safest metadata template for a
        # newly materialised reduced-rate branch. It remains lower precedence
        # than all specific branches after _new_branch_priority.
        fallback_template = max(candidates, key=lambda row: int(row["priority"]))

        for branch in correction["rate_candidates"]:
            rate = _rate_key(branch["rate"])
            matches = by_rate.get(rate, [])
            if len(matches) > 1:
                raise ValueError(
                    f"{code}:{income}:{rate:g}% expected at most one projected rule, "
                    f"found {len(matches)}"
                )

            remediation_conditions = [
                _runtime_condition(condition)
                for condition in branch.get("conditions", [])
            ]
            projected_conditions = _merge_conditions(
                common_conditions,
                remediation_conditions,
            )

            if matches:
                rule = matches[0]
            else:
                rule = dict(fallback_template)
                rule["rule_id"] = (
                    f"CZ-{code}-{income.upper()}-SEMANTIC-REMEDIATION-"
                    f"{str(branch['rate']).replace('.', '_')}"
                )
                rule["rate"] = branch["rate"]
                rule["priority"] = _new_branch_priority(candidates, fallback_template)
                payload["rules"].append(rule)
                candidates.append(rule)
                by_rate.setdefault(rate, []).append(rule)

            rule["conditions"] = projected_conditions
            rule["review_package_sha256"] = package_hash
            rule["verification_status"] = "needs_review"
            rule["verification_authority"] = "semantic_remediation_machine_projection"
            rule["approval_dataset_release"] = None
            rule["approval_created_at"] = None
            rule["dataset_release"] = CANDIDATE_RELEASE
            changed_rule_ids.append(str(rule["rule_id"]))

    if write:
        dump(path, payload)

    return {
        "country": code,
        "package_sha256": package_hash,
        "changed_rule_ids": changed_rule_ids,
        "correction_count": len(corrections),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--country", required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    result = project_country(args.country, write=not args.check)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
