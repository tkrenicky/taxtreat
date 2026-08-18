(() => {
  "use strict";

  const originalOpen = window.open.bind(window);
  const loadingHtml = `<!doctype html>
    <title>TaxTreat</title>
    <style>
      html,body{margin:0;min-height:100%;background:#EFEDE4;color:#1B2A4A}
      body{min-height:100vh;display:grid;place-items:center;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif}
      main{width:min(420px,calc(100% - 40px));padding:28px;border:1px solid #E1E0D8;border-radius:12px;background:#FBFAF6;text-align:center}
      b{display:block;margin-bottom:8px;font-family:Georgia,"Iowan Old Style","Palatino Linotype",serif;font-size:25px;font-weight:500}
      p{margin:0;color:#697183;font-size:13px;line-height:1.5}
    </style>
    <main><b>TaxTreat</b><p>Připravuji klientský report…</p></main>`;

  window.open = (...args) => {
    const popup = originalOpen(...args);
    if (!popup) return popup;

    try {
      const originalWrite = popup.document.write.bind(popup.document);
      popup.document.write = (html) => {
        const value = String(html ?? "");
        if (value.includes("Připravuji PDF výstup")) {
          return originalWrite(loadingHtml);
        }
        return originalWrite(html);
      };
    } catch (_) {
      // If the browser prevents access, the canonical report flow remains unchanged.
    }
    return popup;
  };
})();
