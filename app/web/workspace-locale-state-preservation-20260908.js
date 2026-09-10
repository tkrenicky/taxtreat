(() => {
  "use strict";

  const STORAGE_KEY = "taxtreat-locale-transition-state-v2";

  function locale() {
    return document.documentElement.lang === "en" || document.querySelector("#taxtreat-ui-language")?.value === "en" ? "en" : "cs";
  }

  function fieldKey(field, index) {
    return {
      form: field.closest("form")?.id || "page",
      name: field.name || null,
      id: field.id || null,
      type: field.type || field.tagName.toLowerCase(),
      index,
      value: field.value,
      checked: "checked" in field ? Boolean(field.checked) : null,
    };
  }

  function captureState(targetLocale) {
    const state = {
      version: 2,
      targetLocale,
      activeView: document.querySelector("[data-view].active")?.dataset.view || null,
      activeStep: document.querySelector(".flow-step.active")?.dataset.step || null,
      fields: [...document.querySelectorAll("input,select,textarea")]
        .filter((field) => field.id !== "taxtreat-ui-language")
        .map(fieldKey),
      capturedAt: Date.now(),
    };
    try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch (_problem) {}
    return state;
  }

  function matchingField(saved) {
    if (saved.id) {
      const byId = document.getElementById(saved.id);
      if (byId) return byId;
    }
    if (!saved.name) return null;
    const root = saved.form !== "page" ? document.getElementById(saved.form) : document;
    const candidates = [...(root || document).querySelectorAll(`[name="${CSS.escape(saved.name)}"]`)];
    if (candidates.length === 1) return candidates[0];
    return candidates.find((field) => field.value === saved.value && (field.type || field.tagName.toLowerCase()) === saved.type)
      || candidates.find((field) => (field.type || field.tagName.toLowerCase()) === saved.type)
      || candidates[0]
      || null;
  }

  function restoreFields(state) {
    for (const saved of state.fields || []) {
      const field = matchingField(saved);
      if (!field) continue;
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

  function refreshDependencies() {
    const activePayer = document.querySelector("#active-payer-select");
    const incomeType = document.querySelector('#workspace-payment [name="income_type"]');
    const holdingMode = document.querySelector('#workspace-payment [name="holding_period_mode"]');
    [activePayer, incomeType, holdingMode].forEach((field) => field?.dispatchEvent(new Event("change", { bubbles: true })));
  }

  function restoreState() {
    let state;
    try { state = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || "null"); } catch (_problem) { state = null; }
    if (!state || state.version !== 2 || state.targetLocale !== locale() || Date.now() - Number(state.capturedAt || 0) > 60000) return;
    try { sessionStorage.removeItem(STORAGE_KEY); } catch (_problem) {}
    const restore = () => { restoreFields(state); restoreNavigation(state); };
    restore();
    [30, 120, 350].forEach((delay) => window.setTimeout(restore, delay));
    window.setTimeout(refreshDependencies, 380);
  }

  function targetUrl(target) {
    const url = new URL(window.location.href);
    if (/\/ui\/(cs|en)(?=\/|$)/.test(url.pathname)) url.pathname = url.pathname.replace(/\/ui\/(cs|en)(?=\/|$)/, `/ui/${target}`);
    else url.pathname = `/ui/${target}`;
    return url.href;
  }

  // Live DOM translation had several independent renderers racing each other.
  // Navigate between canonical locale routes instead; preserve the current flow state.
  document.addEventListener("click", (event) => {
    const button = event.target?.closest?.("#taxtreat-language-controls [data-lang]");
    if (!button) return;
    const target = button.dataset.lang === "en" ? "en" : "cs";
    if (target === locale()) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    captureState(target);
    try { localStorage.setItem("taxtreat-ui-language", target); } catch (_problem) {}
    window.location.assign(targetUrl(target));
  }, true);

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
    const baseCurrency = source === "SK" ? "EUR" : "CZK";
    const currency = String(form.elements.currency?.value || baseCurrency).toUpperCase();
    const needsFx = currency !== baseCurrency;
    field.hidden = !needsFx;
    if (status && !needsFx) status.hidden = true;
    const input = form.elements.exchange_rate_czk_per_unit;
    if (input && !needsFx) {
      input.required = false;
      input.value = "";
    }
  }

  const PAIRS = new Map([
    ["Datum nabytí neznám", "Acquisition date unknown"],
    ["Doplňující údaje o transakci", "Additional transaction facts"],
    ["Doplň údaje, které jsou pro tuto transakci relevantní. Pokud je některý údaj již uložený v profilu příjemce, TaxTreat ho předvyplní.", "Complete the facts relevant to this transaction. Facts already stored in the recipient profile are pre-filled by TaxTreat."],
    ["Přímé držení podílu", "Direct shareholding"],
    ["Příjemce drží podíl přímo.", "The recipient holds the interest directly."],
    ["Uveď podle právního vlastnictví podílu.", "Confirm based on the legal ownership of the interest."],
    ["Datum nabytí podílu (pokud je známé)", "Share acquisition date (if known)"],
    ["Pokud je datum známé, uveď ho. Jinak lze pokračovat bez něj.", "Enter the date if known. Otherwise you can continue without it."],
    ["Předmět licenční platby", "Royalty subject"],
    ["Vyber možnost", "Select an option"]
  ]);
  const REVERSE = new Map(Array.from(PAIRS, ([cs, en]) => [en, cs]));

  function translateVisibleResidue(root = document.body) {
    if (!root) return;
    const en = locale() === "en";
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      if (node.parentElement?.closest("blockquote,.legal-excerpt,pre,code")) return;
      const current = node.nodeValue || "";
      const key = current.trim();
      if (!key) return;
      const replacement = en ? PAIRS.get(key) : REVERSE.get(key);
      if (replacement) node.nodeValue = current.replace(key, replacement);
      if (/sazbu\s+null\.?/i.test(node.nodeValue || "")) {
        node.nodeValue = (node.nodeValue || "").replace(/Vnitrostátní pravidlo stanoví sazbu\s+null\.?/gi, "Vnitrostátní pravidlo pro tento příjem nestanoví číselnou sazbu srážkové daně.");
      }
      if (/rate\s+null\.?/i.test(node.nodeValue || "")) {
        node.nodeValue = (node.nodeValue || "").replace(/The domestic rule sets (?:a )?rate\s+null\.?/gi, "The domestic rule does not impose a numeric withholding-tax rate on this income.");
      }
    });
  }

  function fixPayerDialog() {
    const form = document.querySelector("#payer-form");
    if (!form) return;
    const en = locale() === "en";
    const labels = {
      payer_id: ["IČO *", "Company ID *"], payer_name: ["Název *", "Name *"], payer_vat_id: ["DIČ", "Tax ID"],
      payer_address: ["Sídlo", "Registered office"], payer_legal_form: ["Právní forma", "Legal form"], payer_data_box: ["Datová schránka", "Data box"], payer_established_at: ["Datum vzniku", "Date of incorporation"], payer_country: ["Stát plátce *", "Payer country *"]
    };
    Object.entries(labels).forEach(([name, copy]) => {
      const label = form.elements[name]?.closest("label")?.querySelector(":scope > span");
      if (label) label.textContent = copy[en ? 1 : 0];
    });
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
    const resultText = document.querySelector(".result-hero")?.textContent || "";
    const text = reason.textContent.trim();
    if (/NENÍ PŘEDMĚTEM DANĚ/i.test(resultText) && /^Není předmětem daně\.\s*/i.test(text)) reason.textContent = text.replace(/^Není předmětem daně\.\s*/i, "");
    if (/NOT SUBJECT TO TAX/i.test(resultText) && /^Not subject to tax\.\s*/i.test(text)) reason.textContent = text.replace(/^Not subject to tax\.\s*/i, "");
  }

  function improveMissingFieldError() {
    const error = document.querySelector("#workspace-error");
    if (!error || error.hidden || !/Potřebujeme doplnit|Please complete|missing|required/i.test(error.textContent)) return;
    const cards = [...document.querySelectorAll("#workspace-questions .question-card")];
    const missing = cards.filter((card) => {
      const input = card.querySelector("input,select,textarea");
      return input && !String(input.value || "").trim();
    }).map((card) => card.querySelector("strong")?.textContent?.trim()).filter(Boolean);
    if (!missing.length) return;
    error.textContent = locale() === "en" ? `Please complete: ${missing.join("; ")}.` : `Doplň prosím: ${missing.join("; ")}.`;
  }

  function stabilize() {
    syncActivePayerCountry();
    syncFxVisibility();
    translateVisibleResidue();
    fixPayerDialog();
    dedupeResult();
    improveMissingFieldError();
  }

  let timer = 0;
  function schedule() {
    window.clearTimeout(timer);
    timer = window.setTimeout(stabilize, 20);
  }
  document.addEventListener("change", (event) => {
    if (event.target?.id === "active-payer-select" || event.target?.name === "currency" || event.target?.name === "payer_country") [0, 30, 120].forEach((delay) => window.setTimeout(stabilize, delay));
  }, true);
  document.addEventListener("click", (event) => {
    if (event.target?.closest?.("[data-start-flow],[data-next-step],[data-flow-step],[data-edit-payer],[data-save-payer],.payer-choice,[data-nav]")) [0, 30, 120].forEach((delay) => window.setTimeout(stabilize, delay));
  }, true);
  new MutationObserver(schedule).observe(document.documentElement, { subtree: true, childList: true });

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => { restoreState(); stabilize(); }, { once: true });
  else { restoreState(); stabilize(); }
})();