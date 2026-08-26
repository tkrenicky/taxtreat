(() => {
  "use strict";

  const SECTION19_SOURCE = "https://e-sbirka.gov.cz/sb/1992/586";
  const state = { lastAnalysis: null, lastPayload: null };

  function uiLanguage() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
  }

  function isEnglish() { return uiLanguage() === "en"; }

  function injectWorkspaceStyles() {
    if (document.querySelector("#tt-batch-20260821-styles")) return;
    const style = document.createElement("style");
    style.id = "tt-batch-20260821-styles";
    style.textContent = `
      /* Header navigation: larger, clearer hit areas without adding visual bulk. */
      .app-header nav, .app-header .nav, .app-header .workspace-nav { display:flex; align-items:center; gap:6px; }
      .app-header nav a, .app-header .nav a, .app-header .workspace-nav a {
        min-height:42px; padding:0 14px; display:inline-flex; align-items:center; justify-content:center;
        border-radius:8px; font-size:15px; font-weight:750; line-height:1; transition:background .15s ease,color .15s ease;
      }
      .app-header nav a:hover, .app-header .nav a:hover, .app-header .workspace-nav a:hover { background:rgba(255,255,255,.08); }
      .app-header nav a.active, .app-header nav a[aria-current="page"],
      .app-header .nav a.active, .app-header .workspace-nav a.active {
        background:rgba(255,255,255,.10); box-shadow:inset 0 -2px 0 rgba(255,255,255,.9);
      }

      /* Compact active payer picker. */
      .app-header .payer-context:has(#active-payer-select), .app-header label:has(#active-payer-select) {
        width:auto !important; min-width:0 !important; padding:7px 12px 8px !important; border-radius:11px !important;
        gap:2px !important; background:#fbfaf5 !important; box-shadow:none !important; border:1px solid rgba(11,62,53,.12) !important;
      }
      #active-payer-select {
        width:188px !important; min-width:188px !important; max-width:210px !important; height:28px !important;
        padding:0 24px 0 0 !important; border:0 !important; background-color:transparent !important;
        box-shadow:none !important; font-size:15px !important; font-weight:750 !important; color:#0f4038 !important;
      }
      .app-header .payer-context:has(#active-payer-select) > span,
      .app-header label:has(#active-payer-select) > span {
        font-size:9.5px !important; letter-spacing:.06em !important; line-height:1.1 !important; color:#6d7974 !important;
      }

      /* Language selector: no oversized white container, only small text + flags. */
      #taxtreat-language-controls {
        width:auto !important; min-width:0 !important; max-width:none !important; height:auto !important;
        padding:0 !important; margin:0 0 0 4px !important; border:0 !important; border-radius:0 !important;
        background:transparent !important; box-shadow:none !important; display:inline-flex !important; align-items:center !important;
      }
      #taxtreat-language-controls .tt-lang-mini { gap:5px !important; font-size:12.5px !important; color:rgba(255,255,255,.72); }
      #taxtreat-language-controls .tt-lang-mini button {
        color:rgba(255,255,255,.68) !important; text-decoration:none !important; opacity:1 !important;
        display:inline-flex; align-items:center; gap:4px; padding:4px 3px !important; border-radius:6px;
      }
      #taxtreat-language-controls .tt-lang-mini button[data-active="true"] {
        color:#fff !important; background:rgba(255,255,255,.09) !important;
      }

      /* Section 19: heading first, then two full-width factual questions stacked. */
      #cz-section19-facts {
        display:block !important; padding:18px 20px !important; margin-top:18px !important;
        border:1px solid #cadad4 !important; border-radius:12px !important; background:#fbfcfa !important;
      }
      #cz-section19-facts > div:first-child { margin:0 0 18px !important; }
      #cz-section19-facts > div:first-child strong { display:block; font-size:17px; line-height:1.25; margin-bottom:6px; }
      #cz-section19-facts > div:first-child small { font-size:13px; line-height:1.45; color:#687772; }
      #cz-section19-facts > label { display:grid !important; grid-template-columns:1fr !important; gap:7px !important; margin:0 !important; }
      #cz-section19-facts > label + label { margin-top:18px !important; padding-top:18px !important; border-top:1px solid #e2e8e5; }
      #cz-section19-facts > label > span { max-width:860px; font-weight:700; line-height:1.4; }
      #cz-section19-facts > label > select { width:100% !important; max-width:none !important; }
      #cz-section19-facts > label > small { color:#66736f; line-height:1.45; }

      /* Clear provenance in the result. */
      #cz-section19-result.tt-section19-applicable { border-left-color:#1f6a59 !important; background:#f4faf7 !important; }
      #cz-section19-result.tt-section19-not-applicable { border-left-color:#9c8a57 !important; background:#fbf9f2 !important; }
      #cz-section19-result .tt-legal-status { display:inline-flex; padding:4px 8px; border-radius:999px; font-size:11px; font-weight:800; letter-spacing:.03em; margin-bottom:8px; background:#e5f1ec; color:#164d42; }
      .tt-section19-source { margin-top:12px; padding:12px 14px; border:1px solid #d8e3df; border-radius:9px; background:#fff; }
      .tt-section19-source a { font-weight:700; }

      @media (max-width:900px) {
        #active-payer-select { width:160px !important; min-width:160px !important; }
        .app-header nav a, .app-header .nav a, .app-header .workspace-nav a { padding:0 10px; }
      }
    `;
    document.head.append(style);
  }

  const dashboardText = new Map([
    ["Latest results", "Poslední výsledky"],
    ["No results yet", "Zatím bez výsledků"],
    ["The latest results will appear here after a calculation is completed.", "Po dokončení výpočtu se zde zobrazí poslední výsledky."],
  ]);

  function localizeDashboard() {
    const reverse = new Map([...dashboardText].map(([en, cs]) => [cs, en]));
    const map = isEnglish() ? reverse : dashboardText;
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      const original = node.nodeValue;
      const key = original.trim();
      const replacement = map.get(key);
      if (replacement) node.nodeValue = original.replace(key, replacement);
    });
  }

  function polishLanguageButtons() {
    document.querySelectorAll("#taxtreat-language-controls .tt-lang-mini button").forEach((button) => {
      const lang = button.dataset.lang;
      if (lang === "cs") button.textContent = "🇨🇿 CZ";
      if (lang === "en") button.textContent = "🇬🇧 EN";
      button.dataset.active = String(lang === uiLanguage());
    });
  }

  function section19Layers(analysis) {
    return (analysis?.layer_results || []).filter((item) => item.layer === "eu_relief" && String(item.rule_id || "").includes("DIVIDEND"));
  }

  function section19Status(analysis) {
    const treatment = analysis?.tax_treatment || analysis?.candidate_tax_treatment;
    const layers = section19Layers(analysis);
    const applicable = analysis?.status === "FINAL" && treatment === "domestic_exemption" || layers.some((item) => item.outcome === "applicable");
    const unresolved = !analysis || layers.some((item) => item.outcome === "unresolved");
    const notApplicable = layers.length > 0 && layers.every((item) => ["not_applicable", "failed"].includes(item.outcome));
    if (applicable) return "applicable";
    if (notApplicable) return "not_applicable";
    if (unresolved) return "unresolved";
    return "reviewed";
  }

  function sourceCountry() {
    return String(state.lastPayload?.source_country || document.body.dataset.sourceCountry || "CZ").toUpperCase();
  }

  function incomeType() {
    return state.lastPayload?.income_type || document.querySelector('#workspace-payment [name="income_type"]')?.value || "";
  }

  function renderSection19Provenance() {
    const box = document.querySelector("#cz-section19-result");
    if (!box || sourceCountry() !== "CZ" || incomeType() !== "dividend") return;
    const status = section19Status(state.lastAnalysis);
    box.classList.remove("tt-section19-applicable", "tt-section19-not-applicable");
    if (status === "applicable") box.classList.add("tt-section19-applicable");
    if (status === "not_applicable") box.classList.add("tt-section19-not-applicable");
    const en = isEnglish();
    const copy = {
      applicable: en
        ? ["Section 19 applies", "The Czech domestic exemption is the primary legal basis. Czech withholding tax is therefore 0%. The treaty remains a secondary protection only."]
        : ["§ 19 ZDP se použije", "Primárním právním titulem je české vnitrostátní osvobození podle § 19 ZDP. Česká srážková daň je proto 0 %. Smlouva zůstává pouze sekundární ochranou."],
      not_applicable: en
        ? ["Section 19 does not apply", "The domestic exemption was assessed first but is not available on the entered facts. The final treatment therefore follows the applicable treaty or the domestic rate."]
        : ["§ 19 ZDP se neuplatní", "Vnitrostátní osvobození bylo posouzeno jako první, ale podle zadaných údajů není dostupné. Konečné daňové zacházení proto určuje příslušná smlouva nebo vnitrostátní sazba."],
      unresolved: en
        ? ["Section 19 is not yet resolved", "Complete the remaining factual items. Until then, TaxTreat must not present the treaty result as the sole final legal basis."]
        : ["§ 19 ZDP zatím nelze uzavřít", "Je nutné doplnit zbývající skutkové údaje. Do té doby TaxTreat nesmí prezentovat smluvní výsledek jako jediný konečný právní titul."],
      reviewed: en
        ? ["Section 19 assessed", "The domestic exemption was assessed before treaty relief. The legal basis shown below must remain consistent with that assessment."]
        : ["§ 19 ZDP posouzen", "Vnitrostátní osvobození bylo posouzeno před smluvní úlevou. Níže uvedený právní titul musí být s tímto výsledkem konzistentní."],
    }[status];

    box.innerHTML = `
      <div class="tt-legal-status">${copy[0]}</div>
      <h2>${en ? "Domestic exemption under Section 19" : "Vnitrostátní osvobození podle § 19 ZDP"}</h2>
      <p>${copy[1]}</p>
      <div class="tt-section19-source">
        <strong>${en ? "Relevant Czech legal basis" : "Relevantní český právní základ"}</strong><br>
        ${en ? "Section 19(1)(ze), Section 19(3), Section 19(6) and Section 19(11) of the Czech Income Taxes Act." : "§ 19 odst. 1 písm. ze), § 19 odst. 3, § 19 odst. 6 a § 19 odst. 11 ZDP."}
        <br><a href="${SECTION19_SOURCE}" target="_blank" rel="noopener">${en ? "Official e-Sbírka source ↗" : "Oficiální zdroj e-Sbírka ↗"}</a>
      </div>`;
  }

  function markReportSections(doc) {
    const phrases = [
      ["JAK SE STANOVÍ SAZBA", "tt-report-logic"], ["HOW THE RATE IS DETERMINED", "tt-report-logic"],
      ["PRÁVNÍ ZÁKLAD", "tt-report-legal"], ["LEGAL BASIS", "tt-report-legal"],
      ["POUŽITÉ PŘEDPOKLADY", "tt-report-assumptions"], ["ASSUMPTIONS USED", "tt-report-assumptions"],
      ["VÝPOČET", "tt-report-calculation"], ["CALCULATION", "tt-report-calculation"],
    ];
    const elements = [...doc.querySelectorAll("body *")];
    phrases.forEach(([phrase, className]) => {
      const el = elements.find((node) => node.children.length === 0 && node.textContent.trim().toUpperCase() === phrase);
      const section = el?.closest("section,article,.card,.panel") || el?.parentElement?.parentElement;
      section?.classList.add(className);
    });
  }

  function addProfessionalReportCss(doc) {
    const style = doc.createElement("style");
    style.id = "tt-professional-report-20260821";
    style.textContent = `
      :root { --tt-ink:#123f37; --tt-muted:#667771; --tt-line:#d6e1dd; --tt-cream:#f5f2e9; --tt-paper:#fffdfa; --tt-mint:#eef6f2; --tt-green:#174d43; }
      html,body { background:var(--tt-paper) !important; color:#1f302c !important; }
      body { font-size:10.5pt !important; line-height:1.42 !important; }
      h1,h2,h3 { color:var(--tt-ink) !important; overflow-wrap:normal !important; word-break:normal !important; }
      h1 { font-size:24pt !important; line-height:1.08 !important; }
      h2 { font-size:16pt !important; line-height:1.18 !important; }
      h3 { font-size:11.5pt !important; }
      p,li,td,th,dd,dt { overflow-wrap:break-word; word-break:normal; hyphens:none; }
      section,article,.card,.panel { border-color:var(--tt-line) !important; }
      .tt-report-logic,.tt-report-legal,.tt-report-assumptions,.tt-report-calculation { break-inside:avoid-page !important; page-break-inside:avoid !important; }
      blockquote,table,tr,.source-card,.legal-source,.deadline-card { break-inside:avoid-page !important; page-break-inside:avoid !important; }
      a { color:var(--tt-green) !important; }
      .tt-report-section19 { margin:12px 0 18px; padding:14px 16px; border:1px solid var(--tt-line); border-left:4px solid var(--tt-green); border-radius:10px; background:var(--tt-mint); break-inside:avoid-page; }
      .tt-report-section19 h3 { margin:0 0 6px; font-size:13pt !important; }
      .tt-report-section19 p { margin:5px 0; }
      .tt-report-section19 .legal-ref { font-size:9.5pt; color:var(--tt-muted); }
      .tt-report-zero { color:var(--tt-green) !important; font-size:28pt !important; line-height:1 !important; white-space:nowrap !important; }
      @page { size:A4; margin:14mm 14mm 15mm; }
      @media print {
        html,body { -webkit-print-color-adjust:exact !important; print-color-adjust:exact !important; background:var(--tt-paper) !important; }
        .tt-report-logic { break-before:auto; }
        .tt-report-logic,.tt-report-legal,.tt-report-assumptions,.tt-report-calculation { break-inside:avoid-page !important; }
        h1,h2,h3 { break-after:avoid-page; }
      }
    `;
    doc.head.append(style);
  }

  function replaceExactText(doc, from, to) {
    const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      const current = node.nodeValue;
      const trimmed = current.trim();
      if (trimmed === from) node.nodeValue = current.replace(trimmed, to);
    });
  }

  function addSection19ToReport(doc) {
    if (sourceCountry() !== "CZ" || incomeType() !== "dividend") return;
    const status = section19Status(state.lastAnalysis);
    const en = (doc.documentElement.lang || "cs").toLowerCase().startsWith("en");
    const legalHeading = [...doc.querySelectorAll("body *")].find((node) => node.children.length === 0 && ["PRÁVNÍ ZÁKLAD","LEGAL BASIS"].includes(node.textContent.trim().toUpperCase()));
    const host = legalHeading?.closest("section,article,.card,.panel") || legalHeading?.parentElement?.parentElement || doc.body;
    const card = doc.createElement("section");
    card.className = "tt-report-section19";
    const title = status === "applicable"
      ? (en ? "Primary legal basis: domestic exemption under Section 19" : "Primární právní titul: vnitrostátní osvobození podle § 19 ZDP")
      : status === "not_applicable"
        ? (en ? "Section 19 assessed – exemption not available" : "§ 19 ZDP posouzen – osvobození se neuplatní")
        : (en ? "Section 19 assessment" : "Posouzení § 19 ZDP");
    const body = status === "applicable"
      ? (en ? "The domestic exemption applies on the entered facts and is the primary basis for the 0% Czech withholding tax result. Treaty protection is secondary." : "Podle zadaných údajů se použije vnitrostátní osvobození. Primárním titulem pro nulovou českou srážkovou daň je proto § 19 ZDP; smluvní ochrana je sekundární.")
      : status === "not_applicable"
        ? (en ? "The domestic exemption was tested first but is not available on the entered facts. The final result therefore follows the treaty or the domestic rate." : "Vnitrostátní osvobození bylo testováno jako první, ale podle zadaných údajů není dostupné. Konečný výsledek proto vychází ze smlouvy nebo z vnitrostátní sazby.")
        : (en ? "The domestic exemption has been considered, but the available facts do not permit a final conclusion." : "Vnitrostátní osvobození bylo zohledněno, ale dostupné skutkové údaje zatím neumožňují konečný závěr.");
    card.innerHTML = `<h3>${title}</h3><p>${body}</p><p class="legal-ref"><strong>${en ? "Relevant provisions:" : "Relevantní ustanovení:"}</strong> ${en ? "Section 19(1)(ze), Section 19(3), Section 19(6) and Section 19(11) of Act No. 586/1992 Coll." : "§ 19 odst. 1 písm. ze), § 19 odst. 3, § 19 odst. 6 a § 19 odst. 11 zákona č. 586/1992 Sb."} · <a href="${SECTION19_SOURCE}">${en ? "Official e-Sbírka source" : "Oficiální zdroj e-Sbírka"} ↗</a></p><p class="legal-ref">${en ? "Relevant statutory text concerns profit distributions paid by a subsidiary to its parent company and the statutory company, ownership, beneficial-owner and tax-status conditions." : "Relevantní zákonný text se týká podílů na zisku vyplácených dceřinou společností mateřské společnosti a navazujících podmínek právní formy, držby podílu, skutečného vlastnictví a daňového postavení."}</p>`;
    host.parentElement?.insertBefore(card, host);

    if (status === "applicable") {
      replaceExactText(doc, "čl. 10", "§ 19 ZDP");
      replaceExactText(doc, "Article 10", "Section 19");
      const treatyPrimary = [...doc.querySelectorAll("body *")].find((node) => /Smlouva mezi Českou republikou a Rakouskem.*čl\. 10/i.test(node.textContent || ""));
      if (treatyPrimary && treatyPrimary.children.length === 0) treatyPrimary.textContent = "§ 19 ZDP – vnitrostátní osvobození (smlouva s Rakouskem představuje sekundární ochranu)";
    }
  }

  function fixReportLayout(doc) {
    [...doc.querySelectorAll("body *")].forEach((el) => {
      if (el.children.length === 0 && ["0 %","0%"].includes(el.textContent.trim())) el.classList.add("tt-report-zero");
      if (/^\d{2}\s*\/\s*\d{2}$/.test(el.textContent.trim())) el.style.display = "none";
    });
    markReportSections(doc);
    addProfessionalReportCss(doc);
  }

  function transformReportHtml(html) {
    if (!html) return html;
    const doc = new DOMParser().parseFromString(html, "text/html");
    fixReportLayout(doc);
    return "<!doctype html>\n" + doc.documentElement.outerHTML;
  }

  function refreshUi() {
    injectWorkspaceStyles();
    localizeDashboard();
    polishLanguageButtons();
    renderSection19Provenance();
  }

  const previousFetch = window.fetch.bind(window);
  window.fetch = async function taxTreatUiReportBatchFetch(resource, options = {}) {
    const url = typeof resource === "string" ? resource : resource?.url || "";
    if (url.endsWith("/analysis/intake") && options?.body) {
      try { state.lastPayload = JSON.parse(String(options.body)); } catch (_problem) {}
    }
    const response = await previousFetch(resource, options);
    if (url.endsWith("/analysis/intake") && response.ok) {
      try {
        const body = await response.clone().json();
        state.lastAnalysis = body?.analysis || null;
        window.setTimeout(refreshUi, 0);
      } catch (_problem) {}
    }
    if (url.endsWith("/analysis/report") && response.ok) {
      try {
        const body = await response.clone().json();
        if (body?.html) body.html = transformReportHtml(body.html);
        const headers = new Headers(response.headers);
        headers.set("Content-Type", "application/json");
        return new Response(JSON.stringify(body), { status: response.status, statusText: response.statusText, headers });
      } catch (_problem) { return response; }
    }
    return response;
  };

  function boot() {
    refreshUi();
    document.addEventListener("click", () => window.setTimeout(refreshUi, 0), true);
    document.addEventListener("change", (event) => {
      if (event.target?.id === "taxtreat-ui-language") window.setTimeout(refreshUi, 0);
      if (event.target?.name === "income_type") window.setTimeout(refreshUi, 0);
    }, true);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once:true });
  else boot();
})();
