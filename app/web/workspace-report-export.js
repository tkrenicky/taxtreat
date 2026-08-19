(() => {
  "use strict";

  const historyStyles = document.createElement("link");
  historyStyles.rel = "stylesheet";
  historyStyles.href = "/ui-assets/workspace-output-history.css?v=20260819-3";
  document.head.append(historyStyles);

  const nativeFetch = window.fetch.bind(window);
  const outputHistory = [];
  const incomeLabels = {
    dividend: "Dividendy",
    interest: "Úroky",
    royalty: "Licenční poplatky",
  };
  let lastAnalysisPayload = null;
  let lastAnalysisResponse = null;
  let pendingReportFingerprint = null;

  function requestUrl(resource) {
    if (typeof resource === "string") return resource;
    if (resource && typeof resource.url === "string") return resource.url;
    return "";
  }

  function reportPartyContext() {
    const payer = document.querySelector("#active-payer-select option:checked")?.textContent?.trim() || "";
    const recipient = document.querySelector("#flow-recipient-name")?.textContent?.trim() || "";
    return { payer, recipient };
  }

  function enrichPayloadForReport(payload) {
    if (!payload || typeof payload !== "object") return payload;
    const { payer, recipient } = reportPartyContext();
    payload.facts = payload.facts && typeof payload.facts === "object" ? payload.facts : {};
    if (payer) payload.facts.report_payer_name = payer;
    if (recipient) payload.facts.report_recipient_name = recipient;
    return payload;
  }

  function parseAnalysisPayload(resource, options = {}) {
    const url = requestUrl(resource);
    if (!url.endsWith("/analysis/intake") || !options.body) return null;
    try {
      const payload = enrichPayloadForReport(JSON.parse(String(options.body)));
      if (payload && payload.source_country && payload.recipient_country) {
        options.body = JSON.stringify(payload);
        lastAnalysisPayload = payload;
        return payload;
      }
    } catch (_problem) {
      // Output history must never interfere with the calculation request.
    }
    return null;
  }

  function clientQuestionsRemain(body) {
    return (body?.intake?.questions || []).some((question) => question.client_answerable);
  }

  function payloadFingerprint(payload) {
    return JSON.stringify(payload);
  }

  async function buildReport(payload) {
    const response = await nativeFetch("/analysis/report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(enrichPayloadForReport(structuredClone(payload))),
    });
    const body = await response.json();
    if (!response.ok || !body.html || !body.report) {
      throw new Error(body.detail?.code || "Report se nepodařilo vytvořit.");
    }
    return body;
  }

  function reportRecord(body, payload = null, analysisResponse = null) {
    const facts = body.report.assumptions?.transaction_facts || {};
    return {
      id: String(body.report.report_id),
      html: body.html,
      generatedAt: String(body.report.generated_at || ""),
      recipientCountry: String(body.report.scope?.recipient_country || "—"),
      incomeType: String(body.report.scope?.income_type || ""),
      status: String(body.report.result?.status || ""),
      rate: body.report.result?.rate,
      payerName: String(facts.report_payer_name || ""),
      recipientName: String(facts.report_recipient_name || ""),
      fingerprint: payload ? payloadFingerprint(payload) : "",
      payload: payload ? structuredClone(payload) : null,
      analysisResponse: analysisResponse
        ? structuredClone(analysisResponse)
        : null,
    };
  }

  function compactGeneratedAt(value) {
    if (!value) return "právě vytvořeno";
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;
    return new Intl.DateTimeFormat("cs-CZ", {
      day: "numeric", month: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit",
    }).format(parsed);
  }

  function statusNeedsReview(status) {
    const normalized = String(status || "").toUpperCase();
    return normalized.includes("REVIEW") || normalized.includes("UNCERTAIN") || normalized.includes("MANUAL");
  }

  function statusLabel(status) {
    return statusNeedsReview(status) ? "VYŽADUJE DOPLNĚNÍ" : "DOKONČENO";
  }

  function formatRate(rate) {
    if (rate === null || rate === undefined || rate === "") return "sazba —";
    const numeric = Number(rate);
    if (Number.isNaN(numeric)) return `sazba ${rate}`;
    return `sazba ${new Intl.NumberFormat("cs-CZ", { maximumFractionDigits: 2 }).format(numeric)} %`;
  }

  function historyTitle(record, fallback = "Výstup") {
    const base = `${incomeLabels[record.incomeType] || record.incomeType || fallback} · ${record.recipientCountry}`;
    if (record.payerName && record.recipientName) return `${base} · ${record.payerName} → ${record.recipientName}`;
    return base;
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
      reportWindow.document.querySelectorAll("details").forEach((details) => { details.open = true; });
      reportWindow.focus();
      reportWindow.print();
    };
    reportWindow.addEventListener("load", printReport, { once: true });
    window.setTimeout(printReport, 250);
  }

  function openStoredReport(record, printAfterLoad = false) {
    const reportWindow = window.open("", "_blank");
    if (!reportWindow) {
      showExportProblem("Prohlížeč zablokoval nové okno. Povol vyskakovací okna pro TaxTreat a zkus export znovu.");
      return;
    }
    prepareReportWindow(reportWindow, record.html, printAfterLoad);
  }

  function openStoredResult(record) {
    if (
      record.payload &&
      record.analysisResponse &&
      window.TaxTreatWorkspace?.openStoredResult
    ) {
      lastAnalysisPayload = structuredClone(record.payload);
      lastAnalysisResponse = structuredClone(record.analysisResponse);

      window.TaxTreatWorkspace.openStoredResult(
        record.payload,
        record.analysisResponse
      );
      return;
    }

    // Fallback for any old in-memory record without the calculation body.
    openStoredReport(record, false);
  }

  function actionButton(label, action) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "secondary compact";
    button.textContent = label;
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      action();
    });
    return button;
  }

  function outputRow(record, compact = false) {
    const row = document.createElement("article");
    row.className = compact
      ? "output-history-row compact is-clickable"
      : "output-history-row";

    row.dataset.outputReportId = record.id;

    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = historyTitle(record);

    const meta = document.createElement("small");
    meta.textContent = `${compactGeneratedAt(record.generatedAt)} · ${formatRate(record.rate)}`;

    copy.append(title, meta);

    const actions = document.createElement("div");
    actions.className = "output-history-actions";
    actions.append(
      actionButton("Tisk / PDF", () => openStoredReport(record, true))
    );

    row.append(copy, actions);

    if (compact) {
      row.tabIndex = 0;
      row.setAttribute("role", "button");
      row.setAttribute("aria-label", `Otevřít výsledek: ${historyTitle(record)}`);

      row.addEventListener("click", () => openStoredResult(record));
      row.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openStoredResult(record);
        }
      });
    }

    return row;
  }

  function reviewRow(record) {
    const row = document.createElement("article");
    row.className = "review-history-row";
    row.dataset.reviewReportId = record.id;

    const copy = document.createElement("div");

    const eyebrow = document.createElement("small");
    eyebrow.textContent = compactGeneratedAt(record.generatedAt);

    const title = document.createElement("strong");
    title.textContent = historyTitle(record, "Platba");

    const meta = document.createElement("span");
    meta.textContent = formatRate(record.rate);

    copy.append(eyebrow, title, meta);

    const status = document.createElement("b");
    status.className = statusNeedsReview(record.status)
      ? "review-history-status attention"
      : "review-history-status";
    status.textContent = statusLabel(record.status);

    const actions = document.createElement("div");
    actions.className = "output-history-actions";
    actions.append(
      actionButton("Otevřít výsledek", () => openStoredResult(record)),
      actionButton("Tisk / PDF", () => openStoredReport(record, true)),
    );

    row.append(copy, status, actions);
    return row;
  }

  function renderOutputHistory() {
    const dashboardCards = document.querySelectorAll(
      '[data-view="dashboard"] .dashboard-grid > article.card'
    );
    const dashboardCard = dashboardCards.item(1);

    if (!dashboardCard) return;

    dashboardCard.replaceChildren();

    const head = document.createElement("div");
    head.className = "card-head";

    const heading = document.createElement("h2");
    heading.textContent = "Poslední výsledky";

    const count = document.createElement("span");
    count.textContent = String(outputHistory.length);

    head.append(heading, count);
    dashboardCard.append(head);

    if (!outputHistory.length) {
      const empty = document.createElement("div");
      empty.className = "empty";

      const title = document.createElement("strong");
      title.textContent = "Zatím bez výsledků";

      const copy = document.createElement("p");
      copy.textContent =
        "Po dokončení výpočtu se zde zobrazí poslední výsledky.";

      empty.append(title, copy);
      dashboardCard.append(empty);
      return;
    }

    outputHistory
      .slice(0, 3)
      .forEach((record) => dashboardCard.append(outputRow(record, true)));
  }

  function renderReviewHistory() {
    const reviewsCard = document.querySelector('[data-view="reviews"] > article.card');
    if (!reviewsCard) return;
    reviewsCard.replaceChildren();
    if (!outputHistory.length) {
      const empty = document.createElement("div"); empty.className = "empty";
      const title = document.createElement("strong"); title.textContent = "Zatím bez výsledků";
      const copy = document.createElement("p"); copy.textContent = "Po dokončení prvního výpočtu se zde zobrazí výsledek a report.";
      empty.append(title, copy); reviewsCard.append(empty); return;
    }
    const head = document.createElement("div"); head.className = "card-head";
    const heading = document.createElement("h2"); heading.textContent = "Výsledky";
    const count = document.createElement("span"); count.textContent = String(outputHistory.length);
    head.append(heading, count); reviewsCard.append(head);
    outputHistory.forEach((record) => reviewsCard.append(reviewRow(record)));
  }

  function renderDashboardMetrics() {
    const metrics = document.querySelectorAll('[data-view="dashboard"] .dashboard-metrics > article');
    const completed = metrics.item(2);
    const attention = metrics.item(3);
    const attentionCount = outputHistory.filter((record) => statusNeedsReview(record.status)).length;
    if (completed) {
      completed.querySelector("span").textContent = "Dokončené výpočty";
      completed.querySelector("strong").textContent = String(outputHistory.length);
      completed.querySelector("small").textContent = "v této relaci stránky";
    }
    if (attention) {
      attention.querySelector("strong").textContent = String(attentionCount);
      attention.querySelector("small").textContent = "výpočtů s chybějícími údaji";
    }
  }

  function renderWorkspaceHistory() {
    renderOutputHistory();
    renderReviewHistory();
    renderDashboardMetrics();
  }

  function rememberReport(
    body,
    payload = null,
    analysisResponse = null
  ) {
    const record = reportRecord(body, payload, analysisResponse);

    const existing = outputHistory.findIndex((item) =>
      (record.fingerprint && item.fingerprint === record.fingerprint) ||
      item.id === record.id
    );

    if (existing >= 0) {
      const previous = outputHistory[existing];

      if (!record.payload && previous.payload) {
        record.payload = previous.payload;
      }

      if (!record.analysisResponse && previous.analysisResponse) {
        record.analysisResponse = previous.analysisResponse;
      }

      outputHistory.splice(existing, 1);
    }

    outputHistory.unshift(record);

    if (outputHistory.length > 10) {
      outputHistory.length = 10;
    }

    renderWorkspaceHistory();
    return record;
  }

  async function cacheCompletedReport(payload, analysisResponse) {
    const fingerprint = payloadFingerprint(payload);
    if (fingerprint === pendingReportFingerprint) return;
    pendingReportFingerprint = fingerprint;
    try {
      rememberReport(await buildReport(payload), payload, analysisResponse);
    } catch (_problem) {
      // A failed convenience preload must not change the calculation result.
    } finally {
      if (pendingReportFingerprint === fingerprint) pendingReportFingerprint = null;
    }
  }

  window.fetch = async function taxtreatReportAwareFetch(resource, options = {}) {
    const mutableOptions = { ...options };
    const payload = parseAnalysisPayload(resource, mutableOptions);
    const response = await nativeFetch(resource, mutableOptions);
    if (payload && response.ok) {
      response.clone().json().then((body) => {
        if (!clientQuestionsRemain(body)) {
          lastAnalysisResponse = body;
          cacheCompletedReport(payload, body);
        }
      }).catch(() => {});
    }
    return response;
  };

  const resultActions = document.querySelector('.flow-step[data-step="4"] .flow-actions');
  const openButton = resultActions?.querySelector(".primary");
  renderWorkspaceHistory();
  if (!resultActions || !openButton) return;

  openButton.removeAttribute("data-nav");
  openButton.type = "button";
  openButton.textContent = "Tisk / PDF reportu";
  openButton.dataset.reportAction = "print";

  function showExportProblem(message) {
    let notice = document.querySelector("#report-export-notice");
    if (!notice) {
      notice = document.createElement("div");
      notice.id = "report-export-notice";
      notice.className = "report-export-notice";
      notice.setAttribute("role", "alert");
      notice.setAttribute("aria-live", "assertive");

      const resultActions = document.querySelector(
        '.flow-step[data-step="4"] .flow-actions'
      );

      if (resultActions) resultActions.before(notice);
      else document.body.append(notice);
    }

    notice.textContent = message;
    notice.hidden = false;
    notice.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
    });
  }

  async function exportReport(printAfterLoad, button) {
    if (!lastAnalysisPayload) {
      showExportProblem("Nejprve dokonči výpočet podle zadaných údajů. PDF lze vytvořit až po přiřazení právních pravidel.");
      return;
    }
    const reportWindow = window.open("", "_blank");
    if (!reportWindow) {
      showExportProblem("Prohlížeč zablokoval nové okno. Povol vyskakovací okna pro TaxTreat a zkus export znovu.");
      return;
    }
    const originalLabel = button.textContent;
    button.disabled = true;
    button.textContent = "Připravuji report…";
    reportWindow.document.write(`<!doctype html>
<html lang="cs">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TaxTreat · Příprava reportu</title>
<style>
body{
  margin:0;
  background:#F3F0E8;
  color:#18332D;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
}
main{
  max-width:680px;
  margin:12vh auto;
  padding:36px;
  border:1px solid #DDE3DE;
  border-radius:12px;
  background:#FFFDF8;
}
strong{
  display:block;
  margin-bottom:8px;
  color:#173F39;
  font:600 26px/1.15 Georgia,serif;
}
p{
  margin:0;
  color:#708079;
  line-height:1.55;
}
</style>
</head>
<body>
<main>
<strong>Připravuji report</strong>
<p>TaxTreat vytváří výstup podle dokončeného výpočtu.</p>
</main>
</body>
</html>`);
    try {
      const body = await buildReport(lastAnalysisPayload);
      const record = rememberReport(body, lastAnalysisPayload, lastAnalysisResponse);
      prepareReportWindow(reportWindow, record.html, printAfterLoad);
    } catch (problem) {
      reportWindow.close();
      showExportProblem(problem?.message || "Report se nepodařilo vytvořit.");
    } finally {
      button.disabled = false;
      button.textContent = originalLabel;
    }
  }

  openButton.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopImmediatePropagation();
    exportReport(true, openButton);
  }, true);
})();
