(() => {
  "use strict";

  const CS_NOTICE = '<strong>Informační nástroj:</strong> TaxTreat zobrazuje automatizované informace z právních zdrojů a zadaných údajů; neposkytuje individuální právní ani daňové poradenství ani doporučení.';
  const EN_NOTICE = '<strong>Information tool:</strong> TaxTreat displays automated information derived from legal sources and the facts entered by the user; it does not provide individual legal or tax advice or recommendations.';

  function language() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
  }

  function refresh() {
    const en = language() === "en";
    const activePayerLabel = document.querySelector(".app-header .payer-context:has(#active-payer-select) > span, .app-header label:has(#active-payer-select) > span");
    if (activePayerLabel) activePayerLabel.textContent = en ? "ACTIVE PAYER" : "AKTIVNÍ PLÁTCE";

    const notice = document.querySelector(".information-only-note");
    if (notice) notice.innerHTML = en ? EN_NOTICE : CS_NOTICE;

    document.querySelectorAll("#taxtreat-language-controls .tt-lang-mini button").forEach((button) => {
      const lang = button.dataset.lang;
      if (lang === "cs") button.textContent = "🇨🇿 CZ";
      if (lang === "en") button.textContent = "🇬🇧 EN";
      const active = lang === language();
      button.dataset.active = String(active);
      button.style.opacity = "1";
      button.style.textDecoration = "none";
      button.setAttribute("aria-pressed", String(active));
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
