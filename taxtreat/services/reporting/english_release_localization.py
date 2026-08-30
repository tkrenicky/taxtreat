from __future__ import annotations

import re
from typing import Any


def _is_english_cz_report(report: dict[str, Any]) -> bool:
    scope = report.get("scope") or {}
    return (
        str(report.get("language") or "").lower() == "en"
        and str(scope.get("source_country") or "CZ").upper() == "CZ"
    )


def finalize_english_report_html(html: str, report: dict[str, Any]) -> str:
    """Finalize residual English copy after the shared Czech editorial template.

    The client-report template is intentionally source-country oriented and is
    localized after rendering. This final pass is semantic rather than visual:
    it removes mixed-language residues caused by replacement ordering and makes
    the domestic-exemption hierarchy explicit in the English report.
    """
    if not _is_english_cz_report(report):
        return html

    localized = html

    residuals = (
        ("PRÁVNÍ USTANOVENÍ", "LEGAL PROVISION"),
        ("VNITROSTÁTNÍ PRÁVO", "DOMESTIC LAW"),
        ("SMLOUVA", "TREATY"),
        (
            "Applied rate vychází z těchto zadaných údajů:",
            "The applied rate is based on the following entered facts:",
        ),
        (" ZDP)", " of the Czech Income Taxes Act)"),
    )
    for old, new in residuals:
        localized = localized.replace(old, new)

    recipient = str((report.get("scope") or {}).get("recipient_country") or "").upper()
    if recipient:
        localized = re.sub(
            r"of the Double Tax Treaty between the Czech Republic and .*? o zamezení dvojího zdanění",
            f"of the Double Tax Treaty between the Czech Republic and {recipient}",
            localized,
        )
        localized = re.sub(
            r"Double Tax Treaty between the Czech Republic and .*? o zamezení dvojího zdanění",
            f"Double Tax Treaty between the Czech Republic and {recipient}",
            localized,
        )

    result = report.get("result") or {}
    if (
        str(result.get("status") or "") == "FINAL"
        and str(result.get("tax_treatment") or "") == "domestic_exemption"
    ):
        localized = localized.replace(
            "Applied legal basis",
            "Primary legal basis — domestic exemption",
            1,
        )
        marker = "Primary legal basis — domestic exemption"
        if marker in localized and "Treaty treatment is supplementary." not in localized:
            localized = localized.replace(
                marker,
                marker + '<span class="tt-en-domestic-hierarchy"> · Treaty treatment is supplementary.</span>',
                1,
            )

    localized = localized.replace('lang="cs"', 'lang="en"')
    return localized
