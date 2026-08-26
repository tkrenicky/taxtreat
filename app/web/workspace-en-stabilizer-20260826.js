(() => {
  "use strict";

  const EXACT = new Map([
    ["* Označuje povinný údaj.", "* Required field."],
    ["ÚDAJE PODLE DRUHU PŘÍJMU", "INCOME-SPECIFIC FACTS"],
    ["Vyplň dostupné skutkové údaje před výpočtem. Údaje uložené v profilu příjemce jsou předvyplněny a lze je pro tuto platbu změnit.", "Complete the available transaction facts before calculation. Facts stored in the recipient profile are pre-filled and can be changed for this payment."],
    ["← Zpět k příjemci", "← Back to recipient"],
    ["CHYBÍ ÚDAJE PRO PŘIŘAZENÍ PRAVIDLA", "FACTS REQUIRED TO ASSIGN A RULE"],
    ["Srážková daň v CZK", "Withholding tax in CZK"],
    ["Sazbu nelze určit bez doplnění potřebných podmínek", "The rate cannot be determined until the required facts are completed"],
    ["Zadané údaje zatím neumožňují v TaxTreat přiřadit konkrétní právní pravidlo a sazbu.", "The entered facts do not yet allow TaxTreat to assign a specific legal rule and rate."],
    ["Po doplnění údajů", "After completing the facts"],
    ["Lhůty nelze uzavřít, dokud zadané údaje neumožní přiřadit příslušné pravidlo nebo měsíční úhrn rozhodný pro oznamovací povinnost.", "The deadlines cannot be finalized until the entered facts allow the applicable rule to be assigned or the monthly aggregate relevant for the notification obligation to be determined."],
    ["1. VÝCHOZÍ VNITROSTÁTNÍ PRAVIDLO", "1. BASE DOMESTIC RULE"],
    ["2. POUŽITÉ SMLUVNÍ PRAVIDLO", "2. APPLIED TREATY RULE"],
    ["1. POUŽITÉ PRAVIDLO", "1. APPLIED DOMESTIC RULE"],
    ["2. OBECNÁ ČESKÁ SAZBA BEZ OSVOBOZENÍ", "2. GENERAL CZECH RATE WITHOUT EXEMPTION"],
    ["VÝCHOZÍ VNITROSTÁTNÍ PRAVIDLO", "BASE DOMESTIC RULE"],
    ["POUŽITÉ SMLUVNÍ PRAVIDLO", "APPLIED TREATY RULE"],
    ["POUŽITÉ PRAVIDLO", "APPLIED DOMESTIC RULE"],
    ["OBECNÁ ČESKÁ SAZBA BEZ OSVOBOZENÍ", "GENERAL CZECH RATE WITHOUT EXEMPTION"],
    ["SEKUNDÁRNÍ SMLUVNÍ OCHRANA", "SECONDARY TREATY PROTECTION"]
  ]);
  const REVERSE = new Map([...EXACT].map(([cs, en]) => [en, cs]));

  function language() {
    const pressed = document.querySelector('#taxtreat-language-controls .tt-lang-mini button[aria-pressed="true"]')?.dataset.lang;
    if (pressed === "en" || pressed === "cs") return pressed;
    const active = document.querySelector('#taxtreat-language-controls .tt-lang-mini button[data-active="true"]')?.dataset.lang;
    if (active === "en" || active === "cs") return active;
    const stored = localStorage.getItem("taxtreat-ui-language");
    if (stored === "en" || stored === "cs") return stored;
    const select = document.querySelector("#taxtreat-ui-language")?.value;
    return select === "en" ? "en" : "cs";
  }

  function translateValue(value) {
    let text = String(value || "");
    const en = language() === "en";
    const map = en ? EXACT : REVERSE;

    for (const [from, to] of map) {
      if (text.includes(from)) text = text.split(from).join(to);
    }

    if (en) {
      text = text
        .replace(/Under Article\s+(\d+)\s+of the double tax treaty,\s*se při zadaných údajích příjem v České republice nezdaňuje\./gi,
          "Under Article $1 of the double tax treaty, the entered facts result in no Czech taxation.")
        .replace(/Podle článku\s+(\d+)\s+smlouvy o zamezení dvojího zdanění se při zadaných údajích příjem v České republice nezdaňuje\./gi,
          "Under Article $1 of the double tax treaty, the entered facts result in no Czech taxation.")
        .replace(/\b([0-9][0-9\s.,]*)\s*Kč\b/g, "$1 CZK")
        .replace(/\bKč\b/g, "CZK");
    } else {
      text = text
        .replace(/Under Article\s+(\d+)\s+of the double tax treaty,\s*the entered facts result in no Czech taxation\./gi,
          "Podle článku $1 smlouvy o zamezení dvojího zdanění se při zadaných údajích příjem v České republice nezdaňuje.")
        .replace(/\b([0-9][0-9\s.,]*)\s*CZK\b/g, "$1 Kč");
    }
    return text;
  }

  function translateRoot(root) {
    if (!root) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
      const current = node.nodeValue || "";
      const next = translateValue(current);
      if (next !== current) node.nodeValue = next;
    }
  }

  let translating = false;
  function refresh() {
    if (translating) return;
    translating = true;
    try {
      // In EN mode translate the full workspace body. This is deliberate: result copy
      // is injected by several late renderers and must not escape the final EN pass.
      translateRoot(document.body);
      const reportLanguage = document.querySelector("#taxtreat-report-language");
      if (reportLanguage && !reportLanguage.dataset.userChosen && language() === "en" && reportLanguage.value !== "en") {
        reportLanguage.value = "en";
        localStorage.setItem("taxtreat-report-language", "en");
      }
    } finally {
      translating = false;
    }
  }

  let timer = 0;
  function schedule() {
    clearTimeout(timer);
    timer = window.setTimeout(refresh, 10);
  }

  document.addEventListener("change", (event) => {
    if (event.target?.id === "taxtreat-report-language") event.target.dataset.userChosen = "true";
    if (event.target?.id === "taxtreat-ui-language" || event.target?.matches?.('[name="income_type"],[name="recipient_country"]')) {
      [0, 40, 120, 300, 700].forEach((delay) => window.setTimeout(refresh, delay));
    }
  }, true);

  document.addEventListener("click", (event) => {
    if (event.target?.closest?.("#taxtreat-language-controls")) {
      [0, 40, 120, 300, 700].forEach((delay) => window.setTimeout(refresh, delay));
      return;
    }
    const target = event.target?.closest?.('[data-next-step], [data-nav], [data-report-action], button[type="submit"]');
    if (!target) return;
    [0, 60, 180, 420, 900].forEach((delay) => window.setTimeout(refresh, delay));
  }, true);

  const observer = new MutationObserver((mutations) => {
    if (translating) return;
    if (!mutations.some((m) => m.type === "characterData" || m.addedNodes?.length)) return;
    schedule();
  });
  observer.observe(document.documentElement, { childList: true, subtree: true, characterData: true });

  [0, 80, 220, 600, 1200, 2200].forEach((delay) => window.setTimeout(refresh, delay));
})();
