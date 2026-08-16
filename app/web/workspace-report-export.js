(() => {
  "use strict";

  const nativeFetch = window.fetch.bind(window);
  let lastAnalysisPayload = null;

  function requestUrl(resource) {
    if (typeof resource === "string") return resource;
    if (resource && typeof resource.url === "string") return resource.url;
    return "";
  }

  function captureAnalysisPayload(resource, options = {}) {
    const url = requestUrl(resource);
    if (!url.endsWith("/analysis/intake") || !options.body) return;
    try {
      const payload = JSON.parse(String(options.body));
      if (payload && payload.source_country && payload.recipient_country) {
        lastAnalysisPayload = payload;
      }
    } catch (_problem) {
      // Export must never interfere with the calculation request itself.
    }
  }

  window.fetch = function taxtreatReportAwareFetch(resource, options) {
    captureAnalysisPayload(resource, options);
    return nativeFetch(resource, options);
  };

  const resultActions = document.querySelector(
    '.flow-step[data-step="4"] .flow-actions'
  );
  const openButton = resultActions?.querySelector(".primary");

  if (!resultActions || !openButton) return;

  openButton.removeAttribute("data-nav");
  openButton.type = "button";
  openButton.textContent = "Otevřít profesionální report";
  openButton.dataset.reportAction = "open";

  const printButton = document.createElement("button");
  printButton.type = "button";
  printButton.className = "secondary";
  printButton.textContent = "Tisk / uložit PDF";
  printButton.dataset.reportAction = "print";
  resultActions.insertBefore(printButton, openButton);

  function showExportProblem(message) {
    window.alert(message);
  }

  function prepareReportWindow(reportWindow, html, printAfterLoad) {
    reportWindow.document.open();
    reportWindow.document.write(html);
    reportWindow.document.close();
    reportWindow.opener = null;

    if (!printAfterLoad) {
      reportWindow.focus();
      return;
    }

    let printed = false;
    const printReport = () => {
      if (printed) return;
      printed = true;
      reportWindow.document
        .querySelectorAll("details")
        .forEach((details) => { details.open = true; });
      reportWindow.focus();
      reportWindow.print();
    };

    reportWindow.addEventListener("load", printReport, { once: true });
    window.setTimeout(printReport, 250);
  }

  async function exportReport(printAfterLoad, button) {
    if (!lastAnalysisPayload) {
      showExportProblem(
        "Nejprve dokonči výpočet. Report lze vytvořit až z vyhodnocené platby."
      );
      return;
    }

    const reportWindow = window.open("", "_blank");
    if (!reportWindow) {
      showExportProblem(
        "Prohlížeč zablokoval nové okno. Povol vyskakovací okna pro TaxTreat a zkus export znovu."
      );
      return;
    }

    const originalLabel = button.textContent;
    button.disabled = true;
    button.textContent = "Připravuji report…";
    reportWindow.document.write(
      "<!doctype html><title>TaxTreat</title><p style='font-family:system-ui;padding:32px'>Připravuji profesionální report…</p>"
    );

    try {
      const response = await nativeFetch("/analysis/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(lastAnalysisPayload),
      });
      const body = await response.json();
      if (!response.ok || !body.html) {
        throw new Error(
          body.detail?.code || "Report se nepodařilo vytvořit."
        );
      }
      prepareReportWindow(reportWindow, body.html, printAfterLoad);
    } catch (problem) {
      reportWindow.close();
      showExportProblem(
        problem?.message || "Report se nepodařilo vytvořit."
      );
    } finally {
      button.disabled = false;
      button.textContent = originalLabel;
    }
  }

  openButton.addEventListener(
    "click",
    (event) => {
      event.preventDefault();
      event.stopImmediatePropagation();
      exportReport(false, openButton);
    },
    true
  );

  printButton.addEventListener("click", () => {
    exportReport(true, printButton);
  });
})();
