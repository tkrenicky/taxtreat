from __future__ import annotations

import json
from pathlib import Path

from taxtreat.engine.legal_rule_engine import _royalty_category_groups

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    failures: list[str] = []

    expected = {
        "all_other_article_12_royalties": {
            "film_broadcast",
            "software",
            "industrial_ip",
            "equipment_financial",
            "equipment_operating",
            "other",
        },
        "all_royalties_except_industrial_commercial_scientific_equipment": {
            "copyright_nonfilm",
            "film_broadcast",
            "software",
            "industrial_ip",
            "other",
        },
        # This legacy browser value is deliberately fail-closed to non-film
        # copyright only. Film/broadcast has its own atomic UI category.
        "copyright_literary_artistic_or_scientific": {"copyright_nonfilm"},
        "industrial_commercial_scientific_equipment": {
            "equipment_financial",
            "equipment_operating",
        },
    }

    for value, groups in expected.items():
        actual = _royalty_category_groups(value)
        if actual != groups:
            failures.append(f"{value}: expected {sorted(groups)}, got {sorted(actual)}")

    tw = json.loads((ROOT / "data" / "legal_rules_stage6" / "tw.json").read_text(encoding="utf-8"))
    tw_rule = next(r for r in tw["rules"] if r["rule_id"] == "CZ-TW-ROYALTY-CURRENT-2")
    tw_category = next(c["value"] for c in tw_rule["conditions"] if c["fact"] == "royalty_category")
    if tw_category != "all_royalties_except_industrial_commercial_scientific_equipment":
        failures.append("TW 10% royalty branch must explicitly exclude equipment")

    if failures:
        raise AssertionError("Royalty mapping regression failures:\n" + "\n".join(failures))

    print("Royalty mapping regressions: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
