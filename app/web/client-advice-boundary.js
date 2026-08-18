(() => {
  "use strict";

  const SAFE_RESULT_COPY =
    "Zobrazený výsledek je automatizovaný informační výstup založený na zadaných údajích, " +
    "výchozích předpokladech a níže uvedených právních zdrojích. Nejde o individuální daňové " +
    "nebo právní posouzení, doporučení ani určení postupu uživatele.";

  function applyAdviceBoundary() {
    const explanation = document.querySelector("#hero-explanation");
    if (explanation && explanation.textContent !== SAFE_RESULT_COPY) {
      explanation.textContent = SAFE_RESULT_COPY;
    }
  }

  const reportFlow = document.createElement("script");
  reportFlow.src = "/ui-assets/client-report-flow.js";
  reportFlow.async = false;
  document.head.append(reportFlow);

  document.addEventListener("DOMContentLoaded", () => {
    applyAdviceBoundary();
    const result = document.querySelector("#result");
    if (!result) return;
    new MutationObserver(applyAdviceBoundary).observe(result, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true,
    });
  });
})();
