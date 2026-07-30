from pathlib import Path
from typing import Any

import yaml


ROOT = Path("knowledge_base/countries")
ALLOWED_INCOME_TYPES = {"dividends", "interest", "royalties"}
ALLOWED_STATUSES = {"draft", "reviewed", "verified"}


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError("Root YAML value must be a mapping.")

    return data


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    data = load_yaml(path)

    required = {
        "id",
        "payer_country",
        "recipient_country",
        "income_type",
        "domestic_law",
        "treaty",
        "documentation",
        "sources",
        "status",
    }

    missing = required - data.keys()
    if missing:
        errors.append(f"Missing fields: {', '.join(sorted(missing))}")

    if data.get("income_type") not in ALLOWED_INCOME_TYPES:
        errors.append(f"Invalid income_type: {data.get('income_type')!r}")

    if data.get("status") not in ALLOWED_STATUSES:
        errors.append(f"Invalid status: {data.get('status')!r}")

    for field in ("payer_country", "recipient_country"):
        value = data.get(field)
        if not isinstance(value, str) or len(value) != 2 or value != value.upper():
            errors.append(f"{field} must be an uppercase two-letter code.")

    domestic_law = data.get("domestic_law")
    if not isinstance(domestic_law, dict):
        errors.append("domestic_law must be a mapping.")
    else:
        if "standard_rate" not in domestic_law:
            errors.append("domestic_law.standard_rate is required.")
        if "legal_reference" not in domestic_law:
            errors.append("domestic_law.legal_reference is required.")

    treaty = data.get("treaty")
    if not isinstance(treaty, dict):
        errors.append("treaty must be a mapping.")
    elif "applicable" not in treaty:
        errors.append("treaty.applicable is required.")

    if not isinstance(data.get("documentation"), list):
        errors.append("documentation must be a list.")

    if not isinstance(data.get("sources"), list):
        errors.append("sources must be a list.")

    return errors


def main() -> int:
    files = sorted(ROOT.rglob("*.yaml"))

    if not files:
        print("No knowledge-base files found.")
        return 1

    failed = 0

    for path in files:
        errors = validate_file(path)

        if errors:
            failed += 1
            print(f"FAIL {path}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {path}")

    print()
    print(f"Validated: {len(files)}")
    print(f"Failed: {failed}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
