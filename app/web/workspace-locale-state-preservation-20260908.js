(() => {
  "use strict";

  const STORAGE_KEY = "taxtreat-locale-transition-state-v3";

  function locale() {
    return document.documentElement.lang === "en" ? "en" : "cs";
  }

  function fieldSnapshot(field, index) {
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

  function buildState(targetLocale) {
    const activeView = document.querySelector("[data-view].active")?.dataset.view || null;
    const activeStep = document.querySelector(".flow-step.active")?.dataset.step || null;
    const statusText = document.querySelector("#workspace-result-status")?.textContent || "";
    return {
      version: 3,
      targetLocale,
      activeView,
      activeStep,
      rerunResult:
        activeView === "flow" &&
        activeStep === "4" &&
        !/ČEKÁ NA VÝPOČET|WAITING FOR CALCULATION/i.test(statusText),
      fields: [...document.querySelectorAll("input,select,textarea")]
        .filter((field) => field.id !== "taxtreat-ui-language")
        .map(fieldSnapshot),
      capturedAt: Date.now(),
    };
  }

  function captureState(targetLocale) {
    const state = buildState(targetLocale);
    try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch (_problem) {}
    return state;
  }

  function matchingField(saved) {
    if (saved.id) {
      const byId = document.getElementById(saved.id);
      if (byId) return byId;
    }
    if (!saved.name) return null;
    const root = saved.form && saved.form !== "page" ? document.getElementById(saved.form) : document;
    const candidates = [...(root || document).querySelectorAll(`[name="${CSS.escape(saved.name)}"]`)];
    if (candidates.length === 1) return candidates[0];
    const sameType = candidates.filter(
      (item) => (item.type || item.tagName.toLowerCase()) === saved.type,
    );
    return sameType.find((item) => item.value === saved.value) || sameType[0] || candidates[0] || null;
  }

  function restoreFields(state) {
    for (const saved of state.fields || []) {
      const field = matchingField(saved);
      if (!field || field.id === "taxtreat-ui-language") continue;
      if (field.type === "checkbox" || field.type === "radio") {
        field.checked = Boolean(saved.checked);
      } else if (field.tagName === "SELECT") {
        if ([...field.options].some((option) => option.value === saved.value)) field.value = saved.value;
      } else {
        field.value = saved.value ?? "";
      }
    }
  }

  function restoreNavigation(state) {
    if (state.activeView) {
      document.querySelectorAll("[data-view]").forEach((view) => {
        view.classList.toggle("active", view.dataset.view === state.activeView);
      });
      document.querySelectorAll("[data-nav]").forEach((button) => {
        button.classList.toggle(
          "active",
          state.activeView !== "flow" && button.dataset.nav === state.activeView,
        );
      });
    }
    if (state.activeView === "flow" && state.activeStep) {
      const activeStep = Number(state.activeStep);
      document.querySelectorAll(".flow-step").forEach((step) => {
        step.classList.toggle("active", step.dataset.step === state.activeStep);
      });
      document.querySelectorAll("[data-flow-step]").forEach((button) => {
        button.classList.toggle("active", Number(button.dataset.flowStep) <= activeStep);
      });
    }
  }

  function dispatchChange(field) {
    if (field) field.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function refreshDependencies() {
    dispatchChange(document.querySelector("#active-payer-select"));
    dispatchChange(document.querySelector('#workspace-payment [name="income_type"]'));
    dispatchChange(document.querySelector('#workspace-payment [name="holding_period_mode"]'));
    dispatchChange(document.querySelector('#workspace-payment [name="currency"]'));
  }

  function rerunResult(state) {
    if (!state.rerunResult) return;
    const form = document.querySelector("#workspace-payment");
    const submit = document.querySelector("#workspace-submit");
    if (!form || !submit) return;
    form.requestSubmit(submit);
  }

  function clearState() {
    try { sessionStorage.removeItem(STORAGE_KEY); } catch (_problem) {}
  }

  function restoreState() {
    let state = null;
    try { state = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || "null"); } catch (_problem) {}
    if (
      !state ||
      state.version !== 3 ||
      state.targetLocale !== locale() ||
      Date.now() - Number(state.capturedAt || 0) > 60000
    ) {
      return;
    }

    // First restore the persisted payer/profile context and ordinary form fields.
    restoreFields(state);
    restoreNavigation(state);

    // Re-render country/income dependent controls, then restore values that may
    // have been recreated by those renderers.
    window.setTimeout(() => {
      refreshDependencies();
      restoreFields(state);
      restoreNavigation(state);
    }, 50);

    window.setTimeout(() => {
      restoreFields(state);
      refreshDependencies();
      restoreFields(state);
      restoreNavigation(state);
    }, 160);

    // Step 4 contains computed DOM, not persistent state. Re-run the calculation
    // in the canonical target locale instead of trying to repaint stale result DOM.
    window.setTimeout(() => {
      restoreFields(state);
      refreshDependencies();
      restoreFields(state);
      if (state.rerunResult) rerunResult(state);
      else restoreNavigation(state);
      clearState();
    }, 320);
  }

  function captureForLanguageControl(event) {
    const button = event.target?.closest?.("#taxtreat-language-controls [data-lang]");
    if (!button) return;
    const target = button.dataset.lang === "en" ? "en" : "cs";
    if (target !== locale()) captureState(target);
  }

  // The canonical locale router listens on click and navigates to /ui/cs or /ui/en.
  // Capture state earlier on pointer/keyboard intent so the router can navigate
  // without any live DOM translation race.
  document.addEventListener("pointerdown", captureForLanguageControl, true);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") captureForLanguageControl(event);
  }, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", restoreState, { once: true });
  } else {
    restoreState();
  }
})();

