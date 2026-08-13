(() => {
  "use strict";

  const views = [...document.querySelectorAll("[data-view]")];
  const navButtons = [...document.querySelectorAll("[data-nav]")];
  const flowSteps = [...document.querySelectorAll(".flow-step")];
  const progressButtons = [...document.querySelectorAll("[data-flow-step]")];
  const form = document.querySelector("#workspace-payment");
  const recipientForm = document.querySelector("#new-recipient-form");
  const followUp = document.querySelector("#workspace-follow-up");
  const questionsRoot = document.querySelector("#workspace-questions");
  const payerDialog = document.querySelector("#payer-dialog");
  const payerForm = document.querySelector("#payer-form");
  const residenceForm = document.querySelector("#residency-document-form");
  const countryNames = { AT: "Rakousko", CH: "Švýcarsko", DE: "Německo", SG: "Singapur", TW: "Tchaj-wan" };
  const countryGenitives = { AT: "Rakouska", CH: "Švýcarska", DE: "Německa", SG: "Singapuru", TW: "Tchaj-wanu" };
  let recipient = { name: "Demo GmbH", country: "AT", type: "Společnost" };
  let payer = { name: "Demo CZ s.r.o.", id: "" };
  let lastPayload = null;
  let pendingQuestions = [];

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

  document.querySelectorAll("[data-tooltip]").forEach((button) => button.addEventListener("click", () => {
    const panel = document.getElementById(button.dataset.tooltip);
    const willOpen = panel.hidden;
    document.querySelectorAll(".tooltip-panel").forEach((item) => { item.hidden = true; });
    panel.hidden = !willOpen;
    button.setAttribute("aria-expanded", String(willOpen));
  }));

  document.querySelectorAll("[data-edit-payer]").forEach((button) => button.addEventListener("click", () => {
    payerForm.elements.payer_name.value = payer.name;
    payerForm.elements.payer_id.value = payer.id;
    payerDialog.showModal();
  }));
  document.querySelectorAll("[data-close-payer]").forEach((button) => button.addEventListener("click", () => payerDialog.close()));
  payerForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(payerForm);
    payer = { name: String(data.get("payer_name")).trim(), id: String(data.get("payer_id")).trim() };
    document.querySelectorAll("[data-payer-name]").forEach((node) => { node.textContent = payer.name; });
    document.querySelectorAll("[data-payer-avatar]").forEach((node) => { node.textContent = payer.name.slice(0, 1).toUpperCase(); });
    payerDialog.close();
  });

  document.querySelector("[data-residency-document]").addEventListener("click", () => {
    residenceForm.hidden = false;
    residenceForm.querySelector("input").focus();
  });
  document.querySelector("[data-close-residency]").addEventListener("click", () => { residenceForm.hidden = true; });
  residenceForm.addEventListener("submit", (event) => {
    event.preventDefault();
    document.querySelector("[data-residency-document]").textContent = "✓ Potvrzení je evidováno v profilu";
    residenceForm.hidden = true;
  });

  function renderRecipient() {
    document.querySelector("#flow-recipient-name").textContent = recipient.name;
    document.querySelector("#flow-recipient-avatar").textContent = recipient.name.slice(0, 1).toUpperCase();
    document.querySelector("#flow-recipient-meta").textContent = `${countryNames[recipient.country]} · ${recipient.type.toLowerCase()} · nový profil`;
    document.querySelectorAll("[data-recipient-name]").forEach((node) => { node.textContent = recipient.name; });
    document.querySelectorAll("[data-recipient-country]").forEach((node) => { node.textContent = countryGenitives[recipient.country]; });
  }

  recipientForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(recipientForm);
    recipient = { name: String(data.get("recipient_name")).trim(), country: String(data.get("recipient_country")), type: String(data.get("recipient_type")) };
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

  function setText(selector, value) { document.querySelector(selector).textContent = value; }

  function completeMonths(acquisitionDate, transactionDate) {
    const start = new Date(`${acquisitionDate}T00:00:00Z`);
    const end = new Date(`${transactionDate}T00:00:00Z`);
    let months = (end.getUTCFullYear() - start.getUTCFullYear()) * 12 + end.getUTCMonth() - start.getUTCMonth();
    if (end.getUTCDate() < start.getUTCDate()) months -= 1;
    return Math.max(0, months);
  }

  function updatePeQuestion() {
    const wording = {
      dividend: "Váže se účast, pro kterou jsou dividendy vypláceny, skutečně ke stálé provozovně příjemce v České republice?",
      interest: "Váže se pohledávka, ze které jsou úroky placeny, skutečně ke stálé provozovně příjemce v České republice?",
      royalty: "Váže se právo nebo majetek, za které jsou licenční poplatky placeny, skutečně ke stálé provozovně příjemce v České republice?"
    };
    setText("#pe-question-text", wording[form.elements.income_type.value] || "Váže se příjem skutečně ke stálé provozovně příjemce v České republice?");
  }
  form.elements.income_type.addEventListener("change", updatePeQuestion);

  function createQuestion(question) {
    const field = document.createElement("article");
    field.className = "question-card";
    const copy = document.createElement("div");
    const title = document.createElement("strong"); title.textContent = question.prompt;
    const why = document.createElement("p"); why.textContent = question.why;
    copy.append(title, why);
    const inputPath = question.input_path;
    let input;
    if (question.response_type === "boolean") {
      input = document.createElement("select");
      [["", "Vyber odpověď"], ["true", "Ano"], ["false", "Ne"]].forEach(([value, label]) => {
        const option = document.createElement("option"); option.value = value; option.textContent = label; input.append(option);
      });
    } else if (question.response_type === "choice") {
      input = document.createElement("select");
      [["", "Vyber možnost"], ...(question.options || [])].forEach(([value, label]) => {
        const option = document.createElement("option"); option.value = value; option.textContent = label; input.append(option);
      });
    } else if (question.response_type === "structured_cnb_rate") {
      const wrapper = document.createElement("div");
      wrapper.className = "structured-answer";
      [["czk_per_unit", "Kurz ČNB (CZK za jednotku měny)", "number"], ["source_url", "Odkaz na kurzovní lístek ČNB", "url"]].forEach(([name, placeholder, type]) => {
        const child = document.createElement("input"); child.name = name; child.type = type; child.required = true; child.placeholder = placeholder;
        if (type === "number") { child.min = "0.000001"; child.step = "0.000001"; }
        wrapper.append(child);
      });
      wrapper.dataset.inputPath = inputPath;
      field.append(copy, wrapper);
      return field;
    } else {
      input = document.createElement("input");
      input.type = question.response_type === "date" ? "date" : "number";
      if (question.response_type === "decimal_percent") { input.min = "0"; input.max = "100"; input.step = "0.01"; input.placeholder = "např. 25"; }
    }
    input.required = true;
    input.dataset.inputPath = inputPath;
    input.dataset.responseType = question.response_type;
    field.append(copy, input);
    return field;
  }

  function renderClientQuestions(questions) {
    pendingQuestions = questions.filter((question) => question.client_answerable);
    questionsRoot.replaceChildren();
    pendingQuestions.forEach((question) => questionsRoot.append(createQuestion(question)));
    followUp.hidden = pendingQuestions.length === 0;
    setText("#workspace-question-count", `${pendingQuestions.length} ${pendingQuestions.length === 1 ? "údaj" : "údaje"}`);
    setText("#workspace-submit", pendingQuestions.length ? "Doplnit údaje a dokončit kontrolu →" : "Vyhodnotit vstupní údaje →");
    if (pendingQuestions.length) followUp.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function applyAnswers(payload) {
    questionsRoot.querySelectorAll("[data-input-path]").forEach((input) => {
      const path = input.dataset.inputPath;
      if (input.classList.contains("structured-answer")) {
        const rateDate = [payload.transaction_amount.payment_date, payload.transaction_amount.accounting_date].sort()[0];
        payload.transaction_amount.exchange_rate = { source: "CNB", currency: payload.transaction_amount.currency, czk_per_unit: input.querySelector('[name="czk_per_unit"]').value, effective_date: rateDate, source_url: input.querySelector('[name="source_url"]').value };
      } else if (path === "derived.acquisition_date") {
        payload.facts.holding_period_months = completeMonths(input.value, payload.transaction_date);
      } else if (path && path.startsWith("facts.")) {
        const name = path.slice(6);
        payload.facts[name] = input.dataset.responseType === "boolean" ? input.value === "true" : input.dataset.responseType === "decimal_percent" ? Number(input.value) : input.value;
      }
    });
  }

  function professionalTitle(question) {
    return { recipient_eligibility: "Podmínky případného osvobození", future_holding_period: "Dodatečné splnění doby držby", domestic_exemption: "Podmínky vnitrostátního osvobození" }[question.advisor_topic] || "Podmínka vyžadující odborné posouzení";
  }

  function actionItem(question) {
    const node = document.createElement("div"); node.className = "action-item adviser";
    const strong = document.createElement("strong"); strong.textContent = professionalTitle(question);
    const detail = document.createElement("small"); detail.textContent = "V dostupných údajích nebyly uzavřeny všechny právní podmínky. Výsledek je proto označen k odbornému posouzení.";
    node.append(strong, detail);
    return node;
  }

  function resultExplanation(analysis) {
    if (analysis.status === "FINAL") return `Použitá sazba ${analysis.rate} % byla určena na základě zadaných údajů a evidovaných pravidel. Níže jsou uvedeny podklady výsledku.`;
    if (analysis.candidate_rate !== null && analysis.candidate_rate !== undefined) return `Byla identifikována sazba ${analysis.candidate_rate} %. Její použití závisí na odborném ověření právních podmínek uvedených níže.`;
    return "Sazbu zatím nelze určit. Ve výsledku jsou uvedeny podmínky, které vyžadují odborné posouzení.";
  }

  function citationCard(citation) {
    const card = document.createElement("article"); card.className = "citation-card";
    const title = document.createElement("strong");
    const isTreaty = String(citation.rule_id || "").includes("CURRENT");
    title.textContent = isTreaty ? `Smlouva o zamezení dvojího zdanění · článek ${citation.article || "—"}` : `Český zákon o daních z příjmů · § ${citation.article || "—"}`;
    const link = document.createElement("a"); link.href = citation.source_url; link.target = "_blank"; link.rel = "noreferrer noopener"; link.textContent = "Otevřít zdroj ↗";
    const detail = document.createElement("p"); detail.textContent = `Pravidlo ${citation.rule_id} · evidovaný zdroj ${citation.source_id}`;
    card.append(title, link, detail);
    return card;
  }

  function renderResult(payload, response) {
    const analysis = response.analysis;
    const calculation = analysis.withholding_tax_calculation;
    const professional = (response.intake?.questions || []).filter((question) => !question.client_answerable);
    const status = document.querySelector("#workspace-result-status");
    status.textContent = analysis.status === "FINAL" ? "VÝPOČET DOKONČEN" : "ODBORNÉ OVĚŘENÍ";
    status.className = analysis.status === "FINAL" ? "badge" : "badge warning";
    const grossCzk = calculationValue(calculation, "gross_amount_czk", "tax_base_czk");
    const taxCzk = calculationValue(calculation, "withholding_tax_czk", "withholding_tax_czk");
    const netCzk = calculationValue(calculation, "net_amount_czk", "net_amount_czk");
    setText("#workspace-tax", calculation ? money(taxCzk) : "—");
    setText("#workspace-rate", analysis.rate === null ? analysis.candidate_rate === null ? "Sazbu nelze určit bez odborného posouzení" : `Identifikovaná sazba: ${analysis.candidate_rate} %` : `${analysis.rate} % z daňového základu`);
    setText("#workspace-gross", grossCzk !== null ? money(grossCzk) : payload.transaction_amount.currency === "CZK" ? money(payload.transaction_amount.amount) : `${payload.transaction_amount.amount} ${payload.transaction_amount.currency}`);
    setText("#workspace-tax-row", calculation ? money(taxCzk) : "—");
    setText("#workspace-net", calculation ? money(netCzk) : "—");
    setText("#workspace-reason", resultExplanation(analysis));
    const actions = document.querySelector("#workspace-actions"); actions.replaceChildren();
    professional.forEach((question) => actions.append(actionItem(question)));
    setText("#workspace-action-count", String(professional.length));
    if (!professional.length) {
      const item = document.createElement("div"); item.className = "action-item complete";
      const strong = document.createElement("strong"); strong.textContent = "Bez otevřených odborných položek";
      const small = document.createElement("small"); small.textContent = "Zadané údaje postačují pro dokončení výpočtu.";
      item.append(strong, small); actions.append(item);
    }
    const citations = document.querySelector("#workspace-citations"); citations.replaceChildren();
    (analysis.citations || []).forEach((citation) => citations.append(citationCard(citation)));
    if (!citations.children.length) { const p = document.createElement("p"); p.textContent = `Právní dataset: ${analysis.dataset_version || "neuveden"}`; citations.append(p); }
    showStep(3);
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const error = document.querySelector("#workspace-error"); error.hidden = true;
    const paymentDate = String(data.get("payment_date"));
    const accountingDate = String(data.get("accounting_date"));
    const transactionDate = [paymentDate, accountingDate].sort()[0];
    const peConnection = String(data.get("pe_connection"));
    const facts = { beneficial_owner: true, recipient_is_treaty_resident: true, recipient_entity_type: recipient.type === "Fyzická osoba" ? "individual" : recipient.type === "Fond" ? "fund" : recipient.type === "Společnost" ? "company" : "other" };
    if (peConnection !== "unknown") facts.permanent_establishment_connection = peConnection === "true";
    const payload = {
      source_country: "CZ", recipient_country: recipient.country, income_type: String(data.get("income_type")), transaction_date: transactionDate,
      facts, determinations: {}, transaction_amount: { amount: String(data.get("amount")), currency: String(data.get("currency")), payment_date: paymentDate, accounting_date: accountingDate }
    };
    if (pendingQuestions.length) applyAnswers(payload);
    try {
      const response = await fetch("/analysis/intake", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail?.code || "Výpočet se nepodařilo dokončit.");
      const clientQuestions = (body.intake?.questions || []).filter((question) => question.client_answerable);
      lastPayload = payload;
      if (clientQuestions.length) renderClientQuestions(clientQuestions);
      else { renderClientQuestions([]); renderResult(payload, body); }
    } catch (problem) { error.textContent = problem.message; error.hidden = false; }
  });
})();
