(() => {
  "use strict";

  const STORAGE_KEY = "taxtreat-locale-transition-state-v1";
  let pendingLiveState = null;
  let liveRestoreToken = 0;

  function fieldKey(field, index) {
    const form = field.closest("form")?.id || "page";
    const name = field.name || field.id || `field-${index}`;
    return `${form}|${name}|${field.type || field.tagName}|${index}`;
  }

  function buildState(targetLocale) {
    const activeView = document.querySelector("[data-view].active")?.dataset.view || null;
    const activeStep = document.querySelector(".flow-step.active")?.dataset.step || null;
    const fields = [...document.querySelectorAll("input, select, textarea")]
      .filter((field) => field.id !== "taxtreat-ui-language")
      .map((field, index) => ({
        key: fieldKey(field, index),
        form: field.closest("form")?.id || "page",
        name: field.name || null,
        id: field.id || null,
        type: field.type || field.tagName.toLowerCase(),
        index,
        value: field.value,
        checked: "checked" in field ? Boolean(field.checked) : null,
      }));

    return { version: 1, targetLocale, activeView, activeStep, fields, capturedAt: Date.now() };
  }

  function captureState(targetLocale) {
    const state = buildState(targetLocale);
    pendingLiveState = state;
    try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch (_problem) {}
    return state;
  }

  function matchingField(saved) {
    if (saved.id) {
      const byId = document.getElementById(saved.id);
      if (byId) return byId;
    }
    if (saved.name) {
      const root = saved.form && saved.form !== "page" ? document.getElementById(saved.form) : document;
      const candidates = [...(root || document).querySelectorAll(`[name="${CSS.escape(saved.name)}"]`)];
      if (candidates.length === 1) return candidates[0];
      if (candidates.length > 1) {
        const sameType = candidates.filter((item) => (item.type || item.tagName.toLowerCase()) === saved.type);
        const checkedMatch = sameType.find((item) => item.value === saved.value);
        if (checkedMatch) return checkedMatch;
        return sameType[0] || candidates[0];
      }
    }
    return null;
  }

  function restoreFields(savedFields) {
    for (const saved of savedFields || []) {
      const field = matchingField(saved);
      if (!field || field.id === "taxtreat-ui-language") continue;
      if (field.type === "checkbox" || field.type === "radio") field.checked = Boolean(saved.checked);
      else if (field.tagName === "SELECT") {
        if ([...field.options].some((option) => option.value === saved.value)) field.value = saved.value;
      } else field.value = saved.value ?? "";
    }
  }

  function restoreNavigation(state) {
    if (state.activeView) {
      document.querySelectorAll("[data-view]").forEach((view) => view.classList.toggle("active", view.dataset.view === state.activeView));
      document.querySelectorAll("[data-nav]").forEach((button) => button.classList.toggle("active", state.activeView !== "flow" && button.dataset.nav === state.activeView));
    }
    if (state.activeView === "flow" && state.activeStep) {
      const activeStep = Number(state.activeStep);
      document.querySelectorAll(".flow-step").forEach((step) => step.classList.toggle("active", step.dataset.step === state.activeStep));
      document.querySelectorAll("[data-flow-step]").forEach((button) => button.classList.toggle("active", Number(button.dataset.flowStep) <= activeStep));
    }
  }

  function applyState(state) {
    if (!state || state.version !== 1) return false;
    restoreFields(state.fields);
    restoreNavigation(state);
    return true;
  }

  function refreshDependentFields() {
    const incomeType = document.querySelector('#workspace-payment [name="income_type"]');
    const holdingMode = document.querySelector('#workspace-payment [name="holding_period_mode"]');
    if (incomeType) incomeType.dispatchEvent(new Event("change", { bubbles: true }));
    if (holdingMode) holdingMode.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function clearPendingRestore() {
    if (!pendingLiveState) return;
    liveRestoreToken += 1;
    pendingLiveState = null;
    try { sessionStorage.removeItem(STORAGE_KEY); } catch (_problem) {}
  }

  function restoreState() {
    let state = null;
    try { state = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || "null"); } catch (_problem) { state = null; }
    if (!state || state.version !== 1) return;
    const locale = document.documentElement.lang === "en" ? "en" : "cs";
    if (state.targetLocale !== locale || Date.now() - Number(state.capturedAt || 0) > 30000) return;
    try { sessionStorage.removeItem(STORAGE_KEY); } catch (_problem) {}
    pendingLiveState = state;
    applyState(state);
    refreshDependentFields();
    scheduleLiveRestore(state);
  }

  function scheduleLiveRestore(state) {
    const token = ++liveRestoreToken;
    const applyIfCurrent = () => {
      if (token !== liveRestoreToken || pendingLiveState !== state) return;
      const locale = document.documentElement.lang === "en" ? "en" : "cs";
      if (locale !== state.targetLocale) return;
      applyState(state);
    };
    [0, 25, 75, 180, 400, 900].forEach((delay) => window.setTimeout(applyIfCurrent, delay));
    window.setTimeout(() => {
      if (token === liveRestoreToken && pendingLiveState === state) pendingLiveState = null;
    }, 1200);
  }

  function captureForLanguageControl(event) {
    const button = event.target?.closest?.("#taxtreat-language-controls [data-lang]");
    if (!button) return;
    const target = button.dataset.lang === "en" ? "en" : "cs";
    const current = document.documentElement.lang === "en" ? "en" : "cs";
    if (target !== current) {
      const state = captureState(target);
      scheduleLiveRestore(state);
    }
  }

  function cancelStaleRestoreForNavigation(event) {
    const navigation = event.target?.closest?.("[data-nav],[data-flow-step],[data-next-step],[data-start-flow],#workspace-submit");
    if (!navigation || !pendingLiveState) return;
    clearPendingRestore();
  }

  function isEditableField(target) {
    return target instanceof HTMLInputElement || target instanceof HTMLSelectElement || target instanceof HTMLTextAreaElement;
  }

  function cancelStaleRestoreForDirectUserIntent(event) {
    if (!pendingLiveState || !isEditableField(event.target)) return;
    if (event.target.id === "taxtreat-ui-language") return;
    clearPendingRestore();
  }

  function cancelStaleRestoreForContextChange(event) {
    if (!pendingLiveState) return;
    const field = event.target;
    if (!(field instanceof HTMLSelectElement)) return;
    if (field.id === "active-payer-select" || field.id === "active-source-country" || field.name === "payer_country") clearPendingRestore();
  }

  document.addEventListener("pointerdown", (event) => {
    captureForLanguageControl(event);
    cancelStaleRestoreForDirectUserIntent(event);
  }, true);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") captureForLanguageControl(event);
    if (isEditableField(event.target) && event.target.id !== "taxtreat-ui-language") cancelStaleRestoreForDirectUserIntent(event);
  }, true);
  document.addEventListener("click", cancelStaleRestoreForNavigation, true);
  document.addEventListener("change", cancelStaleRestoreForContextChange, true);

  const languageSelect = document.getElementById("taxtreat-ui-language");
  if (languageSelect) {
    languageSelect.addEventListener("change", () => {
      const state = pendingLiveState;
      if (!state) return;
      scheduleLiveRestore(state);
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", restoreState, { once: true });
  else restoreState();
})();

(() => {
  "use strict";

  function language() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || (document.documentElement.lang === "en" ? "en" : "cs");
  }

  function syncActivePayerCountry() {
    const select = document.querySelector("#active-payer-select");
    const api = window.TaxTreatWorkspaceSourceCountry;
    if (!select || !api) return;
    const code = api.getPayerCountry?.(select.value) || "CZ";
    if (api.getActiveCode?.() !== code) api.setActiveCode?.(code);
  }

  function syncFxVisibility() {
    const form = document.querySelector("#workspace-payment");
    const field = document.querySelector("#workspace-exchange-rate-field");
    const status = document.querySelector("#workspace-fx-status");
    if (!form || !field) return;
    const source = window.TaxTreatWorkspaceSourceCountry?.getActiveCode?.() || document.body.dataset.sourceCountry || "CZ";
    const baseCurrency = String(source).toUpperCase() === "SK" ? "EUR" : "CZK";
    const selectedCurrency = String(form.elements.currency?.value || baseCurrency).toUpperCase();
    const needsFx = selectedCurrency !== baseCurrency;
    field.hidden = !needsFx;
    if (status && !needsFx) status.hidden = true;
    const input = form.elements.exchange_rate_czk_per_unit;
    if (input && !needsFx) {
      input.required = false;
      input.value = "";
    }
  }

  const CS_EN = new Map([
    ["Datum nabytí neznám", "Acquisition date unknown"],
    ["Vyber odpověď", "Select an answer"],
    ["Vyber možnost", "Select an option"],
    ["Doplňující údaje pro možné vnitrostátní osvobození", "Additional facts for potential domestic exemption"],
    ["Podíl, přímé držení, dobu držby, skutečné vlastnictví a vazbu ke stálé provozovně už TaxTreat používá z odpovědí výše.", "TaxTreat already uses the ownership percentage, direct holding, holding period, beneficial ownership and permanent-establishment connection from the answers above."],
    ["Je příjemce běžnou obchodní společností (např. GmbH, AG, Ltd. nebo S.A.), nikoli fyzickou osobou, fondem nebo daňově transparentním subjektem?", "Is the recipient an ordinary commercial company (e.g. GmbH, AG, Ltd. or S.A.), rather than an individual, fund or tax-transparent entity?"],
    ["Pokud si nejsi jistý právní formou příjemce, zvol raději „Ne“ nebo údaj ověř v korporátních podkladech.", "If you are unsure about the recipient’s legal form, select “No” or verify it in the corporate documentation."],
    ["Podléhá příjemce ve státě své daňové rezidence běžné dani z příjmů právnických osob a není od této daně osvobozen ani v režimu s nulovou sazbou?", "Is the recipient subject to ordinary corporate income tax in its state of tax residence and neither exempt from that tax nor subject to a zero-rate regime?"],
    ["Jde o faktické daňové postavení příjemce, nikoli o posouzení českého § 19.", "This concerns the recipient’s actual tax status, not the assessment under Section 19 of the Czech Income Taxes Act."],
    ["Pro tento informační výstup nebyl vrácen konkrétní odkaz na právní zdroj.", "No specific legal-source link was returned for this information output."]
  ]);
  const EN_CS = new Map(Array.from(CS_EN, ([cs, en]) => [en, cs]));

  function translateResidue() {
    const en = language() === "en";
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
      if (node.parentElement?.closest("blockquote,.legal-excerpt,pre,code")) continue;
      const current = node.nodeValue || "";
      const key = current.trim();
      if (!key) continue;
      const replacement = en ? CS_EN.get(key) : EN_CS.get(key);
      if (replacement) node.nodeValue = current.replace(key, replacement);
      if (/Vnitrostátní pravidlo stanoví sazbu\s+null\.?/i.test(node.nodeValue || "")) {
        node.nodeValue = (node.nodeValue || "").replace(/Vnitrostátní pravidlo stanoví sazbu\s+null\.?/gi, "Vnitrostátní pravidlo pro tento příjem nestanoví číselnou sazbu srážkové daně.");
      }
      if (/The domestic rule (?:sets|provides) (?:a )?rate\s+null\.?/i.test(node.nodeValue || "")) {
        node.nodeValue = (node.nodeValue || "").replace(/The domestic rule (?:sets|provides) (?:a )?rate\s+null\.?/gi, "The domestic rule does not impose a numeric withholding-tax rate on this income.");
      }
    }
  }

  function fixPayerDialog() {
    const form = document.querySelector("#payer-form");
    if (!form) return;
    const en = language() === "en";
    const labels = {
      payer_id: ["IČO *", "Company ID *"],
      payer_name: ["Název *", "Name *"],
      payer_vat_id: ["DIČ", "Tax ID"],
      payer_address: ["Sídlo", "Registered office"],
      payer_legal_form: ["Právní forma", "Legal form"],
      payer_data_box: ["Datová schránka", "Data box"],
      payer_established_at: ["Datum vzniku", "Date of incorporation"],
      payer_country: ["Stát plátce *", "Payer country *"]
    };
    for (const [name, copy] of Object.entries(labels)) {
      const label = form.elements[name]?.closest("label")?.querySelector(":scope > span");
      if (label) label.textContent = copy[en ? 1 : 0];
    }
    const title = document.querySelector("#payer-dialog-title");
    if (title) title.textContent = en ? "Edit payer" : "Upravit plátce";
    const cancel = form.querySelector("[data-close-payer]");
    const save = form.querySelector("[data-save-payer]");
    if (cancel) cancel.textContent = en ? "Cancel" : "Zrušit";
    if (save) save.textContent = en ? "Save changes" : "Uložit změny";
  }

  function dedupeResult() {
    const reason = document.querySelector("#workspace-reason");
    if (!reason) return;
    const hero = document.querySelector(".result-hero")?.textContent || "";
    const text = reason.textContent.trim();
    if (/Není předmětem daně/i.test(hero) && /^Není předmětem daně[.:]?\s*/i.test(text)) reason.textContent = text.replace(/^Není předmětem daně[.:]?\s*/i, "");
    if (/Not subject to tax/i.test(hero) && /^Not subject to tax[.:]?\s*/i.test(text)) reason.textContent = text.replace(/^Not subject to tax[.:]?\s*/i, "");
  }

  function nameMissingFacts() {
    const reason = document.querySelector("#workspace-reason");
    const cards = [...document.querySelectorAll("#workspace-questions .question-card")];
    if (!reason || !cards.length) return;
    const missing = cards.filter((card) => {
      const input = card.querySelector("input,select,textarea");
      return input && !String(input.value || "").trim();
    }).map((card) => card.querySelector("strong")?.textContent?.trim()).filter(Boolean);
    if (!missing.length) return;
    const generic = /Additional factual condition requires completion or review|Zadané údaje zatím neumožňují|cannot be finalized|nelze uzavřít/i;
    if (!generic.test(reason.textContent || "")) return;
    reason.textContent = language() === "en"
      ? `Missing information: ${missing.join("; ")}.`
      : `Chybí doplnit: ${missing.join("; ")}.`;
  }

  function stabilize() {
    syncActivePayerCountry();
    syncFxVisibility();
    translateResidue();
    fixPayerDialog();
    dedupeResult();
    nameMissingFacts();
  }

  let mutationTimer = 0;
  new MutationObserver(() => {
    window.clearTimeout(mutationTimer);
    mutationTimer = window.setTimeout(stabilize, 30);
  }).observe(document.documentElement, { subtree: true, childList: true });

  document.addEventListener("change", (event) => {
    if (event.target?.id === "taxtreat-ui-language" || event.target?.id === "active-payer-select" || event.target?.name === "currency" || event.target?.name === "payer_country") {
      [0, 40, 150, 500, 1000, 1300].forEach((delay) => window.setTimeout(stabilize, delay));
    }
  }, true);
  document.addEventListener("click", (event) => {
    if (event.target?.closest?.("#taxtreat-language-controls,[data-nav],[data-flow-step],[data-next-step],[data-start-flow],[data-edit-payer],[data-save-payer],.payer-choice")) {
      [0, 40, 150, 500, 1000, 1300].forEach((delay) => window.setTimeout(stabilize, delay));
    }
  }, true);

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", stabilize, { once: true });
  else stabilize();
})();