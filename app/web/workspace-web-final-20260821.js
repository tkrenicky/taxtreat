(() => {
  "use strict";

  const SECTION19_URL = "https://e-sbirka.gov.cz/sb/1992/586";
  const state = { payload: null, analysis: null };

  function lang() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
  }

  function isEn() { return lang() === "en"; }

  function installStyles() {
    if (document.querySelector("#tt-web-final-20260821-style")) return;
    const style = document.createElement("style");
    style.id = "tt-web-final-20260821-style";
    style.textContent = `
      /* Header navigation: intentionally larger than previous iterations. */
      .app-header nav { display:flex!important; align-items:center!important; gap:10px!important; }
      .app-header nav button[data-nav] {
        min-height:50px!important;
        padding:0 20px!important;
        border-radius:10px!important;
        font-size:18px!important;
        line-height:1!important;
        font-weight:750!important;
        letter-spacing:-.01em!important;
      }
      .app-header nav button[data-nav].active {
        background:rgba(255,255,255,.14)!important;
        box-shadow:inset 0 -3px 0 rgba(255,255,255,.95)!important;
      }

      /* Compact active-payer control. */
      .app-header .payer-context {
        width:auto!important;
        min-width:0!important;
        max-width:190px!important;
        min-height:42px!important;
        padding:5px 9px!important;
        border-radius:9px!important;
        box-shadow:none!important;
      }
      .app-header .payer-context > span {
        font-size:8.5px!important;
        line-height:1!important;
        letter-spacing:.06em!important;
        margin-bottom:2px!important;
      }
      #active-payer-select {
        width:165px!important;
        min-width:0!important;
        max-width:165px!important;
        height:24px!important;
        padding:0 18px 0 0!important;
        border:0!important;
        box-shadow:none!important;
        background:transparent!important;
        font-size:13.5px!important;
        line-height:1.1!important;
        font-weight:750!important;
      }

      /* Keep the language control independent of the active view. */
      #taxtreat-language-controls {
        display:inline-flex!important;
        width:auto!important;
        min-width:0!important;
        max-width:none!important;
        padding:0!important;
        margin:0 0 0 8px!important;
        border:0!important;
        background:transparent!important;
        box-shadow:none!important;
        flex:0 0 auto!important;
      }
      #taxtreat-language-controls .tt-lang-mini {
        display:inline-flex!important;
        align-items:center!important;
        gap:8px!important;
      }
      #taxtreat-language-controls .tt-lang-mini button {
        display:inline-flex!important;
        align-items:center!important;
        gap:5px!important;
        padding:4px 3px!important;
        border:0!important;
        background:transparent!important;
        font-size:12.5px!important;
        line-height:1!important;
      }
      .tt-final-flag {
        display:inline-block;
        width:18px;
        height:12px;
        border-radius:2px;
        overflow:hidden;
        box-shadow:0 0 0 1px rgba(255,255,255,.3);
        flex:0 0 auto;
      }
      .tt-final-flag svg { display:block; width:100%; height:100%; }

      /* Section 19 factual questions mirror the other transaction fact rows. */
      #cz-section19-facts > label {
        display:grid!important;
        grid-template-columns:minmax(0,1fr) minmax(210px,320px)!important;
        grid-template-areas:"q control" "help control"!important;
        column-gap:28px!important;
        row-gap:5px!important;
        align-items:center!important;
        padding:16px 0!important;
      }
      #cz-section19-facts > label > span { grid-area:q!important; margin:0!important; font-size:14px!important; line-height:1.35!important; }
      #cz-section19-facts > label > select { grid-area:control!important; width:100%!important; min-height:44px!important; font-size:14px!important; }
      #cz-section19-facts > label > small { grid-area:help!important; margin:0!important; font-size:12px!important; line-height:1.35!important; }

      /* Step 4 domestic exemption presentation. */
      .tt-s19-primary-result {
        margin:16px 0!important;
        padding:18px 20px!important;
        border:1px solid #bfd5cc!important;
        border-left:4px solid #1f6656!important;
        border-radius:12px!important;
        background:#f3f8f5!important;
      }
      .tt-s19-primary-result .tt-s19-badge {
        display:inline-flex;
        padding:4px 8px;
        margin-bottom:8px;
        border-radius:999px;
        background:#dfeee8;
        color:#174d42;
        font-size:11px;
        font-weight:800;
        letter-spacing:.03em;
      }
      .tt-s19-primary-result h2 { margin:0 0 8px!important; }
      .tt-s19-primary-result p { margin:6px 0!important; }
      .tt-s19-primary-result .tt-s19-source {
        margin-top:12px;
        padding:12px 14px;
        border:1px solid #d3e1dc;
        border-radius:9px;
        background:#fff;
      }
      .tt-s19-primary-result .tt-s19-source blockquote {
        margin:8px 0 0;
        padding:10px 12px;
        border-left:3px solid #1f6656;
        background:#f7faf8;
        font-size:13px;
        line-height:1.5;
      }
      .tt-s19-secondary-note {
        margin-top:10px!important;
        color:#66736f!important;
        font-size:13px!important;
      }

      @media (max-width:1000px) {
        .app-header nav button[data-nav] { font-size:16px!important; padding:0 14px!important; min-height:46px!important; }
        #active-payer-select { width:145px!important; max-width:145px!important; }
        #cz-section19-facts > label { grid-template-columns:1fr!important; grid-template-areas:"q" "control" "help"!important; }
      }
    `;
    document.head.append(style);
  }

  const flagCz = `<span class="tt-final-flag" aria-hidden="true"><svg viewBox="0 0 30 20" xmlns="http://www.w3.org/2000/svg"><rect width="30" height="10" fill="#fff"/><rect y="10" width="30" height="10" fill="#d7141a"/><path d="M0 0L13 10L0 20Z" fill="#11457e"/></svg></span>`;
  const flagGb = `<span class="tt-final-flag" aria-hidden="true"><svg viewBox="0 0 60 30" xmlns="http://www.w3.org/2000/svg"><rect width="60" height="30" fill="#012169"/><path d="M0 0L60 30M60 0L0 30" stroke="#fff" stroke-width="6"/><path d="M0 0L60 30M60 0L0 30" stroke="#c8102e" stroke-width="3"/><path d="M30 0V30M0 15H60" stroke="#fff" stroke-width="10"/><path d="M30 0V30M0 15H60" stroke="#c8102e" stroke-width="6"/></svg></span>`;

  function refreshLanguageControl() {
    const control = document.querySelector("#taxtreat-language-controls");
    if (!control) return;
    const mini = control.querySelector(".tt-lang-mini");
    if (!mini) return;
    mini.querySelectorAll("button").forEach((button) => {
      const code = button.dataset.lang || (/EN/i.test(button.textContent) ? "en" : "cs");
      button.dataset.lang = code;
      button.innerHTML = `${code === "en" ? flagGb : flagCz}<span>${code === "en" ? "EN" : "CZ"}</span>`;
    });
    const header = document.querySelector(".app-header");
    if (header && control.parentElement !== header) {
      const account = header.querySelector(".account");
      header.insertBefore(control, account || null);
    }
  }

  function refreshHeaderCopy() {
    const label = document.querySelector(".app-header .payer-context > span");
    if (label) label.textContent = isEn() ? "ACTIVE PAYER" : "AKTIVNÍ PLÁTCE";
    refreshLanguageControl();
  }

  function facts() {
    return state.payload?.facts && typeof state.payload.facts === "object" ? state.payload.facts : {};
  }

  function normalizeBool(value) {
    if (value === true || value === false) return value;
    if (typeof value !== "string") return null;
    const v = value.trim().toLowerCase();
    if (["true","yes","ano","1"].includes(v)) return true;
    if (["false","no","ne","0"].includes(v)) return false;
    return null;
  }

  function firstFact(...patterns) {
    for (const [key, value] of Object.entries(facts())) {
      if (patterns.some((p) => p.test(key))) return value;
    }
    return undefined;
  }

  function boolFact(...patterns) { return normalizeBool(firstFact(...patterns)); }

  function section19EngineApplies() {
    const a = state.analysis || {};
    if (a.tax_treatment === "domestic_exemption" || a.candidate_tax_treatment === "domestic_exemption") return true;
    return (a.layer_results || []).some((item) => item.layer === "eu_relief" && item.outcome === "applicable" && String(item.rule_id || "").includes("DIVIDEND"));
  }

  function section19FallbackApplies() {
    if (String(state.payload?.source_country || "CZ").toUpperCase() !== "CZ" || state.payload?.income_type !== "dividend") return false;
    const companyForm = document.querySelector('[name="section19_company_form"]')?.value;
    const taxable = document.querySelector('[name="section19_taxable_company"]')?.value;
    const ownership = Number(facts().ownership_percent ?? firstFact(/ownership.*percent/i,/share.*percent/i));
    const direct = facts().direct_ownership === true ? true : boolFact(/direct.*ownership/i);
    const beneficial = boolFact(/beneficial.*owner/i);
    const pe = boolFact(/permanent.*establishment.*connection/i,/pe.*connection/i);
    const holdingMonths = Number(facts().holding_period_months ?? firstFact(/holding.*month/i));
    return companyForm === "true" && taxable === "true" && Number.isFinite(ownership) && ownership >= 10 && direct === true && beneficial === true && pe === false && Number.isFinite(holdingMonths) && holdingMonths >= 12;
  }

  function s19Applies() { return section19EngineApplies() || section19FallbackApplies(); }

  function textNodes(root) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    return nodes;
  }

  function replaceExact(root, from, to) {
    textNodes(root).forEach((node) => {
      if (node.nodeValue.trim() === from) node.nodeValue = node.nodeValue.replace(from, to);
    });
  }

  function replaceContains(root, re, to) {
    textNodes(root).forEach((node) => {
      if (re.test(node.nodeValue)) node.nodeValue = node.nodeValue.replace(re, to);
    });
  }

  function step4Root() {
    return document.querySelector('.flow-step[data-step="4"]') || document.querySelector('[data-step="4"]') || document.body;
  }

  function findCardByText(root, patterns) {
    const elements = [...root.querySelectorAll("section,article,.card,.panel,div")];
    return elements.find((el) => patterns.some((p) => p.test(el.textContent || ""))) || null;
  }

  function renderSection19Primary() {
    if (!s19Applies()) return;
    const root = step4Root();
    const en = isEn();

    /* Remove the legally wrong rate language in the visible result. */
    replaceExact(root, "0 %", en ? "Exempt" : "Osvobozeno");
    replaceExact(root, "0%", en ? "Exempt" : "Osvobozeno");
    replaceExact(root, "Použitá sazba", "Daňový režim");
    replaceExact(root, "Applied rate", "Tax treatment");
    replaceExact(root, "Sazba české srážkové daně", "Česká srážková daň");
    replaceExact(root, "Czech withholding tax rate", "Czech withholding tax");
    replaceContains(root, /Česká srážková daň je proto\s*0\s*%\.?/gi, "Česká srážková daň se neuplatní z důvodu osvobození podle § 19 ZDP.");
    replaceContains(root, /Czech withholding tax is therefore\s*0\s*%\.?/gi, "Czech withholding tax does not apply because the dividend is exempt under Section 19.");

    /* Correct the primary legal rule. */
    replaceContains(root, /Použitý právní základ\s*:?\s*čl\.?\s*10[^\n]*/gi, "Použitý právní základ: § 19 ZDP");
    replaceContains(root, /Applied legal (?:basis|rule)\s*:?\s*Article\s*10[^\n]*/gi, "Applied legal basis: Section 19 of the Czech Income Taxes Act");

    let box = root.querySelector("#tt-s19-primary-result");
    if (!box) {
      box = document.createElement("section");
      box.id = "tt-s19-primary-result";
      box.className = "tt-s19-primary-result";

      const legalSources = findCardByText(root, [/Právní podklady/i,/Legal sources/i]);
      const appliedRule = findCardByText(root, [/Použité právní pravidlo/i,/Applied legal rule/i]);
      const anchor = legalSources || appliedRule;
      if (anchor?.parentNode) anchor.parentNode.insertBefore(box, anchor);
      else root.append(box);
    }

    box.innerHTML = en ? `
      <div class="tt-s19-badge">SECTION 19 APPLIES</div>
      <h2>Domestic exemption under Section 19</h2>
      <p><strong>Primary legal basis: Section 19 of the Czech Income Taxes Act.</strong></p>
      <p>Based on the entered facts, the dividend is exempt under Czech domestic law. Czech withholding tax therefore does not apply. The treaty is relevant only as secondary protection and is not the legal basis for this exemption.</p>
      <div class="tt-s19-source">
        <strong>Relevant Czech legal provision</strong>
        <blockquote><strong>Reading aid:</strong> a profit share paid by a Czech subsidiary to its qualifying parent company is exempt where the statutory parent/subsidiary conditions are met. The relevant conditions follow principally from Section 19(1)(ze), Section 19(3), Section 19(4) and Section 19(6).</blockquote>
        <p><a href="${SECTION19_URL}" target="_blank" rel="noopener">Official Czech text in e-Sbírka ↗</a></p>
      </div>
      <p class="tt-s19-secondary-note"><strong>Treaty:</strong> secondary limitation of Czech taxing rights only; not the primary legal basis for this result.</p>` : `
      <div class="tt-s19-badge">§ 19 ZDP SE POUŽIJE</div>
      <h2>Vnitrostátní osvobození podle § 19 ZDP</h2>
      <p><strong>Primární právní titul: § 19 ZDP.</strong></p>
      <p>Podle zadaných údajů je dividenda osvobozena podle českého vnitrostátního práva. Česká srážková daň se proto neuplatní. Smlouva je relevantní pouze jako sekundární ochrana a není právním titulem tohoto osvobození.</p>
      <div class="tt-s19-source">
        <strong>Relevantní text § 19 ZDP</strong>
        <blockquote>§ 19 odst. 1 písm. ze) bod 1 osvobozuje příjmy z podílu na zisku vyplácené dceřinou společností mateřské společnosti při splnění zákonných podmínek. Navazující podmínky vyplývají zejména z § 19 odst. 3, 4 a 6 ZDP.</blockquote>
        <p><a href="${SECTION19_URL}" target="_blank" rel="noopener">Oficiální znění v e-Sbírce ↗</a></p>
      </div>
      <p class="tt-s19-secondary-note"><strong>SZDZ:</strong> pouze sekundární omezení českého práva zdanit; není primárním právním titulem tohoto výsledku.</p>`;

    /* Rename treaty card rather than deleting it. */
    const treatyCard = findCardByText(root, [/čl\.?\s*10.*Rakous/i,/Article\s*10.*Austr/i,/Smlouva.*zamezení dvojího zdanění/i,/treaty.*double taxation/i]);
    if (treatyCard && !treatyCard.contains(box)) {
      const heading = treatyCard.querySelector("h2,h3,strong");
      if (heading && !/§\s*19|Section 19/i.test(heading.textContent)) {
        heading.textContent = en ? "Secondary treaty protection" : "Sekundární smluvní ochrana";
      }
    }
  }

  function refreshUi() {
    installStyles();
    refreshHeaderCopy();
    renderSection19Primary();
  }

  const previousFetch = window.fetch.bind(window);
  window.fetch = async function taxTreatWebFinalFetch(resource, options = {}) {
    const url = typeof resource === "string" ? resource : resource?.url || "";
    if (url.endsWith("/analysis/intake") && options?.body) {
      try { state.payload = JSON.parse(String(options.body)); } catch (_e) {}
    }
    const response = await previousFetch(resource, options);
    if (url.endsWith("/analysis/intake") && response.ok) {
      try {
        const body = await response.clone().json();
        state.analysis = body?.analysis || body || null;
        window.setTimeout(refreshUi, 0);
      } catch (_e) {}
    }
    return response;
  };

  document.addEventListener("change", (event) => {
    if (event.target?.id === "taxtreat-ui-language" || ["section19_company_form","section19_taxable_company"].includes(event.target?.name)) {
      window.setTimeout(refreshUi, 0);
    }
  }, true);

  document.addEventListener("click", (event) => {
    if (event.target?.closest("[data-nav],[data-next-step],[data-flow-step],[data-start-flow],#taxtreat-language-controls")) {
      window.setTimeout(refreshUi, 0);
      window.setTimeout(refreshUi, 120);
    }
  }, true);

  window.addEventListener("popstate", () => window.setTimeout(refreshUi, 0));
  refreshUi();
})();
