from __future__ import annotations

import json
from pathlib import Path

from taxtreat.engine.legal_rule_engine import _royalty_category_groups

ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "data" / "legal_rules_stage6"

UI_CATEGORIES = {
    "copyright_literary_artistic_scientific_nonfilm_nonsoftware",
    "cinematographic_films_or_broadcast_media",
    "computer_software",
    "patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
    "financial_lease_of_equipment",
    "operating_lease_or_other_use_of_equipment",
    "other",
}


def main() -> int:
    failures: list[str] = []
    treaty_values: set[str] = set()

    for ui_value in sorted(UI_CATEGORIES):
        groups = _royalty_category_groups(ui_value)
        if not groups:
            failures.append(f"UI royalty category {ui_value!r} maps to no atomic group")

    for path in sorted(RULE_DIR.glob("*.json")):
        package = json.loads(path.read_text(encoding="utf-8"))
        country = package.get("country_pair", {}).get("recipient_country")

        for rule in package.get("rules", []):
            if rule.get("legal_layer") not in {"treaty", "protocol", "mli"}:
                continue
            if rule.get("effect") != "rate" or rule.get("income_type") != "royalty":
                continue

            for condition in rule.get("conditions", []):
                if condition.get("fact") != "royalty_category":
                    continue
                if condition.get("operator") not in {"==", "!="}:
                    continue

                value = str(condition.get("value") or "").strip()
                treaty_values.add(value)
                groups = _royalty_category_groups(value)

                if not groups:
                    failures.append(
                        f"{country} {rule.get('rule_id')}: royalty_category={value!r} "
                        "maps to no atomic royalty group"
                    )

    if failures:
        raise AssertionError(
            "Royalty taxonomy coverage failures:\n" + "\n".join(sorted(set(failures)))
        )

    print(
        "Royalty taxonomy coverage: PASS "
        f"({len(UI_CATEGORIES)} UI categories; {len(treaty_values)} treaty category values)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
