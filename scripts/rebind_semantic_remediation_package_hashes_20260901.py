from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/legal_reviews/global_cz_outbound"
QUEUE = BASE / "cz_country_qa_queue.json"
REGISTRY = (
    ROOT
    / "data/legal_consolidation/semantic_remediation_condition_candidates_20260829.json"
)
CANDIDATES = ROOT / "data/legal_rule_candidates/semantic_remediation_20260901"
RUNTIME = ROOT / "data/legal_rules_stage6"
MACHINE_RELEASE = BASE / "semantic_remediation_machine_release_20260901.json"
GATE = BASE / "production_source_release_gate_v2.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _rebind_rules(
    payload: dict[str, Any],
    *,
    country: str,
    incomes: set[str],
    authority: str,
    package_hash: str,
) -> int:
    changed = 0
    matched_scopes: set[str] = set()
    for rule in payload.get("rules", []):
        if (
            str(rule.get("recipient_country")).upper() != country
            or str(rule.get("income_type")) not in incomes
            or str(rule.get("verification_authority")) != authority
        ):
            continue
        matched_scopes.add(str(rule["income_type"]))
        if rule.get("review_package_sha256") != package_hash:
            rule["review_package_sha256"] = package_hash
            changed += 1
    if matched_scopes != incomes:
        missing = sorted(incomes - matched_scopes)
        raise RuntimeError(f"{country}: no {authority} rules for scopes {missing}")
    return changed


def rebind(*, check: bool = False) -> list[str]:
    queue = load(QUEUE)
    registry = load(REGISTRY)
    machine_release = load(MACHINE_RELEASE)
    gate = load(GATE)

    queue_hashes = {
        str(row["partner_country"]).upper(): str(row["package_sha256"])
        for row in queue["packages"]
    }
    scopes: dict[str, set[str]] = {}
    for row in registry["corrections"]:
        scopes.setdefault(str(row["country"]).upper(), set()).add(
            str(row["income_type"])
        )

    release_rows = {
        (str(row["partner_country"]).upper(), str(row["income_type"])): row
        for row in machine_release["records"]
    }
    gate_rows = {
        str(row["partner_country"]).upper(): row
        for row in gate["treaty_partners"]
    }
    changed_paths: list[str] = []

    for country, incomes in sorted(scopes.items()):
        package_hash = queue_hashes[country]
        candidate_path = CANDIDATES / f"{country.lower()}.json"
        runtime_path = RUNTIME / f"{country.lower()}.json"
        candidate = load(candidate_path)
        runtime = load(runtime_path)
        country_changed = False

        stage6 = candidate.get("stage6_production") or {}
        if stage6.get("package_sha256") != package_hash:
            stage6["package_sha256"] = package_hash
            candidate["stage6_production"] = stage6
            country_changed = True
        country_changed |= bool(
            _rebind_rules(
                candidate,
                country=country,
                incomes=incomes,
                authority="semantic_remediation_machine_projection",
                package_hash=package_hash,
            )
        )
        runtime_changed = bool(
            _rebind_rules(
                runtime,
                country=country,
                incomes=incomes,
                authority="semantic_remediation_machine_validation",
                package_hash=package_hash,
            )
        )

        for income in incomes:
            release_row = release_rows[(country, income)]
            if release_row.get("package_sha256") != package_hash:
                release_row["package_sha256"] = package_hash
                if str(MACHINE_RELEASE.relative_to(ROOT)) not in changed_paths:
                    changed_paths.append(str(MACHINE_RELEASE.relative_to(ROOT)))

        gate_row = gate_rows[country]
        machine_event = gate_row["release_evidence"][
            "semantic_remediation_machine_release"
        ]
        if machine_event.get("package_sha256") != package_hash:
            machine_event["package_sha256"] = package_hash
            if str(GATE.relative_to(ROOT)) not in changed_paths:
                changed_paths.append(str(GATE.relative_to(ROOT)))

        if country_changed:
            changed_paths.append(str(candidate_path.relative_to(ROOT)))
            if not check:
                dump(candidate_path, candidate)
        if runtime_changed:
            changed_paths.append(str(runtime_path.relative_to(ROOT)))
            if not check:
                dump(runtime_path, runtime)

    if changed_paths and check:
        raise RuntimeError(
            "Stale semantic-remediation package hashes: "
            + ", ".join(sorted(changed_paths))
        )
    if changed_paths:
        dump(MACHINE_RELEASE, machine_release)
        dump(GATE, gate)
    return sorted(set(changed_paths))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    changed = rebind(check=args.check)
    print(
        "Semantic-remediation package hashes: "
        + (f"rebound {len(changed)} files" if changed else "PASS")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
