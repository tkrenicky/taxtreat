(() => {
  const routeDesign = window.location.pathname.split("/").filter(Boolean).at(-1);
  const design = ["editorial", "atlas", "civic"].includes(routeDesign)
    ? routeDesign
    : new URLSearchParams(window.location.search).get("design");
  if (["editorial", "atlas", "civic"].includes(design)) {
    document.body.dataset.design = design;
    const switcher = document.querySelector("#design-switcher");
    switcher.hidden = false;
    switcher.querySelector(`[data-design-link="${design}"]`).classList.add("active");
  }
  "use strict";

  const BUILD_VERSION = "20260817-1";

  async function checkForNewBuild() {
    try {
      const response = await fetch(window.location.pathname, {
        cache: "no-store",
      });
      const html = await response.text();
      const deployed = html.match(/workspace\.js\?v=([0-9-]+)/)?.[1];
      if (!deployed || deployed === BUILD_VERSION || document.querySelector("#new-build-notice")) return;
      const notice = document.createElement("aside"); notice.id = "new-build-notice"; notice.className = "new-build-notice";
      const copy = document.createElement("span"); copy.textContent = "Je dostupná novější verze TaxTreat. Rozpracovaný výsledek může používat starší pravidla zobrazení.";
      const reload = document.createElement("button"); reload.type = "button"; reload.textContent = "Načíst novou verzi"; reload.addEventListener("click", () => window.location.reload());
      notice.append(copy, reload); document.body.append(notice);
    } catch (_problem) {
      // Kontrola verze nesmí přerušit práci v aplikaci.
    }
  }
  window.setInterval(checkForNewBuild, 60000);

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
  const fxStatus = document.querySelector("#workspace-fx-status");
  const exchangeRateField = document.querySelector("#workspace-exchange-rate-field");
  const exchangeRateInput = form.elements.exchange_rate_czk_per_unit;
  const exchangeRateLabel = document.querySelector("#workspace-exchange-rate-label");
  const activePayerSelect = document.querySelector("#active-payer-select");
  const payerList = document.querySelector("#payer-list");
  const flowPayerList = document.querySelector("#flow-payer-list");
  let votingWasEdited = false;
  const regionNames = new Intl.DisplayNames(["cs-CZ"], { type: "region" });
  const knownCountryGenitives = { AT: "Rakouska", CH: "Švýcarska", DE: "Německa", SG: "Singapuru", TW: "Tchaj-wanu" };
  function countryName(code) {
    try { return regionNames.of(String(code || "").toUpperCase()) || String(code || ""); }
    catch (_problem) { return String(code || ""); }
  }
  function countryGenitive(code) {
    return knownCountryGenitives[String(code || "").toUpperCase()] || countryName(code);
  }
  async function loadJurisdictionCatalog() {
    const selects = [recipientForm?.elements.recipient_country, recipientEditForm?.elements.recipient_country].filter(Boolean);
    selects.forEach((select) => { select.disabled = true; });
    try {
      const response = await fetch("/jurisdictions", { cache: "no-store" });
      const body = await response.json();
      if (!response.ok || !Array.isArray(body.jurisdictions) || body.jurisdictions.length !== 101) {
        throw new Error("Incomplete jurisdiction catalog");
      }
      const jurisdictions = [...body.jurisdictions].sort((a, b) =>
        countryName(a.iso2).localeCompare(countryName(b.iso2), "cs")
      );
      selects.forEach((select) => {
        const current = select.value;
        const placeholder = select.closest("#new-recipient-form") ? "Vyber stát" : null;
        select.replaceChildren();
        if (placeholder) {
          const option = document.createElement("option"); option.value = ""; option.textContent = placeholder; select.append(option);
        }
        jurisdictions.forEach((item) => {
          const option = document.createElement("option");
          option.value = item.iso2;
          option.textContent = countryName(item.iso2);
          select.append(option);
        });
        if ([...select.options].some((option) => option.value === current)) select.value = current;
      });
    } catch (_problem) {
      // Keep the server-rendered fallback rather than blocking the workspace.
    } finally {
      selects.forEach((select) => { select.disabled = false; });
    }
  }
  let recipient = {
    name: "Demo GmbH",
    country: "AT",
    type: "Společnost",
    beneficialOwner: true,
    treatyResident: true,
    relationships: {
      "demo-cz": { peConnection: false, ownershipPercent: "", directOwnership: "", acquisitionDate: "", votingOwnershipPercent: "" },
      "alfa-cz": { peConnection: false, ownershipPercent: "25", directOwnership: "true", acquisitionDate: "2024-06-01", votingOwnershipPercent: "25" }
    }
  };
  let payers = [
    { key: "demo-cz", name: "Demo CZ s.r.o.", id: "12345678", vatId: "CZ12345678" },
    { key: "alfa-cz", name: "Alfa Services CZ a.s.", id: "87654321", vatId: "CZ87654321" }
  ];
  let activePayerKey = "demo-cz";
  let editingPayerKey = null;
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

  function activePayer() {
    return payers.find((item) => item.key === activePayerKey) || payers[0];
  }

  function currentRelationship() {
    if (!recipient.relationships[activePayerKey]) {
      recipient.relationships[activePayerKey] = { peConnection: false, ownershipPercent: "", directOwnership: "", acquisitionDate: "", votingOwnershipPercent: "" };
    }
    return recipient.relationships[activePayerKey];
  }

  navButtons.forEach((button) => button.addEventListener("click", () => showView(button.dataset.nav)));
  document.querySelectorAll("[data-start-flow]").forEach((button) => button.addEventListener("click", () => showStep(1)));
  document.querySelectorAll("[data-open-recipient]").forEach((button) => button.addEventListener("click", () => showView("recipient-detail")));
  document.querySelectorAll("[data-next-step]").forEach((button) => button.addEventListener("click", () => showStep(Number(button.dataset.nextStep))));
  progressButtons.forEach((button) => button.addEventListener("click", () => {
    const step = Number(button.dataset.flowStep);
    if (step < 4 || lastPayload) showStep(step);
  }));
  document.querySelectorAll("[data-create-recipient]").forEach((button) => button.addEventListener("click", () => {
    showStep(2);
    recipientForm.hidden = false;
    recipientForm.querySelectorAll("input,select").forEach((field) => { field.disabled = false; field.readOnly = false; });
    recipientForm.querySelector("input").focus();
  }));
  document.querySelector("[data-show-recipient-form]").addEventListener("click", () => {
    recipientForm.hidden = !recipientForm.hidden;
    if (!recipientForm.hidden) {
      recipientForm.querySelectorAll("input,select").forEach((field) => { field.disabled = false; field.readOnly = false; });
      recipientForm.querySelector("input").focus();
    }
  });

  document.querySelectorAll("[data-tooltip]").forEach((button) => button.addEventListener("click", () => {
    const panel = document.getElementById(button.dataset.tooltip);
    const willOpen = panel.hidden;
    document.querySelectorAll(".tooltip-panel").forEach((item) => { item.hidden = true; });
    panel.hidden = !willOpen;
    button.setAttribute("aria-expanded", String(willOpen));
  }));

  function openPayerDialog(key = null) {
    editingPayerKey = key;
    const selected = key ? payers.find((item) => item.key === key) : null;
    document.querySelector("#payer-dialog-title").textContent = selected ? "Upravit plátce" : "Přidat plátce";
    payerForm.elements.payer_name.value = selected?.name || "";
    payerForm.elements.payer_id.value = selected?.id || "";
    payerForm.elements.payer_vat_id.value = selected?.vatId || "";
    payerDialog.showModal();
  }
  document.querySelectorAll("[data-create-payer]").forEach((button) => button.addEventListener("click", () => openPayerDialog()));
  document.querySelectorAll("[data-close-payer]").forEach((button) => button.addEventListener("click", () => payerDialog.close()));
  payerForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(payerForm);
    const values = { name: String(data.get("payer_name")).trim(), id: String(data.get("payer_id")).trim(), vatId: String(data.get("payer_vat_id")).trim() };
    if (editingPayerKey) {
      Object.assign(payers.find((item) => item.key === editingPayerKey), values);
    } else {
      const key = `payer-${Date.now()}`;
      payers.push({ key, ...values });
      activePayerKey = key;
    }
    renderPayers();
    renderRecipient();
    payerDialog.close();
  });

  activePayerSelect.addEventListener("change", () => {
    activePayerKey = activePayerSelect.value;
    renderPayers();
    renderRecipient();
  });

  function payerCard(item, compact = false) {
    const article = document.createElement("article");
    article.className = compact ? "card payer-choice" : "card entity-card payer-record";
    if (item.key === activePayerKey) article.classList.add("selected");
    const avatar = document.createElement("div"); avatar.className = "avatar"; avatar.textContent = item.name.slice(0, 1).toUpperCase();
    const copy = document.createElement("div");
    const title = document.createElement("h2"); title.textContent = item.name;
    const meta = document.createElement("p"); meta.textContent = `Česká republika · IČO ${item.id || "neuvedeno"}${item.vatId ? ` · DIČ ${item.vatId}` : ""}`;
    copy.append(title, meta);
    if (compact) {
      const label = document.createElement("label");
      const radio = document.createElement("input"); radio.type = "radio"; radio.name = "flow-payer"; radio.value = item.key; radio.checked = item.key === activePayerKey;
      radio.addEventListener("change", () => { activePayerKey = item.key; renderPayers(); renderRecipient(); });
      const state = document.createElement("em"); state.textContent = radio.checked ? "Vybráno" : "Vybrat";
      const edit = document.createElement("button"); edit.className = "secondary compact payer-choice-edit"; edit.type = "button"; edit.textContent = "Upravit plátce";
      edit.addEventListener("click", (event) => { event.preventDefault(); event.stopPropagation(); activePayerKey = item.key; renderPayers(); renderRecipient(); openPayerDialog(item.key); });
      label.append(radio, avatar, copy, state); article.append(label, edit);
      return article;
    }
    const details = document.createElement("dl");
    [["Příjemci", "1"], ["Platby", "0"], ["Stav", item.key === activePayerKey ? "Aktivní" : "Připraven"]].forEach(([term, value]) => {
      const group = document.createElement("div"); const dt = document.createElement("dt"); const dd = document.createElement("dd");
      dt.textContent = term; dd.textContent = value; group.append(dt, dd); details.append(group);
    });
    const actions = document.createElement("div"); actions.className = "payer-actions";
    const activate = document.createElement("button"); activate.className = "secondary compact"; activate.type = "button";
    activate.textContent = item.key === activePayerKey ? "Aktivní plátce" : "Nastavit jako aktivního"; activate.disabled = item.key === activePayerKey;
    activate.addEventListener("click", () => { activePayerKey = item.key; renderPayers(); renderRecipient(); });
    const edit = document.createElement("button"); edit.className = "secondary compact"; edit.type = "button"; edit.textContent = "Upravit";
    edit.addEventListener("click", () => openPayerDialog(item.key)); actions.append(activate, edit);
    article.append(avatar, copy, details, actions);
    return article;
  }

  function renderPayers() {
    const selected = activePayer();
    activePayerSelect.replaceChildren();
    payers.forEach((item) => {
      const option = document.createElement("option"); option.value = item.key; option.textContent = item.name; option.selected = item.key === activePayerKey; activePayerSelect.append(option);
    });
    payerList.replaceChildren(...payers.map((item) => payerCard(item)));
    flowPayerList.replaceChildren(...payers.map((item) => payerCard(item, true)));
    document.querySelectorAll("[data-payer-name]").forEach((node) => { node.textContent = selected.name; });
    document.querySelectorAll("[data-payer-avatar]").forEach((node) => { node.textContent = selected.name.slice(0, 1).toUpperCase(); });
    document.querySelectorAll(".dashboard-metrics article:first-child strong").forEach((node) => { node.textContent = String(payers.length); });
  }

  document.querySelectorAll("[data-edit-recipient]").forEach((button) => button.addEventListener("click", (event) => {
    event.stopPropagation();
    const relationship = currentRelationship();
    recipientEditForm.elements.recipient_name.value = recipient.name;
    recipientEditForm.elements.recipient_country.value = recipient.country;
    recipientEditForm.elements.recipient_type.value = recipient.type;
    recipientEditForm.elements.ownership_percent.value = relationship.ownershipPercent;
    recipientEditForm.elements.acquisition_date.value = relationship.acquisitionDate;
    recipientEditForm.elements.direct_ownership.value = relationship.directOwnership;
    recipientEditForm.elements.beneficial_owner.value = String(recipient.beneficialOwner);
    recipientEditForm.elements.treaty_resident.value = String(recipient.treatyResident);
    recipientEditForm.elements.pe_connection.value = String(relationship.peConnection);
    recipientDialog.showModal();
  }));
  document.querySelectorAll("[data-close-recipient]").forEach((button) => button.addEventListener("click", () => recipientDialog.close()));
  recipientEditForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(recipientEditForm);
    recipient = { ...recipient, name: String(data.get("recipient_name")).trim(), country: String(data.get("recipient_country")), type: String(data.get("recipient_type")), beneficialOwner: String(data.get("beneficial_owner")) === "true", treatyResident: String(data.get("treaty_resident")) === "true" };
    Object.assign(currentRelationship(), { ownershipPercent: String(data.get("ownership_percent")), acquisitionDate: String(data.get("acquisition_date")), directOwnership: String(data.get("direct_ownership")), peConnection: String(data.get("pe_connection")) === "true" });
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
    const relationship = currentRelationship();
    const country = countryName(recipient.country);
    const initial = recipient.name.slice(0, 1).toUpperCase();
    document.querySelector("#flow-recipient-name").textContent = recipient.name;
    document.querySelector("#flow-recipient-avatar").textContent = initial;
    document.querySelector("#flow-recipient-meta").textContent = `${country} · ${recipient.type.toLowerCase()} · základní údaje vyplněny`;
    document.querySelectorAll("[data-recipient-name]").forEach((node) => { node.textContent = recipient.name; });
    document.querySelectorAll("[data-recipient-avatar]").forEach((node) => { node.textContent = initial; });
    document.querySelectorAll("[data-recipient-country]").forEach((node) => { node.textContent = countryGenitive(recipient.country); });
    document.querySelectorAll("[data-recipient-country-name]").forEach((node) => { node.textContent = country; });
    document.querySelectorAll("[data-recipient-type]").forEach((node) => { node.textContent = recipient.type.toLowerCase(); });
    document.querySelectorAll("[data-profile-beneficial]").forEach((node) => { node.textContent = recipient.beneficialOwner ? "Ano" : "Ne"; });
    document.querySelectorAll("[data-profile-pe]").forEach((node) => { node.textContent = relationship.peConnection ? "Ano" : "Ne"; });
    document.querySelectorAll("[data-profile-ownership]").forEach((node) => { node.textContent = relationship.ownershipPercent ? `${relationship.ownershipPercent} %` : "Nevyplněno"; });
    document.querySelectorAll("[data-profile-acquisition]").forEach((node) => { node.textContent = relationship.acquisitionDate || "Nevyplněno"; });
    form.elements.beneficial_owner.value = String(recipient.beneficialOwner);
    form.elements.treaty_resident.value = String(recipient.treatyResident);
    form.elements.pe_connection.value = String(relationship.peConnection);
    form.elements.ownership_percent.value = relationship.ownershipPercent;
    form.elements.direct_ownership.value = relationship.directOwnership;
    form.elements.acquisition_date.value = relationship.acquisitionDate;
    form.elements.holding_period_mode.value = relationship.acquisitionDate ? "known_date" : "";
    form.elements.voting_ownership_percent.value = relationship.votingOwnershipPercent || relationship.ownershipPercent;
    votingWasEdited = Boolean(relationship.votingOwnershipPercent);
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

  function cnbSourceUrl(rateDate) {
    const [year, month, day] = rateDate.split("-");
    const query = new URLSearchParams({ date: `${day}.${month}.${year}` });
    return `https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/index.html?${query}`;
  }

  function showFxStatus(copy, kind = "") {
    fxStatus.hidden = false;
    fxStatus.className = `fx-status ${kind}`.trim();
    fxStatus.textContent = copy;
  }

  function syncExchangeRateFromField() {
    const currency = form.elements.currency.value;
    const rateDate = form.elements.transaction_date.value;
    const entered = exchangeRateInput.value;
    if (currency === "CZK" || !rateDate || !entered || Number(entered) <= 0) {
      clientAnswers.exchangeRate = null;
      return null;
    }
    const existing = clientAnswers.exchangeRate;
    const reference = existing?.cnb_reference_czk_per_unit || null;
    const isAutomatic = reference !== null && Math.abs(Number(entered) - Number(reference)) < 1e-12;
    clientAnswers.exchangeRate = {
      source: "CNB",
      currency,
      czk_per_unit: entered,
      effective_date: rateDate,
      source_url: existing?.source_url || cnbSourceUrl(rateDate),
      entry_method: isAutomatic ? "automatic" : "manual_override",
      cnb_reference_czk_per_unit: reference
    };
    if (isAutomatic) {
      showFxStatus(`Kurz ČNB: 1 ${currency} = ${entered} CZK k rozhodnému datu ${formatCzechDate(rateDate)}.`, "success");
    } else {
      const comparison = reference ? ` Automaticky načtený kurz ČNB byl ${reference} CZK.` : "";
      showFxStatus(`Kurz byl pro tuto kontrolu ručně upraven na 1 ${currency} = ${entered} CZK.${comparison} Rozhodné datum je ${formatCzechDate(rateDate)}; zdrojem zůstává kurzovní lístek ČNB.`, "warning");
    }
    return clientAnswers.exchangeRate;
  }

  async function loadCnbRate() {
    const currency = form.elements.currency.value;
    const rateDate = form.elements.transaction_date.value;
    if (currency === "CZK") {
      clientAnswers.exchangeRate = null;
      exchangeRateInput.value = "";
      exchangeRateInput.required = false;
      exchangeRateField.hidden = true;
      fxStatus.hidden = true;
      return null;
    }
    exchangeRateField.hidden = false;
    exchangeRateInput.required = true;
    exchangeRateLabel.textContent = `Kurz v CZK za 1 ${currency}`;
    if (!rateDate) {
      clientAnswers.exchangeRate = null;
      exchangeRateInput.value = "";
      showFxStatus("Kurz ČNB bude načten automaticky po zadání rozhodného data.");
      return null;
    }
    showFxStatus(`Načítá se kurz ČNB pro ${currency} k rozhodnému datu…`);
    try {
      const query = new URLSearchParams({ currency, date: rateDate });
      const response = await fetch(`/exchange-rates/cnb?${query}`);
      const body = await response.json();
      if (!response.ok) throw new Error("Kurz ČNB není dostupný.");
      clientAnswers.exchangeRate = {
        source: "CNB",
        currency,
        czk_per_unit: body.czk_per_unit,
        effective_date: rateDate,
        source_url: body.source_url,
        entry_method: "automatic",
        cnb_reference_czk_per_unit: body.czk_per_unit
      };
      exchangeRateInput.value = body.czk_per_unit;
      const published = body.published_for && body.published_for !== rateDate
        ? ` Použit byl poslední kurz vyhlášený ${formatCzechDate(body.published_for)}.`
        : "";
      showFxStatus(`Kurz načten automaticky z kurzovního lístku ČNB pro rozhodné datum ${formatCzechDate(rateDate)}: 1 ${currency} = ${body.czk_per_unit} CZK.${published}`, "success");
      return clientAnswers.exchangeRate;
    } catch (_problem) {
      clientAnswers.exchangeRate = null;
      exchangeRateInput.value = "";
      showFxStatus("Kurz ČNB se nepodařilo načíst. Po vyhodnocení bude možné zadat kurz ručně; rozhodné datum ani odkaz se znovu zadávat nebudou.", "warning");
      return null;
    }
  }

  form.elements.currency.addEventListener("change", loadCnbRate);
  form.elements.transaction_date.addEventListener("change", loadCnbRate);
  exchangeRateInput.addEventListener("input", syncExchangeRateFromField);

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

  function completeDays(acquisitionDate, transactionDate) {
    const start = new Date(`${acquisitionDate}T00:00:00Z`);
    const end = new Date(`${transactionDate}T00:00:00Z`);
    return Math.max(0, Math.floor((end - start) / 86400000));
  }

  function completeYears(acquisitionDate, transactionDate) {
    const start = new Date(`${acquisitionDate}T00:00:00Z`);
    const end = new Date(`${transactionDate}T00:00:00Z`);
    let years = end.getUTCFullYear() - start.getUTCFullYear();

    if (
      end.getUTCMonth() < start.getUTCMonth() ||
      (
        end.getUTCMonth() === start.getUTCMonth() &&
        end.getUTCDate() < start.getUTCDate()
      )
    ) years -= 1;

    return Math.max(0, years);
  }

  function applyHoldingPeriodFacts(facts, acquisitionDate, transactionDate) {
    if (!acquisitionDate || !transactionDate) return;

    facts.holding_period_months =
      completeMonths(acquisitionDate, transactionDate);

    facts.continuous_holding_period_days =
      completeDays(acquisitionDate, transactionDate);

    facts.holding_period_years =
      completeYears(acquisitionDate, transactionDate);
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
    if (question.response_type === "boolean" || question.response_type === "boolean_rule_value") {
      input = document.createElement("select");

      const values = question.response_type === "boolean_rule_value"
        ? [["", "Vyber odpověď"], ["__yes__", "Ano"], ["__no__", "Ne"]]
        : [["", "Vyber odpověď"], ["true", "Ano"], ["false", "Ne"]];

      values.forEach(([value, label]) => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = label;
        input.append(option);
      });

      if (question.response_type === "boolean_rule_value") {
        input.dataset.trueValue = JSON.stringify(question.true_value);
        input.dataset.falseValue = JSON.stringify(question.false_value);
      }
    } else if (question.response_type === "choice") {
      input = document.createElement("select");
      [["", "Vyber možnost"], ...(question.options || [])].forEach(([value, label]) => {
        const option = document.createElement("option"); option.value = value; option.textContent = label; input.append(option);
      });
    } else if (question.response_type === "structured_cnb_rate") {
      const wrapper = document.createElement("div");
      wrapper.className = "structured-answer";
      const child = document.createElement("input"); child.name = "czk_per_unit"; child.type = "number"; child.required = true; child.placeholder = "CZK za 1 jednotku měny"; child.min = "0.000001"; child.step = "0.000001";
      const note = document.createElement("small"); note.textContent = "Rozhodné datum bylo převzato ze zadání. Odkaz na odpovídající kurzovní lístek ČNB doplní TaxTreat automaticky.";
      wrapper.append(child, note);
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
        clientAnswers.exchangeRate = { source: "CNB", currency: payload.transaction_amount.currency, czk_per_unit: input.querySelector('[name="czk_per_unit"]').value, effective_date: rateDate, source_url: cnbSourceUrl(rateDate) };
      } else if (path === "derived.acquisition_date") {
        clientAnswers.acquisitionDate = input.value;
      } else if (path && path.startsWith("facts.")) {
        const name = path.slice(6);

        if (input.dataset.responseType === "boolean_rule_value") {
          const encoded = input.value === "__yes__"
            ? input.dataset.trueValue
            : input.dataset.falseValue;

          clientAnswers.facts[name] = JSON.parse(encoded);

        } else if (input.dataset.responseType === "boolean") {
          clientAnswers.facts[name] = input.value === "true";

        } else if (
          ["decimal_percent", "number"].includes(
            input.dataset.responseType
          )
        ) {
          clientAnswers.facts[name] = Number(input.value);

        } else {
          clientAnswers.facts[name] = input.value;
        }
      }
    });

    Object.assign(
      payload.facts,
      clientAnswers.facts,
    );

    if (clientAnswers.acquisitionDate) {
      applyHoldingPeriodFacts(
        payload.facts,
        clientAnswers.acquisitionDate,
        payload.transaction_date,
      );
    }
    if (clientAnswers.exchangeRate) payload.transaction_amount.exchange_rate = { ...clientAnswers.exchangeRate, currency: payload.transaction_amount.currency };
  }

  function professionalTitle(question) {
    return {
      recipient_eligibility: "Podmínky případného osvobození",
      future_holding_period: "Dodatečné splnění doby držby",
      domestic_exemption: "Podmínky vnitrostátního osvobození",
      interest_treaty_special_condition: "Zvláštní smluvní podmínka úroku",
      royalty_treaty_legal_condition: "Zvláštní smluvní podmínka licenční platby"
    }[question.advisor_topic] || "Podmínka vyžadující odborné posouzení";
  }

  function actionItem(question) {
    const node = document.createElement("div"); node.className = "action-item adviser";
    const strong = document.createElement("strong"); strong.textContent = question.prompt || professionalTitle(question);
    const detail = document.createElement("small"); detail.textContent = question.why || "Podmínku nelze uzavřít pouze ze zadaných údajů.";
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

  function concreteReviewItems(analysis, payload, professional, reviewReasons = []) {
    const items = reviewReasons.length
      ? reviewReasons.map((reason) => reviewItem(reason.title, reason.detail))
      : professional.map((question) => actionItem(question));
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

  function selectedCitation(analysis) {
    const selected = selectedRuleId(analysis);
    return (analysis.citations || []).find((citation) => String(citation.rule_id || "") === selected) || null;
  }

  function provisionLabel(citation) {
    if (!citation) return "příslušného ustanovení";
    const article = citation.article ? `článku ${citation.article}` : "příslušného ustanovení";
    return citation.paragraph ? `${article}, ${citation.paragraph}` : article;
  }

  function legalProvisionLabel(citation) {
    if (!citation) return "příslušného ustanovení";
    const layer = String(citation.legal_layer || "");
    const provision = ["domestic", "eu_relief"].includes(layer)
      ? `§ ${citation.article || "—"}`
      : `článku ${citation.article || "—"}`;
    return citation.paragraph ? `${provision}, ${citation.paragraph}` : provision;
  }

  function resultExplanation(analysis, payload) {
    const citation = selectedCitation(analysis);
    const layer = String(citation?.legal_layer || "");
    const treatment = analysis.tax_treatment || analysis.candidate_tax_treatment;
    if (analysis.status === "FINAL" && treatment === "exclusive_foreign_taxation") return `Podle ${legalProvisionLabel(citation)} příslušné smlouvy může být příjem zdaněn pouze ve státě daňové rezidence příjemce. V České republice proto nevzniká srážková daň; česká daň k odvodu činí 0 Kč.`;
    if (analysis.status === "FINAL" && treatment === "domestic_exemption") return `Příjem je v České republice osvobozen podle ${legalProvisionLabel(citation)} zákona č. 586/1992 Sb., o daních z příjmů. Česká daň k odvodu proto činí 0 Kč.`;
    if (analysis.status === "FINAL" && layer === "eu_relief") return `Příjem je v České republice osvobozen podle ${legalProvisionLabel(citation)} zákona č. 586/1992 Sb., o daních z příjmů; všechny podmínky vybraného pravidla byly splněny zadanými a ověřenými údaji.`;
    if (analysis.status === "FINAL" && ["treaty", "protocol", "mli"].includes(layer)) return `Česká srážková daň je ${analysis.rate} %. Výsledek vychází z ${provisionLabel(citation)} příslušné smlouvy ve znění použitelných změn. Rozhodující byly podmínky konkrétního pravidla uvedené v právních podkladech.`;
    if (analysis.status === "FINAL" && layer === "domestic") return `Česká srážková daň je ${analysis.rate} %. Výsledek vychází z ${legalProvisionLabel(citation)} zákona č. 586/1992 Sb., o daních z příjmů, protože nebylo použito pravidlo s nižší sazbou.`;
    if (analysis.status === "FINAL") return `Použitá sazba ${analysis.rate} % byla určena na základě zadaných údajů a vybraného právního pravidla uvedeného níže.`;
    if (treatment === "exclusive_foreign_taxation") return "Zadané údaje směřují k použití smluvního pravidla, podle něhož se příjem zdaňuje pouze ve státě rezidence příjemce. Před uzavřením výsledku je třeba ověřit konkrétní podmínky uvedené níže.";
    if (treatment === "domestic_exemption") return "Zadané údaje směřují k osvobození příjmu v České republice. Před uzavřením výsledku je třeba ověřit konkrétní podmínky uvedené níže.";
    if (analysis.candidate_rate !== null && analysis.candidate_rate !== undefined) return `Byla identifikována sazba ${analysis.candidate_rate} %. Její použití závisí na odborném ověření právních podmínek uvedených níže.`;
    return "Sazbu zatím nelze určit. Konkrétní důvod je uveden v části Odborné ověření níže.";
  }

  function citationDetail(citation) {
    const rate = citation.rate === null || citation.rate === undefined ? null : `${citation.rate} %`;
    const ownership = (citation.conditions || []).find((condition) => ["minimum_ownership", "ownership_percent", "direct_or_indirect_voting_ownership"].includes(condition.fact) && condition.operator === ">=");
    if (citation.tax_treatment === "exclusive_foreign_taxation") return "Smluvní pravidlo přiznává právo zdanit příjem pouze státu daňové rezidence příjemce.";
    if (citation.tax_treatment === "domestic_exemption") return "Vnitrostátní pravidlo stanoví osvobození příjmu při splnění všech kvalifikačních podmínek.";
    if (["treaty", "protocol", "mli"].includes(citation.legal_layer)) return ownership ? `Pravidlo stanoví sazbu ${rate} při podílu alespoň ${ownership.value} % a při splnění ostatních uvedených podmínek.` : `Pravidlo příslušné smlouvy stanoví sazbu ${rate} při splnění jeho podmínek.`;
    if (citation.legal_layer === "eu_relief") return "Pravidlo vnitrostátního osvobození se použije při splnění všech kvalifikačních podmínek.";
    if (citation.legal_layer === "domestic") return `Vnitrostátní pravidlo stanoví sazbu ${rate}.`;
    return "Právní ustanovení použité při výpočtu.";
  }

  function excerptHasBrokenEncoding(excerpt) {
    return /[õÕ]|\b(spolecnost|smluvnõ|prõjem|skutecný|zdaneny|clánku|predpisu|vlastnõk)\b/i.test(String(excerpt || ""));
  }

  function displayLegalExcerpt(citation) {
    const officialText = String(citation.official_text || "").trim();
    if (officialText) return officialText;
    const excerpt = String(citation.excerpt || "").trim();
    if (excerpt) return excerpt;
    return "Pro toto pravidlo není v právním datasetu uložen text ustanovení.";
  }

  function citationRole(citation, selected, position) {
    const layer = String(citation.legal_layer || "");
    if (layer === "domestic") return `${position}. Výchozí vnitrostátní pravidlo`;
    if (["treaty", "protocol", "mli"].includes(layer)) {
      return `${position}. ${selected ? "Použité smluvní pravidlo" : "Smluvní pravidlo"}`;
    }
    if (layer === "eu_relief") {
      return `${position}. ${selected ? "Použité osvobození" : "Pravidlo osvobození"}`;
    }
    return `${position}. ${selected ? "Použité pravidlo" : "Související právní pravidlo"}`;
  }

  function citationCard(citation, analysis, position) {
    const card = document.createElement("article"); card.className = "citation-card";
    const selected = String(citation.rule_id || "") === selectedRuleId(analysis);
    const title = document.createElement("strong");
    const layer = String(citation.legal_layer || "");
    if (!selected) card.classList.add("context");
    const role = document.createElement("span"); role.className = "citation-role";
    role.textContent = citationRole(citation, selected, position);
    const paragraph = citation.paragraph ? ` · ${citation.paragraph}` : "";
    title.textContent = ["treaty", "protocol", "mli"].includes(layer) ? `Smlouva o zamezení dvojího zdanění · článek ${citation.article || "—"}${paragraph}` : `Zákon č. 586/1992 Sb., o daních z příjmů · § ${citation.article || "—"}${paragraph}`;
    const link = document.createElement("a"); link.href = citation.source_url; link.target = "_blank"; link.rel = "noreferrer noopener"; link.textContent = "Otevřít zdroj ↗";
    const detail = document.createElement("p");
    detail.textContent = !selected && layer === "domestic"
      ? `Výchozí vnitrostátní sazba činí ${citation.rate} %. V následujícím kroku je zohledněno pravidlo, které tuto sazbu omezuje nebo nahrazuje.`
      : citationDetail(citation);
    card.append(role, title, link, detail);
    if ((citation.official_text || citation.excerpt) && layer !== "domestic") {
      const disclosure = document.createElement("details"); disclosure.className = "citation-excerpt"; disclosure.open = true;
      const summary = document.createElement("summary"); summary.textContent = citation.official_text ? "Znění použitého ustanovení" : "Evidované znění použitého ustanovení";
      const excerpt = document.createElement("blockquote"); excerpt.textContent = displayLegalExcerpt(citation);
      disclosure.append(summary, excerpt); card.append(disclosure);
    }
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
    const nonTaxing = ["exclusive_foreign_taxation", "domestic_exemption"].includes(analysis.tax_treatment);
    setText("#workspace-remittance-deadline", schedule.tax_remittance_deadline ? formatCzechDate(schedule.tax_remittance_deadline) : analysis.status === "FINAL" && nonTaxing ? "Daň se neodvádí" : "Po dokončení posouzení");
    setText("#workspace-notification-deadline", schedule.notification_deadline ? formatCzechDate(schedule.notification_deadline) : schedule.notification_required === false ? "Oznámení se nepodává" : "Po dokončení posouzení");
    const note = document.querySelector("#workspace-deadline-note");
    if (schedule.status !== "READY") note.textContent = "Lhůty nelze uzavřít, dokud není určeno konečné daňové zacházení nebo měsíční úhrn rozhodný pro oznamovací povinnost.";
    else if (schedule.notification_regime === "exempt_or_treaty_non_taxable_annual") note.textContent = "Česká daň se při tomto daňovém zacházení neodvádí. Oznámení podle § 38da zákona č. 586/1992 Sb., o daních z příjmů se u dividend a licenčních poplatků podává do 31. ledna následujícího roku.";
    else if (schedule.notification_regime === "non_taxing_interest_above_monthly_threshold_annual") note.textContent = `Česká daň se neodvádí. Měsíční úhrn úroků stejného druhu činí ${money(schedule.monthly_same_type_income_czk)} a přesáhl 300 000 Kč; oznámení podle § 38da zákona č. 586/1992 Sb., o daních z příjmů se podává do uvedeného data.`;
    else if (schedule.notification_regime === "non_taxing_interest_monthly_threshold_not_exceeded") note.textContent = `Česká daň se neodvádí. Měsíční úhrn úroků stejného druhu činí ${money(schedule.monthly_same_type_income_czk)} a nepřesáhl 300 000 Kč; oznamovací povinnost podle § 38da zákona č. 586/1992 Sb., o daních z příjmů proto nevzniká.`;
    else note.textContent = "Odvod sražené daně a oznámení o příjmu plynoucím do zahraničí mají shodnou lhůtu: konec následujícího kalendářního měsíce.";
    const caution = document.querySelector("#workspace-dividend-deadline-caution");
    caution.hidden = !schedule.dividend_timing_review_required;
  }

  function decisiveCitations(analysis) {
    const selected = selectedRuleId(analysis);
    const citations = [...(analysis.legal_path || analysis.citations || [])];
    const layerOrder = { domestic: 0, treaty: 1, protocol: 2, mli: 3, eu_relief: 4 };
    citations.sort((left, right) => {
      const layerDifference = (layerOrder[left.legal_layer] ?? 9) - (layerOrder[right.legal_layer] ?? 9);
      if (layerDifference) return layerDifference;
      return Number(String(right.rule_id || "") === selected) - Number(String(left.rule_id || "") === selected);
    });
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
    const reviewReasons = response.intake?.review_reasons || [];
    const reviewItems = concreteReviewItems(analysis, payload, professional, reviewReasons);
    const status = document.querySelector("#workspace-result-status");
    status.textContent = analysis.status === "FINAL" ? "VÝSLEDEK DOKONČEN" : "ODBORNÉ OVĚŘENÍ";
    status.className = analysis.status === "FINAL" ? "badge" : "badge warning";
    const grossCzk = calculationValue(calculation, "gross_amount_czk", "tax_base_czk");
    const taxCzk = calculationValue(calculation, "withholding_tax_czk", "withholding_tax_czk");
    const netCzk = calculationValue(calculation, "net_amount_czk", "net_amount_czk");
    const treatment = analysis.tax_treatment || analysis.candidate_tax_treatment;
    const nonTaxing = ["exclusive_foreign_taxation", "domestic_exemption"].includes(treatment);
    setText("#workspace-tax-label", nonTaxing ? "Česká daň k odvodu" : "Srážková daň v CZK");
    setText("#workspace-tax-row-label", nonTaxing ? "Česká daň k odvodu" : "Srážková daň");
    setText("#workspace-tax", calculation ? money(taxCzk) : "—");
    setText("#workspace-rate", treatment === "exclusive_foreign_taxation" ? `Zdanění pouze ve státě rezidence příjemce (${countryNames[recipient.country]})` : treatment === "domestic_exemption" ? "Příjem je v České republice osvobozen" : analysis.rate === null ? analysis.candidate_rate === null ? "Sazbu nelze určit bez odborného posouzení" : `Identifikovaná sazba: ${analysis.candidate_rate} %` : `${analysis.rate} % z daňového základu`);
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
    decisiveCitations(analysis).forEach((citation, index) => citations.append(citationCard(citation, analysis, index + 1)));
    if (!citations.children.length) { const p = document.createElement("p"); p.textContent = "Pro tento výsledek nebyl vrácen konkrétní odkaz na právní zdroj."; citations.append(p); }
    renderComplianceSchedule(analysis);
    showStep(4);
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
      right_or_property_not_effectively_connected_to_czech_pe_or_fixed_base: String(data.get("pe_connection")) !== "true",
      claim_not_effectively_connected_to_czech_pe: String(data.get("pe_connection")) !== "true",
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
    Object.assign(currentRelationship(), {
      peConnection: String(data.get("pe_connection")) === "true",
      ownershipPercent,
      directOwnership,
      acquisitionDate,
      votingOwnershipPercent: votingOwnership
    });
    if (incomeType === "dividend") {
      if (ownershipPercent) facts.ownership_percent = Number(ownershipPercent);
      if (directOwnership) facts.direct_ownership = directOwnership === "true";
      if (votingOwnership) {
        const votingPercent = Number(votingOwnership);

        facts.direct_or_indirect_voting_ownership =
          votingPercent;

        facts.voting_ownership =
          votingPercent;

        facts.voting_power_control =
          votingPercent;
      }

      if (
        holdingPeriodMode === "known_date" &&
        acquisitionDate
      ) {
        applyHoldingPeriodFacts(
          facts,
          acquisitionDate,
          transactionDate,
        );
      }
      if (holdingPeriodMode === "at_least_12_months") facts.holding_period_months = 12;
      if (holdingPeriodMode === "less_than_12_months") facts.holding_period_months = 0;
    }
    if (incomeType === "interest" && armLengthAmount) facts.arm_length_amount = armLengthAmount === "true";
    if (incomeType === "royalty" && royaltyCategory) facts.royalty_category = royaltyCategory;
    if (String(data.get("currency")) !== "CZK") {
      const currentRate = clientAnswers.exchangeRate;
      if (!currentRate || currentRate.currency !== String(data.get("currency")) || currentRate.effective_date !== transactionDate) await loadCnbRate();
      syncExchangeRateFromField();
    }
    const payload = {
      source_country: "CZ", recipient_country: recipient.country, income_type: incomeType, transaction_date: transactionDate,
      facts, determinations: {}, transaction_amount: { amount: String(data.get("amount")), currency: String(data.get("currency")), payment_date: transactionDate, accounting_date: transactionDate }
    };
    if (incomeType === "interest") payload.transaction_amount.prior_same_type_monthly_amount_czk = String(data.get("prior_same_type_monthly_amount_czk") || "0");
    if (clientAnswers.exchangeRate) payload.transaction_amount.exchange_rate = { ...clientAnswers.exchangeRate };
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

  renderPayers();
  renderRecipient();
  loadJurisdictionCatalog();
  renderTransactionFacts();
  checkForNewBuild();
})();
