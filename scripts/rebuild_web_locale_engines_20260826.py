from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "app" / "main.py"
LOCALE_MODULE = ROOT / "taxtreat" / "services" / "web_locale_engine.py"

MODULE = r'''from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

Locale = Literal["cs", "en"]

# The English workspace is compiled before it reaches the browser. The browser
# never translates an already-rendered Czech DOM. /ui/en and /ui/cs are two
# separate runtime entry points and every JS dependency of /ui/en is served
# through /ui-engine/en/ after source-level localisation.
PAIR_FILES = (
    "workspace-canonical-live-i18n-20260824.js",
    "workspace-canonical-live-i18n-dynamic-20260824.js",
    "workspace-cz-relief-i18n.js",
    "workspace-live-language-and-ir-layout-20260824.js",
    "workspace-step4-en-complete-20260821.js",
    "workspace-en-residual-hardening-20260826.js",
    "workspace-en-final-residue2-20260826.js",
    "workspace-en-stabilizer-20260826.js",
    "workspace-result-integrity-20260826.js",
    "workspace-payer-dialog-i18n-20260821.js",
    "workspace-payer-detail-i18n-20260821.js",
    "workspace-footer-i18n-20260821.js",
)

# Explicit translations cover dynamic engine output which is not necessarily
# present in a [CZ, EN] UI pair in the historical browser i18n layers.
EXTRA_TRANSLATIONS: dict[str, str] = {
    "CHYBÍ ÚDAJE PRO PŘIŘAZENÍ PRAVIDLA": "FACTS REQUIRED TO ASSIGN A RULE",
    "VÝPOČET DOKONČEN": "CALCULATION COMPLETED",
    "Srážková daň v CZK": "Withholding tax in CZK",
    "Česká daň k odvodu": "Czech tax payable",
    "Sazbu nelze určit bez doplnění potřebných podmínek": "The rate cannot be determined until the required facts are completed",
    "Zadané údaje zatím neumožňují v TaxTreat přiřadit konkrétní právní pravidlo a sazbu.": "The entered facts do not yet allow TaxTreat to assign a specific legal rule and rate.",
    "Po doplnění údajů": "After completing the facts",
    "Lhůty nelze uzavřít, dokud zadané údaje neumožní přiřadit příslušné pravidlo nebo měsíční úhrn rozhodný pro oznamovací povinnost.": "The deadlines cannot be finalized until the entered facts allow the applicable rule to be assigned or the monthly aggregate relevant for the notification obligation to be determined.",
    "VÝCHOZÍ VNITROSTÁTNÍ PRAVIDLO": "BASE DOMESTIC RULE",
    "POUŽITÉ SMLUVNÍ PRAVIDLO": "APPLIED TREATY RULE",
    "SMLUVNÍ PRAVIDLO": "TREATY RULE",
    "POUŽITÉ PRAVIDLO": "APPLIED DOMESTIC RULE",
    "OBECNÁ ČESKÁ SAZBA BEZ OSVOBOZENÍ": "GENERAL CZECH RATE WITHOUT EXEMPTION",
    "SEKUNDÁRNÍ SMLUVNÍ OCHRANA": "SECONDARY TREATY PROTECTION",
    "Výše úroku mezi spojenými osobami": "Interest amount between associated enterprises",
    "Zadané údaje nepotvrzují, že výše úroku odpovídá obvyklým podmínkám.": "The entered facts do not confirm that the interest amount is consistent with arm's length conditions.",
    "Oznámení se nepodává": "No notification required",
    "Daň se neodvádí": "No tax remittance required",
    "Česká daň se neodvádí.": "No Czech tax is remitted.",
    "Všechny údaje potřebné pro výpočet jsou zadány": "All facts required for the calculation are entered",
    "Výsledek vychází z uvedených údajů a zobrazeného právního základu.": "The result is based on the entered facts and the legal basis shown.",
    "Podmínky použitelné sazby": "Conditions for the applicable rate",
    "Z dostupných údajů zatím nelze uzavřít všechny podmínky právního pravidla. Je třeba ověřit chybějící skutkové okolnosti uvedené u vstupních údajů a kontrolu přepočítat.": "The available facts do not yet establish all conditions of the legal rule. Complete the missing factual items and recalculate.",
    "Podmínka vyžadující odborné posouzení": "Condition requiring professional review",
    "Podmínku nelze uzavřít pouze ze zadaných údajů.": "The condition cannot be concluded from the entered facts alone.",
    "Podmínky případného osvobození": "Conditions for a potential exemption",
    "Dodatečné splnění doby držby": "Subsequent satisfaction of the holding period",
    "Podmínky vnitrostátního osvobození": "Conditions for the domestic exemption",
    "Zvláštní smluvní podmínka úroku": "Special treaty condition for interest",
    "Zvláštní smluvní podmínka licenční platby": "Special treaty condition for royalties",
    "Výchozí vnitrostátní sazba činí": "The base Czech domestic rate is",
    "V následujícím kroku je zohledněno pravidlo, které tuto sazbu omezuje nebo nahrazuje.": "The next legal layer applies any rule that limits or replaces that rate.",
    "Smlouva o zamezení dvojího zdanění": "Double Tax Treaty",
    "Zákon č. 586/1992 Sb., o daních z příjmů": "Czech Income Taxes Act (Act No. 586/1992 Coll.)",
    "Znění použitého ustanovení": "Text of the applied provision",
    "Evidované znění použitého ustanovení": "Recorded text of the applied provision",
    "Otevřít zdroj": "Open source",
    "Rozhodné datum a navazující lhůty": "Reference date and compliance deadlines",
    "Rozhodné datum zadané pro výpočet": "Reference date used for the calculation",
    "Odvod srážkové daně": "Withholding tax remittance",
    "Oznámení příjmu plynoucího do zahraničí": "Outbound income notification",
    "Možné vnitrostátní osvobození": "Potential domestic exemption",
    "Základní podmínky:": "Key conditions:",
    "Relevantní ustanovení": "Relevant provisions",
    "Příjem je v České republice osvobozen": "Income is exempt from Czech withholding tax",
    "Zdanění pouze ve státě rezidence příjemce": "Taxation only in the recipient's state of residence",
    "Česká republika": "Czech Republic",
    "Neuvedeno": "Not provided",
    "Nevyplněno": "Not provided",
    "společnost": "company",
    "Společnost": "Company",
    "Fyzická osoba": "Individual",
    "Jiný subjekt": "Other entity",
    "Tchaj-wan": "Taiwan",
    "Rakousko": "Austria",
    "Rakouska": "Austria",
    "Německo": "Germany",
    "Německa": "Germany",
    "Švýcarsko": "Switzerland",
    "Švýcarska": "Switzerland",
    "Singapur": "Singapore",
    "Singapuru": "Singapore",
    "Licenční poplatky": "Royalties",
    "Úroky": "Interest",
    "Dividendy": "Dividends",
}

# Browser translation scripts are intentionally excluded from the EN compiled
# bootstrap. They were the source of the old race condition. Mixed files that
# also contain tax logic remain, but are compiled into English before execution.
EN_SKIP_ASSETS = {
    "workspace-header-language-20260821.js",
    "workspace-payer-dialog-i18n-20260821.js",
    "workspace-payer-detail-i18n-20260821.js",
    "workspace-footer-i18n-20260821.js",
    "workspace-canonical-live-i18n-20260824.js",
    "workspace-canonical-live-i18n-dynamic-20260824.js",
    "workspace-en-residual-hardening-20260826.js",
    "workspace-en-final-residue2-20260826.js",
    "workspace-en-stabilizer-20260826.js",
}

_CZECH_HINT = re.compile(r"[áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]")
_PAIR_RE = re.compile(r'\[\s*"((?:\\.|[^"\\])*)"\s*,\s*"((?:\\.|[^"\\])*)"\s*\]')


def _decode_js_string(value: str) -> str:
    try:
        return json.loads('"' + value + '"')
    except json.JSONDecodeError:
        return value


@lru_cache(maxsize=4)
def translation_map(web_root_value: str) -> dict[str, str]:
    web_root = Path(web_root_value)
    pairs: dict[str, str] = dict(EXTRA_TRANSLATIONS)
    for filename in PAIR_FILES:
        path = web_root / filename
        if not path.is_file():
            continue
        source = path.read_text(encoding="utf-8")
        for match in _PAIR_RE.finditer(source):
            left = _decode_js_string(match.group(1))
            right = _decode_js_string(match.group(2))
            if not left or not right or left == right:
                continue
            if _CZECH_HINT.search(left) or any(token in left for token in ("VÝCHOZÍ", "POUŽITÉ", "ČEKÁ", "CHYBÍ", "KROK ")):
                pairs.setdefault(left, right)
    return pairs


def _translate(value: str, web_root: Path) -> str:
    result = value
    pairs = translation_map(str(web_root))
    for source, target in sorted(pairs.items(), key=lambda item: len(item[0]), reverse=True):
        result = result.replace(source, target)
    # Currency/format locale is part of the renderer, not a DOM clean-up pass.
    result = result.replace("cs-CZ", "en-GB")
    result = result.replace('localeCompare(countryName(b.iso2), "cs")', 'localeCompare(countryName(b.iso2), "en")')
    result = result.replace(" Kč", " CZK")
    result = result.replace("Kč", "CZK")
    return result


def _strip_live_i18n_bootstrap(source: str) -> str:
    lines = []
    for line in source.splitlines():
        if any(asset in line for asset in EN_SKIP_ASSETS) and "loadScript" in line:
            continue
        lines.append(line)
    return "\n".join(lines) + ("\n" if source.endswith("\n") else "")


def render_workspace_asset(web_root: Path, asset_path: str, locale: Locale) -> str:
    candidate = (web_root / asset_path).resolve()
    root = web_root.resolve()
    if root not in candidate.parents or not candidate.is_file() or candidate.suffix != ".js":
        raise FileNotFoundError(asset_path)
    source = candidate.read_text(encoding="utf-8")
    if locale == "cs":
        return source
    if candidate.name == "workspace-report-export.js":
        source = _strip_live_i18n_bootstrap(source)
    source = _translate(source, web_root)
    # Every dependency loaded by the EN bootstrap is itself compiled as EN.
    source = source.replace('"/ui-assets/', '"/ui-engine/en/')
    source = source.replace("'/ui-assets/", "'/ui-engine/en/")
    # Intake payload returned to the EN engine is server-localised as structured
    # data before rendering; no browser text-node translation is required.
    source = source.replace('fetch("/analysis/intake"', 'fetch("/analysis/intake?lang=en"')
    source = source.replace("url.endsWith(\"/analysis/intake\")", "url.includes(\"/analysis/intake\")")
    source = source.replace("url.endsWith('/analysis/intake')", "url.includes('/analysis/intake')")
    return source


_ROUTER = r'''<script>
(() => {
  const locale = document.documentElement.lang === "en" ? "en" : "cs";
  window.__TAXTREAT_LOCALE__ = locale;
  localStorage.setItem("taxtreat-ui-language", locale);
  if (locale === "en") localStorage.setItem("taxtreat-report-language", "en");
  document.addEventListener("click", (event) => {
    const button = event.target.closest?.("#taxtreat-language-controls [data-lang]");
    if (!button) return;
    const target = button.dataset.lang === "en" ? "en" : "cs";
    event.preventDefault();
    event.stopImmediatePropagation();
    if (target === locale) return;
    localStorage.setItem("taxtreat-ui-language", target);
    window.location.assign(`/ui/${target}`);
  }, true);
})();
</script>'''


def render_workspace_document(web_root: Path, locale: Locale) -> str:
    source = (web_root / "workspace.html").read_text(encoding="utf-8")
    if locale == "en":
        source = _translate(source, web_root)
        source = re.sub(r'<html([^>]*)lang="[^"]*"', r'<html\1lang="en"', source, count=1)
        source = source.replace('src="/ui-assets/', 'src="/ui-engine/en/')
    else:
        source = re.sub(r'<html([^>]*)lang="[^"]*"', r'<html\1lang="cs"', source, count=1)
    # The locale route, not a DOM translator, owns language switching.
    source = source.replace("</body>", _ROUTER + "\n</body>")
    return source


def _translate_payload_value(value: Any, web_root: Path) -> Any:
    if isinstance(value, str):
        translated = _translate(value, web_root)
        # Fail closed for user-facing Czech residue: never leak a half-Czech
        # prompt into the dedicated English engine.
        if _CZECH_HINT.search(translated):
            return "Additional factual condition requires completion or review."
        return translated
    if isinstance(value, list):
        return [_translate_payload_value(item, web_root) for item in value]
    if isinstance(value, dict):
        return {key: _translate_payload_value(item, web_root) for key, item in value.items()}
    return value


def localize_intake_response(payload: dict[str, Any], web_root: Path, locale: Locale) -> dict[str, Any]:
    if locale != "en":
        return payload
    return _translate_payload_value(payload, web_root)
'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"missing patch marker: {label}")
    return text.replace(old, new, 1)


def main() -> None:
    LOCALE_MODULE.write_text(MODULE, encoding="utf-8")
    source = MAIN.read_text(encoding="utf-8")

    source = replace_once(
        source,
        "from fastapi.responses import FileResponse\n",
        "from fastapi.responses import FileResponse, HTMLResponse, Response\n",
        "response imports",
    )
    source = replace_once(
        source,
        "from taxtreat.services.reporting import (\n    build_professional_report,\n    render_report_html,\n)\n",
        "from taxtreat.services.reporting import (\n    build_professional_report,\n    render_report_html,\n)\nfrom taxtreat.services.web_locale_engine import (\n    localize_intake_response,\n    render_workspace_asset,\n    render_workspace_document,\n)\n",
        "locale imports",
    )

    old_ui = '''@app.get("/ui", include_in_schema=False)\ndef guided_intake_ui():\n    return FileResponse(\n        WEB_ROOT / "workspace.html",\n        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},\n    )\n'''
    new_ui = '''@app.get("/ui", include_in_schema=False)\ndef guided_intake_ui(lang: Literal["cs", "en"] = "cs"):\n    return HTMLResponse(\n        render_workspace_document(WEB_ROOT, lang),\n        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},\n    )\n\n\n@app.get("/ui/{lang}", include_in_schema=False)\ndef guided_intake_ui_locale(lang: Literal["cs", "en"]):\n    return HTMLResponse(\n        render_workspace_document(WEB_ROOT, lang),\n        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},\n    )\n\n\n@app.get("/ui-engine/{lang}/{asset_path:path}", include_in_schema=False)\ndef guided_intake_ui_engine(lang: Literal["cs", "en"], asset_path: str):\n    try:\n        content = render_workspace_asset(WEB_ROOT, asset_path, lang)\n    except FileNotFoundError as exc:\n        raise HTTPException(status_code=404, detail="Unknown UI engine asset") from exc\n    return Response(\n        content=content,\n        media_type="application/javascript",\n        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},\n    )\n'''
    source = replace_once(source, old_ui, new_ui, "ui routes")

    old_intake = '''@app.post("/analysis/intake")\ndef analysis_intake(payload: AnalysisPayload):\n    analysis = analyze(payload)\n    request = payload.model_dump(mode="json")\n    return {\n        "analysis": analysis,\n        "intake": build_intake_plan(request, analysis),\n    }\n'''
    new_intake = '''@app.post("/analysis/intake")\ndef analysis_intake(payload: AnalysisPayload, lang: Literal["cs", "en"] = "cs"):\n    analysis = analyze(payload)\n    request = payload.model_dump(mode="json")\n    response = {\n        "analysis": analysis,\n        "intake": build_intake_plan(request, analysis),\n    }\n    return localize_intake_response(response, WEB_ROOT, lang)\n'''
    source = replace_once(source, old_intake, new_intake, "intake locale")

    MAIN.write_text(source, encoding="utf-8")
    print("dual locale web engines rebuilt")


if __name__ == "__main__":
    main()
