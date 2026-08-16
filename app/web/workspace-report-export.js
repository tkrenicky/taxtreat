(() => {
  "use strict";

  const nativeFetch = window.fetch.bind(window);
  const outputHistory = [];
  const incomeLabels = {
    dividend: "Dividendy",
    interest: "Úroky",
    royalty: "Licenční poplatky",
  };
  let lastAnalysisPayload = null;
  let pendingReportFingerprint = null;

  function requestUrl(resource) {
    if (typeof resource === "string") return resource;
    if (resource && typeof resource.url === "string") return resource.url;
    return "";
  }

  function parseAnalysisPayload(resource, options = {}) {
    const url = requestUrl(resource);
    if (!url.endsWith("/analysis/intake") || !options.body) return null;
    try {
      const payload = JSON.parse(String(options.body));
      if (payload && payload.source_country && payload.recipient_country) {
        lastAnalysisPayload = payload;
        return payload;
      }
    } catch (_problem) {
      // Output history must never interfere with the calculation request.
    }
    return null;
  }

  function clientQuestionsRemain(body) {
    return (body?.intake?.questions || []).some(
      (question) => question.client_answerable
    );
  }

  function payloadFingerprint(payload) {
    return JSON.stringify(payload);
  }

  async function buildReport(payload) {
    const response = await nativeFetch("/analysis/report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await response.json();
    if (!response.ok || !body.html || !body.report) {
      throw new Error(
        body.detail?.code || "Report se nepodařilo vytvořit."
      );
    }
    return body;
  }

  function reportRecord(body) {
    return {
      id: String(body.report.report_id),
      html: body.html,
      generatedAt: String(body.report.generated_at || ""),
      recipientCountry: String(body.report.scope?.recipient_country || "—"),
      incomeType: String(body.report.scope?.income_type || ""),
      status: String(body.report.result?.status || ""),
      rate: body.report.result?.rate,
    };
  }

  function compactGeneratedAt(value) {
    if (!value) return "právě vytvořeno";
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;
    return new Intl.DateTimeFormat("cs-CZ", {
      day: "numeric",
      month: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(parsed);
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

  function openStoredReport(record, printAfterLoad = false) {
    const reportWindow = window.open("", "_blank");
    if (!reportWindow) {
      window.alert(
        "Prohlížeč zablokoval nové okno. Povol vyskakovací okna pro TaxTreat a zkus export znovu."
      );
      return;
    }
    prepareReportWindow(reportWindow, record.html, printAfterLoad);
  }

  function actionButton(label, action) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "secondary compact";
    button.textContent = label;
    button.addEventListener("click", action);
    return button;
  }

  function outputRow(record, compact = false) {
    const row = document.createElement("article");
    row.className = compact ? "output-history-row compact" : "output-history-row";
    row.dataset.outputReportId = record.id;

    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = `${incomeLabels[record.incomeType] || record.incomeType || "Výstup"} · ${record.recipientCountry}`;
    const meta = document.createElement("small");
    meta.textContent = `${record.id} · ${compactGeneratedAt(record.generatedAt)}`;
    copy.append(title, meta);

    const actions = document.createElement("div");
    actions.className = "output-history-actions";
    actions.append(
      actionButton("Otevřít report", () => openStoredReport(record)),
      actionButton("Tisk / PDF", () => openStoredReport(record, true)),
    );

    row.append(copy, actions);
    return row;
  }

  function renderOutputHistory() {
    const dashboardCards = document.querySelectorAll(
      '[data-view="dashboard"] .dashboard-grid > article.card'
    );
    const dashboardCard = dashboardCards.item(1);
    const outputsCard = document.querySelector('[data-view="outputs"] > article.card');

    if (dashboardCard) {
      dashboardCard.replaceChildren();
      const head = document.createElement("div");
      head.className = "card-head";
      const heading = document.createElement("h2");
      heading.textContent = "Poslední výstupy";
      const count = document.createElement("span");
      count.textContent = String(outputHistory.length);
      head.append(heading, count);
      dashboardCard.append(head);

      if (!outputHistory.length) {
        const empty = document.createElement("div");
        empty.className = "empty";
        const title = document.createElement("strong");
        title.textContent = "Zatím bez výstupů";
        const copy = document.createElement("p");
        copy.textContent = "Po dokončení kontroly platby se zde objeví její výsledek.";
        empty.append(title, copy);
        dashboardCard.append(empty);
      } else {
        outputHistory.slice(0, 3).forEach(
          (record) => dashboardCard.append(outputRow(record, true))
        );
      }
    }

    if (outputsCard) {
      outputsCard.replaceChildren();
      if (!outputHistory.length) {
        const empty = document.createElement("div");
        empty.className = "empty";
        const title = document.createElement("strong");
        title.textContent = "Zatím bez výstupů";
        const copy = document.createElement("p");
        copy.textContent = "Výstup vznikne po dokončení kontroly platby.";
        empty.append(title, copy);
        outputsCard.append(empty);
      } else {
        const head = document.createElement("div");
        head.className = "card-head";
        const heading = document.createElement("h2");
        heading.textContent = "Vytvořené výstupy";
        const count = document.createElement("span");
        count.textContent = String(outputHistory.length);
        head.append(heading, count);
        outputsCard.append(head);
        outputHistory.forEach(
          (record) => outputsCard.append(outputRow(record))
        );
      }
    }
  }

  function rememberReport(body) {
    const record = reportRecord(body);
    const existing = outputHistory.findIndex((item) => item.id === record.id);
    if (existing >= 0) outputHistory.splice(existing, 1);
    outputHistory.unshift(record);
    if (outputHistory.length > 10) outputHistory.length = 10;
    renderOutputHistory();
    return record;
  }

  async function cacheCompletedReport(payload) {
    const fingerprint = payloadFingerprint(payload);
    if (fingerprint === pendingReportFingerprint) return;
    pendingReportFingerprint = fingerprint;
    try {
      rememberReport(await buildReport(payload));
    } catch (_problem) {
      // A failed convenience preload must not change the calculation result.
    } finally {
      if (pendingReportFingerprint === fingerprint) {
        pendingReportFingerprint = null;
      }
    }
  }

  window.fetch = async function taxtreatReportAwareFetch(resource, options) {
    const payload = parseAnalysisPayload(resource, options);
    const response = await nativeFetch(resource, options);
    if (payload && response.ok) {
      response.clone().json().then((body) => {
        if (!clientQuestionsRemain(body)) cacheCompletedReport(payload);
      }).catch(() => {});
    }
    return response;
  };

  const resultActions = document.querySelector(
    '.flow-step[data-step="4"] .flow-actions'
  );
  const openButton = resultActions?.querySelector(".primary");

  renderOutputHistory();
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
      const body = await buildReport(lastAnalysisPayload);
      const record = rememberReport(body);
      prepareReportWindow(reportWindow, record.html, printAfterLoad);
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
