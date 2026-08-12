(() => {
  "use strict";

  const views = [...document.querySelectorAll("[data-view]")];
  const navButtons = [...document.querySelectorAll("[data-nav]")];
  const flowSteps = [...document.querySelectorAll(".flow-step")];
  const progressButtons = [...document.querySelectorAll("[data-flow-step]")];
  const form = document.querySelector("#workspace-payment");
  const recipientForm = document.querySelector("#new-recipient-form");
  const countryNames = { AT: "Rakousko", CH: "Švýcarsko", DE: "Německo", SG: "Singapur", TW: "Tchaj-wan" };
  let recipient = { name: "Demo GmbH", country: "AT", type: "Společnost" };
  let lastPayload = null;

  function showView(name) {
    views.forEach((view) => view.classList.toggle("active", view.dataset.view === name));
    navButtons.forEach((button) => button.classList.toggle("active", button.dataset.nav === name));
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function showStep(number) {
    showView("flow");
    flowSteps.forEach((step) => step.classList.toggle("active", step.dataset.step === String(number)));
    progressButtons.forEach((button) => button.classList.toggle("active", Number(button.dataset.flowStep) <= number));
  }

  navButtons.forEach((button) => button.addEventListener("click", () => showView(button.dataset.nav)));
  document.querySelectorAll("[data-start-flow]").forEach((button) => button.addEventListener("click", () => showStep(1)));
  document.querySelectorAll("[data-open-recipient]").forEach((button) => button.addEventListener("click", () => showView("recipient-detail")));
  document.querySelectorAll("[data-next-step]").forEach((button) => button.addEventListener("click", () => showStep(Number(button.dataset.nextStep))));
  progressButtons.forEach((button) => button.addEventListener("click", () => {
    const step = Number(button.dataset.flowStep);
    if (step < 3 || lastPayload) showStep(step);
  }));
  document.querySelectorAll("[data-create-recipient]").forEach((button) => button.addEventListener("click", () => {
    showStep(1);
    recipientForm.hidden = false;
    recipientForm.querySelector("input").focus();
  }));
  document.querySelector("[data-show-recipient-form]").addEventListener("click", () => {
    recipientForm.hidden = !recipientForm.hidden;
    if (!recipientForm.hidden) recipientForm.querySelector("input").focus();
  });

  function renderRecipient() {
    document.querySelector("#flow-recipient-name").textContent = recipient.name;
    document.querySelector("#flow-recipient-avatar").textContent = recipient.name.slice(0, 1).toUpperCase();
    document.querySelector("#flow-recipient-meta").textContent = `${countryNames[recipient.country]} · ${recipient.type.toLowerCase()} · nový profil`;
    document.querySelectorAll("[data-recipient-name]").forEach((node) => { node.textContent = recipient.name; });
  }

  recipientForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(recipientForm);
    recipient = {
      name: String(data.get("recipient_name")).trim(),
      country: String(data.get("recipient_country")),
      type: String(data.get("recipient_type"))
    };
    renderRecipient();
    recipientForm.hidden = true;
  });

  function money(value) {
    if (value === null || value === undefined || value === "") return "—";
    return new Intl.NumberFormat("cs-CZ", { maximumFractionDigits: 0 }).format(Number(value)) + " Kč";
  }

  function calculationValue(calculation, canonicalName, legacyName) {
    if (!calculation) return null;
    return calculation[canonicalName] ?? calculation[legacyName] ?? null;
  }

  function setText(selector, text) {
    document.querySelector(selector).textContent = text;
  }

  function actionItem(title, detail, kind) {
    const node = document.createElement("div");
    node.className = `action-item ${kind}`;
    const strong = document.createElement("strong");
    strong.textContent = title;
    const small = document.createElement("small");
    small.className = "action-kind";
    small.textContent = detail;
    node.append(strong, small);
    return node;
  }

  function resultExplanation(analysis) {
    if (analysis.status === "FINAL") {
      return `Použitá sazba ${analysis.rate} % byla uzavřena na základě zadaných údajů a evidovaných pravidel. Níže jsou uvedeny podklady výsledku.`;
    }
    if (analysis.candidate_rate !== null && analysis.candidate_rate !== undefined) {
      return `Pravidla identifikovala sazbu ${analysis.candidate_rate} %, její použití však zatím nelze uzavřít. Doplň klientské údaje a podmínky označené k ověření daňovým poradcem.`;
    }
    return "Sazbu zatím nelze uzavřít. Níže jsou uvedeny informace a odborné podmínky, které je třeba doplnit.";
  }

  function citationCard(citation) {
    const card = document.createElement("article");
    card.className = "citation-card";
    const title = document.createElement("strong");
    const isTreaty = String(citation.rule_id || "").includes("CURRENT");
    title.textContent = isTreaty
      ? `Smlouva o zamezení dvojího zdanění · článek ${citation.article || "—"}`
      : `Český zákon o daních z příjmů · § ${citation.article || "—"}`;
    const link = document.createElement("a");
    link.href = citation.source_url;
    link.target = "_blank";
    link.rel = "noreferrer noopener";
    link.textContent = "Otevřít zdroj ↗";
    const detail = document.createElement("p");
    detail.textContent = `Pravidlo ${citation.rule_id} · evidovaný zdroj ${citation.source_id}`;
    card.append(title, link, detail);
    return card;
  }

  function renderResult(payload, response) {
    const analysis = response.analysis;
    const calculation = analysis.withholding_tax_calculation;
    const questions = response.intake?.questions || [];
    const status = document.querySelector("#workspace-result-status");
    status.textContent = analysis.status === "FINAL" ? "VÝPOČET DOKONČEN" : "VYŽADUJE DOPLNĚNÍ";
    status.className = analysis.status === "FINAL" ? "badge" : "badge warning";
    const grossCzk = calculationValue(calculation, "gross_amount_czk", "tax_base_czk");
    const taxCzk = calculationValue(calculation, "withholding_tax_czk", "withholding_tax_czk");
    const netCzk = calculationValue(calculation, "net_amount_czk", "net_amount_czk");
    setText("#workspace-tax", calculation ? money(taxCzk) : "—");
    setText("#workspace-rate", analysis.rate === null
      ? analysis.candidate_rate === null ? "Sazbu nelze uzavřít bez doplnění údajů" : `Sazba k ověření: ${analysis.candidate_rate} %`
      : `${analysis.rate} % z daňového základu`);
    const grossDisplay = grossCzk !== null
      ? money(grossCzk)
      : payload.transaction_amount.currency === "CZK"
        ? money(payload.transaction_amount.amount)
        : `${payload.transaction_amount.amount} ${payload.transaction_amount.currency}`;
    setText("#workspace-gross", grossDisplay);
    setText("#workspace-tax-row", calculation ? money(taxCzk) : "—");
    setText("#workspace-net", calculation ? money(netCzk) : "—");
    setText("#workspace-reason", resultExplanation(analysis));

    const actions = document.querySelector("#workspace-actions");
    actions.replaceChildren();
    questions.forEach((question) => actions.append(actionItem(
      question.prompt,
      question.client_answerable ? "Doplní klient" : "Ověří daňový poradce",
      question.client_answerable ? "client" : "adviser"
    )));
    setText("#workspace-action-count", String(questions.length));
    if (!questions.length) actions.append(actionItem("Bez otevřených položek", "Zadané údaje postačují pro výpočet.", "client"));

    const citations = document.querySelector("#workspace-citations");
    citations.replaceChildren();
    (analysis.citations || []).forEach((citation) => citations.append(citationCard(citation)));
    if (!citations.children.length) {
      const p = document.createElement("p");
      p.textContent = `Právní dataset: ${analysis.dataset_version || "neuveden"}`;
      citations.append(p);
    }
    showStep(3);
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const error = document.querySelector("#workspace-error");
    error.hidden = true;
    const payload = {
      source_country: "CZ",
      recipient_country: recipient.country,
      income_type: String(data.get("income_type")),
      transaction_date: String(data.get("transaction_date")),
      facts: {
        beneficial_owner: true,
        recipient_is_treaty_resident: true,
        recipient_entity_type: recipient.type === "Fyzická osoba" ? "individual"
          : recipient.type === "Fond" ? "fund"
          : recipient.type === "Společnost" ? "company" : "other",
        permanent_establishment_connection: !data.get("no_pe_connection")
      },
      determinations: {},
      transaction_amount: {
        amount: String(data.get("amount")),
        currency: String(data.get("currency"))
      }
    };
    try {
      const response = await fetch("/analysis/intake", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail?.code || "Výpočet se nepodařilo dokončit.");
      lastPayload = payload;
      renderResult(payload, body);
    } catch (problem) {
      error.textContent = problem.message;
      error.hidden = false;
    }
  });
})();
