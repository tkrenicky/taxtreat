(() => {
  "use strict";

  const pairs = [
    ["PLÁTCE", "PAYER"],
    ["Přidat plátce", "Add payer"],
    ["Upravit plátce", "Edit payer"],
    ["Základní údaje plátce", "Payer basic details"],
    ["Stát plátce *", "Payer country *"],
    ["Česká republika", "Czech Republic"],
    ["Slovensko", "Slovakia"],
    ["IČO *", "Company ID *"],
    ["IČO", "Company ID"],
    ["Název *", "Name *"],
    ["Název", "Name"],
    ["DIČ", "Tax ID"],
    ["Sídlo", "Registered office"],
    ["Právní forma", "Legal form"],
    ["Datová schránka", "Data box"],
    ["Datum vzniku", "Date of incorporation"],
    ["Načíst z ARES", "Retrieve from ARES"],
    ["Načítám údaje z ARES…", "Retrieving data from ARES…"],
    ["Po zadání 8 číslic TaxTreat načte identifikační údaje z ARES.", "After entering 8 digits, TaxTreat will retrieve identification details from ARES."],
    ["Pro slovenského plátce se údaje z českého registru ARES nenačítají; identifikační údaje vyplň ručně.", "For a Slovak payer, data are not retrieved from the Czech ARES register; enter the identification details manually."],
    ["Údaje byly načteny z ARES. Před uložením je můžeš upravit.", "The data were retrieved from ARES. You can edit them before saving."],
    ["Údaje se z ARES nepodařilo načíst. Pole můžeš vyplnit ručně.", "The data could not be retrieved from ARES. You can complete the fields manually."],
    ["Zrušit", "Cancel"],
    ["Uložit", "Save"],
    ["Uložit změny", "Save changes"],
    ["Vytvořit plátce", "Create payer"],
    ["Zavřít", "Close"],
    ["Povinný údaj", "Required field"],
    ["Označuje povinný údaj.", "Required field."],
  ];

  const csToEn = new Map(pairs);
  const enToCs = new Map(pairs.map(([cs, en]) => [en, cs]));
  const originalText = new WeakMap();
  const originalAttr = new WeakMap();

  function language() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
  }

  function translateLiteral(value, toEnglish) {
    const key = String(value || "").trim();
    const map = toEnglish ? csToEn : enToCs;
    return map.get(key) || key;
  }

  function translateTextNode(node, toEnglish) {
    if (!node?.nodeValue?.trim()) return;
    if (!originalText.has(node)) originalText.set(node, node.nodeValue);
    const stored = originalText.get(node);
    const trimmed = stored.trim();
    let source = trimmed;
    if (!toEnglish && csToEn.has(trimmed)) source = csToEn.get(trimmed);
    const translated = toEnglish ? (csToEn.get(trimmed) || trimmed) : (enToCs.get(source) || trimmed);
    node.nodeValue = stored.replace(trimmed, translated);
  }

  function translateAttributes(element, toEnglish) {
    ["placeholder", "aria-label", "title"].forEach((name) => {
      if (!element.hasAttribute?.(name)) return;
      let attrs = originalAttr.get(element);
      if (!attrs) { attrs = {}; originalAttr.set(element, attrs); }
      if (!(name in attrs)) attrs[name] = element.getAttribute(name);
      const original = attrs[name];
      let translated = original;
      if (toEnglish) {
        translated = translateLiteral(original, true)
          .replace(/^např\. CZ12345678$/i, "e.g. CZ12345678")
          .replace(/^např\. SK2020000000$/i, "e.g. SK2020000000");
      }
      element.setAttribute(name, translated);
    });
  }

  function refreshDialog() {
    const dialog = document.querySelector("#payer-dialog");
    if (!dialog) return;
    const toEnglish = language() === "en";
    const walker = document.createTreeWalker(dialog, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => translateTextNode(node, toEnglish));
    [dialog, ...dialog.querySelectorAll("[placeholder],[aria-label],[title]")].forEach((element) => translateAttributes(element, toEnglish));

    const country = dialog.querySelector('[name="payer_country"]');
    if (country) {
      [...country.options].forEach((option) => {
        if (option.value === "CZ") option.textContent = toEnglish ? "Czech Republic" : "Česká republika";
        if (option.value === "SK") option.textContent = toEnglish ? "Slovakia" : "Slovensko";
      });
    }

    const status = dialog.querySelector("#ares-lookup-status");
    if (status) {
      const isSk = country?.value === "SK";
      status.textContent = toEnglish
        ? (isSk
          ? "For a Slovak payer, data are not retrieved from the Czech ARES register; enter the identification details manually."
          : "After entering 8 digits, TaxTreat will retrieve identification details from ARES.")
        : (isSk
          ? "Pro slovenského plátce se údaje z českého registru ARES nenačítají; identifikační údaje vyplň ručně."
          : "Po zadání 8 číslic TaxTreat načte identifikační údaje z ARES.");
    }
  }

  function boot() {
    refreshDialog();
    document.addEventListener("click", (event) => {
      if (event.target?.closest?.("[data-create-payer], [data-edit-payer], #payer-dialog")) window.setTimeout(refreshDialog, 0);
    }, true);
    document.addEventListener("change", (event) => {
      if (event.target?.id === "taxtreat-ui-language" || event.target?.name === "payer_country") window.setTimeout(refreshDialog, 0);
    }, true);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once:true });
  else boot();
})();
