(() => {
  "use strict";

  const form = document.querySelector("#case-form");
  const currency = document.querySelector("#currency");
  const amount = document.querySelector("#amount");
  const incomeType = document.querySelector("#income-type");
  const fxFields = document.querySelector("#fx-fields");
  const dividendFields = document.querySelector("#dividend-fields");
  const emptyState = document.querySelector("#empty-state");
  const result = document.querySelector("#result");
  const submitButton = form.querySelector("button[type=submit]");
  const reportButton = document.querySelector("#report-button");
  const formError = document.querySelector("#form-error");
  const reportError = document.querySelector("#report-error");
  let currentPayload = null;

  const value = (data, name) => String(data.get(name) || "").trim();

  function toggleFx() {
    const isCzk = currency.value === "CZK";
    fxFields.hidden = isCzk;
    amount.step = isCzk ? "1" : "0.01";
    amount.inputMode = isCzk ? "numeric" : "decimal";
    amount.placeholder = isCzk ? "100000" : "100000.00";
  }

  function toggleIncomeDetails() {
    dividendFields.hidden = incomeType.value !== "dividend";
  }

  function completeMonths(fromValue, toValue) {
    if (!fromValue || !toValue) return null;
    const from = new Date(`${fromValue}T00:00:00Z`);
    const to = new Date(`${toValue}T00:00:00Z`);
    if (Number.isNaN(from.valueOf()) || Number.isNaN(to.valueOf()) || from > to) {
      return null;
    }
    let months = (to.getUTCFullYear() - from.getUTCFullYear()) * 12
      + to.getUTCMonth() - from.getUTCMonth();
    if (to.getUTCDate() < from.getUTCDate()) months -= 1;
    return Math.max(0, months);
  }

  function amountPayload(data) {
    const amount = value(data, "amount");
    if (!amount) return null;

    const selectedCurrency = value(data, "currency");
    const payload = { amount, currency: selectedCurrency };
    if (selectedCurrency !== "CZK") {
      const paymentDate = value(data, "payment_date");
      const accountingDate = value(data, "accounting_date");
      const rate = value(data, "czk_per_unit");
      const rateDate = value(data, "rate_date");
      const rateUrl = value(data, "rate_url");
      if (paymentDate) payload.payment_date = paymentDate;
      if (accountingDate) payload.accounting_date = accountingDate;
      if (rate || rateDate || rateUrl) {
        payload.exchange_rate = {
          source: "CNB",
          currency: selectedCurrency,
          czk_per_unit: rate,
          effective_date: rateDate,
          source_url: rateUrl
        };
      }
    }
    return payload;
  }

  function buildPayload() {
    const data = new FormData(form);
    const payload = {
      source_country: value(data, "source_country"),
      recipient_country: value(data, "recipient_country"),
      income_type: value(data, "income_type"),
      transaction_date: value(data, "transaction_date"),
      facts: {
        beneficial_owner: true,
        recipient_is_treaty_resident: true,
        permanent_establishment_connection: !data.get("no_pe_connection"),
        recipient_entity_type: value(data, "recipient_entity_type")
      },
      determinations: {}
    };
    const transactionAmount = amountPayload(data);
    if (transactionAmount) payload.transaction_amount = transactionAmount;
    if (payload.income_type === "dividend") {
      const ownership = value(data, "ownership_percent");
      const votingOwnership = value(data, "voting_ownership_percent");
      const acquisitionDate = value(data, "acquisition_date");
      if (ownership) payload.facts.ownership_percent = Number(ownership);
      if (votingOwnership) {
        payload.facts.direct_or_indirect_voting_ownership = Number(votingOwnership);
      }
      payload.facts.direct_ownership = Boolean(data.get("direct_ownership"));
      const months = completeMonths(acquisitionDate, payload.transaction_date);
      if (months !== null) payload.facts.holding_period_months = months;
    }
    return payload;
  }

  function statusCopy(status, treatment = null) {
    if (status === "FINAL" && treatment === "exclusive_foreign_taxation") {
      return ["Pravidlo přiřazené k zadaným údajům", "Podle použitého smluvního pravidla je v TaxTreat při zadaných údajích přiřazeno pravidlo bez českého zdanění; jde o automatizované informační přiřazení, nikoli individuální daňové posouzení."];
    }
    if (status === "FINAL" && treatment === "domestic_exemption") {
      return ["Pravidlo přiřazené k zadaným údajům", "Podle použitého vnitrostátního pravidla je v TaxTreat při zadaných údajích přiřazeno pravidlo osvobození; jde o automatizované informační přiřazení, nikoli individuální daňové posouzení."];
    }
    const copies = {
      FINAL: ["Výpočet dokončen", "TaxTreat podle zadaných údajů přiřadil evidované právní pravidlo a provedl výpočet podle zadaných údajů."],
      REVIEW_REQUIRED: ["Je třeba doplnit údaje", "Doplňte konkrétní vstupní informace, aby TaxTreat mohl automatizovaně přiřadit relevantní pravidlo."],
      OUT_OF_SCOPE: ["Mimo podporovaný rozsah", "Transakce nespadá do aktuálně podporovaného rozsahu českých odchozích plateb."]
    };
    return copies[status] || ["Chybí údaj pro přiřazení pravidla", "Z dostupných vstupních údajů nelze konkrétní právní pravidlo automatizovaně přiřadit."];
  }

  function statusBadgeCopy(status) {
    return {
      FINAL: "DOKONČENO",
      REVIEW_REQUIRED: "DOPLNIT ÚDAJE",
      OUT_OF_SCOPE: "MIMO ROZSAH"
    }[status] || "CHYBÍ ÚDAJ";
  }

  function revealButton(label, onClick) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "reveal-button";
    button.textContent = label;
    button.addEventListener("click", onClick, { once: true });
    return button;
  }

  function clientFactName(inputPath) {
    if (!inputPath || !inputPath.startsWith("facts.")) return null;
    const name = inputPath.slice("facts.".length);
    return /^[a-z0-9_]+$/.test(name) ? name : null;
  }

  function isClientInputPath(inputPath) {
    return Boolean(clientFactName(inputPath))
      || inputPath === "derived.acquisition_date";
  }

  function createQuestionInput(question, drafts) {
    const factName = clientFactName(question.input_path);
    if (!question.client_answerable || !isClientInputPath(question.input_path)) {
      return null;
    }

    const label = document.createElement("label");
    label.className = "question-answer";
    const caption = document.createElement("span");
    caption.textContent = "Doplnění údaje";
    const inputId = "answer-" + question.question_id.replace(/[^a-z0-9_-]/gi, "-");
    const draft = drafts[question.input_path];
    const existing = draft
      ? draft.value
      : factName ? currentPayload?.facts?.[factName] : undefined;

    let input;
    if (question.response_type === "boolean") {
      input = document.createElement("select");
      [
        ["", "Vyberte odpověď"],
        ["true", "Ano"],
        ["false", "Ne"]
      ].forEach(([optionValue, optionLabel]) => {
        const option = document.createElement("option");
        option.value = optionValue;
        option.textContent = optionLabel;
        input.append(option);
      });
    } else if (question.response_type === "choice") {
      input = document.createElement("select");
      [["", "Vyberte možnost"], ...(question.options || [])].forEach(
        ([optionValue, optionLabel]) => {
          const option = document.createElement("option");
          option.value = optionValue;
          option.textContent = optionLabel;
          input.append(option);
        }
      );
    } else {
      input = document.createElement("input");
      input.type = question.response_type === "date" ? "date"
        : question.response_type === "text" ? "text" : "number";
      if (question.response_type === "decimal_percent") {
        input.min = "0";
        input.max = "100";
        input.step = "0.01";
        input.placeholder = "např. 25";
      } else if (question.response_type === "integer") {
        input.min = "0";
        input.step = "1";
        input.placeholder = "počet celých měsíců";
      }
    }
    input.id = inputId;
    input.className = "question-input";
    input.dataset.inputPath = question.input_path;
    input.dataset.responseType = question.response_type;
    if (existing !== undefined && existing !== null) {
      input.value = String(existing);
    }
    label.htmlFor = inputId;
    label.append(caption, input);
    return label;
  }

  function captureDraftAnswers(root, drafts) {
    root.querySelectorAll(".question-input").forEach((input) => {
      drafts[input.dataset.inputPath] = {
        value: input.value,
        responseType: input.dataset.responseType,
        valid: input.checkValidity()
      };
    });
  }

  function applyClientAnswers(payload, drafts) {
    let supplied = 0;
    Object.entries(drafts).forEach(([inputPath, draft]) => {
      if (!draft.valid) {
        throw new Error("Zkontrolujte formát doplněných údajů.");
      }
      const raw = draft.value.trim();
      if (!raw) return;
      const factName = clientFactName(inputPath);
      if (inputPath === "derived.acquisition_date") {
        const months = completeMonths(raw, payload.transaction_date);
        if (months === null) {
          throw new Error("Datum nabytí podílu musí předcházet datu transakce.");
        }
        payload.facts.holding_period_months = months;
        supplied += 1;
        return;
      }
      if (!factName) {
        throw new Error("Tento údaj upravte v základním zadání transakce.");
      }

      let answer = raw;
      if (draft.responseType === "boolean") {
        answer = raw === "true";
      } else if (draft.responseType === "integer") {
        answer = Number.parseInt(raw, 10);
      } else if (draft.responseType === "decimal_percent") {
        answer = Number(raw);
      }
      payload.facts[factName] = answer;
      supplied += 1;
    });
    return supplied;
  }

  async function submitGuidedAnswers(button, drafts) {
    const root = document.querySelector("#questions");
    const answerError = document.querySelector("#answer-error");
    answerError.hidden = true;
    captureDraftAnswers(root, drafts);
    const nextPayload = structuredClone(currentPayload);
    try {
      const supplied = applyClientAnswers(nextPayload, drafts);
      if (!supplied) {
        throw new Error("Doplňte alespoň jeden skutkový údaj.");
      }
      button.disabled = true;
      button.textContent = "Aktualizuji výpočet…";
      const response = await postJson("/analysis/intake", nextPayload);
      currentPayload = nextPayload;
      renderResponse(response);
    } catch (error) {
      answerError.textContent = error.message;
      answerError.hidden = false;
    } finally {
      button.disabled = false;
      button.textContent = "Aktualizovat výpočet";
    }
  }

  function renderAdvisorItems(items) {
    const section = document.querySelector("#advisor-review-section");
    const root = document.querySelector("#advisor-items");
    root.replaceChildren();
    section.hidden = items.length === 0;
    document.querySelector("#advisor-count").textContent = items.length;
    items.forEach((item) => {
      const card = document.createElement("article");
      card.className = "question advisor-item";
      const tag = document.createElement("span");
      tag.className = "tag review";
      tag.textContent = "Nelze určit z dostupných údajů";
      const prompt = document.createElement("p");
      prompt.textContent = item.prompt;
      const why = document.createElement("small");
      why.textContent = item.why;
      card.append(tag, prompt, why);
      root.append(card);
    });
  }

  function renderQuestions(allQuestions) {
    const questions = allQuestions.filter((question) => question.client_answerable);
    const advisorItems = allQuestions.filter((question) => !question.client_answerable);
    const root = document.querySelector("#questions");
    const section = document.querySelector("#client-questions-section");
    const pageSize = 3;
    const pageCount = Math.max(1, Math.ceil(questions.length / pageSize));
    const drafts = {};
    let pageIndex = 0;
    root.replaceChildren();
    section.hidden = questions.length === 0;
    renderAdvisorItems(advisorItems);

    if (!questions.length) {
      document.querySelector("#question-count").textContent = "0";
      return;
    }

    function render() {
      captureDraftAnswers(root, drafts);
      root.replaceChildren();

      const start = pageIndex * pageSize;
      const end = Math.min(start + pageSize, questions.length);
      const progress = document.createElement("div");
      progress.className = "wizard-progress";
      const progressCopy = document.createElement("div");
      const progressLabel = document.createElement("strong");
      progressLabel.textContent = `Položky ${start + 1}–${end} z ${questions.length}`;
      const progressStep = document.createElement("span");
      progressStep.textContent = `Krok ${pageIndex + 1} z ${pageCount}`;
      progressCopy.append(progressLabel, progressStep);
      const progressTrack = document.createElement("div");
      progressTrack.className = "wizard-progress-track";
      const progressFill = document.createElement("span");
      progressFill.style.width = `${((pageIndex + 1) / pageCount) * 100}%`;
      progressTrack.append(progressFill);
      progress.append(progressCopy, progressTrack);
      root.append(progress);

      questions.slice(start, end).forEach((question) => {
        const card = document.createElement("article");
        card.className = "question";
        const tag = document.createElement("span");
        tag.className = "tag";
        tag.textContent = "Údaj k doplnění";
        const prompt = document.createElement("p");
        prompt.textContent = question.prompt;
        const why = document.createElement("small");
        why.textContent = question.why;
        card.append(tag, prompt, why);
        const input = createQuestionInput(question, drafts);
        if (input) card.append(input);
        root.append(card);
      });

      const navigation = document.createElement("div");
      navigation.className = "wizard-navigation";
      if (pageIndex > 0) {
        const previous = document.createElement("button");
        previous.type = "button";
        previous.className = "wizard-back";
        previous.textContent = "← Zpět";
        previous.addEventListener("click", () => {
          captureDraftAnswers(root, drafts);
          pageIndex -= 1;
          render();
        });
        navigation.append(previous);
      }
      if (pageIndex < pageCount - 1) {
        const next = document.createElement("button");
        next.type = "button";
        next.className = "wizard-next";
        next.textContent = "Další položky →";
        next.addEventListener("click", () => {
          captureDraftAnswers(root, drafts);
          pageIndex += 1;
          render();
        });
        navigation.append(next);
      }
      root.append(navigation);

      if (
        Object.keys(drafts).length
        || root.querySelector(".question-input")
      ) {
        const actions = document.createElement("div");
        actions.className = "question-actions";
        const button = document.createElement("button");
        button.type = "button";
        button.className = "secondary wizard-save";
        button.textContent = "Aktualizovat výpočet";
        button.addEventListener(
          "click",
          () => submitGuidedAnswers(button, drafts)
        );
        actions.append(button);
        root.append(actions);
      }
    }

    render();
    document.querySelector("#question-count").textContent = questions.length;
  }

  function renderDocuments(documents) {
    const root = document.querySelector("#documents");
    const initialLimit = 6;
    const values = documents.length ? documents : ["K tomuto informačnímu výstupu nejsou evidovány další související podklady."];

    function render(limit) {
      root.replaceChildren();
      values.slice(0, limit).forEach((documentName) => {
        const item = document.createElement("li");
        item.textContent = documentName;
        root.append(item);
      });
      if (limit < values.length) {
        const item = document.createElement("li");
        item.className = "reveal-item";
        item.append(revealButton(
          `Zobrazit zbývající podklady (${values.length - limit})`,
          () => render(values.length)
        ));
        root.append(item);
      }
    }

    render(initialLimit);
    document.querySelector("#document-count").textContent = documents.length;
  }

  function formatCzk(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return "—";
    return new Intl.NumberFormat("cs-CZ", { maximumFractionDigits: 2 }).format(numeric) + " Kč";
  }

  function renderCalculation(calculation) {
    const card = document.querySelector("#calculation-card");
    if (!calculation || calculation.status !== "CALCULATED") {
      card.hidden = true;
      return;
    }
    document.querySelector("#gross-czk").textContent = formatCzk(calculation.gross_amount_czk);
    document.querySelector("#tax-czk-label").textContent = ["exclusive_foreign_taxation", "domestic_exemption"].includes(calculation.tax_treatment) ? "Česká daň k odvodu" : "Srážková daň";
    document.querySelector("#tax-czk").textContent = formatCzk(calculation.withholding_tax_czk);
    document.querySelector("#net-czk").textContent = formatCzk(calculation.net_amount_czk);
    card.hidden = false;
  }

  function renderResponse(payload) {
    const analysis = payload.analysis;
    const intake = payload.intake;
    const [title, description] = statusCopy(analysis.status, analysis.tax_treatment);
    emptyState.hidden = true;
    result.hidden = false;
    document.querySelector("#status-title").textContent = title;
    document.querySelector("#status-description").textContent = description;
    const badge = document.querySelector("#status-badge");
    badge.textContent = statusBadgeCopy(analysis.status);
    badge.className = "status-badge" +
      (analysis.status === "FINAL" ? " final" : analysis.status === "OUT_OF_SCOPE" ? " out" : "");
    renderQuestions(intake.questions || []);
    renderDocuments(intake.required_documents || []);
    renderCalculation(analysis.withholding_tax_calculation);
  }

  async function postJson(url, payload) {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const body = await response.json();
    if (!response.ok) {
      const detail = body.detail;
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return body;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    formError.hidden = true;
    submitButton.disabled = true;
    submitButton.firstChild.textContent = "Přiřazuji pravidla… ";
    try {
      currentPayload = buildPayload();
      const response = await postJson("/analysis/intake", currentPayload);
      renderResponse(response);
      result.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
      formError.textContent = "Výpočet nebylo možné dokončit: " + error.message;
      formError.hidden = false;
    } finally {
      submitButton.disabled = false;
      submitButton.firstChild.textContent = "Vypočítat srážkovou daň ";
    }
  });

  reportButton.addEventListener("click", async () => {
    if (!currentPayload) return;
    reportError.hidden = true;
    const reportWindow = window.open("", "_blank");
    if (!reportWindow) {
      reportError.textContent = "Prohlížeč zablokoval nové okno. Povol vyskakovací okna pro TaxTreat a zkus Tisk / PDF znovu.";
      reportError.hidden = false;
      return;
    }
    reportButton.disabled = true;
    reportWindow.document.write("<!doctype html><title>TaxTreat</title><p style='font-family:system-ui;padding:32px'>Připravuji PDF výstup…</p>");
    try {
      const response = await postJson("/analysis/report", currentPayload);
      reportWindow.document.open();
      reportWindow.document.write(response.html);
      reportWindow.document.close();
      reportWindow.opener = null;
      let printed = false;
      const printOutput = () => {
        if (printed) return;
        printed = true;
        reportWindow.__taxtreatPrintCalled = true;
        reportWindow.focus();
        reportWindow.print();
      };
      reportWindow.addEventListener("load", printOutput, { once: true });
      window.setTimeout(printOutput, 250);
    } catch (error) {
      reportWindow.close();
      reportError.textContent = "Výstup nebylo možné vytvořit: " + error.message;
      reportError.hidden = false;
    } finally {
      reportButton.disabled = false;
    }
  });

  currency.addEventListener("change", toggleFx);
  incomeType.addEventListener("change", toggleIncomeDetails);
  form.elements.transaction_date.value = new Date().toISOString().slice(0, 10);
  toggleFx();
  toggleIncomeDetails();
})();
