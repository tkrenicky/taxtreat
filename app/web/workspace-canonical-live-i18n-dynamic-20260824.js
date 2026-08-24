(() => {
  "use strict";

  const CS_MARKER = /Daňová rezidence:|Typ subjektu:|Skutečný vlastník(?: příjmu)?:|Vazba (?:na|ke) stálou provozovnu(?: v ČR)?:|Podíl na plátci:|Datum nabytí podílu:|profilové údaje vyplněny|základní údaje vyplněny/;
  const EN_MARKER = /Tax residence:|Entity type:|Beneficial owner:|Permanent establishment connection:|Ownership in payer:|Share acquisition date:|profile details completed|basic details completed/;

  function language() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
  }

  function translateDynamicLine(text, toEnglish) {
    if (toEnglish) {
      if (!CS_MARKER.test(text)) return text;
      return text
        .replace(/Daňová rezidence:\s*Rakouska/g, "Tax residence: Austria")
        .replace(/Daňová rezidence:/g, "Tax residence:")
        .replace(/Typ subjektu:/g, "Entity type:")
        .replace(/Skutečný vlastník(?: příjmu)?:/g, "Beneficial owner:")
        .replace(/Vazba (?:na|ke) stálou provozovnu(?: v ČR)?:/g, "Permanent establishment connection:")
        .replace(/Podíl na plátci:/g, "Ownership in payer:")
        .replace(/Datum nabytí podílu:/g, "Share acquisition date:")
        .replace(/profilové údaje vyplněny/g, "profile details completed")
        .replace(/základní údaje vyplněny/g, "basic details completed")
        .replace(/Rakouska|Rakousko/g, "Austria")
        .replace(/\bSpolečnost\b/g, "Company")
        .replace(/\bspolečnost\b/g, "company")
        .replace(/\bNevyplněno\b/g, "Not provided")
        .replace(/\bAno\b/g, "Yes")
        .replace(/\bNe\b/g, "No");
    }

    if (!EN_MARKER.test(text)) return text;
    return text
      .replace(/Tax residence:\s*Austria/g, "Daňová rezidence: Rakouska")
      .replace(/Tax residence:/g, "Daňová rezidence:")
      .replace(/Entity type:/g, "Typ subjektu:")
      .replace(/Beneficial owner:/g, "Skutečný vlastník:")
      .replace(/Permanent establishment connection:/g, "Vazba na stálou provozovnu:")
      .replace(/Ownership in payer:/g, "Podíl na plátci:")
      .replace(/Share acquisition date:/g, "Datum nabytí podílu:")
      .replace(/profile details completed/g, "profilové údaje vyplněny")
      .replace(/basic details completed/g, "základní údaje vyplněny")
      .replace(/\bAustria\b/g, "Rakousko")
      .replace(/\bCompany\b/g, "Společnost")
      .replace(/\bcompany\b/g, "společnost")
      .replace(/\bNot provided\b/g, "Nevyplněno")
      .replace(/\bYes\b/g, "Ano")
      .replace(/\bNo\b/g, "Ne");
  }

  function refresh() {
    const toEnglish = language() === "en";
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      if (node.parentElement?.closest("blockquote,.legal-excerpt,pre,code")) return;
      const current = node.nodeValue || "";
      const next = translateDynamicLine(current, toEnglish);
      if (next !== current) node.nodeValue = next;
    });
  }

  function schedule() {
    [0, 50, 150, 400, 900].forEach((delay) => window.setTimeout(refresh, delay));
  }

  document.addEventListener("change", (event) => {
    if (event.target?.id === "taxtreat-ui-language") schedule();
  }, true);
  document.addEventListener("click", () => window.setTimeout(schedule, 0), true);
  schedule();
})();
