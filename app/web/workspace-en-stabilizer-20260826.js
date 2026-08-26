(() => {
  "use strict";

  const EXACT = new Map([
    ["* Označuje povinný údaj.", "* Required field."],
    ["ÚDAJE PODLE DRUHU PŘÍJMU", "INCOME-SPECIFIC FACTS"],
    ["Vyplň dostupné skutkové údaje před výpočtem. Údaje uložené v profilu příjemce jsou předvyplněny a lze je pro tuto platbu změnit.", "Complete the available transaction facts before calculation. Facts stored in the recipient profile are pre-filled and can be changed for this payment."],
    ["← Zpět k příjemci", "← Back to recipient"],
    ["1. VÝCHOZÍ VNITROSTÁTNÍ PRAVIDLO", "1. BASE DOMESTIC RULE"],
    ["2. POUŽITÉ SMLUVNÍ PRAVIDLO", "2. APPLIED TREATY RULE"],
    ["1. POUŽITÉ PRAVIDLO", "1. APPLIED DOMESTIC RULE"],
    ["2. OBECNÁ ČESKÁ SAZBA BEZ OSVOBOZENÍ", "2. GENERAL CZECH RATE WITHOUT EXEMPTION"],
    ["1. VÝCHOZÍ VNITROSTÁTNÍ PRAVIDLO", "1. BASE DOMESTIC RULE"],
    ["VÝCHOZÍ VNITROSTÁTNÍ PRAVIDLO", "BASE DOMESTIC RULE"],
    ["POUŽITÉ SMLUVNÍ PRAVIDLO", "APPLIED TREATY RULE"],
    ["POUŽITÉ PRAVIDLO", "APPLIED DOMESTIC RULE"],
    ["OBECNÁ ČESKÁ SAZBA BEZ OSVOBOZENÍ", "GENERAL CZECH RATE WITHOUT EXEMPTION"],
    ["SEKUNDÁRNÍ SMLUVNÍ OCHRANA", "SECONDARY TREATY PROTECTION"]
  ]);
  const REVERSE = new Map([...EXACT].map(([cs, en]) => [en, cs]));

  function language() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
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
        .replace(/\b([0-9][0-9\s.,]*)\s*Kč\b/g, "$1 CZK");
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

  function activeRoots() {
    return [...document.querySelectorAll('.flow-step.active, #workspace-payment, [data-view="workspace"]')];
  }

  let translating = false;
  function refresh() {
    if (translating) return;
    translating = true;
    try {
      const roots = activeRoots();
      if (roots.length) roots.forEach(translateRoot);
      else translateRoot(document.body);
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
    timer = window.setTimeout(refresh, 20);
  }

  document.addEventListener("change", (event) => {
    if (event.target?.id === "taxtreat-report-language") event.target.dataset.userChosen = "true";
    if (event.target?.id === "taxtreat-ui-language" || event.target?.matches?.('[name="income_type"],[name="recipient_country"]')) {
      [0, 60, 180, 420].forEach((delay) => window.setTimeout(refresh, delay));
    }
  }, true);

  document.addEventListener("click", (event) => {
    const target = event.target?.closest?.('[data-next-step], [data-nav], [data-report-action], button[type="submit"]');
    if (!target) return;
    [0, 80, 250, 600].forEach((delay) => window.setTimeout(refresh, delay));
  }, true);

  const observer = new MutationObserver((mutations) => {
    if (translating) return;
    if (!mutations.some((m) => m.type === "characterData" || m.addedNodes?.length)) return;
    schedule();
  });
  observer.observe(document.documentElement, { childList: true, subtree: true, characterData: true });

  [0, 100, 300, 800, 1600].forEach((delay) => window.setTimeout(refresh, delay));
})();
