(() => {
  "use strict";

  const pairs = [
    ["ZÁKLADNÍ ÚDAJE", "BASIC DATA"],
    ["REGISTRACE", "REGISTRATION"],
    ["ADRESA", "ADDRESS"],
    ["Česká republika", "Czech Republic"],
    ["Slovensko", "Slovakia"],
    ["IČO", "Company ID"],
    ["DIČ", "Tax ID"],
    ["Sídlo", "Registered office"],
    ["Právní forma", "Legal form"],
    ["Datová schránka", "Data box"],
    ["Datum vzniku", "Date of incorporation"],
    ["Upravit", "Edit"],
    ["Zpět", "Back"],
  ];

  const csToEn = new Map(pairs);
  const enToCs = new Map(pairs.map(([cs, en]) => [en, cs]));

  function language() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
  }

  function translateMeta(text, toEnglish) {
    if (!text) return text;
    if (toEnglish) {
      return text
        .replace(/^Česká republika\s*·\s*IČO\s*/i, "Czech Republic · Company ID ")
        .replace(/^Slovensko\s*·\s*IČO\s*/i, "Slovakia · Company ID ")
        .replace(/\s*·\s*DIČ\s*/gi, " · Tax ID ");
    }
    return text
      .replace(/^Czech Republic\s*·\s*Company ID\s*/i, "Česká republika · IČO ")
      .replace(/^Slovakia\s*·\s*Company ID\s*/i, "Slovensko · IČO ")
      .replace(/\s*·\s*Tax ID\s*/gi, " · DIČ ");
  }

  function translateText(root) {
    if (!root) return;
    const toEnglish = language() === "en";
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      const original = node.nodeValue;
      const trimmed = original.trim();
      if (!trimmed) return;
      let replacement = toEnglish ? csToEn.get(trimmed) : enToCs.get(trimmed);
      if (!replacement) {
        const dynamic = translateMeta(trimmed, toEnglish);
        if (dynamic !== trimmed) replacement = dynamic;
      }
      if (replacement) node.nodeValue = original.replace(trimmed, replacement);
    });
  }

  function injectStyles() {
    if (document.querySelector("#tt-payer-detail-style-20260821")) return;
    const style = document.createElement("style");
    style.id = "tt-payer-detail-style-20260821";
    style.textContent = `
      .payer-detail, .payer-profile, [data-payer-detail] { color:#173e37; }
      .payer-detail h1, .payer-profile h1, [data-payer-detail] h1 {
        font-size:28px !important; line-height:1.15 !important; margin-bottom:6px !important;
      }
      .payer-detail h2, .payer-profile h2, [data-payer-detail] h2 {
        font-size:18px !important; line-height:1.25 !important; margin:0 0 8px !important;
      }
      .payer-detail h3, .payer-profile h3, [data-payer-detail] h3,
      .payer-detail .eyebrow, .payer-profile .eyebrow, [data-payer-detail] .eyebrow {
        font-size:11px !important; line-height:1.2 !important; letter-spacing:.06em !important; text-transform:uppercase;
      }
      .payer-detail p, .payer-profile p, [data-payer-detail] p,
      .payer-detail dd, .payer-profile dd, [data-payer-detail] dd,
      .payer-detail dt, .payer-profile dt, [data-payer-detail] dt {
        font-size:14px !important; line-height:1.45 !important;
      }
      .payer-detail .meta, .payer-profile .meta, [data-payer-detail] .meta,
      .payer-detail .subtitle, .payer-profile .subtitle, [data-payer-detail] .subtitle {
        font-size:13px !important; line-height:1.4 !important; color:#6b7874 !important;
      }
    `;
    document.head.append(style);
  }

  function candidateRoot() {
    return document.querySelector(".payer-detail, .payer-profile, [data-payer-detail]") ||
      [...document.querySelectorAll("main section, main article, main div")].find((el) => {
        const text = el.textContent || "";
        return /BASIC DATA|ZÁKLADNÍ ÚDAJE|REGISTRATION|REGISTRACE/.test(text) && /IČO|Company ID|DIČ|Tax ID/.test(text);
      });
  }

  function refresh() {
    injectStyles();
    const root = candidateRoot();
    if (!root) return;
    translateText(root);
  }

  function boot() {
    refresh();
    document.addEventListener("click", () => window.setTimeout(refresh, 0), true);
    document.addEventListener("change", (event) => {
      if (event.target?.id === "taxtreat-ui-language") window.setTimeout(refresh, 0);
    }, true);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once:true });
  else boot();
})();