(() => {
  "use strict";

  function language() {
    return document.documentElement.lang === "en" ? "en" : "cs";
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
    const source =
      window.TaxTreatWorkspaceSourceCountry?.getActiveCode?.() ||
      document.body.dataset.sourceCountry ||
      "CZ";
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
      payer_country: ["Stát plátce *", "Payer country *"],
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
    if (/Není předmětem daně/i.test(hero) && /^Není předmětem daně[.:]?\s*/i.test(text)) {
      reason.textContent = text.replace(/^Není předmětem daně[.:]?\s*/i, "");
    }
    if (/Not subject to tax/i.test(hero) && /^Not subject to tax[.:]?\s*/i.test(text)) {
      reason.textContent = text.replace(/^Not subject to tax[.:]?\s*/i, "");
    }
  }

  function nameMissingFacts() {
    const reason = document.querySelector("#workspace-reason");
    const cards = [...document.querySelectorAll("#workspace-questions .question-card")];
    if (!reason || !cards.length) return;
    const missing = cards
      .filter((card) => {
        const input = card.querySelector("input,select,textarea");
        return input && !String(input.value || "").trim();
      })
      .map((card) => card.querySelector("strong")?.textContent?.trim())
      .filter(Boolean);
    if (!missing.length) return;
    const generic =
      /Additional factual condition requires completion or review|Zadané údaje zatím neumožňují|cannot be finalized|nelze uzavřít/i;
    if (!generic.test(reason.textContent || "")) return;
    reason.textContent =
      language() === "en"
        ? `Missing information: ${missing.join("; ")}.`
        : `Chybí doplnit: ${missing.join("; ")}.`;
  }

  function stabilize() {
    syncActivePayerCountry();
    syncFxVisibility();
    fixPayerDialog();
    dedupeResult();
    nameMissingFacts();
  }

  let timer = 0;
  new MutationObserver(() => {
    window.clearTimeout(timer);
    timer = window.setTimeout(stabilize, 30);
  }).observe(document.documentElement, { subtree: true, childList: true });

  document.addEventListener(
    "change",
    (event) => {
      if (
        event.target?.id === "active-payer-select" ||
        event.target?.name === "currency" ||
        event.target?.name === "payer_country"
      ) {
        [0, 40, 150].forEach((delay) => window.setTimeout(stabilize, delay));
      }
    },
    true,
  );

  document.addEventListener(
    "click",
    (event) => {
      if (
        event.target?.closest?.(
          "[data-nav],[data-flow-step],[data-next-step],[data-start-flow],[data-edit-payer],[data-save-payer],.payer-choice",
        )
      ) {
        [0, 40, 150].forEach((delay) => window.setTimeout(stabilize, delay));
      }
    },
    true,
  );

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", stabilize, { once: true });
  } else {
    stabilize();
  }
})();
