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

  const ENHANCEMENT_SCRIPTS = [
    "/ui-assets/workspace-locale-state-preservation-20260908.js?v=20260908-locale-state2",
    "/ui-assets/workspace-cz-relief-i18n.js?v=20260820-4",
    "/ui-assets/workspace-section19-completeness-20260830.js?v=20260830-s19complete1",
    "/ui-assets/source-country-context.js?v=20260819-sk1",
    "/ui-assets/workspace-source-country-adapter.js?v=20260820-3",
    "/ui-assets/workspace-payer-country.js?v=20260821-freeze2",
    "/ui-assets/workspace-final-polish-v2.js?v=20260821-freeze1",
    "/ui-assets/workspace-report-context.js?v=20260820-1",
    "/ui-assets/workspace-ui-report-batch-20260821.js?v=20260821-batch1",
    "/ui-assets/workspace-header-language-20260821.js?v=20260821-batch1",
    "/ui-assets/workspace-payer-dialog-i18n-20260821.js?v=20260821-batch1",
    "/ui-assets/workspace-payer-detail-i18n-20260821.js?v=20260821-batch1",
    "/ui-assets/workspace-footer-i18n-20260821.js?v=20260821-batch1",
    "/ui-assets/workspace-main-nav-size-fix-20260821.js?v=20260823-cz1",
    "/ui-assets/workspace-cz-ui-polish-20260823.js?v=20260823-czfinal3",
    "/ui-assets/workspace-cz-final-hardening-20260823.js?v=20260823-czfinal4",
    "/ui-assets/workspace-cz-nav-final-20260823.js?v=20260823-czfinal5",
    "/ui-assets/workspace-canonical-live-i18n-20260824.js?v=20260824-live1",
    "/ui-assets/workspace-canonical-live-i18n-dynamic-20260824.js?v=20260824-live2",
    "/ui-assets/workspace-live-language-and-ir-layout-20260824.js?v=20260824-live3",
    "/ui-assets/workspace-en-stabilizer-20260826.js?v=20260826-en1",
    "/ui-assets/workspace-en-residual-hardening-20260826.js?v=20260826-en2",
    "/ui-assets/workspace-en-final-residue2-20260826.js?v=20260826-en3",
  ];

  async function loadEnhancements() {
    for (const src of ENHANCEMENT_SCRIPTS) {
      try {
        await loadScript(src);
      } catch (problem) {
        console.error(problem);
      }
    }
  }

  loadEnhancements();
})();
