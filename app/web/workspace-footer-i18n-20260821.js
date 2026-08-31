(() => {
  "use strict";

  function language() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
  }

  function refresh() {
    const toEnglish = language() === "en";
    const map = toEnglish
      ? new Map([["Zásady ochrany dat","Data protection"],["Podmínky použití","Terms of use"]])
      : new Map([["Data protection","Zásady ochrany dat"],["Terms of use","Podmínky použití"]]);

    const footer = document.querySelector("footer, .app-footer");
    if (!footer) return;
    const walker = document.createTreeWalker(footer, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      const current = node.nodeValue;
      const key = current.trim();
      const replacement = map.get(key);
      if (replacement) node.nodeValue = current.replace(key, replacement);
    });
  }

  function boot() {
    refresh();
    document.addEventListener("change", (event) => {
      if (event.target?.id === "taxtreat-ui-language") window.setTimeout(refresh, 0);
    }, true);
    document.addEventListener("click", (event) => {
      if (event.target?.closest?.("#taxtreat-language-controls")) window.setTimeout(refresh, 0);
    }, true);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once:true });
  else boot();
})();
