(() => {
  "use strict";

  const views = [...document.querySelectorAll("[data-view]")];
  const navButtons = [...document.querySelectorAll("[data-nav]")];
  const flowSteps = [...document.querySelectorAll(".flow-step")];
  const progressButtons = [...document.querySelectorAll("[data-flow-step]")];
  const form = document.querySelector("#workspace-payment");
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

  function actionItem(title, detail) {
    const node = document.createElement("div");
    node.className = "action-item";
    const strong = document.createElement("strong");
    strong.textContent = title;
    const small = document.createElement("small");
    small.textContent = detail;
    node.append(strong, small);
    return node;
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
    setText("#workspace-rate", analysis.rate === null ? "Sazbu nelze uzavřít bez doplnění údajů" : `${analysis.rate} % z daňového základu`);
    setText("#workspace-gross", calculation ? money(grossCzk) : `${payload.transaction_amount.amount} ${payload.transaction_amount.currency}`);
    setText("#workspace-tax-row", calculation ? money(taxCzk) : "—");
    setText("#workspace-net", calculation ? money(netCzk) : "—");
    setText("#workspace-reason", analysis.explanation || "Výsledek vychází z uvedených skutečností a evidovaných právních pravidel.");

    const actions = document.querySelector("#workspace-actions");
    actions.replaceChildren();
    questions.forEach((question) => actions.append(actionItem(question.prompt, question.client_answerable ? "Doplní klient" : "Ověří daňový poradce")));
    setText("#workspace-action-count", String(questions.length));
    if (!questions.length) actions.append(actionItem("Bez otevřených položek", "Zadané údaje postačují pro výpočet."));

    const citations = document.querySelector("#workspace-citations");
    citations.replaceChildren();
    (analysis.citations || []).forEach((citation) => {
      const p = document.createElement("p");
      p.textContent = typeof citation === "string" ? citation : JSON.stringify(citation);
      citations.append(p);
    });
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
      recipient_country: "AT",
      income_type: String(data.get("income_type")),
      transaction_date: String(data.get("transaction_date")),
      facts: {
        beneficial_owner: true,
        recipient_is_treaty_resident: true,
        recipient_entity_type: "company",
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
