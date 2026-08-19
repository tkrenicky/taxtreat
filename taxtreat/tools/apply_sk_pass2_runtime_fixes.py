from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAIN_PATH = ROOT / "app" / "main.py"

_IMPORT_ANCHOR = """from taxtreat.services.calculation import (\n    build_withholding_compliance_schedule,\n    build_withholding_tax_calculation,\n)\n"""
_IMPORT_REPLACEMENT = _IMPORT_ANCHOR + """from taxtreat.services.source_country_calculation import (\n    build_source_country_withholding_compliance_schedule,\n    build_source_country_withholding_tax_calculation,\n)\n"""

_NON_CZ_ANCHOR = """    if source != \"CZ\":\n        try:\n            require_source_country_analysis_release(source)\n"""
_NON_CZ_REPLACEMENT = """    if source != \"CZ\":\n        try:\n            return require_source_country_analysis_release(source)\n"""

_FALLTHROUGH_ANCHOR = """        raise HTTPException(\n            status_code=409,\n            detail={\n                \"code\": \"SOURCE_COUNTRY_RELEASE_GATE_MISSING\",\n                \"source_country\": source,\n            },\n        )\n\n    treaty_pair_id = f\"{source}-{recipient}\"\n"""
_FALLTHROUGH_REPLACEMENT = """\n    treaty_pair_id = f\"{source}-{recipient}\"\n"""

_CALC_ANCHOR = """    calculation = build_withholding_tax_calculation(\n        amount,\n"""
_CALC_REPLACEMENT = """    calculation = build_source_country_withholding_tax_calculation(\n        source_country,\n        amount,\n"""

_COMPLIANCE_ANCHOR = """        build_withholding_compliance_schedule(\n            payload.transaction_date,\n"""
_COMPLIANCE_REPLACEMENT = """        build_source_country_withholding_compliance_schedule(\n            source_country,\n            payload.transaction_date,\n"""


def _replace_once(text: str, anchor: str, replacement: str, label: str) -> str:
    count = text.count(anchor)
    if count != 1:
        raise RuntimeError(
            f"Expected exactly one {label} anchor, found {count}; refusing to patch."
        )
    return text.replace(anchor, replacement, 1)


def build_integrated_main(text: str) -> str:
    if "build_source_country_withholding_tax_calculation" not in text:
        text = _replace_once(text, _IMPORT_ANCHOR, _IMPORT_REPLACEMENT, "source calculation import")
    if "return require_source_country_analysis_release(source)" not in text:
        text = _replace_once(text, _NON_CZ_ANCHOR, _NON_CZ_REPLACEMENT, "non-CZ release return")
    if "SOURCE_COUNTRY_RELEASE_GATE_MISSING" in text:
        text = _replace_once(text, _FALLTHROUGH_ANCHOR, _FALLTHROUGH_REPLACEMENT, "non-CZ fallthrough")
    if "calculation = build_source_country_withholding_tax_calculation(" not in text:
        text = _replace_once(text, _CALC_ANCHOR, _CALC_REPLACEMENT, "source calculation call")
    if "build_source_country_withholding_compliance_schedule(" not in text:
        text = _replace_once(text, _COMPLIANCE_ANCHOR, _COMPLIANCE_REPLACEMENT, "source compliance call")
    return text


def main() -> None:
    original = MAIN_PATH.read_text(encoding="utf-8")
    integrated = build_integrated_main(original)
    if integrated == original:
        print("SK pass-2 runtime fixes already applied; no changes.")
        return
    MAIN_PATH.write_text(integrated, encoding="utf-8")
    print("Applied SK pass-2 runtime fixes to app/main.py")


if __name__ == "__main__":
    main()
