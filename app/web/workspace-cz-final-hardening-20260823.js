(() => {
  "use strict";

  let lastAnalysis = null;

  function isCzech() {
    return (document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs") === "cs";
  }

  function installStyles() {
    let style = document.querySelector("#tt-cz-final-hardening-20260823");
    if (!style) {
      style = document.createElement("style");
      style.id = "tt-cz-final-hardening-20260823";
      document.head.append(style);
    }

    style.textContent = `
      /* PAYER LIST: actual DOM is avatar | copy | dl(metrics) | actions. */
      [data-view="payers"] .payer-record{
        display:grid!important;
        grid-template-columns:52px minmax(230px,1fr) 210px 260px!important;
        column-gap:16px!important;
        align-items:center!important;
      }
      [data-view="payers"] .payer-record > .avatar{
        grid-column:1!important;
        justify-self:center!important;
      }
      [data-view="payers"] .payer-record > .avatar + div{
        grid-column:2!important;
        min-width:0!important;
        align-self:center!important;
      }
      [data-view="payers"] .payer-record > dl{
        grid-column:3!important;
        display:grid!important;
        grid-template-columns:repeat(3,minmax(0,1fr))!important;
        gap:10px!important;
        width:100%!important;
        margin:0!important;
        align-items:center!important;
      }
      [data-view="payers"] .payer-record > dl > div{
        display:grid!important;
        grid-template-rows:auto auto!important;
        gap:4px!important;
        justify-items:center!important;
        align-items:center!important;
        margin:0!important;
        min-width:0!important;
        text-align:center!important;
      }
      [data-view="payers"] .payer-record > dl dt,
      [data-view="payers"] .payer-record > dl dd{
        margin:0!important;
        line-height:1.15!important;
        white-space:nowrap!important;
      }
      [data-view="payers"] .payer-record > .payer-actions{
        grid-column:4!important;
        display:grid!important;
        grid-template-columns:minmax(158px,1fr) 88px!important;
        gap:10px!important;
        align-items:center!important;
        width:100%!important;
        margin:0!important;
      }
      [data-view="payers"] .payer-record > .payer-actions button{
        width:100%!important;
        min-width:0!important;
        height:40px!important;
        min-height:40px!important;
        margin:0!important;
        padding:0 10px!important;
        display:flex!important;
        align-items:center!important;
        justify-content:center!important;
        white-space:nowrap!important;
        line-height:1!important;
        font-size:14px!important;
      }
      @media (max-width:900px){
        [data-view="payers"] .payer-record{
          grid-template-columns:48px minmax(0,1fr)!important;
          row-gap:14px!important;
        }
        [data-view="payers"] .payer-record > dl{
          grid-column:2!important;
          grid-row:2!important;
        }
        [data-view="payers"] .payer-record > .payer-actions{
          grid-column:2!important;
          grid-row:3!important;
          max-width:300px!important;
        }
      }

      /* STEP 3: one desktop row, first 3 equal, currency narrow; all controls share one top line. */
      .flow-step[data-step="3"] .payment-form .field-grid{
        display:grid!important;
        grid-template-columns:repeat(3,minmax(0,1fr)) 120px!important;
        column-gap:18px!important;
        row-gap:10px!important;
        align-items:start!important;
      }
      .flow-step[data-step="3"] .payment-form .field-grid > .payment-income-field,
      .flow-step[data-step="3"] .payment-form .field-grid > .transaction-date-field,
      .flow-step[data-step="3"] .payment-form .field-grid > .payment-amount-field,
      .flow-step[data-step="3"] .payment-form .field-grid > .payment-currency-field{
        display:grid!important;
        grid-template-rows:26px 60px auto!important;
        align-content:start!important;
        width:100%!important;
        min-width:0!important;
        max-width:none!important;
        margin:0!important;
      }
      .flow-step[data-step="3"] .payment-form .field-grid > label > span:first-child{
        min-height:26px!important;
        margin:0!important;
        display:flex!important;
        align-items:center!important;
      }
      .flow-step[data-step="3"] .payment-form .field-grid > label > input,
      .flow-step[data-step="3"] .payment-form .field-grid > label > select{
        height:60px!important;
        min-height:60px!important;
        margin:0!important;
        align-self:start!important;
      }
      .flow-step[data-step="3"] .payment-form .field-grid > label > small{
        margin-top:8px!important;
        align-self:start!important;
      }
      .flow-step[data-step="3"] .payment-income-field{grid-column:1!important;grid-row:1!important}
      .flow-step[data-step="3"] .transaction-date-field{grid-column:2!important;grid-row:1!important}
      .flow-step[data-step="3"] .payment-amount-field{grid-column:3!important;grid-row:1!important}
      .flow-step[data-step="3"] .payment-currency-field{grid-column:4!important;grid-row:1!important}
      .flow-step[data-step="3"] #workspace-exchange-rate-field{
        grid-column:3 / 5!important;
        grid-row:2!important;
        max-width:none!important;
      }
      @media (max-width:900px){
        .flow-step[data-step="3"] .payment-form .field-grid{grid-template-columns:1fr 1fr!important}
        .flow-step[data-step="3"] .payment-income-field,
        .flow-step[data-step="3"] .transaction-date-field,
        .flow-step[data-step="3"] .payment-amount-field,
        .flow-step[data-step="3"] .payment-currency-field,
        .flow-step[data-step="3"] #workspace-exchange-rate-field{grid-column:auto!important;grid-row:auto!important}
      }

      /* Section 19 result: no duplicate 'Applied legal rule' when domestic exemption is decisive. */
      .flow-step[data-step="4"].tt-final-domestic-exemption > article.reason{display:none!important}
    `;
  }

  function selectedCitation(analysis) {
    const selected = String(analysis?.selected_rule_id || analysis?.candidate_rule_id || "");
    return (analysis?.citations || analysis?.legal_path || []).find((item) => String(item.rule_id || "") === selected) || null;
  }

  function domesticExemptionIsDecisive() {
    const analysis = lastAnalysis;
    if (!analysis) return false;
    const citation = selectedCitation(analysis);
    return analysis.tax_treatment === "domestic_exemption" || String(citation?.legal_layer || "") === "eu_relief";
  }

  function setText(node, text) {
    if (node && node.textContent !== text) node.textContent = text;
  }

  function normalizeSection19Result() {
    if (!isCzech()) return;
    const root = document.querySelector('.flow-step[data-step="4"]');
    const box = root?.querySelector("#cz-section19-result");
    if (!root || !box) return;

    const decisive = domesticExemptionIsDecisive();
    root.classList.toggle("tt-final-domestic-exemption", decisive);

    const status = box.querySelector(".tt-legal-status");
    const heading = box.querySelector("h1,h2,h3,h4");
    const paragraph = box.querySelector("p");

    if (decisive) {
      box.classList.add("tt-section19-applicable");
      setText(status, "Osvobození podle § 19 ZDP se uplatní");
      setText(heading, "Vnitrostátní osvobození podle § 19 ZDP");
      setText(paragraph, "Při zadaných údajích jsou splněny podmínky osvobození podle § 19 ZDP. Příjem proto nepodléhá české srážkové dani. Smluvní úprava představuje pouze sekundární ochranu.");
    } else {
      const current = status?.textContent || "";
      if (/§\s*19\s*ZDP\s*posouzen/i.test(current)) {
        setText(status, "Posouzení vnitrostátního osvobození");
      }
    }
  }

  function normalizeZdpTerminology() {
    if (!isCzech()) return;
    const root = document.querySelector('.flow-step[data-step="4"]');
    if (!root) return;
    const citations = root.querySelector("#workspace-citations");
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      if (citations?.contains(node.parentElement)) return;
      const current = node.nodeValue || "";
      const next = current.replace(/zákona?\s+č\.\s*586\/1992\s*Sb\.,?\s*o\s+daních\s+z\s+příjmů/gi, "ZDP");
      if (next !== current) node.nodeValue = next;
    });
  }

  function svgFlag(lang) {
    const wrap = document.createElement("span");
    wrap.className = "tt-lang-flag";
    wrap.setAttribute("aria-hidden", "true");
    wrap.innerHTML = lang === "cs"
      ? '<svg viewBox="0 0 30 20" xmlns="http://www.w3.org/2000/svg"><rect width="30" height="10" fill="#fff"/><rect y="10" width="30" height="10" fill="#d7141a"/><path d="M0 0 15 10 0 20Z" fill="#11457e"/></svg>'
      : '<svg viewBox="0 0 60 30" xmlns="http://www.w3.org/2000/svg"><rect width="60" height="30" fill="#012169"/><path d="M0 0 60 30M60 0 0 30" stroke="#fff" stroke-width="6"/><path d="M0 0 60 30M60 0 0 30" stroke="#c8102e" stroke-width="2.5"/><path d="M30 0v30M0 15h60" stroke="#fff" stroke-width="10"/><path d="M30 0v30M0 15h60" stroke="#c8102e" stroke-width="6"/></svg>';
    return wrap;
  }

  function repairFlags() {
    const controls = document.querySelector("#taxtreat-language-controls");
    if (!controls) return;
    controls.querySelectorAll(".tt-lang-mini button").forEach((button) => {
      const lang = button.dataset.lang;
      if (!["cs","en"].includes(lang)) return;
      const label = lang === "cs" ? "CZ" : "EN";
      if (!button.querySelector(".tt-lang-flag") || (button.textContent || "").trim() !== label) {
        button.replaceChildren(svgFlag(lang), document.createTextNode(label));
      }
    });
  }

  function refresh() {
    installStyles();
    repairFlags();
    normalizeSection19Result();
    normalizeZdpTerminology();
  }

  function scheduleRefresh() {
    [0, 50, 150, 400, 900].forEach((delay) => window.setTimeout(refresh, delay));
  }

  const previousFetch = window.fetch.bind(window);
  window.fetch = async function taxTreatCzFinalHardeningFetch(resource, options = {}) {
    const response = await previousFetch(resource, options);
    const url = typeof resource === "string" ? resource : resource?.url || "";
    if (url.endsWith("/analysis/intake") && response.ok) {
      try {
        const body = await response.clone().json();
        lastAnalysis = body?.analysis || null;
      } catch (_problem) {
        lastAnalysis = null;
      }
      scheduleRefresh();
    }
    return response;
  };

  document.addEventListener("click", (event) => {
    if (event.target?.closest("[data-nav],[data-next-step],[data-flow-step],[data-start-flow],#workspace-submit,#taxtreat-language-controls")) {
      scheduleRefresh();
    }
  }, true);

  document.addEventListener("change", (event) => {
    if (event.target?.id === "taxtreat-ui-language") scheduleRefresh();
  }, true);

  refresh();
})();
