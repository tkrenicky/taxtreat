from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "app" / "web"
BOOTSTRAP = WEB / "workspace-report-export.js"
LOCALE_RENDERER = WEB / "workspace-treaty-excerpt-locales-20260824.js"
LOCALE_DIR = WEB / "treaty-excerpt-locales"

NON_AUTHENTIC_OR_SPECIAL = {
    "official_translation_non_authentic",
    "official_synthesised_text",
    "official_synthesised_excerpt",
    "machine_translation_from_official_text",
    "verified_stage6_rule_summary",
    "current_application_suspended",
}


def bootstrap_assets() -> list[str]:
    source = BOOTSTRAP.read_text(encoding="utf-8")
    return re.findall(r'"/ui-assets/([^"?]+\.js)(?:\?[^"]*)?"', source)


def verify_assets_exist() -> None:
    missing = [name for name in bootstrap_assets() if not (WEB / name).is_file()]
    if missing:
        raise AssertionError(f"Missing bootstrap assets: {missing}")


def locale_statuses() -> set[str]:
    statuses: set[str] = set()
    for path in sorted(LOCALE_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for section in ("articles", "rules"):
            for item in (payload.get(section) or {}).values():
                en = item.get("en") if isinstance(item, dict) else None
                status = en.get("status") if isinstance(en, dict) else None
                if status:
                    statuses.add(str(status))
    return statuses


def verify_visible_status_mapping() -> None:
    renderer = LOCALE_RENDERER.read_text(encoding="utf-8")
    present = locale_statuses()
    required = present.intersection(NON_AUTHENTIC_OR_SPECIAL)
    missing = sorted(status for status in required if f"{status}:" not in renderer)
    if missing:
        raise AssertionError(f"Treaty statuses without visible UI mapping: {missing}")
    if "dataset.ttTreatyLocaleStatus" not in renderer:
        raise AssertionError("Treaty locale status is not persisted on rendered excerpts")
    if "tt-treaty-status" not in renderer:
        raise AssertionError("Treaty provenance marker is not rendered")
    if "current_application_suspended" in present and "application currently suspended" not in renderer.lower():
        raise AssertionError("Suspended treaty provisions do not have visible blocking copy")


def main() -> int:
    verify_assets_exist()
    verify_visible_status_mapping()
    print("Web integrity guards: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
