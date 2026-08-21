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
  const sourceMetrics = [...document.querySelectorAll('[data-view="sources"] .source-metrics article')];
  const metaDescription = document.querySelector('meta[name="description"]');
  const payersSubtitle = document.querySelector('[data-view="payers"] .page-title span');

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

  function setSourceMetrics(ctx) {
    if (sourceMetrics.length < 3) return;

    const metrics = ctx.sourceMetrics || {};
    const jurisdictionLabel = sourceMetrics[0].querySelector("span");
    const jurisdictionValue = sourceMetrics[0].querySelector("strong");
    const scopeLabel = sourceMetrics[1].querySelector("span");
    const scopeValue = sourceMetrics[1].querySelector("strong");

    if (jurisdictionLabel) {
      jurisdictionLabel.textContent = metrics.jurisdictionLabel || "";
    }
    if (jurisdictionValue) {
      jurisdictionValue.textContent = metrics.jurisdictionValue || "";
    }
    if (scopeLabel) {
      scopeLabel.textContent = metrics.scopeLabel || "";
    }
    if (scopeValue) {
      scopeValue.textContent = metrics.scopeValue || "";
    }
  }

  function applyCurrencyDefaults(ctx) {
    if (currency && [...currency.options].some((option) => option.value === ctx.baseCurrency)) {
      currency.value = ctx.baseCurrency;
    }

    if (fxField) {
      fxField.hidden = ctx.hideWorkspaceFxControls === true;
    }
    if (fxStatus) {
      fxStatus.hidden = ctx.hideWorkspaceFxControls === true;
    }
  }

  function applyCopy(ctx) {
    document.body.dataset.sourceCountry = ctx.code;
    const taxLabel = document.querySelector("#workspace-tax-label");
    const taxRowLabel = document.querySelector("#workspace-tax-row-label");
    if (taxLabel) taxLabel.textContent = ctx.taxResultLabelWithCurrency;
    if (taxRowLabel) taxRowLabel.textContent = ctx.taxResultLabel;
    if (complianceHeading) complianceHeading.textContent = ctx.complianceLegalReference;
    if (complianceTitle) complianceTitle.textContent = ctx.complianceTitle;

    if (complianceRows[1]?.querySelector("dt")) {
      complianceRows[1].querySelector("dt").textContent = ctx.remittanceLabel;
    }
    if (complianceRows[2]?.querySelector("dt")) {
      complianceRows[2].querySelector("dt").textContent = ctx.notificationLabel;
    }

    prereleaseNotice.textContent = ctx.prereleaseNotice || "";
    if (complianceNote) {
      complianceNote.textContent = ctx.complianceNoteDefault || "";
    }
    if (metaDescription) {
      metaDescription.content = ctx.metaDescription || "";
    }
    if (payersSubtitle) {
      payersSubtitle.textContent = ctx.payerSubtitle || "";
    }

    setMatchingText(
      '[data-view="recipient-detail"] dt',
      "Vazba ke stálé provozovně v ČR",
      ctx.peLocationLabel
    );
    setMatchingText(
      '[data-view="recipient-detail"] dt',
      "Väzba príjmu na stálu prevádzkareň v SR",
      ctx.peLocationLabel
    );

    setMatchingText(
      '[data-view="flow"] span, [data-view="recipient-detail"] dt, [data-view="recipient-detail"] p',
      "v České republice",
      `v ${ctx.permanentEstablishmentLocation}`
    );
    setMatchingText(
      '[data-view="flow"] span, [data-view="recipient-detail"] dt, [data-view="recipient-detail"] p',
      "v Slovenskej republike",
      `v ${ctx.permanentEstablishmentLocation}`
    );
    setMatchingText(
      '[data-view="flow"] span, [data-view="recipient-detail"] dt, [data-view="recipient-detail"] p',
      "v ČR",
      `v ${ctx.permanentEstablishmentShortLocation}`
    );
    setMatchingText(
      '[data-view="flow"] span, [data-view="recipient-detail"] dt, [data-view="recipient-detail"] p',
      "v SR",
      `v ${ctx.permanentEstablishmentShortLocation}`
    );

    setMatchingText(
      '[data-view="flow"] span, [data-view="flow"] small, [data-view="flow"] legend',
      "českého plátce",
      ctx.payerGenitiveLabel
    );
    setMatchingText(
      '[data-view="flow"] span, [data-view="flow"] small, [data-view="flow"] legend',
      "slovenského plátce",
      ctx.payerGenitiveLabel
    );

    if (interestMonthlyField) {
      interestMonthlyField.hidden =
        ctx.interestMonthlyAmountFieldVisible === false;
    }

    setSourceMetrics(ctx);
  }

  function applyReleaseState(ctx) {
    prereleaseNotice.hidden = ctx.runtimeReleased;
    if (submit) {
      submit.dataset.sourceCountry = ctx.code;
      submit.textContent = ctx.runtimeReleased
        ? "Zobrazit pravidla a výpočet →"
        : `${ctx.label} · výpočet zatím není vydán`;
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

  function blockProhibitedFxListener(event) {
    const ctx = context();
    if (ctx.hideWorkspaceFxControls !== true) return;

    event.stopImmediatePropagation();

    if (fxField) fxField.hidden = true;
    if (fxStatus) fxStatus.hidden = true;
  }

  currency?.addEventListener(
    "change",
    blockProhibitedFxListener,
    true
  );
  transactionDate?.addEventListener(
    "change",
    blockProhibitedFxListener,
    true
  );

  const nativeFetch = window.fetch.bind(window);
  window.fetch = async function sourceCountryAwareFetch(resource, options = {}) {
    const url = typeof resource === "string" ? resource : String(resource?.url || "");
    const ctx = context();
    const prohibitedPrefixes = Array.isArray(ctx.prohibitedFxServicePrefixes)
      ? ctx.prohibitedFxServicePrefixes
      : [];

    if (prohibitedPrefixes.some((prefix) => url.startsWith(prefix))) {
      throw new Error(
        `FX service ${url} is prohibited for ${ctx.code} source-country context`
      );
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
      error.textContent = `${ctx.label} je stále v pre-release režimu. Výpočet se záměrně nespustil, aby nebyl použit nevydaný právní výstup.`;
    }
  }, true);

  window.TaxTreatWorkspaceSourceCountry = Object.freeze({
    getActiveCode: () => currentCode,
    getActiveContext: () => context(),
    setActiveCode: (code) => applyContext(code),
  });

  applyContext(payerCountries.get(activePayerKey()) || "CZ");
})();
