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
  const transactionDate = paymentForm.elements.transaction_date;
  const fxField = document.querySelector("#workspace-exchange-rate-field");
  const fxStatus = document.querySelector("#workspace-fx-status");
  const complianceHeading = document.querySelector(".compliance-schedule .card-head span");
  const complianceTitle = document.querySelector(".compliance-schedule h2");
  const complianceRows = [...document.querySelectorAll(".compliance-schedule dl > div")];
  const complianceNote = document.querySelector("#workspace-deadline-note");
  const interestMonthlyField = paymentForm.elements.prior_same_type_monthly_amount_czk?.closest("label");

  const prereleaseNotice = document.createElement("div");
  prereleaseNotice.id = "workspace-source-country-notice";
  prereleaseNotice.className = "demo-notice";
  prereleaseNotice.hidden = true;
  prereleaseNotice.setAttribute("role", "status");
  document.querySelector('.flow-step[data-step="3"] .page-title')?.after(prereleaseNotice);

  function setMatchingText(selector, from, to) {
    document.querySelectorAll(selector).forEach((node) => {
      if (node.textContent.includes(from)) node.textContent = node.textContent.replaceAll(from, to);
    });
  }

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
    if (taxLabel) taxLabel.textContent = ctx.code === "SK" ? "Slovenská zrážková daň v EUR" : "Srážková daň v CZK";
    if (taxRowLabel) taxRowLabel.textContent = ctx.code === "SK" ? "Zrážková daň" : "Srážková daň";
    if (complianceHeading) complianceHeading.textContent = ctx.complianceLegalReference;
    if (complianceTitle) complianceTitle.textContent = ctx.code === "SK" ? "Rozhodný dátum a nadväzujúce lehoty" : "Rozhodné datum a navazující lhůty";

    if (complianceRows[1]?.querySelector("dt")) {
      complianceRows[1].querySelector("dt").textContent = ctx.code === "SK" ? "Odvod zrážkovej dane" : "Odvod srážkové daně";
    }
    if (complianceRows[2]?.querySelector("dt")) {
      complianceRows[2].querySelector("dt").textContent = ctx.code === "SK" ? "Mesačné oznámenie OZN4311v26" : "Oznámení příjmu plynoucího do zahraničí";
    }

    if (ctx.code === "SK") {
      prereleaseNotice.textContent = "Slovenský balík je dostupný pouze pro technický náhled. Standardní corporate outbound WHT compliance je modelována jako měsíční OZN4311v26 podle § 43 ods. 11; oznámení i odvod jsou do 15. dne následujícího kalendářního měsíce. Finální výpočet zůstává blokovaný do dokončení právního review a release gate.";
      if (complianceNote) complianceNote.textContent = "SK compliance model: mesačné OZN4311v26 a odvod zrážkovej dane najneskôr do 15. dňa nasledujúceho kalendárneho mesiaca. Ordinary annual WHT return není pro standardní dividend/interest/royalty flow nakonfigurován.";
      setMatchingText('[data-view="flow"] span, [data-view="recipient-detail"] dt, [data-view="recipient-detail"] p', "v České republice", "v Slovenskej republike");
      setMatchingText('[data-view="flow"] span, [data-view="recipient-detail"] dt, [data-view="recipient-detail"] p', "v ČR", "v SR");
      setMatchingText('[data-view="flow"] span, [data-view="flow"] small, [data-view="flow"] legend', "českého plátce", "slovenského plátce");
      if (interestMonthlyField) interestMonthlyField.hidden = true;
    } else {
      prereleaseNotice.textContent = "";
      if (complianceNote) complianceNote.textContent = "Lhůty se zobrazí po dokončení výpočtu.";
      setMatchingText('[data-view="flow"] span, [data-view="recipient-detail"] dt, [data-view="recipient-detail"] p', "v Slovenskej republike", "v České republice");
      setMatchingText('[data-view="flow"] span, [data-view="recipient-detail"] dt, [data-view="recipient-detail"] p', "v SR", "v ČR");
      setMatchingText('[data-view="flow"] span, [data-view="flow"] small, [data-view="flow"] legend', "slovenského plátce", "českého plátce");
      if (interestMonthlyField) interestMonthlyField.hidden = false;
    }
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

  function blockCnbListenerForSk(event) {
    if (currentCode !== "SK") return;
    event.stopImmediatePropagation();
    if (fxField) fxField.hidden = true;
    if (fxStatus) fxStatus.hidden = true;
  }
  currency?.addEventListener("change", blockCnbListenerForSk, true);
  transactionDate?.addEventListener("change", blockCnbListenerForSk, true);

  const nativeFetch = window.fetch.bind(window);
  window.fetch = async function sourceCountryAwareFetch(resource, options = {}) {
    const url = typeof resource === "string" ? resource : String(resource?.url || "");
    if (currentCode === "SK" && url.startsWith("/exchange-rates/cnb")) {
      throw new Error("CNB exchange-rate service is prohibited for Slovak source-country context");
    }
    if (url.includes("/analysis") && options.body) {
      try {
        const payload = JSON.parse(String(options.body));
        payload.source_country = currentCode;
        options = { ...options, body: JSON.stringify(payload) };
      } catch (_problem) {
        // The analysis endpoint validates malformed payloads itself.
      }
    }
    return nativeFetch(resource, options);
  };

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
