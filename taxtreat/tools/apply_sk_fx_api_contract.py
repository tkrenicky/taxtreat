from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAIN_PATH = ROOT / "app" / "main.py"

_CLASS_ANCHOR = '''    def normalize_codes(cls, value: str) -> str:\n        return value.upper()\n\n\nclass TransactionAmount(BaseModel):\n'''
_CLASS_REPLACEMENT = '''    def normalize_codes(cls, value: str) -> str:\n        return value.upper()\n\n\nclass SkExchangeRate(BaseModel):\n    source: str = Field(pattern=r"^(?i:ECB|NBS)$")\n    currency: str = Field(pattern=r"^[A-Za-z]{3}$")\n    eur_per_unit: Decimal = Field(\n        gt=0,\n        max_digits=30,\n        decimal_places=12,\n    )\n    effective_date: date\n    source_url: str = Field(pattern=r"^https://")\n    entry_method: Literal["automatic", "manual_override"] = "automatic"\n\n    @field_validator("source", "currency")\n    @classmethod\n    def normalize_codes(cls, value: str) -> str:\n        return value.upper()\n\n\nclass TransactionAmount(BaseModel):\n'''

_RATE_ANCHOR = "    exchange_rate: CnbExchangeRate | None = None\n"
_RATE_REPLACEMENT = "    exchange_rate: CnbExchangeRate | SkExchangeRate | None = None\n"

_CALL_ANCHOR = '''        tax_treatment=(\n            result.tax_treatment.value\n            if getattr(result, "tax_treatment", None) is not None\n            else None\n        ),\n    )\n    analysis["withholding_tax_calculation"] = calculation\n'''
_CALL_REPLACEMENT = '''        tax_treatment=(\n            result.tax_treatment.value\n            if getattr(result, "tax_treatment", None) is not None\n            else None\n        ),\n        transaction_date=payload.transaction_date,\n    )\n    analysis["withholding_tax_calculation"] = calculation\n'''


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one {label} anchor, found {count}; refusing to patch.")
    return text.replace(old, new, 1)


def build_integrated_main(text: str) -> str:
    if "class SkExchangeRate(BaseModel):" not in text:
        text = _replace_once(text, _CLASS_ANCHOR, _CLASS_REPLACEMENT, "SK FX class")
    if "CnbExchangeRate | SkExchangeRate | None" not in text:
        text = _replace_once(text, _RATE_ANCHOR, _RATE_REPLACEMENT, "FX union")
    if "transaction_date=payload.transaction_date" not in text:
        text = _replace_once(text, _CALL_ANCHOR, _CALL_REPLACEMENT, "SK withholding date")
    return text


def main() -> None:
    original = MAIN_PATH.read_text(encoding="utf-8")
    integrated = build_integrated_main(original)
    if integrated == original:
        print("SK FX API contract already applied; no changes.")
        return
    MAIN_PATH.write_text(integrated, encoding="utf-8")
    print("Applied SK FX API contract to app/main.py")


if __name__ == "__main__":
    main()
