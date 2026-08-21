(() => {
  "use strict";

  function step4Root() {
    return document.querySelector('.flow-step[data-step="4"]');
  }

  function ensureReasonAnchor() {
    const root = step4Root();
    if (!root || root.querySelector("#workspace-reason")) return;

    const card = root.querySelector("article.reason") || [...root.querySelectorAll("article,section,.card")].find((el) =>
      /Použité právní pravidlo|Applied legal rule/i.test(el.textContent || "")
    );
    if (!card) return;

    let reason = card.querySelector("p");
    if (!reason) {
      reason = document.createElement("p");
      card.append(reason);
    }
    reason.id = "workspace-reason";
  }

  function repair() {
    ensureReasonAnchor();
  }

  /* Run before the workspace submit handler can use the result anchors. */
  document.addEventListener("submit", (event) => {
    if (event.target?.id === "workspace-payment") repair();
  }, true);

  document.addEventListener("click", (event) => {
    if (event.target?.closest("#workspace-submit,[data-next-step],[data-flow-step]")) repair();
  }, true);

  document.addEventListener("change", (event) => {
    if (event.target?.id === "taxtreat-ui-language") window.setTimeout(repair, 0);
  }, true);

  repair();
})();
