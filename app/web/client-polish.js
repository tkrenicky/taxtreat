(() => {
  "use strict";

  const originalFetch = window.fetch.bind(window);
  let latestPayload = null;
  let renderToken = 0;

  const escapeHtml = (value) => String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

  function readPartyNames() {
    return {
      payer: String(document.querySelector('[name="report_payer_name"]')?.value || "").trim(),
      recipient: String(document.querySelector('[name="report_recipient_name"]')?.value || "").trim(),
    };
  }

  function enrichPayload(payload) {
    const next = structuredClone(payload || {});
    next.facts = next.facts || {};
    const names = readPartyNames();
    if (names.payer) next.facts.report_payer_name = names.payer;
    if (names.recipient) next.facts.report_recipient_name = names.recipient;
    return next;
  }

  function formatNumber(value, maximumFractionDigits = 2) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return "—";
    return new Intl.NumberFormat("cs-CZ", { maximumFractionDigits }).format(numeric);
  }

  function formatRate(value) {
    return value === null || value === undefined || value === "" ? "—" : `${formatNumber(value)} %`;
  }

  function formatDate(value) {
    if (!value) return "—";
    const parsed = new Date(`${String(value).slice(0, 10)}T00:00:00`);
    if (Number.isNaN(parsed.valueOf())) return String(value);
    return new Intl.DateTimeFormat("cs-CZ", { day: "numeric", month: "numeric", year: "numeric" }).format(parsed);
  }

  function incomeLabel(value) {
    return {
      dividend: "Dividendy",
      interest: "Úroky",
      royalty: "Licenční poplatky",
    }[value] || value || "—";
  }

  function sourceLabel(source) {
    if (!source) return "Právní zdroj není v tomto výstupu k dispozici";
    const article = source.article ? String(source.article) : "—";
    const paragraph = source.paragraph ? ` odst. ${String(source.paragraph).replace(/^odst\.\s*/i, "")}` : "";
    if (["treaty", "protocol", "mli"].includes(source.legal_layer)) {
      const layer = source.legal_layer === "protocol" ? "Protokol" : source.legal_layer === "mli" ? "MLI" : "Smlouva o zamezení dvojího zdanění";
      return `${layer} · čl. ${article}${paragraph}`;
    }
    return `Zákon č. 586/1992 Sb., o daních z příjmů · § ${article}${paragraph}`;
  }

  function selectedSource(report) {
    const result = report?.result || {};
    const selectedRuleId = result.selected_rule_id || result.candidate_rule_id;
    const sources = Array.isArray(report?.official_sources) ? report.official_sources : [];
    return sources.find((source) => source.rule_id === selectedRuleId)
      || sources.find((source) => ["treaty", "protocol", "mli"].includes(source.legal_layer))
      || sources[0]
      || null;
  }

  function domesticSource(report) {
    return (report?.official_sources || []).find((source) => source.legal_layer === "domestic") || null;
  }

  function treatySource(report) {
    return (report?.official_sources || []).find((source) => ["treaty", "protocol"].includes(source.legal_layer)) || null;
  }

  function outcomeCopy(analysis) {
    const treatment = analysis?.tax_treatment;
    if (analysis?.status !== "FINAL") return { value: "Je třeba doplnit údaje", mode: "incomplete" };
    if (treatment === "exclusive_foreign_taxation") return { value: "Neuplatňuje se", mode: "final" };
    if (treatment === "domestic_exemption") return { value: "0 %", mode: "final" };
    if (analysis?.rate !== null && analysis?.rate !== undefined) return { value: formatRate(analysis.rate), mode: "final" };
    return { value: "—", mode: "incomplete" };
  }

  function informationalSentence(analysis) {
    if (analysis?.status !== "FINAL") {
      return "Zadané údaje zatím neumožňují zobrazit uzavřený režim nebo sazbu. Doplňte údaje uvedené níže; TaxTreat poté výstup přepočítá.";
    }
    if (analysis?.tax_treatment === "exclusive_foreign_taxation") {
      return "TaxTreat při zadaných údajích a uvedených předpokladech zobrazuje režim, při kterém ve výpočtu nevzniká česká srážková daň. Jde o informační výstup založený na níže uvedeném právním zdroji, nikoli o doporučení k postupu.";
    }
    if (analysis?.tax_treatment === "domestic_exemption") {
      return "TaxTreat při zadaných údajích a uvedených předpokladech zobrazuje režim osvobození. Jde o informační výstup založený na níže uvedeném právním zdroji, nikoli o doporučení k postupu.";
    }
    return `TaxTreat pro zadané údaje zobrazuje sazbu ${formatRate(analysis?.rate)}. Výstup vychází z údajů zadaných uživatelem a z níže uvedených právních zdrojů; nepředstavuje individuální daňové posouzení ani doporučení.`;
  }

  function transactionContext(report) {
    const scope = report?.scope || {};
    const facts = report?.assumptions?.transaction_facts || {};
    const payer = facts.report_payer_name || "Český plátce";
    const recipient = facts.report_recipient_name || scope.recipient_country || "Příjemce";
    return `${payer} → ${recipient} · ${incomeLabel(scope.income_type)}`;
  }

  function renderFacts(report) {
    const scope = report?.scope || {};
    const facts = report?.assumptions?.transaction_facts || {};
    const amount = scope.transaction_amount || {};
    const rows = [
      ["Plátce", facts.report_payer_name || "Název neuveden"],
      ["Příjemce", facts.report_recipient_name || "Název neuveden"],
      ["Rezidence příjemce", scope.recipient_country || "—"],
      ["Druh příjmu", incomeLabel(scope.income_type)],
      ["Datum transakce", formatDate(scope.transaction_date)],
      ["Hrubá částka", amount.amount ? `${formatNumber(amount.amount)} ${amount.currency || ""}`.trim() : "Neuvedena"],
    ];
    document.querySelector("#transaction-facts").innerHTML = rows.map(([label, value]) => `
      <div class="fact-row"><span>${escapeHtml(label)}</span><b>${escapeHtml(value)}</b></div>
    `).join("");
  }

  function renderAssumptions(report) {
    const facts = report?.assumptions?.transaction_facts || {};
    const items = [];
    if (facts.beneficial_owner !== undefined) items.push(["Skutečný vlastník příjmu", facts.beneficial_owner ? "Ano" : "Ne"]);
    if (facts.recipient_is_treaty_resident !== undefined) items.push(["Daňová rezidence pro účely smlouvy", facts.recipient_is_treaty_resident ? "Ano" : "Ne"]);
    if (facts.permanent_establishment_connection !== undefined) items.push(["Vazba ke stálé provozovně v ČR", facts.permanent_establishment_connection ? "Ano" : "Ne"]);
    if (facts.ownership_percent !== undefined) items.push(["Podíl na základním kapitálu", `${formatNumber(facts.ownership_percent)} %`]);
    if (facts.direct_or_indirect_voting_ownership !== undefined) items.push(["Podíl na hlasovacích právech", `${formatNumber(facts.direct_or_indirect_voting_ownership)} %`]);
    if (facts.holding_period_months !== undefined) items.push(["Doba držby podílu", `${formatNumber(facts.holding_period_months)} měsíců`]);
    document.querySelector("#assumption-items").innerHTML = items.map(([label, value]) => `
      <div class="fact-row"><span>${escapeHtml(label)}</span><b>${escapeHtml(value)}</b></div>
    `).join("");
  }

  function renderCalculation(report, analysis) {
    const calculation = report?.result?.withholding_tax_calculation || analysis?.withholding_tax_calculation;
    const root = document.querySelector("#calculation-summary");
    if (!calculation || calculation.status !== "CALCULATED") {
      root.innerHTML = '<p class="quiet-copy">Částkový výpočet není pro aktuální stav k dispozici.</p>';
      return;
    }
    const treatment = analysis?.tax_treatment;
    const appliedRate = ["exclusive_foreign_taxation", "domestic_exemption"].includes(treatment) ? "Neuplatňuje se" : formatRate(analysis?.rate);
    const rows = [
      ["Hrubá částka", `${formatNumber(calculation.gross_amount)} ${calculation.transaction_currency || ""}`.trim()],
      ["Daňový základ", `${formatNumber(calculation.gross_amount_czk)} Kč`],
      ["Česká daň k odvodu", `${formatNumber(calculation.withholding_tax_czk)} Kč`],
      ["Zobrazená sazba / režim", appliedRate],
      ["Čistá částka", `${formatNumber(calculation.net_amount_czk)} Kč`],
    ];
    root.innerHTML = rows.map(([label, value], index) => `
      <div class="calculation-row${index === 2 ? " emphasis" : ""}"><span>${escapeHtml(label)}</span><b>${escapeHtml(value)}</b></div>
    `).join("");
  }

  function renderLegalBasis(report) {
    const source = selectedSource(report);
    const root = document.querySelector("#legal-basis-content");
    if (!source) {
      root.innerHTML = '<p class="quiet-copy">Pro tento výstup není k dispozici samostatně zobrazený právní zdroj.</p>';
      return;
    }
    const excerpt = String(source.excerpt || "").trim();
    const shortExcerpt = excerpt.length > 620 ? `${excerpt.slice(0, 620).replace(/\s+\S*$/, "")} …` : excerpt;
    const link = source.source_url
      ? `<a class="source-link" href="${escapeHtml(source.source_url)}" target="_blank" rel="noopener">Otevřít oficiální zdroj ↗</a>`
      : "";
    root.innerHTML = `
      <div class="legal-reference">${escapeHtml(sourceLabel(source))}</div>
      ${shortExcerpt ? `<blockquote>${escapeHtml(shortExcerpt)}</blockquote>` : '<p class="quiet-copy">Samostatný výňatek není v datech tohoto zdroje uložen.</p>'}
      ${link}
    `;
  }

  function renderDeadlines(report) {
    const schedule = report?.result?.withholding_compliance_schedule || {};
    const cards = [];
    if (schedule.remittance_deadline) cards.push(["Odvod srážkové daně", formatDate(schedule.remittance_deadline), "Lhůta vypočtená TaxTreat z data transakce a zobrazeného režimu."]);
    if (schedule.notification_deadline) cards.push(["Oznámení podle § 38da ZDP", formatDate(schedule.notification_deadline), "Informačně zobrazená lhůta; připadne-li konec lhůty na nepracovní den, TaxTreat zohledňuje posun podle evidovaného pravidla."]);
    document.querySelector("#deadline-items").innerHTML = cards.length
      ? cards.map(([label, date, note]) => `<article class="deadline-card"><span>${escapeHtml(label)}</span><b>${escapeHtml(date)}</b><p>${escapeHtml(note)}</p></article>`).join("")
      : '<p class="quiet-copy">Pro aktuální výstup není zobrazen samostatný termín.</p>';
  }

  function renderDocumentation(report) {
    const items = Array.isArray(report?.required_documentation) ? report.required_documentation : [];
    document.querySelector("#documentation-items").innerHTML = items.length
      ? items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")
      : '<li>Pro tento výstup není uveden samostatný seznam podkladů.</li>';
  }

  function renderRateComparison(report, analysis) {
    const domestic = domesticSource(report);
    const treaty = treatySource(report);
    const selected = selectedSource(report);
    const treatment = analysis?.tax_treatment;
    const selectedDisplay = ["exclusive_foreign_taxation", "domestic_exemption"].includes(treatment)
      ? (treatment === "domestic_exemption" ? "Osvobození" : "Neuplatňuje se")
      : formatRate(analysis?.rate);
    const rows = [];
    if (domestic) rows.push(["Vnitrostátní pravidlo", domestic.rate !== null && domestic.rate !== undefined ? formatRate(domestic.rate) : "—"]);
    if (treaty) rows.push(["Smluvní pravidlo", treaty.rate !== null && treaty.rate !== undefined ? formatRate(treaty.rate) : (treaty === selected ? selectedDisplay : "—")]);
    rows.push(["Zobrazený výsledek", selectedDisplay]);
    document.querySelector("#result-comparison").innerHTML = rows.map(([label, value]) => `
      <div><span>${escapeHtml(label)}</span><b>${escapeHtml(value)}</b></div>
    `).join("");
  }

  async function renderClientResult(payload, intakeResponse) {
    const token = ++renderToken;
    try {
      const reportResponse = await originalFetch("/analysis/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!reportResponse.ok) return;
      const reportBody = await reportResponse.json();
      if (token !== renderToken) return;
      const report = reportBody.report;
      const analysis = intakeResponse.analysis || {};
      const outcome = outcomeCopy(analysis);
      const result = document.querySelector("#result");
      if (!result) return;

      result.dataset.clientState = outcome.mode;
      document.querySelector("#transaction-context").textContent = transactionContext(report);
      document.querySelector("#hero-outcome").textContent = outcome.value;
      document.querySelector("#hero-explanation").textContent = informationalSentence(analysis);
      renderRateComparison(report, analysis);
      renderFacts(report);
      renderAssumptions(report);
      renderCalculation(report, analysis);
      renderLegalBasis(report);
      renderDeadlines(report);
      renderDocumentation(report);

      document.querySelector("#client-result-layout").hidden = false;
      document.querySelector("#legacy-result-header").hidden = outcome.mode === "final";
      const legacyCalc = document.querySelector("#calculation-card");
      if (legacyCalc) legacyCalc.hidden = true;

      const docsPanel = document.querySelector(".documents-panel");
      const docCount = Number(document.querySelector("#document-count")?.textContent || "0");
      if (docsPanel) docsPanel.hidden = docCount === 0;
    } catch (_) {
      // The canonical intake result remains available even if the supplementary
      // report presentation cannot be loaded.
    }
  }

  window.fetch = async (input, init = {}) => {
    const url = typeof input === "string" ? input : input?.url || "";
    let nextInit = init;
    let payload = null;

    if ((url.includes("/analysis/intake") || url.includes("/analysis/report")) && typeof init?.body === "string") {
      try {
        payload = enrichPayload(JSON.parse(init.body));
        nextInit = { ...init, body: JSON.stringify(payload) };
        latestPayload = payload;
      } catch (_) {
        payload = null;
      }
    }

    const response = await originalFetch(input, nextInit);

    if (url.includes("/analysis/intake") && payload && response.ok) {
      response.clone().json().then((body) => {
        window.setTimeout(() => renderClientResult(payload, body), 0);
      }).catch(() => {});
    }

    return response;
  };

  document.addEventListener("DOMContentLoaded", () => {
    const reportButton = document.querySelector("#report-button");
    if (reportButton) reportButton.textContent = "Zobrazit klientský report";

    const observer = new MutationObserver(() => {
      const empty = document.querySelector("#empty-state");
      const result = document.querySelector("#result");
      if (empty?.hasAttribute("hidden")) empty.style.display = "none";
      if (result && !result.hasAttribute("hidden") && latestPayload) {
        const docsPanel = document.querySelector(".documents-panel");
        const docCount = Number(document.querySelector("#document-count")?.textContent || "0");
        if (docsPanel) docsPanel.hidden = docCount === 0;
      }
    });
    observer.observe(document.body, { subtree: true, attributes: true, attributeFilter: ["hidden"], childList: true });
  });
})();