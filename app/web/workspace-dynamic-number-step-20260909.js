(() => {
  "use strict";

  const root = document.querySelector("#workspace-questions");
  if (!root) return;

  function allowDecimalNumberAnswers() {
    root.querySelectorAll('input[data-response-type="number"]').forEach((input) => {
      // Generic treaty numeric facts are not necessarily integers. Without an
      // explicit step, HTML number inputs default to step=1 and the browser can
      // block valid values such as 9.99 before /analysis/intake is submitted.
      input.step = "any";
    });
  }

  allowDecimalNumberAnswers();
  new MutationObserver(allowDecimalNumberAnswers).observe(root, {
    childList: true,
    subtree: true,
  });
})();
