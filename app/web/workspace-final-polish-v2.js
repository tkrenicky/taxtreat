(() => {
  "use strict";

  const CS_NOTICE = '<strong>Informační nástroj:</strong> TaxTreat zobrazuje automatizované informace z právních zdrojů a zadaných údajů; neposkytuje individuální právní ani daňové poradenství ani doporučení.';
  const EN_NOTICE = '<strong>Information tool:</strong> TaxTreat displays automated information derived from legal sources and the facts entered by the user; it does not provide individual legal or tax advice or recommendations.';

  const translations = new Map([
    ["Jazyk", "Language"], ["Jazyk webu", "Website language"], ["Jazyk reportu", "Report language"],
    ["Stát plátce *", "Payer country *"], ["Česká republika", "Czech Republic"], ["Slovensko", "Slovakia"],
    ["Načíst z ARES", "Retrieve from ARES"], ["Načítám údaje z ARES…", "Retrieving data from ARES…"],
    ["Údaje byly načteny z ARES. Před uložením je můžeš upravit.", "The data were retrieved from ARES. You can edit them before saving."],
    ["Údaje se z ARES nepodařilo načíst. Pole můžeš vyplnit ručně.", "The data could not be retrieved from ARES. You can complete the fields manually."],
    ["IČO *", "Company ID *"], ["IČO", "Company ID"], ["Název *", "Name *"], ["DIČ", "Tax ID"], ["Sídlo", "Registered office"], ["Právní forma", "Legal form"], ["Datová schránka", "Data box"], ["Datum vzniku", "Date of incorporation"],
    ["Zrušit", "Cancel"], ["Uložit změny", "Save changes"], ["PŘÍJEMCE", "RECIPIENT"], ["PLÁTCE", "PAYER"],
    ["Ještě dva údaje pro možné osvobození podle § 19 ZDP", "Two more facts for the potential Section 19 exemption"],
    ["Nevím / potřebuji ověřit", "I don't know / needs verification"],
    ["Potvrzení o daňovém rezidentství", "Tax residence certificate"], ["Datum vystavení *", "Issue date *"], ["Platnost do *", "Valid until *"], ["Teď ne", "Not now"], ["Uložit evidenci", "Save record"],
    ["Základní údaje", "Basic details"], ["Daňová rezidence", "Tax residence"], ["Typ subjektu", "Entity type"], ["Podíl na plátci", "Ownership in payer"], ["Datum nabytí podílu", "Share acquisition date"],
    ["Zatím nebylo bezpečně uloženo.", "It has not yet been securely recorded."], ["Spusť první výpočet pro tohoto příjemce.", "Start the first calculation for this recipient."],
    ["Zásady ochrany dat", "Data protection"], ["Podmínky použití", "Terms of use"],
  ]);

  const originals = new WeakMap();
  let refreshScheduled = false;

  function language() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
  }

  function translateValue(value) {
    const key = String(value || "").trim();
    if (language() !== "en") return key;
    return (translations.get(key) || key)
      .replace(/^Česká republika · IČO /, "Czech Republic · Company ID ")
      .replace(/^Slovensko · IČO /, "Slovakia · Company ID ")
      .replace(/ · DIČ /g, " · Tax ID ");
  }

  function translateNode(node) {
    if (!node || node.nodeType !== Node.TEXT_NODE) return;
    const current = node.nodeValue;
    const trimmed = current.trim();
    if (!trimmed) return;
    if (!originals.has(node)) originals.set(node, current);
    const original = originals.get(node);
    const key = original.trim();
    const translated = language() === "en" ? translateValue(key) : key;
    const next = original.replace(key, translated);
    if (node.nodeValue !== next) node.nodeValue = next;
  }

  function translateRoot(root) {
    if (!root) return;
    if (root.nodeType === Node.TEXT_NODE) {
      translateNode(root);
      return;
    }
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) translateNode(walker.currentNode);
  }

  function renderNotice() {
    const notice = document.querySelector(".information-only-note");
    if (!notice) return;
    const next = language() === "en" ? EN_NOTICE : CS_NOTICE;
    if (notice.innerHTML !== next) notice.innerHTML = next;
  }

  function ensureUnknownOptions() {
    ["section19_company_form", "section19_taxable_company"].forEach((name) => {
      const select = document.querySelector(`[name="${name}"]`);
      if (!select || [...select.options].some((option) => option.value === "unknown")) return;
      const option = document.createElement("option");
      option.value = "unknown";
      option.textContent = language() === "en" ? "I don't know / needs verification" : "Nevím / potřebuji ověřit";
      select.append(option);
    });
  }

  function compactLanguageControl() {
    const select = document.querySelector("#taxtreat-ui-language");
    const holder = document.querySelector("#taxtreat-language-controls");
    if (!select || !holder || holder.querySelector(".tt-lang-mini")) return;
    holder.querySelector("span")?.remove();
    select.style.position = "absolute";
    select.style.opacity = "0";
    select.style.pointerEvents = "none";
    select.style.width = "1px";
    select.style.height = "1px";
    const mini = document.createElement("div");
    mini.className = "tt-lang-mini";
    mini.style.cssText = "display:flex;align-items:center;gap:4px;font-size:12px;font-weight:700;white-space:nowrap";
    ["cs", "en"].forEach((lang, index) => {
      if (index) mini.append(document.createTextNode("·"));
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.lang = lang;
      button.textContent = lang.toUpperCase();
      button.style.cssText = "border:0;background:transparent;padding:2px 3px;cursor:pointer;font:inherit;opacity:.5";
      button.addEventListener("click", () => {
        select.value = lang;
        select.dispatchEvent(new Event("change", { bubbles: true }));
      });
      mini.append(button);
    });
    holder.append(mini);
  }

  function syncMini() {
    document.querySelectorAll(".tt-lang-mini button").forEach((button) => {
      const active = button.dataset.lang === language();
      button.style.opacity = active ? "1" : ".45";
      button.style.textDecoration = active ? "underline" : "none";
    });
  }

  function apply(root = document.body) {
    ensureUnknownOptions();
    renderNotice();
    compactLanguageControl();
    translateRoot(root);
    syncMini();
  }

  function scheduleRefresh() {
    if (refreshScheduled) return;
    refreshScheduled = true;
    requestAnimationFrame(() => {
      refreshScheduled = false;
      apply(document.body);
    });
  }

  function boot() {
    apply(document.body);
    document.querySelector("#taxtreat-ui-language")?.addEventListener("change", () => apply(document.body));
    // Do not observe DOM mutations here. The main i18n layer already handles newly
    // inserted UI. A second observer that rewrites innerHTML can feed back into the
    // first observer and freeze the page. Refresh this supplemental polish only
    // after user-driven UI transitions.
    document.addEventListener("click", scheduleRefresh, true);
    document.addEventListener("change", scheduleRefresh, true);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once: true });
  else boot();
})();
