(() => {
  "use strict";

  function formatPayerCopy(root = document) {
    root.querySelectorAll('[data-view="payers"] .payer-record').forEach((card) => {
      const copy = card.querySelector(':scope > .avatar + div');
      const title = copy?.querySelector('h2');
      const meta = copy?.querySelector('p');
      if (!copy || !title || !meta) return;

      const baseName = (title.textContent || "").replace(/\s*\(Česká republika\)\s*$/, "").trim();
      const rawMeta = meta.textContent || "";
      const ico = rawMeta.match(/IČO\s+([^·\n]+)/i)?.[1]?.trim() || "";
      const dic = rawMeta.match(/DIČ\s+([^·\n]+)/i)?.[1]?.trim() || "";

      title.textContent = `${baseName} (Česká republika)`;
      meta.replaceChildren();

      const icoLine = document.createElement("span");
      icoLine.textContent = ico ? `IČO ${ico}` : "IČO neuvedeno";
      icoLine.style.display = "block";
      meta.append(icoLine);

      if (dic) {
        const dicLine = document.createElement("span");
        dicLine.textContent = `DIČ ${dic}`;
        dicLine.style.display = "block";
        meta.append(dicLine);
      }
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
