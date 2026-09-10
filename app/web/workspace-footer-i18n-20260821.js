(() => {
  "use strict";

  const BADGE_ID = "taxtreat-official-sources-badge";

  function language() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
  }

  function ensureOfficialSourcesBadge(footer) {
    if (document.getElementById(BADGE_ID)) return;
    const badge = document.createElement("span");
    badge.id = BADGE_ID;
    badge.setAttribute("role", "note");
    badge.style.cssText = "display:inline-flex;align-items:center;gap:6px;margin-left:12px;padding:3px 8px;border:1px solid currentColor;border-radius:999px;font-size:11px;font-weight:600;line-height:1.2;opacity:.78;white-space:nowrap";
    badge.textContent = "Pouze oficiální zdroje";
    footer.appendChild(badge);
  }

  function refresh() {
    const toEnglish = language() === "en";
    const map = toEnglish
      ? new Map([["Zásady ochrany dat","Data protection"],["Podmínky použití","Terms of use"]])
      : new Map([["Data protection","Zásady ochrany dat"],["Terms of use","Podmínky použití"]]);

    const footer = document.querySelector("footer, .app-footer");
    if (!footer) return;
    ensureOfficialSourcesBadge(footer);

    const walker = document.createTreeWalker(footer, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      const current = node.nodeValue;
      const key = current.trim();
      const replacement = map.get(key);
      if (replacement) node.nodeValue = current.replace(key, replacement);
    });

    const badge = document.getElementById(BADGE_ID);
    if (badge) badge.textContent = toEnglish ? "Official sources only" : "Pouze oficiální zdroje";
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