(() => {
  "use strict";

  const SECTION19_ELIGIBLE = new Set([
    "AT","BE","BG","HR","CY","CZ","DK","EE","FI","FR","DE","GR","HU","IE","IT","LV","LT","LU","MT","NL","PL","PT","RO","SK","SI","ES","SE",
    "CH","NO","IS","LI"
  ]);

  function boolField(name) {
    const value = document.querySelector(`#workspace-payment [name="${name}"]`)?.value;
    if (value === "true") return true;
    if (value === "false") return false;
    return null;
  }

  function reportLanguage() {
    if (window.__TAXTREAT_LOCALE__ === "en" || window.__TAXTREAT_LOCALE__ === "cs") {
      return window.__TAXTREAT_LOCALE__;
    }
    const explicit = document.querySelector("#taxtreat-report-language")?.value;
    if (explicit === "en" || explicit === "cs") return explicit;
    const stored = localStorage.getItem("taxtreat-report-language");
    if (stored === "en" || stored === "cs") return stored;
    return "cs";
  }

  function enrichReportPayload(payload) {
    if (!payload || typeof payload !== "object") return payload;
    payload.facts = payload.facts && typeof payload.facts === "object" ? payload.facts : {};
    payload.facts.__report_language = reportLanguage();

    if (String(payload.source_country || "").toUpperCase() !== "CZ" || payload.income_type !== "dividend") return payload;

    const companyForm = boolField("section19_company_form");
    const taxableCompany = boolField("section19_taxable_company");
    const recipientCountry = String(payload.recipient_country || "").toUpperCase();
    const ownership = Number(payload.facts.ownership_percent || 0);
    const direct = payload.facts.direct_ownership === true;
    const company = payload.facts.recipient_entity_type === "company";

    if (companyForm !== null) payload.facts.recipient_is_qualifying_company_form = companyForm;
    payload.facts.recipient_is_tax_resident_in_eligible_jurisdiction = SECTION19_ELIGIBLE.has(recipientCountry);
    if (taxableCompany !== null) {
      payload.facts.recipient_subject_to_qualifying_corporate_tax = taxableCompany;
      payload.facts.recipient_has_no_tax_exemption_or_zero_rate_option = taxableCompany;
    }
    payload.facts.recipient_is_parent_company = Boolean(company && direct && ownership >= 10);
    return payload;
  }

  const previousFetch = window.fetch.bind(window);
  window.fetch = async function taxtreatReportContextFetch(resource, options = {}) {
    const url = typeof resource === "string" ? resource : String(resource?.url || "");
    if (url.endsWith("/analysis/report") && options.body) {
      try {
        const payload = enrichReportPayload(JSON.parse(String(options.body)));
        options = { ...options, body: JSON.stringify(payload) };
      } catch (_problem) {
        // The report endpoint validates malformed requests itself.
      }
    }
    return previousFetch(resource, options);
  };
})();
