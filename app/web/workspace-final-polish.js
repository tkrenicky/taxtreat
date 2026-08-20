(() => {
  "use strict";

  const translations = new Map([
    ["Jazyk", "Language"],
    ["Jazyk webu", "Website language"],
    ["Jazyk reportu", "Report language"],
    ["Stát plátce *", "Payer country *"],
    ["Česká republika", "Czech Republic"],
    ["Slovensko", "Slovakia"],
    ["Stát plátce určuje, která vnitrostátní pravidla srážkové daně TaxTreat použije. Nejde o samostatný přepínač režimu aplikace.", "The payer country determines which domestic withholding tax rules TaxTreat applies. It is not a separate application-mode switch."],
    ["Pro slovenského plátce se údaje z českého registru ARES nenačítají; identifikační údaje vyplň ručně.", "For a Slovak payer, data are not retrieved from the Czech ARES register; enter the identification details manually."],
    ["Po zadání 8 číslic TaxTreat načte identifikační údaje z ARES.", "After entering 8 digits, TaxTreat retrieves identification details from ARES."],
    ["Ještě dva údaje pro možné osvobození podle § 19 ZDP", "Two more facts for the potential Section 19 exemption"],
    ["Podíl, přímé držení, dobu držby, skutečné vlastnictví a vazbu ke stálé provozovně už TaxTreat používá z odpovědí výše.", "TaxTreat already uses the ownership percentage, direct holding, holding period, beneficial ownership and permanent-establishment connection from the answers above."],
    ["Je příjemce běžnou obchodní společností (např. GmbH, AG, Ltd. nebo S.A.), nikoli fyzickou osobou, fondem nebo daňově transparentním subjektem?", "Is the recipient an ordinary corporate entity (for example GmbH, AG, Ltd. or S.A.), rather than an individual, fund or tax-transparent entity?"],
    ["Pokud si nejsi jistý právní formou příjemce, zvol „Nevím / potřebuji ověřit“. TaxTreat pak osvobození neuzavře, dokud nebude údaj ověřen.", "If you are unsure about the recipient's legal form, select “I don't know / needs verification”. TaxTreat will not finalise the exemption until the fact is verified."],
    ["Podléhá příjemce ve státě své daňové rezidence běžné dani z příjmů právnických osob a není od této daně osvobozen ani v režimu s nulovou sazbou?", "Is the recipient subject to ordinary corporate income tax in its state of tax residence and not exempt from that tax or subject to a zero-rate regime?"],
    ["Jde o faktické daňové postavení příjemce. Pokud jej neznáš, zvol „Nevím / potřebuji ověřit“.", "This asks about the recipient's factual tax status. If you do not know it, select “I don't know / needs verification”."],
    ["Nevím / potřebuji ověřit", "I don't know / needs verification"],
  ]);

  const originals = new WeakMap();

  function language() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
  }

  function translateNode(node) {
    if (!node || node.nodeType !== Node.TEXT_NODE) return;
    const current = node.nodeValue;
    const trimmed = current.trim();
    if (!trimmed) return;
    if (!originals.has(node)) originals.set(node, current);
    const original = originals.get(node);
    const key = original.trim();
    const value = language() === "en" ? (translations.get(key) || key) : key;
    node.nodeValue = original.replace(key, value);
  }

  function applyPayerAndReliefTranslations(root = document.body) {
    if (!root) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(translateNode);
    const ui = document.querySelector("#taxtreat-ui-language");
    if (ui) ui.setAttribute("aria-label", language() === "en" ? "Website language" : "Jazyk webu");
    const report = document.querySelector("#taxtreat-report-language");
    if (report) report.setAttribute("aria-label", language() === "en" ? "Report language" : "Jazyk reportu");
  }

  function ensureUnknownOption(select) {
    if (!select || [...select.options].some((option) => option.value === "unknown")) return;
    const option = document.createElement("option");
    option.value = "unknown";
    option.textContent = "Nevím / potřebuji ověřit";
    select.append(option);
  }

  function polishSection19Questions() {
    const formSelect = document.querySelector('[name="section19_company_form"]');
    const taxSelect = document.querySelector('[name="section19_taxable_company"]');
    ensureUnknownOption(formSelect);
    ensureUnknownOption(taxSelect);

    const formLabel = formSelect?.closest("label");
    const taxLabel = taxSelect?.closest("label");
    if (formLabel?.querySelector("small")) {
      formLabel.querySelector("small").textContent = "Pokud si nejsi jistý právní formou příjemce, zvol „Nevím / potřebuji ověřit“. TaxTreat pak osvobození neuzavře, dokud nebude údaj ověřen.";
    }
    if (taxLabel?.querySelector("small")) {
      taxLabel.querySelector("small").textContent = "Jde o faktické daňové postavení příjemce. Pokud jej neznáš, zvol „Nevím / potřebuji ověřit“.";
    }
  }

  function boot() {
    polishSection19Questions();
    applyPayerAndReliefTranslations();
    document.querySelector("#taxtreat-ui-language")?.addEventListener("change", () => {
      window.setTimeout(() => applyPayerAndReliefTranslations(), 0);
    });
    new MutationObserver((mutations) => {
      polishSection19Questions();
      mutations.forEach((mutation) => mutation.addedNodes.forEach((node) => {
        if (node.nodeType === Node.ELEMENT_NODE) applyPayerAndReliefTranslations(node);
      }));
    }).observe(document.body, { subtree: true, childList: true });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once: true });
  else boot();
})();