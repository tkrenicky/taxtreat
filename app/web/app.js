(() => {
  "use strict";

  const form = document.querySelector("#case-form");
  const currency = document.querySelector("#currency");
  const fxFields = document.querySelector("#fx-fields");
  const emptyState = document.querySelector("#empty-state");
  const result = document.querySelector("#result");
  const submitButton = form.querySelector("button[type=submit]");
  const reportButton = document.querySelector("#report-button");
  const formError = document.querySelector("#form-error");
  const reportError = document.querySelector("#report-error");
  let currentPayload = null;

  const value = (data, name) => String(data.get(name) || "").trim();

  function toggleFx() {
    fxFields.hidden = currency.value === "CZK";
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
      facts: {},
      determinations: {}
    };
    const transactionAmount = amountPayload(data);
    if (transactionAmount) payload.transaction_amount = transactionAmount;
    return payload;
  }

  function statusCopy(status) {
    const copies = {
      FINAL: ["Výpočet dokončen", "Uvolněná právní cesta poskytla finální sazbu."],
      REVIEW_REQUIRED: ["Je potřeba doplnit informace", "Bez níže uvedených údajů nelze bezpečně určit finální sazbu."],
      OUT_OF_SCOPE: ["Mimo podporovaný rozsah", "Tato transakce není součástí současného českého outbound rozsahu."]
    };
    return copies[status] || ["Posouzení vyžaduje kontrolu", "Zkontrolujte zobrazené otázky a doklady."];
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

  function createQuestionInput(question, drafts) {
    const factName = question.client_answerable
      ? clientFactName(question.input_path)
      : null;
    if (!factName) return null;

    const label = document.createElement("label");
    label.className = "question-answer";
    const caption = document.createElement("span");
    caption.textContent = "Odpověď klienta";
    const inputId = "answer-" + question.question_id.replace(/[^a-z0-9_-]/gi, "-");
    const draft = drafts[question.input_path];
    const existing = draft
      ? draft.value
      : currentPayload?.facts?.[factName];

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
    } else {
      input = document.createElement("input");
      input.type = question.response_type === "text" ? "text" : "number";
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
        throw new Error("Zkontrolujte formát zadaných odpovědí.");
      }
      const raw = draft.value.trim();
      if (!raw) return;
      const factName = clientFactName(inputPath);
      if (!factName) {
        throw new Error("Klientská odpověď smí měnit pouze skutkové údaje.");
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
        throw new Error("Vyplňte alespoň jednu odpověď klienta.");
      }
      button.disabled = true;
      button.textContent = "Přepočítávám…";
      const response = await postJson("/analysis/intake", nextPayload);
      currentPayload = nextPayload;
      renderResponse(response);
    } catch (error) {
      answerError.textContent = error.message;
      answerError.hidden = false;
    } finally {
      button.disabled = false;
      button.textContent = "Uložit odpovědi a vyhodnotit";
    }
  }

  function renderQuestions(questions) {
    const root = document.querySelector("#questions");
    const pageSize = 3;
    const pageCount = Math.max(1, Math.ceil(questions.length / pageSize));
    const drafts = {};
    let pageIndex = 0;
    root.replaceChildren();

    function render() {
      captureDraftAnswers(root, drafts);
      root.replaceChildren();

      const start = pageIndex * pageSize;
      const end = Math.min(start + pageSize, questions.length);
      const progress = document.createElement("div");
      progress.className = "wizard-progress";
      const progressCopy = document.createElement("div");
      const progressLabel = document.createElement("strong");
      progressLabel.textContent = `Otázky ${start + 1}–${end} z ${questions.length}`;
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
        tag.className = "tag" + (question.client_answerable ? "" : " review");
        tag.textContent = question.client_answerable ? "Údaj klienta" : "Odborné posouzení";
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
        next.textContent = "Další otázky →";
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
        button.textContent = "Uložit odpovědi a vyhodnotit";
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
    const values = documents.length ? documents : ["V této fázi nejsou vyžádány další doklady."];

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
          `Zobrazit dalších ${values.length - limit} dokladů`,
          () => render(values.length)
        ));
        root.append(item);
      }
    }

    render(initialLimit);
    document.querySelector("#document-count").textContent = documents.length;
  }

  function renderCalculation(calculation) {
    const card = document.querySelector("#calculation-card");
    if (!calculation || calculation.status !== "CALCULATED") {
      card.hidden = true;
      return;
    }
    document.querySelector("#gross-czk").textContent = calculation.gross_amount_czk + " Kč";
    document.querySelector("#tax-czk").textContent = calculation.withholding_tax_czk + " Kč";
    document.querySelector("#net-czk").textContent = calculation.net_amount_czk + " Kč";
    card.hidden = false;
  }

  function renderResponse(payload) {
    const analysis = payload.analysis;
    const intake = payload.intake;
    const [title, description] = statusCopy(analysis.status);
    emptyState.hidden = true;
    result.hidden = false;
    document.querySelector("#status-title").textContent = title;
    document.querySelector("#status-description").textContent = description;
    const badge = document.querySelector("#status-badge");
    badge.textContent = analysis.status;
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
    submitButton.firstChild.textContent = "Vyhodnocuji… ";
    try {
      currentPayload = buildPayload();
      const response = await postJson("/analysis/intake", currentPayload);
      renderResponse(response);
      result.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
      formError.textContent = "Posouzení se nepodařilo: " + error.message;
      formError.hidden = false;
    } finally {
      submitButton.disabled = false;
      submitButton.firstChild.textContent = "Zjistit potřebné informace ";
    }
  });

  reportButton.addEventListener("click", async () => {
    if (!currentPayload) return;
    reportError.hidden = true;
    reportButton.disabled = true;
    try {
      const response = await postJson("/analysis/report", currentPayload);
      const blob = new Blob([response.html], { type: "text/html;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = response.report.report_id + ".html";
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      reportError.textContent = "Report se nepodařilo vytvořit: " + error.message;
      reportError.hidden = false;
    } finally {
      reportButton.disabled = false;
    }
  });

  currency.addEventListener("change", toggleFx);
  form.elements.transaction_date.value = new Date().toISOString().slice(0, 10);
  toggleFx();
})();
