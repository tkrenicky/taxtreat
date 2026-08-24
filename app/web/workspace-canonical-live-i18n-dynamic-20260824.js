(() => {
  "use strict";

  function language() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
  }

  function translateDynamicLine(text, toEnglish) {
    if (toEnglish) {
      return text
        .replace(/Daňová rezidence:/g, "Tax residence:")
        .replace(/Typ subjektu:/g, "Entity type:")
        .replace(/Skutečný vlastník(?: příjmu)?:/g, "Beneficial owner:")
        .replace(/Vazba (?:na|ke) stálou provozovnu(?: v ČR)?:/g, "Permanent establishment connection:")
        .replace(/Podíl na plátci:/g, "Ownership in payer:")
        .replace(/Datum nabytí podílu:/g, "Share acquisition date:")
        .replace(/profilové údaje vyplněny/g, "profile details completed")
        .replace(/základní údaje vyplněny/g, "basic details completed")
        .replace(/Rakouska/g, "Austria")
        .replace(/Rakousko/g, "Austria")
        .replace(/Společnost/g, "Company")
        .replace(/společnost/g, "company")
        .replace(/Nevyplněno/g, "Not provided");
    }
    return text
      .replace(/Tax residence:/g, "Daňová rezidence:")
      .replace(/Entity type:/g, "Typ subjektu:")
      .replace(/Beneficial owner:/g, "Skutečný vlastník:")
      .replace(/Permanent establishment connection:/g, "Vazba na stálou provozovnu:")
      .replace(/Ownership in payer:/g, "Podíl na plátci:")
      .replace(/Share acquisition date:/g, "Datum nabytí podílu:")
      .replace(/profile details completed/g, "profilové údaje vyplněny")
      .replace(/basic details completed/g, "základní údaje vyplněny")
      .replace(/Austria/g, "Rakousko")
      .replace(/Company/g, "Společnost")
      .replace(/company/g, "společnost")
      .replace(/Not provided/g, "Nevyplněno");
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
