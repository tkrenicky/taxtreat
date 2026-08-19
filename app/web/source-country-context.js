(() => {
  "use strict";

  const COUNTRY_CONTEXT = Object.freeze({
    CZ: Object.freeze({
      code: "CZ",
      label: "Česká republika",
      baseCurrency: "CZK",
      fxProvider: "CNB",
      runtimeReleased: true,
      availability: "released",
      domesticLawLabel: "zákon č. 586/1992 Sb., o daních z příjmů",
      complianceFormCode: null,
      complianceLegalReference: "§ 38d a § 38da zákona č. 586/1992 Sb., o daních z příjmů",
      notificationPeriodicity: "country_specific_cz",
      notificationDeadlineRule: "country_specific_cz",
      remittanceDeadlineRule: "country_specific_cz",
      ordinaryAnnualWhtReturnConfigured: true,
      permanentEstablishmentLocation: "České republice",
      permanentEstablishmentShortLocation: "ČR",
      taxLabel: "Česká srážková daň",
    }),
    SK: Object.freeze({
      code: "SK",
      label: "Slovensko",
      baseCurrency: "EUR",
      fxProvider: null,
      runtimeReleased: false,
      availability: "pre_release",
      domesticLawLabel: "zákon č. 595/2003 Z. z. o dani z príjmov",
      complianceFormCode: "OZN4311v26",
      complianceLegalReference: "§ 43 ods. 11 zákona č. 595/2003 Z. z.",
      notificationPeriodicity: "monthly",
      notificationDeadlineRule: "15th_day_of_following_calendar_month",
      remittanceDeadlineRule: "15th_day_of_following_calendar_month",
      ordinaryAnnualWhtReturnConfigured: false,
      permanentEstablishmentLocation: "Slovenskej republike",
      permanentEstablishmentShortLocation: "SR",
      taxLabel: "Slovenská zrážková daň",
    }),
  });

  function getSourceCountryContext(code) {
    const normalized = String(code || "").toUpperCase();
    const context = COUNTRY_CONTEXT[normalized];
    if (!context) throw new Error(`Unsupported source country: ${normalized}`);
    return context;
  }

  function finalAnalysisAllowed(code) {
    return getSourceCountryContext(code).runtimeReleased === true;
  }

  function requiresCnbFx(code, transactionCurrency) {
    const context = getSourceCountryContext(code);
    return context.fxProvider === "CNB" && String(transactionCurrency || "").toUpperCase() !== context.baseCurrency;
  }

  window.TaxTreatSourceCountries = Object.freeze({
    countries: COUNTRY_CONTEXT,
    get: getSourceCountryContext,
    finalAnalysisAllowed,
    requiresCnbFx,
  });
})();
