(() => {
  "use strict";

  const PAIRS = [
    ["Výpočet vychází z níže uvedených předpokladů", "The calculation is based on the assumptions below"],
    ["Předvyplněné odpovědi zkontroluj a změň, pokud pro danou platbu neplatí.", "Review the pre-filled answers and change them if they do not apply to this payment."],
    ["VÝCHOZÍ VNITROSTÁTNÍ PRAVIDLO", "BASE DOMESTIC RULE"],
    ["POUŽITÉ PRAVIDLO", "APPLIED DOMESTIC RULE"],
    ["POUŽITÉ SMLUVNÍ PRAVIDLO", "APPLIED TREATY RULE"],
    ["OBECNÁ ČESKÁ SAZBA BEZ OSVOBOZENÍ", "GENERAL CZECH RATE WITHOUT EXEMPTION"],
    ["SEKUNDÁRNÍ SMLUVNÍ OCHRANA", "SECONDARY TREATY PROTECTION"],
    ["Relevantní ustanovení", "Relevant provisions"],
    ["Uplatní se § 19 zákona o daních z příjmů. Na základě zadaných údajů vnitrostátní osvobození znamená, že česká srážková daň není splatná.", "Section 19 of the Czech Income Taxes Act applies. Based on the entered facts, the domestic exemption means that no Czech withholding tax is payable."],
    ["§ 19 odst. 1 písm. ze) – stanoví osvobození podílu na zisku při splnění zákonných podmínek.", "Section 19(1)(ze) – provides the exemption for profit distributions where the statutory conditions are met."],
    ["§ 19 odst. 3 – vymezuje podmínky vztahující se ke kvalifikovaným společnostem a jejich daňovému postavení.", "Section 19(3) – defines the conditions relating to qualifying companies and their tax status."],
    ["§ 19 odst. 6 – upravuje podmínky účasti a časového testu držby.", "Section 19(6) – sets out the participation and holding-period conditions."],
    ["§ 19 odst. 11 – obsahuje navazující podmínky a vymezení relevantní pro osvobození.", "Section 19(11) – contains additional linked conditions and definitions relevant for the exemption."]
  ];

  function language() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
  }

  function countryPairs() {
    const csNames = new Intl.DisplayNames(["cs-CZ"], { type: "region" });
    const enNames = new Intl.DisplayNames(["en"], { type: "region" });
    const codes = new Set(["AT"]);
    document.querySelectorAll('select[name="recipient_country"] option[value]').forEach((option) => {
      const code = String(option.value || "").toUpperCase();
      if (/^[A-Z]{2}$/.test(code)) codes.add(code);
    });
    return [...codes].map((code) => [csNames.of(code), enNames.of(code)]).filter(([cs, en]) => cs && en && cs !== en);
  }

  function swapText(value, pairs) {
    let next = String(value || "");
    const toEnglish = language() === "en";
    const ordered = [...pairs].sort((a, b) => Math.max(b[0].length, b[1].length) - Math.max(a[0].length, a[1].length));
    for (const [cs, en] of ordered) {
      const from = toEnglish ? cs : en;
      const to = toEnglish ? en : cs;
      if (next.includes(from)) next = next.split(from).join(to);
    }
    return next;
  }

  function normalizeDynamicResultText(value) {
    let next = String(value || "");
    if (language() === "en") {
      next = next
        .replace(/Česká daň se neodvádí\.\s*Měsíční úhrn úroků stejného druhu činí\s*([\d\s.,]+)\s*Kč\s*a přesáhl\s*([\d\s.,]+)\s*Kč;\s*oznámení podle §\s*38da(?:\s+ZDP|\s+zákona č\.\s*586\/1992 Sb\.,?\s*o daních z příjmů)?\s*se podává do uvedeného data\./gi,
          "No Czech tax is remitted. The monthly aggregate of interest of the same type is $1 CZK and exceeded $2 CZK; the notification under Section 38da of the Czech Income Taxes Act is due on the date shown.")
        .replace(/(\d[\d\s.,]*)\s*Kč\b/g, "$1 CZK");
    } else {
      next = next
        .replace(/No Czech tax is remitted\.\s*The monthly aggregate of interest of the same type is\s*([\d\s.,]+)\s*CZK\s*and exceeded\s*([\d\s.,]+)\s*CZK;\s*the notification under Section 38da of the Czech Income Taxes Act is due on the date shown\./gi,
          "Česká daň se neodvádí. Měsíční úhrn úroků stejného druhu činí $1 Kč a přesáhl $2 Kč; oznámení podle § 38da ZDP se podává do uvedeného data.")
        .replace(/(\d[\d\s.,]*)\s*CZK\b/g, "$1 Kč");
    }
    return next;
  }

  function translateTextNodes(root, pairs) {
    if (!root) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
      const current = node.nodeValue || "";
      let next = swapText(current, pairs);
      next = normalizeDynamicResultText(next);
      if (next !== current) node.nodeValue = next;
    }
  }

  function translateCountryLabels() {
    const pairs = countryPairs();
    document.querySelectorAll('[data-recipient-country-name], #flow-recipient-meta, .recipient-row p, .profile-head p').forEach((element) => {
      translateTextNodes(element, pairs);
    });
  }

  function syncReportLanguageDefault() {
    const select = document.querySelector("#taxtreat-report-language");
    if (!select || select.dataset.userSelected === "true") return;
    const target = language() === "en" ? "en" : "cs";
    if (select.value !== target) {
      select.value = target;
      localStorage.setItem("taxtreat-report-language", target);
    }
  }

  function refresh() {
    translateCountryLabels();
    const payment = document.querySelector('.flow-step[data-step="3"].active');
    const result = document.querySelector('.flow-step[data-step="4"].active');
    if (payment) translateTextNodes(payment, PAIRS);
    if (result) translateTextNodes(result, PAIRS);
    syncReportLanguageDefault();
  }

  let timer = 0;
  function schedule() {
    clearTimeout(timer);
    timer = setTimeout(refresh, 20);
  }

  document.addEventListener("change", (event) => {
    if (event.target?.id === "taxtreat-report-language") {
      event.target.dataset.userSelected = "true";
      return;
    }
    if (event.target?.id === "taxtreat-ui-language" || event.target?.matches?.('[name="income_type"],[name="recipient_country"]')) {
      [0, 60, 180, 400].forEach((delay) => setTimeout(refresh, delay));
    }
  }, true);

  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true, characterData: true });
  [0, 80, 250, 700, 1500].forEach((delay) => setTimeout(refresh, delay));
})();
