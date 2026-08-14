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
  const recipientDialog = document.querySelector("#recipient-dialog");
  const recipientEditForm = document.querySelector("#recipient-edit-form");
  const residenceForm = document.querySelector("#residency-document-form");
  const transactionFacts = document.querySelector("#transaction-facts");
  const dividendFacts = document.querySelector("#dividend-facts");
  const interestFacts = document.querySelector("#interest-facts");
  const royaltyFacts = document.querySelector("#royalty-facts");
  const dividendSteps = [...document.querySelectorAll("[data-dividend-step]")];
  const acquisitionDateField = document.querySelector("[data-acquisition-date]");
  let votingWasEdited = false;
  const countryNames = { AT: "Rakousko", CH: "Švýcarsko", DE: "Německo", SG: "Singapur", TW: "Tchaj-wan" };
  const countryGenitives = { AT: "Rakouska", CH: "Švýcarska", DE: "Německa", SG: "Singapuru", TW: "Tchaj-wanu" };
  let recipient = {
    name: "Demo GmbH",
    country: "AT",
    type: "Společnost",
    beneficialOwner: true,
    treatyResident: true,
    peConnection: false,
    ownershipPercent: "",
    directOwnership: "",
    acquisitionDate: "",
    votingOwnershipPercent: ""
  };
  let payer = { name: "Demo CZ s.r.o.", id: "" };
  let lastPayload = null;
  let pendingQuestions = [];
  const clientAnswers = { facts: {}, acquisitionDate: null, exchangeRate: null };

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

  document.querySelectorAll("[data-edit-recipient]").forEach((button) => button.addEventListener("click", (event) => {
    event.stopPropagation();
    recipientEditForm.elements.recipient_name.value = recipient.name;
    recipientEditForm.elements.recipient_country.value = recipient.country;
    recipientEditForm.elements.recipient_type.value = recipient.type;
    recipientEditForm.elements.ownership_percent.value = recipient.ownershipPercent;
    recipientEditForm.elements.acquisition_date.value = recipient.acquisitionDate;
    recipientEditForm.elements.direct_ownership.value = recipient.directOwnership;
    recipientEditForm.elements.beneficial_owner.value = String(recipient.beneficialOwner);
    recipientEditForm.elements.treaty_resident.value = String(recipient.treatyResident);
    recipientEditForm.elements.pe_connection.value = String(recipient.peConnection);
    recipientDialog.showModal();
  }));
  document.querySelectorAll("[data-close-recipient]").forEach((button) => button.addEventListener("click", () => recipientDialog.close()));
  recipientEditForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(recipientEditForm);
    recipient = {
      ...recipient,
      name: String(data.get("recipient_name")).trim(),
      country: String(data.get("recipient_country")),
      type: String(data.get("recipient_type")),
      ownershipPercent: String(data.get("ownership_percent")),
      acquisitionDate: String(data.get("acquisition_date")),
      directOwnership: String(data.get("direct_ownership")),
      beneficialOwner: String(data.get("beneficial_owner")) === "true",
      treatyResident: String(data.get("treaty_resident")) === "true",
      peConnection: String(data.get("pe_connection")) === "true"
    };
    renderRecipient();
    recipientDialog.close();
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
    const country = countryNames[recipient.country];
    const initial = recipient.name.slice(0, 1).toUpperCase();
    document.querySelector("#flow-recipient-name").textContent = recipient.name;
    document.querySelector("#flow-recipient-avatar").textContent = initial;
    document.querySelector("#flow-recipient-meta").textContent = `${country} · ${recipient.type.toLowerCase()} · základní údaje vyplněny`;
    document.querySelectorAll("[data-recipient-name]").forEach((node) => { node.textContent = recipient.name; });
    document.querySelectorAll("[data-recipient-avatar]").forEach((node) => { node.textContent = initial; });
    document.querySelectorAll("[data-recipient-country]").forEach((node) => { node.textContent = countryGenitives[recipient.country]; });
    document.querySelectorAll("[data-recipient-country-name]").forEach((node) => { node.textContent = country; });
    document.querySelectorAll("[data-recipient-type]").forEach((node) => { node.textContent = recipient.type.toLowerCase(); });
    document.querySelectorAll("[data-profile-beneficial]").forEach((node) => { node.textContent = recipient.beneficialOwner ? "Ano" : "Ne"; });
    document.querySelectorAll("[data-profile-pe]").forEach((node) => { node.textContent = recipient.peConnection ? "Ano" : "Ne"; });
    document.querySelectorAll("[data-profile-ownership]").forEach((node) => { node.textContent = recipient.ownershipPercent ? `${recipient.ownershipPercent} %` : "Nevyplněno"; });
    document.querySelectorAll("[data-profile-acquisition]").forEach((node) => { node.textContent = recipient.acquisitionDate || "Nevyplněno"; });
    form.elements.beneficial_owner.value = String(recipient.beneficialOwner);
    form.elements.treaty_resident.value = String(recipient.treatyResident);
    form.elements.pe_connection.value = String(recipient.peConnection);
    form.elements.ownership_percent.value = recipient.ownershipPercent;
    form.elements.direct_ownership.value = recipient.directOwnership;
    form.elements.acquisition_date.value = recipient.acquisitionDate;
    form.elements.holding_period_mode.value = recipient.acquisitionDate ? "known_date" : "";
    form.elements.voting_ownership_percent.value = recipient.votingOwnershipPercent || recipient.ownershipPercent;
    votingWasEdited = Boolean(recipient.votingOwnershipPercent);
    updateDividendProgress();
  }

  recipientForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(recipientForm);
    recipient = {
      ...recipient,
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

  function setText(selector, value) { document.querySelector(selector).textContent = value; }

  function completeMonths(acquisitionDate, transactionDate) {
    const start = new Date(`${acquisitionDate}T00:00:00Z`);
    const end = new Date(`${transactionDate}T00:00:00Z`);
    let months = (end.getUTCFullYear() - start.getUTCFullYear()) * 12 + end.getUTCMonth() - start.getUTCMonth();
    if (end.getUTCDate() < start.getUTCDate()) months -= 1;
    return Math.max(0, months);
  }

  function holdingAnswerIsComplete() {
    const mode = form.elements.holding_period_mode.value;
    return mode === "at_least_12_months" || mode === "less_than_12_months" ||
      (mode === "known_date" && Boolean(form.elements.acquisition_date.value));
  }

  function updateDividendProgress() {
    const ownershipAnswered = form.elements.ownership_percent.value !== "";
    const directAnswered = form.elements.direct_ownership.value !== "";
    const holdingMode = form.elements.holding_period_mode.value;
    dividendSteps[1].hidden = !ownershipAnswered;
    dividendSteps[2].hidden = !ownershipAnswered || !directAnswered;
    acquisitionDateField.hidden = holdingMode !== "known_date";
    dividendSteps[3].hidden = !ownershipAnswered || !directAnswered || !holdingAnswerIsComplete();
  }

  form.elements.ownership_percent.addEventListener("input", () => {
    if (!votingWasEdited) form.elements.voting_ownership_percent.value = form.elements.ownership_percent.value;
    updateDividendProgress();
  });
  form.elements.direct_ownership.addEventListener("change", updateDividendProgress);
  form.elements.holding_period_mode.addEventListener("change", updateDividendProgress);
  form.elements.acquisition_date.addEventListener("input", updateDividendProgress);
  form.elements.voting_ownership_percent.addEventListener("input", () => { votingWasEdited = true; });

  function renderTransactionFacts() {
    const incomeType = form.elements.income_type.value;
    transactionFacts.hidden = !incomeType;
    dividendFacts.hidden = incomeType !== "dividend";
    interestFacts.hidden = incomeType !== "interest";
    royaltyFacts.hidden = incomeType !== "royalty";
    pendingQuestions = [];
    questionsRoot.replaceChildren();
    followUp.hidden = true;
    setText("#workspace-submit", "Vyhodnotit vstupní údaje →");
    if (incomeType === "dividend") updateDividendProgress();
  }
  form.elements.income_type.addEventListener("change", renderTransactionFacts);

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
        const rateDate = payload.transaction_date;
        clientAnswers.exchangeRate = { source: "CNB", currency: payload.transaction_amount.currency, czk_per_unit: input.querySelector('[name="czk_per_unit"]').value, effective_date: rateDate, source_url: input.querySelector('[name="source_url"]').value };
      } else if (path === "derived.acquisition_date") {
        clientAnswers.acquisitionDate = input.value;
      } else if (path && path.startsWith("facts.")) {
        const name = path.slice(6);
        clientAnswers.facts[name] = input.dataset.responseType === "boolean" ? input.value === "true" : input.dataset.responseType === "decimal_percent" ? Number(input.value) : input.value;
      }
    });
    Object.assign(payload.facts, clientAnswers.facts);
    if (clientAnswers.acquisitionDate) payload.facts.holding_period_months = completeMonths(clientAnswers.acquisitionDate, payload.transaction_date);
    if (clientAnswers.exchangeRate) payload.transaction_amount.exchange_rate = { ...clientAnswers.exchangeRate, currency: payload.transaction_amount.currency };
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

  function reviewItem(title, detail) {
    const node = document.createElement("div"); node.className = "action-item adviser";
    const strong = document.createElement("strong"); strong.textContent = title;
    const copy = document.createElement("small"); copy.textContent = detail;
    node.append(strong, copy);
    return node;
  }

  function concreteReviewItems(analysis, payload, professional) {
    const items = professional.map((question) => actionItem(question));
    if (payload.income_type === "dividend" && payload.facts.permanent_establishment_connection === true) {
      items.unshift(reviewItem(
        "Vazba podílu ke stálé provozovně v České republice",
        "Bylo uvedeno, že podíl, ze kterého dividendy plynou, je součástí činnosti stálé provozovny příjemce v České republice. Limity podle čl. 10 odst. 1 a 2 se proto nepoužijí; režim musí být posouzen podle čl. 7 smlouvy a českých pravidel pro stálou provozovnu."
      ));
    }
    if (analysis.status !== "FINAL" && !items.length) {
      items.push(reviewItem(
        "Podmínky použitelné sazby",
        "Z dostupných údajů zatím nelze uzavřít všechny podmínky právního pravidla. Je třeba ověřit chybějící skutkové okolnosti uvedené u vstupních údajů a kontrolu přepočítat."
      ));
    }
    return items;
  }

  function selectedRuleId(analysis) {
    return String(analysis.selected_rule_id || analysis.candidate_rule_id || "");
  }

  function resultExplanation(analysis, payload) {
    const selected = selectedRuleId(analysis);
    if (analysis.status === "FINAL" && analysis.rate === 0 && payload.income_type === "dividend" && selected.endsWith("CURRENT-2")) {
      const holding = Number(payload.facts.holding_period_months || 0);
      const treatyConclusion = "Česká srážková daň je 0 %. Článek 10 odst. 2 písm. b) smlouvy přiznává při alespoň 10% podílu společnosti právo zdanit dividendy pouze státu rezidence příjemce. Pro tuto smluvní cestu se dvanáctiměsíční doba držby nevyžaduje.";
      if (holding >= 12) return `${treatyConclusion} Osvobození podle § 19 zákona o daních z příjmů může představovat další samostatný právní titul, jeho použití však vyžaduje prokázání všech podmínek kvalifikované mateřské a dceřiné společnosti.`;
      return treatyConclusion;
    }
    if (analysis.status === "FINAL" && analysis.rate === 0 && payload.income_type === "dividend" && selected.includes("EU-RELIEF")) {
      return "Česká srážková daň je 0 % na základě osvobození podílu na zisku mezi kvalifikovanou mateřskou a dceřinou společností podle § 19 zákona o daních z příjmů. Příslušná smlouva může nezávisle vést ke stejnému výsledku; použitým právním titulem je v tomto výpočtu vnitrostátní osvobození.";
    }
    if (analysis.status === "FINAL" && analysis.rate === 10 && payload.income_type === "dividend" && selected.endsWith("CURRENT-1")) return "Česká srážková daň je 10 %. Článek 10 odst. 2 písm. a) smlouvy omezuje českou daň na 10 % hrubé částky dividend, pokud je příjemce skutečným vlastníkem dividend a podmínky zvláštního 0% režimu nejsou splněny.";
    if (analysis.status === "FINAL") return `Použitá sazba ${analysis.rate} % byla určena na základě zadaných údajů a rozhodného právního pravidla uvedeného níže.`;
    if (analysis.candidate_rate !== null && analysis.candidate_rate !== undefined) return `Byla identifikována sazba ${analysis.candidate_rate} %. Její použití závisí na odborném ověření právních podmínek uvedených níže.`;
    return "Sazbu zatím nelze určit. Níže jsou uvedeny konkrétní podmínky, které je třeba odborně ověřit.";
  }

  function citationDetail(citation) {
    const ruleId = String(citation.rule_id || "");
    if (ruleId.endsWith("CURRENT-2")) return "Při alespoň 10% podílu společnosti přiznává smlouva právo zdanit dividendy pouze státu rezidence příjemce.";
    if (ruleId.endsWith("CURRENT-1")) return "Obecný smluvní limit české daně činí 10 % hrubé částky dividend.";
    if (ruleId.includes("EU-RELIEF")) return "Osvobození kvalifikované výplaty podílu na zisku podle § 19 zákona o daních z příjmů a pravidel EU.";
    if (ruleId.includes("DOMESTIC")) return "Výchozí sazba podle českého zákona o daních z příjmů.";
    return "Právní ustanovení použité při výpočtu.";
  }

  function citationExcerpt(citation) {
    const ruleId = String(citation.rule_id || "");
    const sourceUrl = String(citation.source_url || "");
    if (!sourceUrl.includes("/sm/2007/31/")) return null;
    if (ruleId.endsWith("CURRENT-2")) return "„Tyto dividendy podléhají zdanění jen ve smluvním státě, jehož je skutečný vlastník dividend rezidentem.“";
    if (ruleId.endsWith("CURRENT-1")) return "„Daň takto uložená nepřesáhne 10 % hrubé částky dividend.“";
    return null;
  }

  function citationCard(citation) {
    const card = document.createElement("article"); card.className = "citation-card";
    const title = document.createElement("strong");
    const ruleId = String(citation.rule_id || "");
    const isTreaty = ruleId.includes("CURRENT");
    const treatyParagraph = ruleId.endsWith("CURRENT-2") ? " odst. 2 písm. b)" : ruleId.endsWith("CURRENT-1") ? " odst. 2 písm. a)" : "";
    title.textContent = isTreaty ? `Smlouva o zamezení dvojího zdanění · článek ${citation.article || "—"}${treatyParagraph}` : ruleId.includes("EU-RELIEF") ? "Zákon o daních z příjmů · § 19" : `Zákon o daních z příjmů · § ${citation.article || "—"}`;
    const link = document.createElement("a"); link.href = citation.source_url; link.target = "_blank"; link.rel = "noreferrer noopener"; link.textContent = "Otevřít zdroj ↗";
    const detail = document.createElement("p"); detail.textContent = citationDetail(citation);
    card.append(title, link, detail);
    const excerptText = citationExcerpt(citation);
    if (excerptText) { const excerpt = document.createElement("blockquote"); excerpt.textContent = excerptText; card.append(excerpt); }
    return card;
  }

  function formatCzechDate(value) {
    if (!value) return "—";
    return new Intl.DateTimeFormat("cs-CZ", { day: "numeric", month: "long", year: "numeric" }).format(new Date(`${value}T12:00:00`));
  }

  function renderComplianceSchedule(analysis) {
    const schedule = analysis.withholding_compliance_schedule;
    if (!schedule) return;
    setText("#workspace-reference-date", formatCzechDate(schedule.reference_date));
    setText("#workspace-remittance-deadline", schedule.tax_remittance_deadline ? formatCzechDate(schedule.tax_remittance_deadline) : analysis.status === "FINAL" && Number(analysis.rate) === 0 ? "Daň se neodvádí" : "Po dokončení posouzení");
    setText("#workspace-notification-deadline", schedule.notification_deadline ? formatCzechDate(schedule.notification_deadline) : "Po dokončení posouzení");
    const note = document.querySelector("#workspace-deadline-note");
    if (schedule.status !== "READY") note.textContent = "Lhůty nelze uzavřít, dokud není určeno konečné daňové zacházení.";
    else if (schedule.notification_regime === "exempt_or_treaty_non_taxable_annual") note.textContent = "Při 0% výsledku se daň neodvádí. Oznámení o příjmu plynoucím do zahraničí se u dividend podává do 31. ledna následujícího roku.";
    else note.textContent = "Odvod sražené daně a oznámení o příjmu plynoucím do zahraničí mají shodnou lhůtu: konec následujícího kalendářního měsíce.";
    const caution = document.querySelector("#workspace-dividend-deadline-caution");
    caution.hidden = !schedule.dividend_timing_review_required;
  }

  function decisiveCitations(analysis) {
    const selected = selectedRuleId(analysis);
    const citations = [...(analysis.citations || [])];
    citations.sort((left, right) => Number(String(right.rule_id || "") === selected) - Number(String(left.rule_id || "") === selected));
    const unique = new Map();
    citations.forEach((citation) => {
      const key = `${citation.source_url || ""}|${citation.article || ""}`;
      if (!unique.has(key)) unique.set(key, citation);
    });
    return [...unique.values()];
  }

  function renderResult(payload, response) {
    const analysis = response.analysis;
    const calculation = analysis.withholding_tax_calculation;
    const professional = (response.intake?.questions || []).filter((question) => !question.client_answerable);
    const reviewItems = concreteReviewItems(analysis, payload, professional);
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
    setText("#workspace-reason", resultExplanation(analysis, payload));
    const actions = document.querySelector("#workspace-actions"); actions.replaceChildren();
    reviewItems.forEach((item) => actions.append(item));
    setText("#workspace-action-count", String(reviewItems.length));
    if (!reviewItems.length) {
      const item = document.createElement("div"); item.className = "action-item complete";
      const strong = document.createElement("strong"); strong.textContent = "Bez otevřených odborných položek";
      const small = document.createElement("small"); small.textContent = "Zadané údaje postačují pro dokončení výpočtu.";
      item.append(strong, small); actions.append(item);
    }
    const citations = document.querySelector("#workspace-citations"); citations.replaceChildren();
    decisiveCitations(analysis).forEach((citation) => citations.append(citationCard(citation)));
    if (!citations.children.length) { const p = document.createElement("p"); p.textContent = "Pro tento výsledek nebyl vrácen konkrétní odkaz na právní zdroj."; citations.append(p); }
    renderComplianceSchedule(analysis);
    showStep(3);
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const error = document.querySelector("#workspace-error"); error.hidden = true;
    const transactionDate = String(data.get("transaction_date"));
    const facts = {
      beneficial_owner: String(data.get("beneficial_owner")) === "true",
      recipient_is_treaty_resident: String(data.get("treaty_resident")) === "true",
      permanent_establishment_connection: String(data.get("pe_connection")) === "true",
      recipient_entity_type: recipient.type === "Fyzická osoba" ? "individual" : recipient.type === "Fond" ? "fund" : recipient.type === "Společnost" ? "company" : "other"
    };
    const incomeType = String(data.get("income_type"));
    const ownershipPercent = String(data.get("ownership_percent"));
    const directOwnership = String(data.get("direct_ownership"));
    const votingOwnership = String(data.get("voting_ownership_percent"));
    const holdingPeriodMode = String(data.get("holding_period_mode"));
    const acquisitionDate = String(data.get("acquisition_date"));
    const armLengthAmount = String(data.get("arm_length_amount"));
    const royaltyCategory = String(data.get("royalty_category"));
    if (incomeType === "dividend") {
      if (ownershipPercent) facts.ownership_percent = Number(ownershipPercent);
      if (directOwnership) facts.direct_ownership = directOwnership === "true";
      if (votingOwnership) facts.direct_or_indirect_voting_ownership = Number(votingOwnership);
      if (holdingPeriodMode === "known_date" && acquisitionDate) facts.holding_period_months = completeMonths(acquisitionDate, transactionDate);
      if (holdingPeriodMode === "at_least_12_months") facts.holding_period_months = 12;
      if (holdingPeriodMode === "less_than_12_months") facts.holding_period_months = 0;
    }
    if (incomeType === "interest" && armLengthAmount) facts.arm_length_amount = armLengthAmount === "true";
    if (incomeType === "royalty" && royaltyCategory) facts.royalty_category = royaltyCategory;
    const payload = {
      source_country: "CZ", recipient_country: recipient.country, income_type: incomeType, transaction_date: transactionDate,
      facts, determinations: {}, transaction_amount: { amount: String(data.get("amount")), currency: String(data.get("currency")), payment_date: transactionDate, accounting_date: transactionDate }
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

  renderRecipient();
  renderTransactionFacts();
})();
