(() => {
  "use strict";

  const reportStatuses = new Map();
  const previousFetch = window.fetch.bind(window);

  function isFinal(status) {
    return String(status || "").toUpperCase() === "FINAL";
  }

  function statusCopy(status) {
    const normalized = String(status || "").toUpperCase();
    const en = document.documentElement.lang === "en";
    if (normalized === "FINAL") return en ? "COMPLETED" : "DOKONČENO";
    if (normalized === "OUT_OF_SCOPE") return en ? "OUT OF SCOPE" : "MIMO ROZSAH";
    return en ? "REQUIRES COMPLETION" : "VYŽADUJE DOPLNĚNÍ";
  }

  window.fetch = async function taxTreatOutputStatusFetch(resource, options = {}) {
    const response = await previousFetch(resource, options);
    const url = typeof resource === "string" ? resource : String(resource?.url || "");
    if (url.endsWith("/analysis/report") && response.ok) {
      try {
        const body = await response.clone().json();
        const id = String(body?.report?.report_id || "");
        const status = String(body?.report?.result?.status || "");
        if (id) reportStatuses.set(id, status);
      } catch (_problem) {}
    }
    return response;
  };

  function syncRows() {
    document.querySelectorAll('[data-view="reviews"] .review-history-row').forEach((row) => {
      const id = String(row.dataset.reviewReportId || "");
      const status = reportStatuses.get(id);
      if (!status) return;
      const badge = row.querySelector(".review-history-status");
      if (!badge) return;
      badge.classList.toggle("attention", !isFinal(status));
      badge.textContent = statusCopy(status);
      row.dataset.analysisStatus = status;
    });
  }

  function syncMetrics() {
    syncRows();
    const metrics = document.querySelectorAll('[data-view="dashboard"] .dashboard-metrics > article');
    const completed = metrics.item(2);
    const attention = metrics.item(3);
    if (!completed && !attention) return;

    const rows = [...document.querySelectorAll('[data-view="reviews"] .review-history-row')];
    const completedCount = rows.filter((row) => row.dataset.analysisStatus === "FINAL").length;
    const attentionCount = rows.filter((row) => row.dataset.analysisStatus && row.dataset.analysisStatus !== "FINAL").length;

    if (completed) {
      const label = completed.querySelector("span");
      const value = completed.querySelector("strong");
      const note = completed.querySelector("small");
      if (label) label.textContent = document.documentElement.lang === "en" ? "Completed calculations" : "Dokončené výpočty";
      if (value) value.textContent = String(completedCount);
      if (note) note.textContent = document.documentElement.lang === "en" ? "FINAL results in this browser session" : "FINAL výsledků v této relaci stránky";
    }

    if (attention) {
      const value = attention.querySelector("strong");
      if (value) value.textContent = String(attentionCount);
    }
  }

  let timer = 0;
  new MutationObserver(() => {
    window.clearTimeout(timer);
    timer = window.setTimeout(syncMetrics, 0);
  }).observe(document.documentElement, { subtree: true, childList: true, characterData: true });

  syncMetrics();
})();
