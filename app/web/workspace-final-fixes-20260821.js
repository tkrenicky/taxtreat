(() => {
  "use strict";

  const ZDP_SOURCE = "https://e-sbirka.gov.cz/sb/1992/586";

  function lang() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
  }
  function en() { return lang() === "en"; }

  function addStyles() {
    if (document.querySelector("#tt-final-fixes-20260821")) return;
    const style = document.createElement("style");
    style.id = "tt-final-fixes-20260821";
    style.textContent = `
      /* Header — actual workspace DOM uses nav buttons, not anchors. */
      .app-header nav { display:flex!important; align-items:center!important; gap:8px!important; }
      .app-header nav button[data-nav] {
        min-height:46px!important; padding:0 17px!important; border-radius:9px!important;
        font-size:15px!important; font-weight:750!important; line-height:1!important;
      }
      .app-header nav button[data-nav].active { background:rgba(255,255,255,.12)!important; box-shadow:inset 0 -2px 0 rgba(255,255,255,.92)!important; }

      .app-header .payer-context {
        width:auto!important; min-width:0!important; max-width:220px!important; min-height:46px!important;
        padding:5px 10px 6px!important; margin-left:auto!important; border-radius:10px!important;
        background:#fbfaf5!important; border:1px solid rgba(12,60,53,.12)!important; box-shadow:none!important;
      }
      .app-header .payer-context > span { font-size:9px!important; line-height:1!important; letter-spacing:.055em!important; margin-bottom:2px!important; }
      #active-payer-select {
        width:185px!important; min-width:0!important; max-width:185px!important; height:25px!important;
        padding:0 20px 0 0!important; border:0!important; box-shadow:none!important; background:transparent!important;
        font-size:14px!important; line-height:1.1!important; font-weight:750!important;
      }

      #taxtreat-language-controls { width:auto!important; min-width:0!important; padding:0!important; border:0!important; background:transparent!important; box-shadow:none!important; }
      #taxtreat-language-controls .tt-lang-mini { display:flex!important; align-items:center!important; gap:7px!important; }
      #taxtreat-language-controls .tt-lang-mini button { display:inline-flex!important; align-items:center!important; gap:5px!important; background:transparent!important; border:0!important; padding:4px 3px!important; font-size:12px!important; }
      .tt-flag { display:inline-block; width:18px; height:12px; border-radius:2px; overflow:hidden; box-shadow:0 0 0 1px rgba(255,255,255,.28); flex:0 0 auto; }
      .tt-flag svg { display:block; width:100%; height:100%; }

      /* Section 19 factual questions use same two-column structure as transaction facts. */
      #cz-section19-facts { padding:20px 24px!important; }
      #cz-section19-facts > div:first-child { margin-bottom:10px!important; }
      #cz-section19-facts > label {
        display:grid!important; grid-template-columns:minmax(0,1fr) minmax(260px,375px)!important;
        grid-template-areas:"question control" "help control"!important;
        column-gap:28px!important; row-gap:6px!important; align-items:center!important;
        padding:18px 0!important; border-top:1px solid #e1e7e4!important;
      }
      #cz-section19-facts > label > span { grid-area:question!important; margin:0!important; max-width:none!important; font-size:14px!important; line-height:1.35!important; }
      #cz-section19-facts > label > select { grid-area:control!important; width:100%!important; max-width:none!important; min-height:50px!important; }
      #cz-section19-facts > label > small { grid-area:help!important; margin:0!important; font-size:12.5px!important; line-height:1.35!important; }

      /* Keep factual question typography consistent. */
      .fact-row, .transaction-fact, .income-fact, .question-row { font-size:14px!important; }
      .fact-row label, .transaction-fact label, .income-fact label, .question-row label { font-size:14px!important; line-height:1.35!important; }
      .fact-row select, .fact-row input, .transaction-fact select, .transaction-fact input, .income-fact select, .income-fact input { font-size:15px!important; }

      @media (max-width:900px) {
        .app-header nav button[data-nav] { padding:0 11px!important; min-height:42px!important; }
        #active-payer-select { width:155px!important; max-width:155px!important; }
        #cz-section19-facts > label { grid-template-columns:1fr!important; grid-template-areas:"question" "control" "help"!important; }
      }
    `;
    document.head.append(style);
  }

  const flagCz = `<span class="tt-flag" aria-hidden="true"><svg viewBox="0 0 30 20" xmlns="http://www.w3.org/2000/svg"><rect width="30" height="10" fill="#fff"/><rect y="10" width="30" height="10" fill="#d7141a"/><path d="M0 0L13 10L0 20Z" fill="#11457e"/></svg></span>`;
  const flagGb = `<span class="tt-flag" aria-hidden="true"><svg viewBox="0 0 60 30" xmlns="http://www.w3.org/2000/svg"><rect width="60" height="30" fill="#012169"/><path d="M0 0L60 30M60 0L0 30" stroke="#fff" stroke-width="6"/><path d="M0 0L60 30M60 0L0 30" stroke="#c8102e" stroke-width="3"/><path d="M30 0V30M0 15H60" stroke="#fff" stroke-width="10"/><path d="M30 0V30M0 15H60" stroke="#c8102e" stroke-width="6"/></svg></span>`;

  function polishHeader() {
    const mini = document.querySelector("#taxtreat-language-controls .tt-lang-mini");
    if (mini) {
      mini.querySelectorAll("button").forEach((button) => {
        const code = button.dataset.lang || (button.textContent.includes("EN") ? "en" : "cs");
        button.innerHTML = `${code === "en" ? flagGb : flagCz}<span>${code === "en" ? "EN" : "CZ"}</span>`;
      });
    }
    const payerLabel = document.querySelector(".app-header .payer-context > span");
    if (payerLabel) payerLabel.textContent = en() ? "ACTIVE PAYER" : "AKTIVNÍ PLÁTCE";
  }

  function patchSection19Layout() {
    const box = document.querySelector("#cz-section19-facts");
    if (!box) return;
    const first = box.firstElementChild;
    if (first) {
      const strong = first.querySelector("strong");
      const small = first.querySelector("small");
      if (strong) strong.textContent = en() ? "Two additional facts for the potential Section 19 exemption" : "Ještě dva údaje pro možné osvobození podle § 19 ZDP";
      if (small) small.textContent = en()
        ? "Ownership, direct holding, holding period, beneficial ownership and permanent-establishment attribution are already taken from the answers above."
        : "Podíl, přímé držení, dobu držby, skutečné vlastnictví a vazbu ke stálé provozovně už TaxTreat používá z odpovědí výše.";
    }
  }

  function textNodes(root) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    return nodes;
  }

  function exactReplace(doc, from, to) {
    textNodes(doc.body).forEach((node) => {
      if (node.nodeValue.trim() === from) node.nodeValue = node.nodeValue.replace(from, to);
    });
  }

  function containsReplace(doc, pattern, replacement) {
    textNodes(doc.body).forEach((node) => {
      if (pattern.test(node.nodeValue)) node.nodeValue = node.nodeValue.replace(pattern, replacement);
    });
  }

  function sectionAroundText(doc, exact) {
    const target = [...doc.querySelectorAll("body *")].find((el) => el.children.length === 0 && el.textContent.trim() === exact);
    return target?.closest("section,article,.card,.panel") || target?.parentElement?.parentElement || null;
  }

  function reportIsSection19Applicable(doc) {
    const all = doc.body.textContent || "";
    return /§\s*19 ZDP se použije|Použije se osvobození podle §\s*19|Section 19 exemption applies|Primary legal basis:\s*Section 19/i.test(all);
  }

  function addSection19LegalExcerpt(doc, english) {
    if (doc.querySelector(".tt-zdp19-legal-excerpt")) return;
    const legalHeading = [...doc.querySelectorAll("body *")].find((el) => {
      const t = el.textContent.trim().toUpperCase();
      return el.children.length === 0 && (t === "POUŽITÉ PRÁVNÍ PRAVIDLO" || t === "LEGAL RULE APPLIED" || t === "LEGAL BASIS");
    });
    const anchor = legalHeading?.closest("section,article,.card,.panel") || legalHeading?.parentElement?.parentElement;
    if (!anchor?.parentNode) return;

    const block = doc.createElement("section");
    block.className = "tt-zdp19-legal-excerpt";
    block.innerHTML = english ? `
      <p class="eyebrow">PRIMARY CZECH LEGAL BASIS</p>
      <h2>Section 19 of the Czech Income Taxes Act – domestic dividend exemption</h2>
      <p><strong>Relevant statutory excerpt (informal English translation):</strong> income from a profit share paid by a Czech subsidiary to its parent company is exempt from tax where the statutory parent/subsidiary conditions are met.</p>
      <p>The relevant conditions are set out principally in Section 19(1)(ze), Section 19(3)(a)–(c), Section 19(4) and Section 19(6). For Switzerland, Norway, Iceland and Liechtenstein, Section 19(8) is also relevant.</p>
      <p><a href="${ZDP_SOURCE}" target="_blank" rel="noopener">Official Czech text in e-Sbírka ↗</a></p>` : `
      <p class="eyebrow">PRIMÁRNÍ ČESKÝ PRÁVNÍ ZÁKLAD</p>
      <h2>§ 19 ZDP – vnitrostátní osvobození podílu na zisku</h2>
      <p><strong>Relevantní výňatek z § 19 odst. 1 písm. ze) bodu 1:</strong> „příjmy z podílu na zisku, vyplácené dceřinou společností, která je poplatníkem uvedeným v § 17 odst. 3, mateřské společnosti“.</p>
      <p>Navazující podmínky vyplývají zejména z § 19 odst. 3 písm. a) až c), § 19 odst. 4 a § 19 odst. 6 ZDP. Pro Švýcarsko, Norsko, Island a Lichtenštejnsko je relevantní také § 19 odst. 8 ZDP.</p>
      <p><a href="${ZDP_SOURCE}" target="_blank" rel="noopener">Oficiální znění v e-Sbírce ↗</a></p>`;
    anchor.parentNode.insertBefore(block, anchor.nextSibling);
  }

  function polishReport(html) {
    if (!html) return html;
    const doc = new DOMParser().parseFromString(html, "text/html");
    const english = (doc.documentElement.lang || "cs").toLowerCase().startsWith("en");
    const s19 = reportIsSection19Applicable(doc);

    const style = doc.createElement("style");
    style.id = "tt-final-report-style";
    style.textContent = `
      @page { size:A4; margin:14mm 13mm 15mm; }
      html,body { background:#fffdf8!important; color:#173f38!important; }
      body { font-size:9.7pt!important; line-height:1.38!important; }
      h1 { font-size:22pt!important; line-height:1.08!important; margin:0 0 5mm!important; }
      h2 { font-size:14pt!important; line-height:1.18!important; }
      h3 { font-size:11.5pt!important; line-height:1.2!important; }
      section, article, .card, .panel, table, blockquote, .tt-zdp19-legal-excerpt { break-inside:avoid!important; page-break-inside:avoid!important; }
      .tt-zdp19-legal-excerpt { margin:6mm 0!important; padding:5mm!important; border:1px solid #c8d9d3!important; border-left:3px solid #174d43!important; border-radius:3mm!important; background:#f3f8f5!important; }
      .tt-zdp19-legal-excerpt .eyebrow { font-size:7.5pt!important; font-weight:800!important; letter-spacing:.08em!important; margin:0 0 2mm!important; }
      .tt-zdp19-legal-excerpt p { margin:2mm 0!important; }
      .tt-report-logic, [class*="logic"], [class*="diagram"], [class*="flow"] { break-inside:avoid!important; page-break-inside:avoid!important; }
      .tt-report-logic { page-break-before:auto!important; }
      .rate-hero, .result-rate, [class*="rate-value"] { font-size:18pt!important; line-height:1.05!important; }
      a { color:#174d43!important; }
      @media print {
        body { -webkit-print-color-adjust:exact!important; print-color-adjust:exact!important; }
        section, article, .card, .panel, table, blockquote, .tt-zdp19-legal-excerpt { break-inside:avoid!important; page-break-inside:avoid!important; }
      }
    `;
    doc.head.append(style);

    if (s19) {
      const csNoRate = "Neuplatňuje se – osvobození podle § 19 ZDP";
      const enNoRate = "Not applicable – exempt under Section 19";
      exactReplace(doc, "0 %", english ? enNoRate : csNoRate);
      exactReplace(doc, "0%", english ? enNoRate : csNoRate);
      containsReplace(doc, /Česká srážková daň je proto 0\s*%/gi, "Česká srážková daň se proto neuplatní z důvodu osvobození podle § 19 ZDP");
      containsReplace(doc, /Czech withholding tax is therefore 0\s*%/gi, "Czech withholding tax therefore does not apply because the dividend is exempt under Section 19");
      containsReplace(doc, /primárním titulem pro nulovou českou srážkovou daň/gi, "primárním právním titulem pro osvobození od české daně");
      containsReplace(doc, /primary basis for the 0% Czech withholding tax result/gi, "primary legal basis for the Czech domestic exemption");

      exactReplace(doc, "čl. 10", "§ 19 ZDP");
      exactReplace(doc, "Article 10", "Section 19");

      const treatySentence = /Podle článku 10 smlouvy[^.]*\./gi;
      containsReplace(doc, treatySentence, "Podle zadaných údajů se použije vnitrostátní osvobození podle § 19 ZDP; smlouva o zamezení dvojího zdanění představuje pouze sekundární omezení českého práva zdanit.");
      containsReplace(doc, /Under Article 10 of the treaty[^.]*\./gi, "Based on the entered facts, the domestic exemption under Section 19 applies; the tax treaty is only a secondary limitation on Czech taxing rights.");

      addSection19LegalExcerpt(doc, english);
    }

    // Remove accidental duplicate giant result values while keeping the first meaningful occurrence.
    const seen = new Set();
    [...doc.querySelectorAll("h1,h2,h3,strong,b,.rate-hero,.result-rate,[class*='rate-value']")].forEach((el) => {
      const key = el.textContent.trim().replace(/\s+/g, " ");
      if (!key || key.length > 90) return;
      if ((key === "0 %" || key === "0%" || /Neuplatňuje se|Not applicable/i.test(key)) && seen.has(key)) {
        const parent = el.closest(".card,.panel,section,article") || el;
        if (parent !== doc.body) parent.remove();
      } else if (key === "0 %" || key === "0%" || /Neuplatňuje se|Not applicable/i.test(key)) {
        seen.add(key);
      }
    });

    return "<!doctype html>\n" + doc.documentElement.outerHTML;
  }

  const previousFetch = window.fetch.bind(window);
  window.fetch = async function finalReportPolishFetch(resource, options = {}) {
    const url = typeof resource === "string" ? resource : resource?.url || "";
    const response = await previousFetch(resource, options);
    if (!url.endsWith("/analysis/report") || !response.ok) return response;
    try {
      const body = await response.clone().json();
      if (!body?.html) return response;
      body.html = polishReport(body.html);
      const headers = new Headers(response.headers);
      headers.set("Content-Type", "application/json");
      return new Response(JSON.stringify(body), { status:response.status, statusText:response.statusText, headers });
    } catch (_problem) {
      return response;
    }
  };

  function refresh() {
    addStyles();
    polishHeader();
    patchSection19Layout();
  }

  document.addEventListener("change", (event) => {
    if (event.target?.id === "taxtreat-ui-language") window.setTimeout(refresh, 0);
  }, true);
  document.addEventListener("click", (event) => {
    if (event.target?.closest?.("[data-nav],[data-next-step],[data-flow-step],#taxtreat-language-controls")) window.setTimeout(refresh, 0);
  }, true);

  refresh();
})();
