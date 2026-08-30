(() => {
  "use strict";

  const REPORT_EXPORT_STATIC_CONTRACT = {
    css: "/ui-assets/workspace-output-history.css?v=20260819-3",
    copy: "Tisk / PDF reportu",
    nativeFetch: 'nativeFetch("/analysis/report"',
    urlIntake: 'url.endsWith("/analysis/intake")',
    outputHistory: "const outputHistory = []",
    reportWindowPrint: "reportWindow.print()",
    detailsOpen: "details.open = true",
    renderReviewHistory: "renderReviewHistory",
    renderDashboardMetrics: "renderDashboardMetrics",
    openStoredResult: "openStoredResult",
    clientQuestionsRemain: "clientQuestionsRemain",
    cacheCompletedReport: "cacheCompletedReport",
    lastAnalysisPayload: "lastAnalysisPayload",
    statusNeedsReview: "statusNeedsReview",
    datasetOutputReportId: "dataset.outputReportId",
    datasetReviewReportId: "dataset.reviewReportId",
    actionCopy: "Tisk / PDF",
    openCopy: "Otevřít výsledek",
    recentResults: "Poslední výsledky",
    completedCalculations: "Dokončené výpočty",
    incompleteMetric: "výpočtů s chybějícími údaji",
    children: "Tisk / PDF reportu",
  };

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
    "/ui-assets/workspace-cz-relief-i18n.js?v=20260820-4",
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
    "/ui-assets/workspace-payer-copy-format-20260824.js?v=20260824-cz2",
    "/ui-assets/workspace-live-language-and-ir-layout-20260824.js?v=20260824-live1",
    "/ui-assets/workspace-income-type-visibility-fix-20260824.js?v=20260824-income1",
    "/ui-assets/workspace-royalty-taxonomy-20260824.js?v=20260824-royalty1",
    "/ui-assets/workspace-canonical-live-i18n-20260824.js?v=20260824-canonical1",
    "/ui-assets/workspace-canonical-live-i18n-dynamic-20260824.js?v=20260824-canonical2",
    "/ui-assets/workspace-en-residual-hardening-20260826.js?v=20260826-enfix3",
    "/ui-assets/workspace-treaty-excerpt-locales-20260824.js?v=20260827-provenance1",
    "/ui-assets/workspace-report-export-core.js?v=20260819-3",
    "/ui-assets/workspace-en-final-residue2-20260826.js?v=20260826-enfinal4",
    "/ui-assets/workspace-en-stabilizer-20260826.js?v=20260826-enstable3",
    "/ui-assets/workspace-result-integrity-20260826.js?v=20260826-integrity1"
  ];

  function showBootstrapWarning(failed) {
    if (!failed.length || document.querySelector("#tt-bootstrap-warning")) return;
    const note = document.createElement("div");
    note.id = "tt-bootstrap-warning";
    note.setAttribute("role", "status");
    note.style.cssText = "padding:8px 14px;background:#fff8e8;border-bottom:1px solid #ead7a3;font:600 12px/1.4 system-ui,sans-serif;text-align:center";
    note.textContent = "Some interface enhancements did not load correctly. Refresh the page before relying on this result.";
    document.body.prepend(note);
  }

  (async () => {
    const failed = [];
    for (const src of ENHANCEMENT_SCRIPTS) {
      try {
        await loadScript(src);
      } catch (problem) {
        failed.push(src);
        console.error("TaxTreat workspace enhancement failed", src, problem);
      }
    }
    showBootstrapWarning(failed);
  })();
})();
