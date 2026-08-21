from __future__ import annotations

from typing import Any


def _english(report: dict[str, Any]) -> bool:
    facts = ((report.get("assumptions") or {}).get("transaction_facts") or {})
    return str(facts.get("__report_language") or "cs").lower() == "en"


def apply_domestic_exemption_english_polish(html: str, report: dict[str, Any]) -> str:
    if not html or not _english(report):
        return html
    result = report.get("result") or {}
    if str(result.get("tax_treatment") or "") != "domestic_exemption":
        return html

    replacements = (
        ("Shrnutí transakce, použitého daňového režimu a výpočtu české srážkové daně.", "Summary of the transaction, the applied tax treatment and the Czech withholding-tax calculation."),
        (">Česká srážková daň</span>", ">Czech withholding tax</span>"),
        (">Daňový režim</span>", ">Tax treatment</span>"),
        (">Použitý právní základ</span>", ">Legal basis applied</span>"),
        (">Smluvní ochrana</span><b>Sekundární</b>", ">Treaty protection</span><b>Secondary</b>"),
        ("Při splnění uvedených předpokladů se použije vnitrostátní osvobození podle § 19 ZDP a česká srážková daň se neuplatní.", "Based on the entered facts, the domestic exemption under Section 19 applies and Czech withholding tax does not apply."),
        ("Výchozí vnitrostátní režim podle § 36 ZDP → osvobození podle § 19 ZDP. SZDZ je v tomto výsledku pouze sekundární ochranou.", "Default Czech domestic treatment under Section 36 → exemption under Section 19. The treaty is only a secondary protection in this result."),
        (">Konečný režim</span>", ">Final treatment</span>"),
        (">Konečný režim</b>", ">Final treatment</b>"),
        ("Osvobození podle § 19 ZDP", "Exempt under Section 19"),
        ("Neuplatňuje se", "Does not apply"),
    )
    localized = html
    for old, new in replacements:
        localized = localized.replace(old, new)
    return localized
