(() => {
  "use strict";

  let lastAnalysis = null;

  function uiLanguage() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
  }

  function isCzech() {
    return uiLanguage() === "cs";
  }

  function installStyles() {
    let style = document.querySelector("#tt-cz-final-hardening-20260823");
    if (!style) {
      style = document.createElement("style");
      style.id = "tt-cz-final-hardening-20260823";
      document.head.append(style);
    }

    style.textContent = `
      /* PAYERS: actual DOM = avatar | company copy | dl(metrics) | actions. */
      [data-view="payers"] .payer-record{
        display:grid!important;
        grid-template-columns:52px minmax(300px,1fr) 240px 330px!important;
        column-gap:22px!important;
        align-items:center!important;
        min-height:142px!important;
      }
      [data-view="payers"] .payer-record > .avatar{
        grid-column:1!important;
        justify-self:center!important;
        align-self:center!important;
      }
      [data-view="payers"] .payer-record > .avatar + div{
        grid-column:2!important;
        min-width:0!important;
        align-self:center!important;
      }
      [data-view="payers"] .payer-record > .avatar + div h2,
      [data-view="payers"] .payer-record > .avatar + div p{
        margin-left:0!important;
        margin-right:0!important;
      }
      [data-view="payers"] .payer-record > dl{
        grid-column:3!important;
        display:grid!important;
        grid-template-columns:repeat(3,minmax(0,1fr))!important;
        gap:14px!important;
        width:100%!important;
        margin:0!important;
        align-self:center!important;
      }
      [data-view="payers"] .payer-record > dl > div{
        display:grid!important;
        grid-template-rows:18px 26px!important;
        gap:5px!important;
        justify-items:center!important;
        align-items:center!important;
        margin:0!important;
        min-width:0!important;
        text-align:center!important;
      }
      [data-view="payers"] .payer-record > dl dt,
      [data-view="payers"] .payer-record > dl dd{
        margin:0!important;
        padding:0!important;
        line-height:1!important;
        white-space:nowrap!important;
      }
      [data-view="payers"] .payer-record > .payer-actions{
        grid-column:4!important;
        display:grid!important;
        grid-template-columns:minmax(210px,1fr) 110px!important;
        gap:12px!important;
        width:100%!important;
        margin:0!important;
        padding-top:23px!important;
        align-self:center!important;
      }
      [data-view="payers"] .payer-record > .payer-actions button{
        width:100%!important;
        min-width:0!important;
        height:40px!important;
        min-height:40px!important;
        margin:0!important;
        padding:0 12px!important;
        display:flex!important;
        align-items:center!important;
        justify-content:center!important;
        white-space:nowrap!important;
        line-height:1!important;
        font-size:14px!important;
      }

      /* RECIPIENT LIST: align avatar, two-line copy and status badge around one visual centre. */
      [data-view="recipients"] .recipient-row{
        display:grid!important;
        grid-template-columns:52px minmax(240px,auto) max-content minmax(0,1fr) max-content max-content!important;
        column-gap:18px!important;
        align-items:center!important;
      }
      [data-view="recipients"] .recipient-row > .avatar{
        grid-column:1!important;
        justify-self:center!important;
        align-self:center!important;
      }
      [data-view="recipients"] .recipient-row > .avatar + div{
        grid-column:2!important;
        display:grid!important;
        grid-template-rows:auto auto!important;
        row-gap:7px!important;
        align-content:center!important;
        margin:0!important;
      }
      [data-view="recipients"] .recipient-row > .avatar + div h2,
      [data-view="recipients"] .recipient-row > .avatar + div p{
        margin:0!important;
      }
      [data-view="recipients"] .recipient-row > .badge{
        grid-column:3!important;
        align-self:center!important;
        justify-self:start!important;
        margin:0!important;
      }

      /* STEP 3: exactly one desktop row, first 3 equal, currency narrow. */
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
        height:26px!important;
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

      /* When Section 19 is the applied domestic exemption, treaty rule card is not shown as applied. */
      .flow-step[data-step="4"].tt-section19-authoritative > article.reason{display:none!important}

      @media (max-width:1050px){
        [data-view="payers"] .payer-record{
          grid-template-columns:48px minmax(0,1fr)!important;
          row-gap:14px!important;
        }
        [data-view="payers"] .payer-record > dl{grid-column:2!important;grid-row:2!important}
        [data-view="payers"] .payer-record > .payer-actions{
          grid-column:2!important;grid-row:3!important;max-width:330px!important;padding-top:0!important;
        }
        .flow-step[data-step="3"] .payment-form .field-grid{grid-template-columns:1fr 1fr!important}
        .flow-step[data-step="3"] .payment-income-field,
        .flow-step[data-step="3"] .transaction-date-field,
        .flow-step[data-step="3"] .payment-amount-field,
        .flow-step[data-step="3"] .payment-currency-field,
        .flow-step[data-step="3"] #workspace-exchange-rate-field{grid-column:auto!important;grid-row:auto!important}
      }
    `;
  }

  function section19Box() {
    return document.querySelector('.flow-step[data-step="4"] #cz-section19-result');
  }

  function section19IsApplicableFromUi() {
    const box = section19Box();
    if (!box) return false;
    const text = box.textContent || "";
    return box.classList.contains("tt-section19-applicable") ||
      /Osvobození\s+podle\s+§\s*19\s*ZDP\s+se\s+uplatní/i.test(text) ||
      /§\s*19\s*ZDP\s+se\s+použije/i.test(text);
  }

  function selectedCitation(analysis) {
    const selected = String(analysis?.selected_rule_id || analysis?.candidate_rule_id || "");
    return (analysis?.citations || analysis?.legal_path || []).find((item) => String(item.rule_id || "") === selected) || null;
  }

  function engineDomesticExemption() {
    if (!lastAnalysis) return false;
    const citation = selectedCitation(lastAnalysis);
    return lastAnalysis.tax_treatment === "domestic_exemption" || String(citation?.legal_layer || "") === "eu_relief";
  }

  function section19Authoritative() {
    return section19IsApplicableFromUi() || engineDomesticExemption();
  }

  function setText(node, text) {
    if (node && node.textContent !== text) node.textContent = text;
  }

  function normalizeSection19Result() {
    if (!isCzech()) return;
    const root = document.querySelector('.flow-step[data-step="4"]');
    const box = section19Box();
    if (!root || !box) return;

    const authoritative = section19Authoritative();
    root.classList.toggle("tt-section19-authoritative", authoritative);

    const status = box.querySelector(".tt-legal-status");
    const heading = box.querySelector("h1,h2,h3,h4");
    const paragraph = box.querySelector("p");

    if (authoritative) {
      box.classList.add("tt-section19-applicable");
      setText(status, "Osvobození podle § 19 ZDP se uplatní");
      setText(heading, "Vnitrostátní osvobození podle § 19 ZDP");
      setText(paragraph, "Při zadaných údajích jsou splněny podmínky osvobození podle § 19 ZDP. Příjem proto nepodléhá české srážkové dani.");
    } else {
      const current = status?.textContent || "";
      if (/§\s*19\s*ZDP\s*posouzen/i.test(current)) {
        setText(status, "Posouzení vnitrostátního osvobození");
      }
      const currentParagraph = paragraph?.textContent || "";
      if (/Níže uvedený právní titul musí být s tímto výsledkem konzistentní/i.test(currentParagraph)) {
        setText(paragraph, "Možnost vnitrostátního osvobození byla posouzena před použitím smluvního pravidla.");
      }
    }
  }

  function enhanceSection19LegalSource() {
    if (!isCzech() || !section19Authoritative()) return;
    const root = document.querySelector('.flow-step[data-step="4"]');
    const citations = root?.querySelector("#workspace-citations");
    if (!citations) return;
    const s19 = [...citations.querySelectorAll(":scope > .citation-card")].find((card) => /§\s*19(?:\D|$)/i.test(card.textContent || ""));
    if (!s19) return;
    const details = s19.querySelector("details.citation-excerpt");
    const block = details?.querySelector("blockquote");
    if (!details || !block) return;
    const desired = [
      "§ 19 odst. 1 písm. ze) – stanoví osvobození podílu na zisku při splnění zákonných podmínek.",
      "§ 19 odst. 3 – vymezuje podmínky vztahující se ke kvalifikovaným společnostem a jejich daňovému postavení.",
      "§ 19 odst. 6 – upravuje podmínky účasti a časového testu držby.",
      "§ 19 odst. 11 – obsahuje navazující podmínky a vymezení relevantní pro osvobození."
    ].join("\n");
    setText(block, desired);
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
    enhanceSection19LegalSource();
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
