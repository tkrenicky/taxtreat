(() => {
  "use strict";

  const previousFetch = window.fetch.bind(window);

  function reportIsEnglish() {
    if (window.__TAXTREAT_LOCALE__ === "en") return true;
    const explicit = document.querySelector("#taxtreat-report-language")?.value;
    if (explicit === "en") return true;
    return localStorage.getItem("taxtreat-report-language") === "en";
  }

  const EXACT = new Map([
    ["Vnitrostátní osvobození podle § 19 ZDP", "Domestic exemption under Section 19"],
    ["Zákon č. 586/1992 Sb. · § 19 ↗", "Czech Income Taxes Act · Section 19 ↗"],
    ["§ 19 ZDP byl posouzen před smluvní úlevou.", "Section 19 was assessed before treaty relief."],
    ["Osvobození podle § 19 ZDP bylo posouzeno jako první a podle zadaných údajů se neuplatní. Daňové zacházení proto určuje smluvní analýza.", "The domestic exemption under Section 19 was assessed first and is not available based on the entered facts. The treaty analysis therefore determines the withholding tax treatment."],
    ["Osvobození podle § 19 ZDP se posuzuje před smluvní úlevou, ale zatím jej nelze uzavřít, protože zůstávají otevřené skutkové podmínky.", "The domestic exemption under Section 19 is assessed before treaty relief but cannot yet be finalised because one or more factual conditions remain open."],
  ]);

  function translateSection19Html(html) {
    if (!html) return html;
    const doc = new DOMParser().parseFromString(html, "text/html");
    doc.documentElement.lang = "en";

    const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);

    nodes.forEach((node) => {
      if (node.parentElement?.closest("blockquote")) return;
      const original = node.nodeValue || "";
      const trimmed = original.trim();
      if (!trimmed) return;

      let translated = EXACT.get(trimmed) || trimmed;
      translated = translated
        .replace(
          "Osvobození se použije – česká srážková daň se neodvádí.",
          "Applicable – Czech withholding tax is not due."
        )
        .replace(
          "Primárním právním titulem je § 19 ZDP; smluvní režim je pouze doplňkový.",
          "The domestic exemption under Section 19 of the Czech Income Taxes Act is the primary legal basis; treaty treatment is supplementary."
        )
        .replace(
          "Osvobození se použije – česká srážková daň se neodvádí. Primárním právním titulem je § 19 ZDP; smluvní režim je pouze doplňkový.",
          "Applicable – Czech withholding tax is not due. The domestic exemption under Section 19 of the Czech Income Taxes Act is the primary legal basis; treaty treatment is supplementary."
        );

      if (translated !== trimmed) {
        node.nodeValue = original.replace(trimmed, translated);
      }
    });

    return "<!doctype html>\n" + doc.documentElement.outerHTML;
  }

  window.fetch = async function taxTreatSection19EnglishReportFetch(resource, options = {}) {
    const response = await previousFetch(resource, options);
    const url = typeof resource === "string" ? resource : String(resource?.url || "");
    if (!url.endsWith("/analysis/report") || !response.ok || !reportIsEnglish()) return response;

    try {
      const body = await response.clone().json();
      if (!body?.html) return response;
      body.html = translateSection19Html(body.html);
      const headers = new Headers(response.headers);
      headers.set("content-type", "application/json; charset=utf-8");
      return new Response(JSON.stringify(body), {
        status: response.status,
        statusText: response.statusText,
        headers,
      });
    } catch (_problem) {
      return response;
    }
  };
})();