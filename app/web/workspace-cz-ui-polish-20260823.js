(() => {
  "use strict";

  const SECTION19_URL = "https://e-sbirka.gov.cz/sb/1992/586";
  let languageObserver = null;
  let section19Observer = null;
  let repairingFlags = false;
  let repairingSection19 = false;

  function uiLanguage() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
  }

  function isCzech() {
    return uiLanguage() === "cs";
  }

  function installStyles() {
    let style = document.querySelector("#tt-cz-ui-polish-20260823");
    if (!style) {
      style = document.createElement("style");
      style.id = "tt-cz-ui-polish-20260823";
      document.head.append(style);
    }

    style.textContent = `
      [data-view="dashboard"] .dashboard-summary .onboarding{display:none!important}
      [data-view="dashboard"] .dashboard-summary:has(.onboarding){display:none!important}

      /* Payers: every row uses exactly the same seven columns. */
      [data-view="payers"] .payer-record{
        display:grid!important;
        grid-template-columns:48px minmax(230px,1fr) 88px 88px 88px 190px 82px!important;
        column-gap:18px!important;
        align-items:center!important;
      }
      [data-view="payers"] .payer-record > :nth-child(1){grid-column:1!important}
      [data-view="payers"] .payer-record > :nth-child(2){grid-column:2!important;min-width:0!important}
      [data-view="payers"] .payer-record > :nth-child(3){grid-column:3!important;text-align:center!important}
      [data-view="payers"] .payer-record > :nth-child(4){grid-column:4!important;text-align:center!important}
      [data-view="payers"] .payer-record > :nth-child(5){grid-column:5!important;text-align:center!important}
      [data-view="payers"] .payer-record > :nth-child(6){grid-column:6!important;justify-self:stretch!important}
      [data-view="payers"] .payer-record > :nth-child(7){grid-column:7!important;justify-self:stretch!important}
      [data-view="payers"] .payer-record > *{
        align-self:center!important;
        margin-top:0!important;
        margin-bottom:0!important;
      }
      [data-view="payers"] .payer-record .avatar{
        width:42px!important;height:42px!important;min-width:42px!important;
        font-size:17px!important;font-weight:750!important;
        display:flex!important;align-items:center!important;justify-content:center!important;
      }
      [data-view="payers"] .payer-record button{
        width:100%!important;height:38px!important;min-height:38px!important;
        margin:0!important;padding:0 12px!important;
        display:inline-flex!important;align-items:center!important;justify-content:center!important;
        font-size:14px!important;font-weight:650!important;border-radius:9px!important;
        white-space:nowrap!important;
      }
      [data-view="payers"] .payer-record .secondary{box-shadow:none!important}

      /* Recipients: lighter controls only in the list view. */
      [data-view="recipients"] .recipient-row{align-items:center!important}
      [data-view="recipients"] .recipient-row .avatar{
        width:42px!important;height:42px!important;min-width:42px!important;
        font-size:17px!important;font-weight:750!important;
      }
      [data-view="recipients"] .recipient-row button{
        min-height:38px!important;height:38px!important;padding:0 14px!important;
        font-size:14px!important;font-weight:650!important;border-radius:9px!important;
        align-self:center!important;margin:0!important;
      }

      /* Stable SVG language flags. */
      #taxtreat-language-controls .tt-lang-mini button{
        display:inline-flex!important;align-items:center!important;gap:5px!important;
      }
      #taxtreat-language-controls .tt-lang-flag{
        width:18px;height:12px;display:inline-block;flex:0 0 auto;
        border-radius:1px;overflow:hidden;box-shadow:0 0 0 1px rgba(255,255,255,.22);
      }
      #taxtreat-language-controls .tt-lang-flag svg{display:block;width:100%;height:100%}

      .tt-no-review-items{display:none!important}
      .flow-step[data-step="4"] .dashboard-grid.tt-summary-only{grid-template-columns:1fr!important}
      #cz-section19-result.tt-section19-applicable .tt-section19-source{display:none!important}
      .flow-step[data-step="4"].tt-section19-active > article.reason{display:none!important}
      #workspace-citations details.citation-excerpt{margin-top:10px}
      #workspace-citations details.citation-excerpt:not([open]) blockquote{display:none}

      /* Step 3 desktop: exactly one row, 3 equal-width fields + a narrower currency field. */
      .flow-step[data-step="3"] .payment-form .field-grid{
        display:grid!important;
        grid-template-columns:minmax(0,1fr) minmax(0,1fr) minmax(0,1fr) 128px!important;
        gap:18px!important;
        align-items:start!important;
      }
      .flow-step[data-step="3"] .payment-form .field-grid > .payment-income-field{
        grid-column:1!important;grid-row:1!important;width:auto!important;min-width:0!important;max-width:none!important;
      }
      .flow-step[data-step="3"] .payment-form .field-grid > .transaction-date-field{
        grid-column:2!important;grid-row:1!important;width:auto!important;min-width:0!important;max-width:none!important;
      }
      .flow-step[data-step="3"] .payment-form .field-grid > .payment-amount-field{
        grid-column:3!important;grid-row:1!important;width:auto!important;min-width:0!important;max-width:none!important;
      }
      .flow-step[data-step="3"] .payment-form .field-grid > .payment-currency-field{
        grid-column:4!important;grid-row:1!important;width:auto!important;min-width:0!important;max-width:none!important;
      }
      .flow-step[data-step="3"] #workspace-exchange-rate-field{
        grid-column:3 / 5!important;grid-row:2!important;max-width:none!important;
      }
      @media (max-width:1050px){
        .flow-step[data-step="3"] .payment-form .field-grid{grid-template-columns:1fr 1fr!important}
        .flow-step[data-step="3"] .payment-form .field-grid > .payment-income-field,
        .flow-step[data-step="3"] .payment-form .field-grid > .transaction-date-field,
        .flow-step[data-step="3"] .payment-form .field-grid > .payment-amount-field,
        .flow-step[data-step="3"] .payment-form .field-grid > .payment-currency-field,
        .flow-step[data-step="3"] #workspace-exchange-rate-field{grid-column:auto!important;grid-row:auto!important}
      }
      @media (max-width:680px){
        .flow-step[data-step="3"] .payment-form .field-grid{grid-template-columns:1fr!important}
      }
    `;
  }

  function enforceMainNavTypography() {
    const width = window.innerWidth || 1440;
    const size = width <= 1080 ? "16px" : width <= 1320 ? "17px" : "18px";
    document.querySelectorAll('.app-header nav button[data-nav]').forEach((button) => {
      button.style.setProperty("font-size", size, "important");
      button.style.setProperty("font-weight", "700", "important");
      button.style.setProperty("line-height", "1.1", "important");
      button.style.setProperty("letter-spacing", "-0.01em", "important");
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

  function repairLanguageFlags() {
    if (repairingFlags) return;
    const controls = document.querySelector("#taxtreat-language-controls");
    if (!controls) return;
    repairingFlags = true;
    try {
      controls.querySelectorAll(".tt-lang-mini button").forEach((button) => {
        const lang = button.dataset.lang;
        if (!["cs", "en"].includes(lang)) return;
        const expected = lang === "cs" ? "CZ" : "EN";
        const hasFlag = Boolean(button.querySelector(".tt-lang-flag"));
        const text = (button.textContent || "").trim();
        if (!hasFlag || text !== expected) {
          button.replaceChildren(svgFlag(lang), document.createTextNode(expected));
        }
        const active = lang === uiLanguage();
        button.dataset.active = String(active);
        button.setAttribute("aria-pressed", String(active));
      });
    } finally {
      repairingFlags = false;
    }
  }

  function ensureLanguageObserver() {
    const controls = document.querySelector("#taxtreat-language-controls");
    if (!controls || languageObserver) return;
    languageObserver = new MutationObserver(() => {
      if (!repairingFlags) window.setTimeout(repairLanguageFlags, 0);
    });
    languageObserver.observe(controls, { childList:true, subtree:true, characterData:true });
  }

  function replaceText(root, pattern, replacement) {
    if (!root) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      const current = node.nodeValue || "";
      pattern.lastIndex = 0;
      if (pattern.test(current)) {
        pattern.lastIndex = 0;
        node.nodeValue = current.replace(pattern, replacement);
      }
      pattern.lastIndex = 0;
    });
  }

  function generalizeDomesticReliefWording() {
    const step3 = document.querySelector('.flow-step[data-step="3"]');
    replaceText(step3, /pro\s+možné\s+osvobození\s+podle\s+§\s*19\s*ZDP/gi, "pro možnost osvobození podle vnitrostátní legislativy");
    replaceText(step3, /pro\s+osvobození\s+podle\s+§\s*19\s*ZDP/gi, "pro možnost osvobození podle vnitrostátní legislativy");
    replaceText(step3, /k\s+možnému\s+osvobození\s+podle\s+§\s*19\s*ZDP/gi, "pro možnost osvobození podle vnitrostátní legislativy");
  }

  function section19Applies(root) {
    const box = root?.querySelector("#cz-section19-result");
    if (!box) return false;
    return box.classList.contains("tt-section19-applicable") || /(?:§\s*19\s*ZDP\s*se\s*použije|osvobození\s+podle\s+§\s*19\s*ZDP\s+se\s+uplatní)/i.test(box.textContent || "");
  }

  function simplifySection19Result(root) {
    const applies = section19Applies(root);
    root.classList.toggle("tt-section19-active", applies);
    if (!applies) return;

    const box = root.querySelector("#cz-section19-result");
    const status = box?.querySelector(".tt-legal-status");
    const heading = box?.querySelector("h1,h2,h3,h4");
    const paragraph = box?.querySelector("p");
    if (status) status.textContent = "Osvobození podle § 19 ZDP se uplatní";
    if (heading) heading.textContent = "Vnitrostátní osvobození podle § 19 ZDP";
    if (paragraph) paragraph.textContent = "Při zadaných údajích jsou splněny podmínky osvobození podle § 19 ZDP. Příjem proto nepodléhá české srážkové dani. Smluvní úprava představuje pouze sekundární ochranu.";
  }

  function ensureSection19Observer() {
    const box = document.querySelector("#cz-section19-result");
    if (!box || section19Observer) return;
    section19Observer = new MutationObserver(() => {
      if (repairingSection19 || !isCzech()) return;
      const root = document.querySelector('.flow-step[data-step="4"]');
      if (!root) return;
      repairingSection19 = true;
      try {
        simplifySection19Result(root);
      } finally {
        repairingSection19 = false;
      }
    });
    section19Observer.observe(box, { childList:true, subtree:true, characterData:true, attributes:true, attributeFilter:["class"] });
  }

  function hideEmptyConditions(root) {
    const actions = root.querySelector("#workspace-actions");
    if (!actions) return;
    const realItems = [...actions.children].filter((item) => !item.classList.contains("complete"));
    const card = actions.closest("article.card") || actions.parentElement;
    const grid = card?.parentElement;
    if (!realItems.length) {
      actions.querySelectorAll(".complete").forEach((item) => item.remove());
      card?.classList.add("tt-no-review-items");
      grid?.classList.add("tt-summary-only");
    } else {
      card?.classList.remove("tt-no-review-items");
      grid?.classList.remove("tt-summary-only");
    }
  }

  function makeSection19Citation() {
    const card = document.createElement("article");
    card.className = "citation-card tt-s19-citation";
    const role = document.createElement("span");
    role.className = "citation-role";
    role.textContent = "1. Použité pravidlo";
    const title = document.createElement("strong");
    title.textContent = "Zákon č. 586/1992 Sb., o daních z příjmů · § 19";
    const link = document.createElement("a");
    link.href = SECTION19_URL;
    link.target = "_blank";
    link.rel = "noreferrer noopener";
    link.textContent = "Otevřít zdroj ↗";
    const detail = document.createElement("p");
    detail.textContent = "Vnitrostátní osvobození podílu na zisku použité pro tento výsledek.";
    const disclosure = document.createElement("details");
    disclosure.className = "citation-excerpt";
    disclosure.open = false;
    const summary = document.createElement("summary");
    summary.textContent = "Relevantní ustanovení";
    const excerpt = document.createElement("blockquote");
    excerpt.textContent = "§ 19 odst. 1 písm. ze), § 19 odst. 3, § 19 odst. 6 a § 19 odst. 11 ZDP.";
    disclosure.append(summary, excerpt);
    card.append(role, title, link, detail, disclosure);
    return card;
  }

  function plainExcerpt(details) {
    if (!details) return;
    details.open = false;
    details.querySelectorAll("mark.legal-decisive-passage").forEach((mark) => mark.replaceWith(document.createTextNode(mark.textContent || "")));
  }

  function reorderLegalSources(root) {
    if (!section19Applies(root)) return;
    const citations = root.querySelector("#workspace-citations");
    if (!citations) return;

    let cards = [...citations.querySelectorAll(":scope > .citation-card")];
    let s19 = cards.find((card) => /§\s*19(?:\D|$)/i.test(card.textContent || ""));
    if (!s19) {
      s19 = makeSection19Citation();
      citations.prepend(s19);
      cards = [s19, ...cards];
    }

    const section36 = cards.find((card) => /§\s*36(?:\D|$)/i.test(card.textContent || ""));
    const treaty = cards.filter((card) => /Smlouva o zamezení dvojího zdanění/i.test(card.textContent || ""));
    const rest = cards.filter((card) => card !== s19 && card !== section36 && !treaty.includes(card));
    const ordered = [s19, section36, ...treaty, ...rest].filter(Boolean);
    ordered.forEach((card) => citations.append(card));

    ordered.forEach((card, index) => {
      const role = card.querySelector(".citation-role");
      const detail = card.querySelector("p");
      if (card === s19) {
        if (role) role.textContent = "1. Použité pravidlo";
      } else if (card === section36) {
        if (role) role.textContent = `${index + 1}. Obecná česká sazba bez osvobození`;
        if (detail) detail.textContent = "Pokud by se neuplatnilo osvobození podle § 19 ZDP ani příznivější smluvní pravidlo, česká vnitrostátní úprava stanoví u tohoto příjmu sazbu 15 %.";
      } else if (treaty.includes(card)) {
        if (role) role.textContent = `${index + 1}. Sekundární smluvní ochrana`;
      } else if (role) {
        role.textContent = role.textContent.replace(/^\d+\./, `${index + 1}.`);
      }
    });

    treaty.forEach((card) => plainExcerpt(card.querySelector("details.citation-excerpt")));
    plainExcerpt(s19.querySelector("details.citation-excerpt"));
  }

  function refreshStep4() {
    if (!isCzech()) return;
    const root = document.querySelector('.flow-step[data-step="4"]');
    if (!root) return;
    repairingSection19 = true;
    try {
      simplifySection19Result(root);
      hideEmptyConditions(root);
      reorderLegalSources(root);
    } finally {
      repairingSection19 = false;
    }
  }

  function refresh() {
    installStyles();
    enforceMainNavTypography();
    repairLanguageFlags();
    ensureLanguageObserver();
    ensureSection19Observer();
    if (!isCzech()) return;
    generalizeDomesticReliefWording();
    refreshStep4();
  }

  function scheduleRefreshes() {
    [0, 80, 220, 600, 1200].forEach((delay) => window.setTimeout(refresh, delay));
  }

  const previousFetch = window.fetch.bind(window);
  window.fetch = async function taxTreatCzUiPolishFetch(resource, options = {}) {
    const response = await previousFetch(resource, options);
    const url = typeof resource === "string" ? resource : resource?.url || "";
    if (url.endsWith("/analysis/intake")) scheduleRefreshes();
    return response;
  };

  document.addEventListener("click", (event) => {
    if (event.target?.closest("[data-nav],[data-next-step],[data-flow-step],[data-start-flow],#workspace-submit,#taxtreat-language-controls")) {
      scheduleRefreshes();
    }
  }, true);

  document.addEventListener("change", (event) => {
    if (event.target?.id === "taxtreat-ui-language" || ["section19_company_form", "section19_taxable_company"].includes(event.target?.name)) {
      scheduleRefreshes();
    }
  }, true);

  window.addEventListener("resize", () => window.setTimeout(enforceMainNavTypography, 50));
  refresh();
})();
