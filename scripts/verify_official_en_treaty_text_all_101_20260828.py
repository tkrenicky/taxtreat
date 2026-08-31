from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTNERS = ROOT / "data" / "cz_treaty_partners.json"
LOCALE_DIR = ROOT / "app" / "web" / "treaty-excerpt-locales"

PUBLIC_OFFICIAL = {
    "official_treaty_text",
    "official_protocol_text",
    "official_translation_non_authentic",
    "current_application_suspended",
}


def status_for_country(country: str) -> tuple[int, int, list[str]]:
    path = LOCALE_DIR / f"{country}.json"
    if not path.is_file():
        return 0, 0, ["missing locale file"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    total = 0
    official = 0
    problems: list[str] = []
    for rule_id, item in (payload.get("rules") or {}).items():
        article = str((item or {}).get("article") or "")
        en = (item or {}).get("en") or {}
        if not article or not en:
            continue
        total += 1
        status = str(en.get("status") or "")
        if status in PUBLIC_OFFICIAL and en.get("text"):
            official += 1
        else:
            problems.append(f"{rule_id}: {status or 'missing'}")
    for article, item in (payload.get("articles") or {}).items():
        en = (item or {}).get("en") or {}
        if not en:
            continue
        total += 1
        status = str(en.get("status") or "")
        if status in PUBLIC_OFFICIAL and en.get("text"):
            official += 1
        else:
            problems.append(f"Article {article}: {status or 'missing'}")
    return total, official, problems


def main() -> int:
    partners = json.loads(PARTNERS.read_text(encoding="utf-8"))
    countries = [str(item["iso2"]).upper() for item in partners] + ["TW"]
    rows = []
    incomplete = []
    for country in countries:
        total, official, problems = status_for_country(country)
        rows.append((country, total, official))
        if total == 0 or official < total:
            incomplete.append((country, total, official, problems))

    print(f"Official-English jurisdiction coverage: {len(countries) - len(incomplete)}/{len(countries)}")
    for country, total, official, problems in incomplete:
        print(f"{country}: official {official}/{total}; " + "; ".join(problems[:8]))
    if incomplete:
        raise AssertionError(
            f"Official English treaty text is incomplete for {len(incomplete)} of {len(countries)} jurisdictions"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
