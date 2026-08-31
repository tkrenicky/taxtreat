(() => {
  "use strict";

  const SECTION19_URL = "https://e-sbirka.gov.cz/sb/1992/586";
  const ELIGIBLE = new Set(["AT","BE","BG","HR","CY","CZ","DK","EE","FI","FR","DE","GR","HU","IE","IT","LV","LT","LU","MT","NL","PL","PT","RO","SK","SI","ES","SE","CH","NO","IS","LI"]);
  const state = { payload: null };

  function en() {
    return (document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs") === "en";
  }

  function facts() {
    return state.payload?.facts && typeof state.payload.facts === "object" ? state.payload.facts : {};
  }

  function normalizeBool(value) {
    if (value === true || value === false) return value;
    if (typeof value === "number") return value !== 0;
    if (typeof value !== "string") return null;
    const v = value.trim().toLowerCase();
    if (["true","yes","ano","1","at_least_12_months","at-least-12-months"].includes(v)) return true;
    if (["false","no","ne","0","less_than_12_months","less-than-12-months"].includes(v)) return false;
    return null;
  }

  function firstFact(...patterns) {
    for (const [key, value] of Object.entries(facts())) {
      if (patterns.some((pattern) => pattern.test(key))) return value;
    }
    return undefined;
  }

  function boolFact(...patterns) { return normalizeBool(firstFact(...patterns)); }

  function boolSelect(name) {
    const value = document.querySelector(`[name="${name}"]`)?.value;
    return value === "true" ? true : value === "false" ? false : null;
  }

  function ownershipPercent() {
    const value = facts().ownership_percent ?? firstFact(/ownership.*percent/i,/share.*percent/i,/capital.*percent/i);
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
  }

  function holdingSatisfied() {
    const flag = boolFact(/holding.*12/i,/twelve.*month/i,/12.*month/i,/holding.*period.*satisfied/i);
    if (flag !== null) return flag;
    const months = Number(firstFact(/holding.*month/i,/months.*held/i));
    return Number.isFinite(months) && months > 0 ? months >= 12 : null;
  }

  function noPeAttribution() {
    const attributable = boolFact(/(income|payment).*(attribut|allocat).*(pe|permanent)/i,/pe.*(attribut|allocat)/i);
    if (attributable !== null) return !attributable;
    return boolFact(/no.*(pe|permanent)/i,/without.*(pe|permanent)/i);
  }

  function conditionState() {
    const f = facts();
    const country = String(state.payload?.recipient_country || "").toUpperCase();
    const entityType = String(f.recipient_entity_type || firstFact(/recipient.*entity.*type/i,/entity.*type/i) || "").toLowerCase();
    const ownership = ownershipPercent();
    return {
      qualifyingForm: boolSelect("section19_company_form"),
      taxableCompany: boolSelect("section19_taxable_company"),
      eligibleJurisdiction: country ? ELIGIBLE.has(country) : null,
      company: entityType === "company" ? true : entityType ? false : null,
      directOwnership: f.direct_ownership === true ? true : f.direct_ownership === false ? false : boolFact(/direct.*ownership/i,/ownership.*direct/i),
      ownershipThreshold: ownership === null ? null : ownership >= 10,
      holdingPeriod: holdingSatisfied(),
      beneficialOwner: boolFact(/beneficial.*owner/i,/owner.*beneficial/i),
      noPeAttribution: noPeAttribution(),
    };
  }

  const labels = {
    qualifyingForm: ["Příjemce nesplňuje požadavek na kvalifikovanou právní formu.", "The recipient does not meet the qualifying legal-form requirement."],
    taxableCompany: ["Příjemce nesplňuje požadavek na běžné zdanění daní z příjmů právnických osob.", "The recipient does not meet the ordinary corporate-tax requirement."],
    eligibleJurisdiction: ["Příjemce není rezidentem státu, pro který lze tento režim § 19 použít.", "The recipient is not resident in a jurisdiction eligible for this Section 19 regime."],
    company: ["Příjemce není pro tento režim posouzen jako společnost.", "The recipient is not treated as a company for this regime."],
    directOwnership: ["Požadovaný podíl není držen přímo.", "The required ownership interest is not held directly."],
    ownershipThreshold: ["Přímý podíl nedosahuje zákonného minima 10 %.", "The direct ownership interest is below the statutory 10% threshold."],
    holdingPeriod: ["Není splněna požadovaná doba držby podílu.", "The required holding period is not satisfied."],
    beneficialOwner: ["Nebylo potvrzeno postavení skutečného vlastníka příjmu.", "Beneficial ownership of the income is not confirmed."],
    noPeAttribution: ["Příjem je přičitatelný stálé provozovně příjemce.", "The income is attributable to the recipient's permanent establishment."],
  };

  function resultStatus(box) {
    const text = box?.textContent || "";
    if (/§\s*19 ZDP se neuplatní|Section 19 does not apply/i.test(text) || box?.classList.contains("tt-section19-not-applicable")) return "not_applicable";
    if (/§\s*19 ZDP se použije|Section 19 applies/i.test(text) || box?.classList.contains("tt-section19-applicable")) return "applicable";
    if (/zatím nelze uzavřít|unresolved|nelze potvrdit/i.test(text)) return "unresolved";
    return null;
  }

  function smallestCardWithHeading(root, cs, english) {
    const exact = en() ? english : cs;
    const headings = [...root.querySelectorAll("h1,h2,h3,h4,h5,strong,b")];
    const heading = headings.find((el) => (el.textContent || "").trim() === exact);
    return heading?.closest(".card,section,article") || heading?.parentElement || null;
  }

  function rewriteSummary(box, status) {
    const english = en();
    const conditions = conditionState();
    const failed = Object.entries(conditions).filter(([,value]) => value === false).map(([key]) => labels[key][english ? 1 : 0]);
    const unknown = Object.entries(conditions).filter(([,value]) => value === null).map(([key]) => labels[key][english ? 1 : 0]);

    if (status === "applicable") {
      box.className = "card tt-section19-applicable tt-s19-summary-only";
      box.innerHTML = english
        ? `<div class="tt-legal-status">Section 19 applies</div><h2>Domestic exemption under Section 19</h2><p><strong>Primary legal basis: Section 19 of the Czech Income Taxes Act.</strong> Czech withholding tax does not apply because the statutory exemption conditions are satisfied.</p>`
        : `<div class="tt-legal-status">§ 19 ZDP se použije</div><h2>Vnitrostátní osvobození podle § 19 ZDP</h2><p><strong>Primární právní titul: § 19 ZDP.</strong> Česká srážková daň se neuplatní, protože jsou splněny zákonné podmínky osvobození.</p>`;
      return;
    }

    if (status === "not_applicable") {
      const reasons = failed.length ? failed : [english ? "At least one statutory condition is not met; the available result data do not identify it more specifically." : "Alespoň jedna zákonná podmínka není splněna; dostupná data výsledku ji neidentifikují přesněji."];
      box.className = "card tt-section19-not-applicable tt-s19-summary-only";
      box.innerHTML = `${english ? '<div class="tt-legal-status">Section 19 does not apply</div><h2>Domestic exemption under Section 19</h2><p>The exemption does not apply because:</p>' : '<div class="tt-legal-status">§ 19 ZDP se neuplatní</div><h2>Vnitrostátní osvobození podle § 19 ZDP</h2><p>Osvobození se neuplatní, protože:</p>'}<ul>${reasons.map((r) => `<li>${r}</li>`).join("")}</ul>`;
      return;
    }

    if (status === "unresolved") {
      const reasons = unknown.length ? unknown : [english ? "A required factual condition has not been verified." : "Nebyla ověřena alespoň jedna požadovaná skutková podmínka."];
      box.className = "card tt-s19-summary-only";
      box.innerHTML = `${english ? '<div class="tt-legal-status">Section 19 cannot be confirmed</div><h2>Domestic exemption under Section 19</h2><p>The exemption cannot be confirmed because the following has not been verified:</p>' : '<div class="tt-legal-status">§ 19 ZDP nelze potvrdit</div><h2>Vnitrostátní osvobození podle § 19 ZDP</h2><p>Osvobození nelze potvrdit, protože nebylo ověřeno:</p>'}<ul>${reasons.map((r) => `<li>${r}</li>`).join("")}</ul>`;
    }
  }

  function patchAppliedRule(root, status) {
    const card = smallestCardWithHeading(root, "Použité právní pravidlo", "Applied legal rule");
    if (!card || status !== "applicable") return;
    card.innerHTML = en()
      ? `<strong>Applied legal rule</strong><p><b>Section 19 of the Czech Income Taxes Act — domestic dividend exemption.</b></p>`
      : `<strong>Použité právní pravidlo</strong><p><b>§ 19 ZDP — vnitrostátní osvobození podílu na zisku.</b></p>`;
  }

  function patchHeadlineRate(root, status) {
    if (status !== "applicable") return;
    [...root.querySelectorAll("p,small,span,div")].forEach((el) => {
      const text = (el.textContent || "").trim();
      if (/^0\s*%\s*z daňového základu$/i.test(text)) el.textContent = "Osvobození podle § 19 ZDP";
      if (/^0\s*%\s*of (the )?tax base$/i.test(text)) el.textContent = "Exempt under Section 19";
    });
  }

  function patchLegalSources(root, status) {
    const duplicate = root.querySelector("#tt-s19-primary-result");
    if (duplicate) duplicate.style.setProperty("display", "none", "important");

    const legalCard = smallestCardWithHeading(root, "Sekundární smluvní ochrana", "Secondary treaty protection");
    if (!legalCard || status !== "applicable") return;

    const heading = legalCard.querySelector("h1,h2,h3,h4,h5,strong,b");
    if (heading) heading.textContent = en() ? "Legal sources" : "Právní podklady";

    legalCard.querySelectorAll(".tt-s19-primary-source").forEach((el) => el.remove());
    const primary = document.createElement("div");
    primary.className = "tt-s19-primary-source";
    primary.innerHTML = en()
      ? `<div class="tt-s19-source-kicker">PRIMARY LEGAL RULE</div><b>Section 19 of the Czech Income Taxes Act</b><p>Domestic dividend exemption applied to this result.</p><a href="${SECTION19_URL}" target="_blank" rel="noopener">Official Czech source · e-Sbírka ↗</a>`
      : `<div class="tt-s19-source-kicker">PRIMÁRNÍ PRÁVNÍ PRAVIDLO</div><b>§ 19 ZDP</b><p>Vnitrostátní osvobození podílu na zisku použité pro tento výsledek.</p><a href="${SECTION19_URL}" target="_blank" rel="noopener">Oficiální zdroj · e-Sbírka ↗</a>`;
    const insertAfter = heading || legalCard.firstChild;
    if (insertAfter?.nextSibling) legalCard.insertBefore(primary, insertAfter.nextSibling);
    else legalCard.append(primary);
  }

  function installStyles() {
    if (document.querySelector("#tt-step4-simplify-style")) return;
    const style = document.createElement("style");
    style.id = "tt-step4-simplify-style";
    style.textContent = `
      #tt-s19-primary-result{display:none!important}
      .tt-s19-summary-only .tt-section19-source,.tt-s19-summary-only .tt-s19-source{display:none!important}
      .tt-s19-summary-only ul{margin:10px 0 0 18px;padding:0}
      .tt-s19-summary-only li{margin:5px 0;line-height:1.45}
      .tt-s19-primary-source{margin:12px 0;padding:13px 14px;border:1px solid #d9e2de;border-radius:9px;background:#f7faf8}
      .tt-s19-source-kicker{font-size:10px;font-weight:800;letter-spacing:.06em;margin-bottom:5px;color:#52635e}
      .tt-s19-primary-source p{margin:5px 0 7px}
    `;
    document.head.append(style);
  }

  function refresh() {
    installStyles();
    const box = document.querySelector("#cz-section19-result");
    if (!box) return;
    const status = resultStatus(box);
    if (!status) return;
    const root = document.querySelector('.flow-step[data-step="4"]') || document.querySelector('[data-step="4"]') || document.body;
    rewriteSummary(box, status);
    patchAppliedRule(root, status);
    patchHeadlineRate(root, status);
    patchLegalSources(root, status);
  }

  const previousFetch = window.fetch.bind(window);
  window.fetch = async function taxTreatStep4SimplifyFetch(resource, options = {}) {
    const url = typeof resource === "string" ? resource : resource?.url || "";
    if (url.endsWith("/analysis/intake") && options?.body) {
      try { state.payload = JSON.parse(String(options.body)); } catch (_e) {}
    }
    const response = await previousFetch(resource, options);
    if (url.endsWith("/analysis/intake")) {
      window.setTimeout(refresh, 0);
      window.setTimeout(refresh, 120);
    }
    return response;
  };

  document.addEventListener("change", (event) => {
    if (event.target?.id === "taxtreat-ui-language" || ["section19_company_form","section19_taxable_company"].includes(event.target?.name)) {
      window.setTimeout(refresh, 0);
    }
  }, true);

  document.addEventListener("click", (event) => {
    if (event.target?.closest("[data-nav],[data-next-step],[data-flow-step],[data-start-flow],#taxtreat-language-controls")) {
      window.setTimeout(refresh, 0);
      window.setTimeout(refresh, 120);
    }
  }, true);

  window.addEventListener("popstate", () => window.setTimeout(refresh, 0));
  refresh();
})();
