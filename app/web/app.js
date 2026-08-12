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

  function renderQuestions(questions) {
    const root = document.querySelector("#questions");
    const initialLimit = 5;

    function render(limit) {
      root.replaceChildren();
      questions.slice(0, limit).forEach((question) => {
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
        root.append(card);
      });
      if (limit < questions.length) {
        root.append(revealButton(
          `Zobrazit dalších ${questions.length - limit} otázek`,
          () => render(questions.length)
        ));
      }
    }

    render(initialLimit);
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
