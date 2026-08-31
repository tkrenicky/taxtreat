(() => {
  "use strict";

  function ensureReasonAnchor() {
    if (document.querySelector("#workspace-reason")) return;
    const step4 = document.querySelector('.flow-step[data-step="4"]');
    if (!step4) return;
    const reasonCard = step4.querySelector(".reason") || [...step4.querySelectorAll("article,section,.card")].find((el) => /Použité právní pravidlo|Applied legal rule/i.test(el.textContent || ""));
    if (!reasonCard) return;
    const p = document.createElement("p");
    p.id = "workspace-reason";
    p.textContent = "";
    reasonCard.append(p);
  }

  function ensureCoreResultAnchors() {
    ensureReasonAnchor();
    const step4 = document.querySelector('.flow-step[data-step="4"]');
    if (!step4) return;

    const required = [
      ["workspace-result-status", ".result-hero", "span"],
      ["workspace-tax-label", ".result-hero", "p"],
      ["workspace-tax", ".result-hero", "strong"],
      ["workspace-rate", ".result-hero", "small"],
      ["workspace-actions", ".dashboard-grid article:nth-child(2)", "div"],
      ["workspace-citations", ".result-sources", "div"]
    ];

    required.forEach(([id, parentSelector, tag]) => {
      if (document.getElementById(id)) return;
      const parent = step4.querySelector(parentSelector);
      if (!parent) return;
      const node = document.createElement(tag);
      node.id = id;
      parent.append(node);
    });
  }

  // Critical: capture phase runs before workspace.js' form submit handler.
  document.addEventListener("submit", (event) => {
    if (event.target?.id === "workspace-payment") ensureCoreResultAnchors();
  }, true);

  document.addEventListener("click", (event) => {
    if (event.target?.closest("#workspace-submit")) ensureCoreResultAnchors();
  }, true);

  ensureCoreResultAnchors();
})();
