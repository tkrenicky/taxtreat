(() => {
  "use strict";

  function syncReviewConditionsVisibility() {
    const actions = document.querySelector("#workspace-actions");
    if (!actions) return;

    const card = actions.closest("article.card");
    if (!card) return;

    const hasReviewItems = actions.querySelector(".action-item") !== null;
    if (card.hidden === hasReviewItems) card.hidden = !hasReviewItems;

    const grid = card.closest(".dashboard-grid");
    if (grid) grid.classList.toggle("single-column", !hasReviewItems);
  }

  const observer = new MutationObserver(syncReviewConditionsVisibility);

  function start() {
    syncReviewConditionsVisibility();
    const resultStep = document.querySelector('.flow-step[data-step="4"]') || document.body;
    observer.observe(resultStep, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ["hidden"],
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start, { once: true });
  } else {
    start();
  }
})();
