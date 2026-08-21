(() => {
  "use strict";

  const ELIGIBLE = new Set(["AT","BE","BG","HR","CY","CZ","DK","EE","FI","FR","DE","GR","HU","IE","IT","LV","LT","LU","MT","NL","PL","PT","RO","SK","SI","ES","SE","CH","NO","IS","LI"]);
  const SOURCE = "https://e-sbirka.gov.cz/sb/1992/586";
  const state = { payload:null, analysis:null };

  function language() { return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs"; }
  function en() { return language() === "en"; }
  function facts() { return state.payload?.facts && typeof state.payload.facts === "object" ? state.payload.facts : {}; }

  function boolSelect(name) {
    const value = document.querySelector(`[name="${name}"]`)?.value;
    return value === "true" ? true : value === "false" ? false : null;
  }

  function firstFact(patterns) {
    for (const [key, value] of Object.entries(facts())) {
      if (patterns.some((pattern) => pattern.test(key))) return value;
    }
    return undefined;
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

  function boolFact(...patterns) { return normalizeBool(firstFact(patterns)); }

  function ownershipPercent() {
    const direct = facts().ownership_percent;
    if (direct !== undefined && direct !== null && direct !== "") return Number(direct);
    const value = firstFact([/ownership.*percent/i,/share.*percent/i,/capital.*percent/i]);
    return Number(value);
  }

  function holdingSatisfied() {
    const flag = boolFact(/holding.*12/i,/twelve.*month/i,/12.*month/i,/holding.*period.*satisfied/i);
    if (flag !== null) return flag;
    const months = Number(firstFact([/holding.*month/i,/months.*held/i]));
    if (Number.isFinite(months) && months > 0) return months >= 12;
    const acquisition = firstFact([/acquisition.*date/i,/share.*acquired/i,/holding.*start/i]);
    const transaction = state.payload?.transaction_date || state.payload?.payment_date || state.payload?.date;
    if (acquisition && transaction) {
      const a = new Date(acquisition); const t = new Date(transaction);
      if (!Number.isNaN(a.valueOf()) && !Number.isNaN(t.valueOf())) {
        const anniversary = new Date(a); anniversary.setFullYear(a.getFullYear() + 1);
        return t >= anniversary;
      }
    }
    return null;
  }

  function noPeAttribution() {
    const attributable = boolFact(/(income|payment).*(attribut|allocat).*(pe|permanent)/i,/pe.*(attribut|allocat)/i);
    if (attributable !== null) return !attributable;
    return boolFact(/no.*(pe|permanent)/i,/without.*(pe|permanent)/i);
  }

  function hasEngineSection19() {
    return (state.analysis?.layer_results || []).some((item) => item.layer === "eu_relief" && String(item.rule_id || "").includes("DIVIDEND"));
  }

  function evaluate() {
    const source = String(state.payload?.source_country || document.body.dataset.sourceCountry || "CZ").toUpperCase();
    if (source !== "CZ" || state.payload?.income_type !== "dividend") return null;
    if (hasEngineSection19()) return null;

    const f = facts();
    const recipientCountry = String(state.payload?.recipient_country || "").toUpperCase();
    const entityType = String(f.recipient_entity_type || firstFact([/recipient.*entity.*type/i,/entity.*type/i]) || "").toLowerCase();
    const conditions = {
      qualifyingForm: boolSelect("section19_company_form"),
      taxableCompany: boolSelect("section19_taxable_company"),
      eligibleJurisdiction: ELIGIBLE.has(recipientCountry),
      company: entityType === "company" ? true : entityType ? false : null,
      directOwnership: f.direct_ownership === true ? true : f.direct_ownership === false ? false : boolFact(/direct.*ownership/i,/ownership.*direct/i),
      ownershipThreshold: Number.isFinite(ownershipPercent()) ? ownershipPercent() >= 10 : null,
      holdingPeriod: holdingSatisfied(),
      beneficialOwner: boolFact(/beneficial.*owner/i,/owner.*beneficial/i),
      noPeAttribution: noPeAttribution(),
    };

    const values = Object.values(conditions);
    if (values.some((value) => value === false)) return { status:"not_applicable", conditions };
    if (values.every((value) => value === true)) return { status:"applicable", conditions };
    return { status:"unresolved", conditions };
  }

  function relevantProvisionCopy() {
    return en()
      ? "Section 19(1)(ze), Section 19(3)(a)–(c), Section 19(4) and Section 19(6) of the Czech Income Taxes Act. For Switzerland, Norway, Iceland and Liechtenstein, Section 19(8) is also relevant."
      : "§ 19 odst. 1 písm. ze), § 19 odst. 3 písm. a) až c), § 19 odst. 4 a § 19 odst. 6 ZDP. Pro Švýcarsko, Norsko, Island a Lichtenštejnsko je relevantní také § 19 odst. 8 ZDP.";
  }

  function patchUi() {
    const result = evaluate();
    if (!result) return;
    const box = document.querySelector("#cz-section19-result");
    if (!box) return;

    if (result.status === "applicable") {
      box.className = "card tt-section19-applicable";
      box.innerHTML = `<div class="tt-legal-status">${en() ? "Section 19 exemption applies" : "Použije se osvobození podle § 19 ZDP"}</div><h2>${en() ? "Domestic exemption under Section 19" : "Vnitrostátní osvobození podle § 19 ZDP"}</h2><p><strong>${en() ? "Primary legal basis: Section 19 of the Czech Income Taxes Act." : "Primární právní titul: § 19 ZDP."}</strong> ${en() ? "All factual conditions captured by TaxTreat are satisfied. The dividend is exempt from Czech income tax and Czech withholding tax therefore does not apply. The treaty is relevant only as a secondary limitation of Czech taxing rights." : "Všechny skutkové podmínky zachycené TaxTreatem jsou splněny. Příjem z podílu na zisku je od české daně osvobozen, a česká srážková daň se proto neuplatní. Smlouva je relevantní pouze jako sekundární omezení českého práva zdanit."}</p><div class="tt-section19-source"><strong>${en() ? "Relevant Czech provisions" : "Relevantní česká ustanovení"}</strong><br>${relevantProvisionCopy()}<br><a href="${SOURCE}" target="_blank" rel="noopener">${en() ? "Official e-Sbírka source ↗" : "Oficiální zdroj e-Sbírka ↗"}</a></div>`;
    } else if (result.status === "not_applicable") {
      box.className = "card tt-section19-not-applicable";
      box.innerHTML = `<div class="tt-legal-status">${en() ? "Section 19 exemption does not apply" : "Osvobození podle § 19 ZDP se neuplatní"}</div><h2>${en() ? "Domestic exemption under Section 19" : "Vnitrostátní osvobození podle § 19 ZDP"}</h2><p>${en() ? "At least one statutory factual condition is not met. The final treatment therefore follows the applicable treaty or the domestic withholding-tax rule." : "Alespoň jedna zákonná skutková podmínka není splněna. Konečné daňové zacházení proto vychází z příslušné smlouvy nebo z vnitrostátního pravidla srážkové daně."}</p>`;
    } else {
      box.className = "card";
      box.innerHTML = `<div class="tt-legal-status">${en() ? "Section 19 assessment unresolved" : "Posouzení § 19 ZDP zatím nelze uzavřít"}</div><h2>${en() ? "Domestic exemption under Section 19" : "Vnitrostátní osvobození podle § 19 ZDP"}</h2><p>${en() ? "At least one factual condition is missing or cannot be derived safely. TaxTreat therefore does not present the treaty as the sole final legal basis." : "Alespoň jedna skutková podmínka chybí nebo ji nelze bezpečně odvodit. TaxTreat proto neprezentuje smlouvu jako jediný konečný právní titul."}</p>`;
    }
  }

  function transformReport(html) {
    const result = evaluate();
    if (!result || !html) return html;
    const doc = new DOMParser().parseFromString(html, "text/html");
    const english = (doc.documentElement.lang || "cs").toLowerCase().startsWith("en");
    const existing = doc.querySelector(".tt-report-section19");
    if (existing) {
      if (result.status === "applicable") {
        existing.innerHTML = `<h3>${english ? "Primary legal basis: domestic exemption under Section 19" : "Primární právní titul: vnitrostátní osvobození podle § 19 ZDP"}</h3><p>${english ? "All factual conditions captured by TaxTreat are satisfied. The dividend is exempt from Czech income tax; Czech withholding tax therefore does not apply. Treaty protection is secondary." : "Všechny skutkové podmínky zachycené TaxTreatem jsou splněny. Příjem z podílu na zisku je od české daně osvobozen; česká srážková daň se proto neuplatní. Smluvní ochrana je sekundární."}</p><p class="legal-ref"><strong>${english ? "Relevant provisions:" : "Relevantní ustanovení:"}</strong> ${english ? "Section 19(1)(ze), Section 19(3)(a)–(c), Section 19(4) and Section 19(6)." : "§ 19 odst. 1 písm. ze), § 19 odst. 3 písm. a) až c), § 19 odst. 4 a § 19 odst. 6 ZDP."} · <a href="${SOURCE}">${english ? "Official e-Sbírka source" : "Oficiální zdroj e-Sbírka"} ↗</a></p>`;
      } else if (result.status === "not_applicable") {
        existing.innerHTML = `<h3>${english ? "Section 19 assessed – exemption not available" : "§ 19 ZDP posouzen – osvobození se neuplatní"}</h3><p>${english ? "At least one statutory factual condition is not met. The final treatment therefore follows the treaty analysis or the domestic withholding-tax rule." : "Alespoň jedna zákonná skutková podmínka není splněna. Konečné daňové zacházení proto vychází ze smluvní analýzy nebo z vnitrostátního pravidla srážkové daně."}</p><p class="legal-ref"><a href="${SOURCE}">${english ? "Official e-Sbírka source" : "Oficiální zdroj e-Sbírka"} ↗</a></p>`;
      } else {
        existing.innerHTML = `<h3>${english ? "Section 19 assessment unresolved" : "Posouzení § 19 ZDP není uzavřeno"}</h3><p>${english ? "At least one factual condition is missing or cannot be derived safely. The treaty result must therefore not be presented as the sole final legal basis." : "Alespoň jedna skutková podmínka chybí nebo ji nelze bezpečně odvodit. Smluvní výsledek proto nesmí být prezentován jako jediný konečný právní titul."}</p>`;
      }
    }

    if (result.status === "applicable") {
      const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT);
      const nodes = [];
      while (walker.nextNode()) nodes.push(walker.currentNode);
      nodes.forEach((node) => {
        const text = node.nodeValue;
        if (/^\s*čl\. 10\s*$/i.test(text)) node.nodeValue = text.replace(/čl\. 10/i, "§ 19 ZDP");
        if (/^\s*Article 10\s*$/i.test(text)) node.nodeValue = text.replace(/Article 10/i, "Section 19");
        if (/česká srážková daň je proto 0\s*%/i.test(text)) node.nodeValue = text.replace(/česká srážková daň je proto 0\s*%/i, "česká srážková daň se proto neuplatní");
        if (/Czech withholding tax is therefore 0\s*%/i.test(text)) node.nodeValue = text.replace(/Czech withholding tax is therefore 0\s*%/i, "Czech withholding tax therefore does not apply");
      });
    }
    return "<!doctype html>\n" + doc.documentElement.outerHTML;
  }

  const previousFetch = window.fetch.bind(window);
  window.fetch = async function taxTreatSection19FallbackFetch(resource, options = {}) {
    const url = typeof resource === "string" ? resource : resource?.url || "";
    if (url.endsWith("/analysis/intake") && options?.body) {
      try { state.payload = JSON.parse(String(options.body)); } catch (_problem) {}
    }
    const response = await previousFetch(resource, options);
    if (url.endsWith("/analysis/intake") && response.ok) {
      try {
        const body = await response.clone().json();
        state.analysis = body?.analysis || null;
        window.setTimeout(patchUi, 0);
      } catch (_problem) {}
    }
    if (url.endsWith("/analysis/report") && response.ok) {
      try {
        const body = await response.clone().json();
        if (body?.html) body.html = transformReport(body.html);
        const headers = new Headers(response.headers); headers.set("Content-Type","application/json");
        return new Response(JSON.stringify(body), { status:response.status, statusText:response.statusText, headers });
      } catch (_problem) { return response; }
    }
    return response;
  };

  document.addEventListener("change", (event) => {
    if (["taxtreat-ui-language","section19_company_form","section19_taxable_company"].includes(event.target?.id) || ["section19_company_form","section19_taxable_company"].includes(event.target?.name)) window.setTimeout(patchUi, 0);
  }, true);
})();
