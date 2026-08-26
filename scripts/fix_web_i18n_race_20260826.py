from pathlib import Path


def replace_required(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Expected text not found in {path}: {old[:120]!r}")
    p.write_text(text.replace(old, new), encoding="utf-8")


# 1) Stop re-running broad translation passes on every arbitrary click.
replace_required(
    "app/web/workspace-canonical-live-i18n-20260824.js",
    '    window.setTimeout(schedule, 0);\n  }, true);',
    '    if (button) window.setTimeout(schedule, 0);\n  }, true);',
)
replace_required(
    "app/web/workspace-canonical-live-i18n-dynamic-20260824.js",
    '  document.addEventListener("click", () => window.setTimeout(schedule, 0), true);\n',
    '',
)
replace_required(
    "app/web/workspace-final-polish-v2.js",
    '    document.addEventListener("click", scheduleRefresh, true);\n',
    '',
)
replace_required(
    "app/web/workspace-en-residual-hardening-20260826.js",
    '  document.addEventListener("click", () => schedule(document.body), true);\n',
    '',
)
replace_required(
    "app/web/workspace-en-residual-hardening-20260826.js",
    '  }).observe(document.documentElement, { childList: true, subtree: true, characterData: true });',
    '  }).observe(document.documentElement, { childList: true, subtree: true });',
)
replace_required(
    "app/web/workspace-en-final-residue2-20260826.js",
    '  document.addEventListener("click", schedule, true);\n',
    '',
)
replace_required(
    "app/web/workspace-en-final-residue2-20260826.js",
    '  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true, characterData: true });',
    '  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true });',
)

# 2) Section 19 legal-source enhancement must exist in EN too, not only CZ.
replace_required(
    "app/web/workspace-cz-final-hardening-20260823.js",
    '  function enhanceSection19LegalSource() {\n    if (!isCzech() || !section19Authoritative()) return;',
    '  function enhanceSection19LegalSource() {\n    if (!section19Authoritative()) return;',
)

# 3) Final residue pass: cover the exact manually observed leftovers in both directions.
p = Path("app/web/workspace-en-final-residue2-20260826.js")
text = p.read_text(encoding="utf-8")
needle = '  const PAIRS = [\n'
insert = (
    '  const PAIRS = [\n'
    '    ["Výpočet vychází z níže uvedených předpokladů", "The calculation is based on the assumptions below"],\n'
    '    ["Předvyplněné odpovědi zkontroluj a změň, pokud pro danou platbu neplatí.", "Review the pre-filled answers and change them if they do not apply to this payment."],\n'
    '    ["VÝCHOZÍ VNITROSTÁTNÍ PRAVIDLO", "BASE DOMESTIC RULE"],\n'
    '    ["POUŽITÉ PRAVIDLO", "APPLIED DOMESTIC RULE"],\n'
)
if needle not in text:
    raise SystemExit("PAIRS marker missing")
text = text.replace(needle, insert, 1)
p.write_text(text, encoding="utf-8")

# 4) Load the final residue pass after report core as the last authoritative UI pass.
p = Path("app/web/workspace-report-export.js")
text = p.read_text(encoding="utf-8")
old = '    .then(() => loadScript("/ui-assets/workspace-en-final-residue2-20260826.js?v=20260826-enfinal1"))\n    .then(() => loadScript("/ui-assets/workspace-treaty-excerpt-locales-20260824.js?v=20260824-treatylocale1"))\n    .then(() => loadScript("/ui-assets/workspace-report-export-core.js?v=20260819-3"))'
new = '    .then(() => loadScript("/ui-assets/workspace-treaty-excerpt-locales-20260824.js?v=20260824-treatylocale1"))\n    .then(() => loadScript("/ui-assets/workspace-report-export-core.js?v=20260819-3"))\n    .then(() => loadScript("/ui-assets/workspace-en-final-residue2-20260826.js?v=20260826-enfinal2"))'
if old not in text:
    raise SystemExit("bootstrap order marker missing")
p.write_text(text.replace(old, new), encoding="utf-8")

print("Applied deterministic i18n race/parity patch")
