(() => {
  "use strict";

  const FIELD_NAMES = ["section19_company_form", "section19_taxable_company"];

  function paymentForm() {
    return document.querySelector("#workspace-payment");
  }

  function isCzechDividend(form) {
    const source = String(document.body.dataset.sourceCountry || "CZ").toUpperCase();
    return source === "CZ" && form?.elements?.income_type?.value === "dividend";
  }

  function fields(form) {
    return FIELD_NAMES.map((name) => form?.elements?.[name]).filter(Boolean);
  }

  function syncRequiredState() {
    const form = paymentForm();
    if (!form) return;
    const required = isCzechDividend(form);
    fields(form).forEach((field) => {
      field.required = required;
      field.setAttribute("aria-required", String(required));
    });
  }

  function missingFields(form) {
    if (!isCzechDividend(form)) return [];
    return fields(form).filter((field) => String(field.value || "") === "");
  }

  function message() {
    return document.documentElement.lang === "en"
      ? "Complete both factual items for the potential Czech domestic dividend exemption before calculating the result."
      : "Před dokončením výpočtu doplň oba skutkové údaje pro možné vnitrostátní osvobození dividend podle § 19 ZDP.";
  }

  function showIncompleteError(form, firstMissing = null) {
    const missing = missingFields(form);
    if (!missing.length) return false;

    const error = document.querySelector("#workspace-error");
    if (error) {
      error.textContent = message();
      error.hidden = false;
    }

    const section = document.querySelector("#cz-section19-facts");
    section?.scrollIntoView({ behavior: "smooth", block: "center" });
    (firstMissing || missing[0])?.focus({ preventScroll: true });
    return true;
  }

  function blockIncompleteSubmit(event) {
    const form = paymentForm();
    if (!form || event.target !== form || !showIncompleteError(form)) return;
    event.preventDefault();
    event.stopImmediatePropagation();
  }

  function handleInvalid(event) {
    const form = paymentForm();
    const field = event.target;
    if (!form || !FIELD_NAMES.includes(field?.name) || !isCzechDividend(form)) return;
    event.preventDefault();
    showIncompleteError(form, field);
  }

  function boot() {
    syncRequiredState();
    const form = paymentForm();
    form?.elements?.income_type?.addEventListener("change", syncRequiredState);
    form?.addEventListener("submit", blockIncompleteSubmit, true);
    fields(form).forEach((field) => field.addEventListener("invalid", handleInvalid));
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
})();
