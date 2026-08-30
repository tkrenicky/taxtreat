(() => {
  "use strict";

  function syncMetrics() {
    const metrics = document.querySelectorAll('[data-view="dashboard"] .dashboard-metrics > article');
    const completed = metrics.item(2);
    const attention = metrics.item(3);
    if (!completed && !attention) return;

    const rows = [...document.querySelectorAll('[data-view="reviews"] .review-history-row')];
    const reviewCount = rows.filter((row) => row.querySelector('.review-history-status.attention')).length;
    const completedCount = Math.max(0, rows.length - reviewCount);

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
      if (value) value.textContent = String(reviewCount);
    }
  }

  let timer = 0;
  new MutationObserver(() => {
    window.clearTimeout(timer);
    timer = window.setTimeout(syncMetrics, 0);
  }).observe(document.documentElement, { subtree: true, childList: true, characterData: true });

  syncMetrics();
})();
