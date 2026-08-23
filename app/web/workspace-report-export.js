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

  loadScript("/ui-assets/workspace-cz-relief-i18n.js?v=20260820-4")
    .then(() => loadScript("/ui-assets/source-country-context.js?v=20260819-sk1"))
    .then(() => loadScript("/ui-assets/workspace-source-country-adapter.js?v=20260820-3"))
    .then(() => loadScript("/ui-assets/workspace-payer-country.js?v=20260821-freeze2"))
    .then(() => loadScript("/ui-assets/workspace-final-polish-v2.js?v=20260821-freeze1"))
    .then(() => loadScript("/ui-assets/workspace-report-context.js?v=20260820-1"))
    .then(() => loadScript("/ui-assets/workspace-ui-report-batch-20260821.js?v=20260821-batch1"))
    .then(() => loadScript("/ui-assets/workspace-header-language-20260821.js?v=20260821-batch1"))
    .then(() => loadScript("/ui-assets/workspace-payer-dialog-i18n-20260821.js?v=20260821-batch1"))
    .then(() => loadScript("/ui-assets/workspace-payer-detail-i18n-20260821.js?v=20260821-batch1"))
    .then(() => loadScript("/ui-assets/workspace-footer-i18n-20260821.js?v=20260821-batch1"))
    .then(() => loadScript("/ui-assets/workspace-section19-fallback-20260821.js?v=20260821-batch1"))
    .then(() => loadScript("/ui-assets/workspace-main-nav-size-fix-20260821.js?v=20260823-cz1"))
    .then(() => loadScript("/ui-assets/workspace-cz-ui-polish-20260823.js?v=20260823-czfinal3"))
    .then(() => loadScript("/ui-assets/workspace-report-export-core.js?v=20260819-3"))
    .catch((problem) => {
      console.error("TaxTreat workspace enhancement bootstrap failed", problem);
    });
})();
