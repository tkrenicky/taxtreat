(() => {
  "use strict";

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = src;
      script.defer = true;
      script.onload = resolve;
      script.onerror = () => reject(new Error(`Failed to load ${src}`));
      document.head.append(script);
    });
  }

  loadScript("/ui-assets/workspace-cz-relief-i18n.js?v=20260820-1")
    .then(() => loadScript("/ui-assets/source-country-context.js?v=20260819-sk1"))
    .then(() => loadScript("/ui-assets/workspace-source-country-adapter.js?v=20260819-sk1"))
    .then(() => loadScript("/ui-assets/workspace-report-export-core.js?v=20260819-3"))
    .catch((problem) => {
      console.error("TaxTreat workspace enhancement bootstrap failed", problem);
    });
})();
