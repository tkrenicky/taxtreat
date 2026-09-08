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

    return {
      version: 1,
      targetLocale,
      activeView,
      activeStep,
      fields,
      capturedAt: Date.now(),
    };
  }

  function captureState(targetLocale) {
    const state = buildState(targetLocale);
    pendingLiveState = state;
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (_problem) {
      // Locale switching must still work if session storage is unavailable.
    }
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
    pendingLiveState = state;

    applyState(state);
    refreshDependentFields();
    [0, 60, 180, 500, 1000].forEach((delay) => window.setTimeout(() => applyState(state), delay));
  }

  function scheduleLiveRestore(state) {
    const token = ++liveRestoreToken;
    const applyIfCurrent = () => {
      if (token !== liveRestoreToken || pendingLiveState !== state) return;
      const locale = document.documentElement.lang === "en" ? "en" : "cs";
      if (locale !== state.targetLocale) return;
      applyState(state);
    };

    // Live language switching stays on the same document, so DOMContentLoaded
    // restoration never fires. Reapply after the other language handlers have
    // translated/re-rendered the workspace, while keeping the sessionStorage
    // path for deployments that navigate to another locale route.
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

  document.addEventListener("pointerdown", captureForLanguageControl, true);
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    captureForLanguageControl(event);
  }, true);

  const languageSelect = document.getElementById("taxtreat-ui-language");
  if (languageSelect) {
    languageSelect.addEventListener("change", () => {
      const state = pendingLiveState;
      if (!state) return;
      scheduleLiveRestore(state);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", restoreState, { once: true });
  } else {
    restoreState();
  }
})();
