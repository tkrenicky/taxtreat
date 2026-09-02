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
      taxResultLabel: "Srážková daň",
      taxResultLabelWithCurrency: "Srážková daň v CZK",
      complianceTitle: "Rozhodné datum a navazující lhůty",
      remittanceLabel: "Odvod srážkové daně",
      notificationLabel: "Oznámení příjmu plynoucího do zahraničí",
      sourceMetrics: Object.freeze({
        jurisdictionLabel: "Podporované jurisdikce",
        jurisdictionValue: "101",
        scopeLabel: "Pokryté kombinace",
        scopeValue: "303",
      }),
      hideWorkspaceFxControls: false,
      prohibitedFxServicePrefixes: Object.freeze([]),
      interestMonthlyAmountFieldVisible: true,
      payerSubtitle: "České subjekty, jejichž platby jsou v TaxTreat zpracovávány.",
      metaDescription: "TaxTreat – informační pracovní prostor pro českou srážkovou daň",
      prereleaseNotice: "",
      complianceNoteDefault: "Lhůty se zobrazí po dokončení výpočtu.",
      peLocationLabel: "Vazba ke stálé provozovně v ČR",
      payerGenitiveLabel: "českého plátce",
    }),
  });

  const TAX_TREATMENT_PRESENTATION = Object.freeze({
    taxable_at_rate: Object.freeze({
      kind: "rate",
      resultLabel: null,
      rateLabel: null,
    }),
    exclusive_foreign_taxation: Object.freeze({
      kind: "non_rate",
      resultLabel: "Neuplatňuje se",
      rateLabel: "Neuplatňuje se",
    }),
    domestic_exemption: Object.freeze({
      kind: "non_rate",
      resultLabel: "Osvobození",
      rateLabel: "0 %",
    }),
    outside_subject_of_tax: Object.freeze({
      kind: "non_rate",
      resultLabel: "Není předmětem daně",
      rateLabel: "N/A",
    }),
    domestic_rate_applies: Object.freeze({
      kind: "non_rate",
      resultLabel: "Smlouva sazbu neomezuje",
      rateLabel: "Dle vnitrostátního práva",
    }),
  });

  function taxTreatmentPresentation(treatment) {
    const normalized = String(treatment || "").trim().toLowerCase();
    return TAX_TREATMENT_PRESENTATION[normalized] || null;
  }

  function getSourceCountryContext(code) {
    const normalized = String(code || "").toUpperCase();
    const context = COUNTRY_CONTEXT[normalized];
    if (!context) throw new Error(`Unsupported public source country: ${normalized}`);
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
    taxTreatmentPresentation,
  });
})();
