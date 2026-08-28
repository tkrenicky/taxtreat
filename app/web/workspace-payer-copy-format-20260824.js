(() => {
  "use strict";

  function formatPayerCopy(root = document) {
    root.querySelectorAll('[data-view="payers"] .payer-record').forEach((card) => {
      if (card.dataset.ttPayerCopyFormatted === "true") return;
      const copy = card.querySelector(':scope > .avatar + div');
      const title = copy?.querySelector('h2');
      const meta = copy?.querySelector('p');
      if (!copy || !title || !meta) return;

      const baseName = (title.textContent || "").replace(/\s*\(Česká republika\)\s*$/, "").trim();
      const rawMeta = meta.textContent || "";
      const ico = rawMeta.match(/IČO\s+([^·\n]+)/i)?.[1]?.trim() || "";
      const dic = rawMeta.match(/DIČ\s+([^·\n]+)/i)?.[1]?.trim() || "";

      if (title.textContent !== baseName) title.textContent = baseName;
      meta.replaceChildren();
      meta.append(document.createTextNode(`Česká republika · IČO ${ico || "neuvedeno"}`));

      if (dic) {
        meta.append(document.createTextNode(" · "));
        const dicGroup = document.createElement("span");
        dicGroup.textContent = `DIČ ${dic}`;
        dicGroup.style.whiteSpace = "nowrap";
        meta.append(dicGroup);
      }
      // Mark after the one intentional rewrite. The observer sees the
      // mutations produced above, but subsequent callbacks are no-ops.
      card.dataset.ttPayerCopyFormatted = "true";
    });
  }

  function install() {
    const payerList = document.querySelector('#payer-list');
    formatPayerCopy();
    if (!payerList) return;

    const observer = new MutationObserver(() => formatPayerCopy(payerList.closest('[data-view="payers"]') || document));
    observer.observe(payerList, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", install, { once: true });
  } else {
    install();
  }
})();
