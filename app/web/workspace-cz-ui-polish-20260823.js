(() => {
  "use strict";

  const SECTION19_URL = "https://e-sbirka.gov.cz/sb/1992/586";

  function isCzech() {
    return (document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs") === "cs";
  }

  function installStyles() {
    if (document.querySelector("#tt-cz-ui-polish-20260823")) return;
    const style = document.createElement("style");
    style.id = "tt-cz-ui-polish-20260823";
    style.textContent = `
      [data-view="dashboard"] .dashboard-summary .onboarding{display:none!important}
      [data-view="dashboard"] .dashboard-summary:has(.onboarding){display:none!important}

      [data-view="payers"] .payer-record .avatar,
      [data-view="recipients"] .recipient-row .avatar{
        width:42px!important;height:42px!important;min-width:42px!important;
        font-size:17px!important;font-weight:750!important;
      }
      [data-view="payers"] .payer-record button,
      [data-view="recipients"] .recipient-row button{
        min-height:38px!important;padding:0 14px!important;
        font-size:14px!important;font-weight:650!important;border-radius:9px!important;
        align-self:center!important;
      }
      [data-view="payers"] .payer-record .secondary,
      [data-view="recipients"] .recipient-row .secondary{box-shadow:none!important}
      [data-view="payers"] .payer-record{
        align-items:center!important;
      }
      [data-view="payers"] .payer-record > *{
        align-self:center;
      }
      [data-view="payers"] .payer-record .payer-actions,
      [data-view="payers"] .payer-record > div:last-child{
        align-items:center!important;
      }

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

      /* Step 3 desktop layout: three normal fields plus a deliberately narrower currency field. */
      .flow-step[data-step="3"] .payment-form .field-grid{
        grid-template-columns:minmax(180px,1.15fr) minmax(190px,1.15fr) minmax(180px,1.15fr) minmax(110px,.55fr)!important;
        align-items:start!important;
      }
      .flow-step[data-step="3"] .payment-currency-field{grid-column:auto!important}
      .flow-step[data-step="3"] #workspace-exchange-rate-field{
        grid-column:3 / 5!important;
        max-width:none!important;
      }
      @media (max-width:1050px){
        .flow-step[data-step="3"] .payment-form .field-grid{grid-template-columns:1fr 1fr!important}
        .flow-step[data-step="3"] #workspace-exchange-rate-field{grid-column:auto!important}
      }
      @media (max-width:680px){
        .flow-step[data-step="3"] .payment-form .field-grid{grid-template-columns:1fr!important}
      }
    `;
    document.head.append(style);
  }

  function enforceMainNavTypography() {
    const width = window.innerWidth || 1440;
    const size = width <= 1080 ? "25px" : width <= 1320 ? "29px" : "32px";
    document.querySelectorAll('.app-header nav button[data-nav]').forEach((button) => {
      button.style.setProperty("font-size", size, "important");
      button.style.setProperty("font-weight", "780", "important");
      button.style.setProperty("line-height", "1", "important");
    });
  }

  function svgFlag(lang) {
    const wrap = document.createElement("span");
    wrap.className = "tt-lang-flag";
    wrap.setAttribute("aria-hidden", "true");
    if (lang === "cs") {
      wrap.innerHTML = '<svg viewBox="0 0 30 20" xmlns="http://www.w3.org/2000/svg"><rect width="30" height="10" fill="#fff"/><rect y="10" width="30" height="10" fill="#d7141a"/><path d="M0 0 15 10 0 20Z" fill="#11457e"/></svg>';
    } else {
      wrap.innerHTML = '<svg viewBox="0 0 60 30" xmlns="http://www.w3.org/2000/svg"><rect width="60" height="30" fill="#012169"/><path d="M0 0 60 30M60 0 0 30" stroke="#fff" stroke-width="6"/><path d="M0 0 60 30M60 0 0 30" stroke="#c8102e" stroke-width="2.5"/><path d="M30 0v30M0 15h60" stroke="#fff" stroke-width="10"/><path d="M30 0v30M0 15h60" stroke="#c8102e" stroke-width="6"/></svg>';
    }
    return wrap;
  }

  function repairLanguageFlags() {
    document.querySelectorAll("#taxtreat-language-controls .tt-lang-mini button").forEach((button) => {
      const lang = button.dataset.lang;
      if (!["cs","en"].includes(lang)) return;
      const flag = button.querySelector(".tt-lang-flag");
      const expected = lang === "cs" ? "CZ" : "EN";
      if (flag && (button.textContent || "").includes(expected)) return;
      button.replaceChildren(svgFlag(lang), document.createTextNode(expected));
    });
  }

  function replaceText(root, pattern, replacement) {
    if (!root) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      const current = node.nodeValue || "";
      if (pattern.test(current)) node.nodeValue = current.replace(pattern, replacement);
      pattern.lastIndex = 0;
    });
  }

  function generalizeDomesticReliefWording() {
    const step3 = document.querySelector('.flow-step[data-step="3"]');
    replaceText(step3, /(?:pro|k)\s+(?:možné|možnost)\s+osvobození\s+podle\s+§\s*19\s*ZDP/gi, "pro možnost osvobození podle vnitrostátní legislativy");
    replaceText(step3, /pro\s+osvobození\s+podle\s+§\s*19\s*ZDP/gi, "pro možnost osvobození podle vnitrostátní legislativy");
  }

  function section19Applies(root) {
    const box = root?.querySelector("#cz-section19-result");
    if (!box) return false;
    return box.classList.contains("tt-section19-applicable") || /§\s*19\s*ZDP\s*se\s*použije/i.test(box.textContent || "");
  }

  function simplifySection19Result(root) {
    const applies = section19Applies(root);
    root.classList.toggle("tt-section19-active", applies);
    if (!applies) return;
    const box = root.querySelector("#cz-section19-result");
    const status = box?.querySelector(".tt-legal-status");
    const heading = box?.querySelector("h1,h2,h3,h4");
    const paragraph = box?.querySelector("p");
    if (status) status.textContent = "§ 19 ZDP se použije";
    if (heading) heading.textContent = "Vnitrostátní osvobození podle § 19 ZDP";
    if (paragraph) paragraph.textContent = "Použité pravidlo: § 19 ZDP. Při zadaných údajích jsou splněny podmínky vnitrostátního osvobození, takže česká srážková daň se neuplatní. Smluvní ochrana je pouze sekundární.";
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
    simplifySection19Result(root);
    hideEmptyConditions(root);
    reorderLegalSources(root);
  }

  function refresh() {
    installStyles();
    enforceMainNavTypography();
    repairLanguageFlags();
    if (!isCzech()) return;
    generalizeDomesticReliefWording();
    refreshStep4();
  }

  function scheduleRefreshes() {
    [0, 80, 220, 600].forEach((delay) => window.setTimeout(refresh, delay));
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
    if (event.target?.id === "taxtreat-ui-language" || ["section19_company_form","section19_taxable_company"].includes(event.target?.name)) {
      scheduleRefreshes();
    }
  }, true);

  window.addEventListener("resize", () => window.setTimeout(enforceMainNavTypography, 50));
  refresh();
})();
