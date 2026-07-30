from pathlib import Path

import yaml


ROOT = Path("knowledge_base/countries/CZ")

TARGETS = [
    "AT", "AU", "BE", "BG", "BR", "CA", "CH", "CN", "CY", "DE", "DK", "EE",
    "ES", "FI", "FR", "GB", "GR", "HK", "HR", "HU", "IE", "IL", "IN", "IS",
    "IT", "JP", "KR", "LT", "LU", "LV", "MX", "MY", "NL", "NO", "NZ", "PL",
    "PT", "RO", "SE", "SG", "SI", "SK", "TH", "TR", "TW", "UA", "US", "VN",
    "ZA",
]

INCOME_TYPES = {
    "dividends": "DIV",
    "interest": "INT",
    "royalties": "ROY",
}


def build_record(country: str, income_type: str, code: str) -> dict:
    return {
        "id": f"CZ-{country}-{code}",
        "payer_country": "CZ",
        "recipient_country": country,
        "income_type": income_type,
        "domestic_law": {
            "standard_rate": 15,
            "legal_reference": "Czech Income Taxes Act",
            "notes": "TO_BE_VERIFIED",
        },
        "treaty": {
            "applicable": None,
            "article": None,
            "paragraph": None,
            "standard_rate": None,
            "beneficial_owner_required": None,
            "reduced_rates": [],
            "notes": "TO_BE_VERIFIED",
        },
        "protocol": {
            "applicable": None,
            "effective_date": None,
            "reference": None,
            "notes": "TO_BE_VERIFIED",
        },
        "eu_directive": {
            "applicable": None,
            "directive": None,
            "minimum_ownership_percent": None,
            "minimum_holding_months": None,
            "conditions": [],
        },
        "documentation": ["TO_BE_COMPLETED"],
        "sources": [],
        "status": "draft",
    }


created = 0
skipped = 0

for country in TARGETS:
    for income_type, code in INCOME_TYPES.items():
        path = ROOT / f"{country}-{income_type}.yaml"

        if path.exists():
            skipped += 1
            continue

        path.write_text(
            yaml.safe_dump(
                build_record(country, income_type, code),
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        created += 1

print(f"Created: {created}")
print(f"Skipped: {skipped}")
