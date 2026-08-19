(() => {
  "use strict";

  const api = window.TaxTreatSourceCountries;
  if (!api) throw new Error("TaxTreat source-country context is not loaded");

  const activePayerSelect = document.querySelector("#active-payer-select");
  const paymentForm = document.querySelector("#workspace-payment");
  if (!activePayerSelect || !paymentForm) return;

  const payerCountries = new Map();
  let currentCode = "CZ";

  function activePayerKey() {
    return String(activePayerSelect.value || "default");
  }

  function context() {
    return api.get(currentCode);
  }

  const countryControl = document.createElement("label");
  countryControl.className = "payer-context source-country-context";
  countryControl.innerHTML = `
    <span>Stát plátce</span>
    <select id="active-source-country" aria-label="Stát aktivního plátce">
      <option value="CZ">Česká republika</option>
      <option value="SK">Slovensko · před vydáním</option>
    </select>
  `;
  activePayerSelect.closest(".payer-context")?.after(countryControl);

  const countrySelect = countryControl.querySelector("select");
  const error = document.querySelector("#workspace-error");
  const submit = document.querySelector("#workspace-submit");
  const currency = paymentForm.elements.currency;
  const fxField = document.querySelector("#workspace-exchange-rate-field");
  const fxStatus = document.querySelector("#workspace-fx-status");
  const complianceHeading = document.querySelector(".compliance-schedule .card-head span");

  const prereleaseNotice = document.createElement("div");
  prereleaseNotice.id = "workspace-source-country-notice";
  prereleaseNotice.className = "demo-notice";
  prereleaseNotice.hidden = true;
  prereleaseNotice.setAttribute("role", "status");
  prereleaseNotice.textContent = "Slovenský balík je dostupný pouze pro technický náhled. Finální výpočet bude aktivován až po dokončení právního review a release gate.";
  document.querySelector('.flow-step[data-step="3"] .page-title')?.after(prereleaseNotice);

  function applyCurrencyDefaults(ctx) {
    if (!currency) return;
    if ([...currency.options].some((option) => option.value === ctx.baseCurrency)) {
      currency.value = ctx.baseCurrency;
    }
    if (ctx.code === "SK") {
      if (fxField) fxField.hidden = true;
      if (fxStatus) fxStatus.hidden = true;
    }
  }

  function applyCopy(ctx) {
    document.body.dataset.sourceCountry = ctx.code;
    const taxLabel = document.querySelector("#workspace-tax-label");
    const taxRowLabel = document.querySelector("#workspace-tax-row-label");
    if (taxLabel) taxLabel.textContent = ctx.code === "SK" ? "Slovenská zrážková daň" : "Srážková daň v CZK";
    if (taxRowLabel) taxRowLabel.textContent = ctx.code === "SK" ? "Zrážková daň" : "Srážková daň";
    if (complianceHeading) complianceHeading.textContent = ctx.complianceLegalReference;
  }

  function applyReleaseState(ctx) {
    prereleaseNotice.hidden = ctx.runtimeReleased;
    if (submit) {
      submit.dataset.sourceCountry = ctx.code;
      submit.textContent = ctx.runtimeReleased
        ? "Zobrazit pravidla a výpočet →"
        : "Slovenský výpočet zatím není vydán";
      submit.setAttribute("aria-disabled", String(!ctx.runtimeReleased));
    }
  }

  function applyContext(code) {
    currentCode = String(code || "CZ").toUpperCase();
    const ctx = context();
    payerCountries.set(activePayerKey(), currentCode);
    countrySelect.value = currentCode;
    applyCurrencyDefaults(ctx);
    applyCopy(ctx);
    applyReleaseState(ctx);
    window.dispatchEvent(new CustomEvent("taxtreat:source-country-change", { detail: ctx }));
  }

  countrySelect.addEventListener("change", () => applyContext(countrySelect.value));
  activePayerSelect.addEventListener("change", () => {
    applyContext(payerCountries.get(activePayerKey()) || "CZ");
  });

  paymentForm.addEventListener("submit", (event) => {
    const ctx = context();
    if (ctx.runtimeReleased) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    if (error) {
      error.hidden = false;
      error.textContent = "Slovenský balík je stále v pre-release režimu. Výpočet se záměrně nespustil, aby nebyl použit nezkontrolovaný právní výstup.";
    }
  }, true);

  window.TaxTreatWorkspaceSourceCountry = Object.freeze({
    getActiveCode: () => currentCode,
    getActiveContext: () => context(),
    setActiveCode: (code) => applyContext(code),
  });

  applyContext(payerCountries.get(activePayerKey()) || "CZ");
})();
