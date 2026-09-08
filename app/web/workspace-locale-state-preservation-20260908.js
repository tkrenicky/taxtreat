(() => {
  "use strict";

  const STORAGE_KEY = "taxtreat-locale-transition-state-v1";

  function fieldKey(field, index) {
    const form = field.closest("form")?.id || "page";
    const name = field.name || field.id || `field-${index}`;
    return `${form}|${name}|${field.type || field.tagName}|${index}`;
  }

  function captureState(targetLocale) {
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

    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify({
        version: 1,
        targetLocale,
        activeView,
        activeStep,
        fields,
        capturedAt: Date.now(),
      }));
    } catch (_problem) {
      // Locale switching must still work if session storage is unavailable.
    }
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
      if (state.activeView !== "flow") {
        document.querySelectorAll("[data-nav]").forEach((button) => {
          button.classList.toggle("active", button.dataset.nav === state.activeView);
        });
      }
    }

    if (state.activeView === "flow" && state.activeStep) {
      document.querySelectorAll(".flow-step").forEach((step) => {
        step.classList.toggle("active", step.dataset.step === state.activeStep);
      });
      document.querySelectorAll("[data-flow-step]").forEach((button) => {
        button.classList.toggle("active", button.dataset.flowStep === state.activeStep);
      });
    }
  }

  function restoreState() {
    let state = null;
    try {
      state = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || "null");
    } catch (_problem) {
      state = null;
    }
    if (!state || state.version !== 1) return;

    const locale = document.documentElement.lang === "en" ? "en" : "cs";
    if (state.targetLocale !== locale || Date.now() - Number(state.capturedAt || 0) > 30000) return;

    try { sessionStorage.removeItem(STORAGE_KEY); } catch (_problem) {}

    const apply = () => {
      restoreFields(state.fields);
      restoreNavigation(state);
    };

    apply();

    const incomeType = document.querySelector('#workspace-payment [name="income_type"]');
    const holdingMode = document.querySelector('#workspace-payment [name="holding_period_mode"]');
    if (incomeType) incomeType.dispatchEvent(new Event("change", { bubbles: true }));
    if (holdingMode) holdingMode.dispatchEvent(new Event("change", { bubbles: true }));

    [0, 60, 180, 500].forEach((delay) => window.setTimeout(apply, delay));
  }

  function captureForLanguageControl(event) {
    const button = event.target?.closest?.("#taxtreat-language-controls [data-lang]");
    if (!button) return;
    const target = button.dataset.lang === "en" ? "en" : "cs";
    const current = document.documentElement.lang === "en" ? "en" : "cs";
    if (target !== current) captureState(target);
  }

  document.addEventListener("pointerdown", captureForLanguageControl, true);
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    captureForLanguageControl(event);
  }, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", restoreState, { once: true });
  } else {
    restoreState();
  }
})();
