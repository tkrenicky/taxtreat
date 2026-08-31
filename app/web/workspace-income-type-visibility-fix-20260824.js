(() => {
  "use strict";

  function currentLanguage() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
  }

  function installStyles() {
    let style = document.querySelector("#tt-income-type-visibility-fix-20260824");
    if (!style) {
      style = document.createElement("style");
      style.id = "tt-income-type-visibility-fix-20260824";
      document.head.append(style);
    }
    style.textContent = `
      #dividend-facts[hidden],
      #interest-facts[hidden],
      #royalty-facts[hidden]{
        display:none!important;
      }
      #interest-facts:not([hidden]),
      #royalty-facts:not([hidden]){
        display:grid!important;
        grid-template-columns:1fr!important;
        gap:18px!important;
      }
    `;
  }

  function fixDomesticExemptionHeading() {
    const root = document.querySelector("#cz-section19-facts");
    const heading = root?.querySelector(":scope > div:first-child strong");
    if (!heading) return;
    const text = (heading.textContent || "").trim();
    if (!/možné osvobození/i.test(text) && !/potential.*exemption/i.test(text)) return;
    heading.textContent = currentLanguage() === "en"
      ? "Additional facts for potential domestic exemption"
      : "Doplňující údaje pro možné vnitrostátní osvobození";
  }

  function refresh() {
    installStyles();
    fixDomesticExemptionHeading();
  }

  function scheduleRefresh() {
    [0, 50, 150].forEach((delay) => window.setTimeout(refresh, delay));
  }

  document.addEventListener("change", (event) => {
    if (event.target?.matches?.('[name="income_type"],#taxtreat-ui-language')) scheduleRefresh();
  }, true);
  document.addEventListener("click", (event) => {
    if (event.target?.closest?.("#taxtreat-language-controls")) scheduleRefresh();
  }, true);

  refresh();
})();
