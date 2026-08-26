(() => {
  "use strict";

  const PAIRS = [
    ["Výpočet vychází z níže uvedených předpokladů", "The calculation is based on the assumptions below"],
    ["Předvyplněné odpovědi zkontroluj a změň, pokud pro danou platbu neplatí.", "Review the pre-filled answers and change them if they do not apply to this payment."],
    ["VÝCHOZÍ VNITROSTÁTNÍ PRAVIDLO", "BASE DOMESTIC RULE"],
    ["POUŽITÉ PRAVIDLO", "APPLIED DOMESTIC RULE"],
    ["1. VÝCHOZÍ VNITROSTÁTNÍ PRAVIDLO", "1. BASE DOMESTIC RULE"],
    ["1. POUŽITÉ PRAVIDLO", "1. APPLIED DOMESTIC RULE"],
    ["Relevantní ustanovení", "Relevant provisions"],
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
    for (const [cs, en] of pairs) {
      const from = toEnglish ? cs : en;
      const to = toEnglish ? en : cs;
      if (next.includes(from)) next = next.split(from).join(to);
    }
    return next;
  }

  function translateTextNodes(root, pairs) {
    const walker = document.createTreeWalker(root || document.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
      const current = node.nodeValue || "";
      const next = swapText(current, pairs);
      if (next !== current) node.nodeValue = next;
    }
  }

  function translateCountryLabels() {
    const pairs = countryPairs();
    document.querySelectorAll('[data-recipient-country-name], #flow-recipient-meta, .recipient-row p, .profile-head p').forEach((element) => {
      const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
      const nodes = [];
      while (walker.nextNode()) nodes.push(walker.currentNode);
      for (const node of nodes) {
        const current = node.nodeValue || "";
        const next = swapText(current, pairs);
        if (next !== current) node.nodeValue = next;
      }
    });
  }

  function translateSection19Evidence() {
    const result = document.querySelector('.flow-step[data-step="4"].active');
    if (!result) return;
    const text = result.textContent || "";
    if (!/Section 19|§\s*19/.test(text)) return;
    translateTextNodes(result, PAIRS);
  }

  function refresh() {
    translateCountryLabels();
    translateSection19Evidence();
  }

  let timer = 0;
  function schedule() {
    clearTimeout(timer);
    timer = setTimeout(refresh, 30);
  }

  document.addEventListener("change", schedule, true);
  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true });
  [0, 100, 350, 900, 1600].forEach((delay) => setTimeout(refresh, delay));
})();
