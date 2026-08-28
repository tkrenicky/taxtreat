(() => {
  const routeDesign = window.location.pathname.split("/").filter(Boolean).at(-1);
  const design = ["editorial", "atlas", "civic"].includes(routeDesign)
    ? routeDesign
    : new URLSearchParams(window.location.search).get("design");
  if (["editorial", "atlas", "civic"].includes(design)) {
    document.body.dataset.design = design;
    const switcher = document.querySelector("#design-switcher");
    if (switcher) {
      switcher.hidden = false;
      switcher.querySelector(`[data-design-link="${design}"]`)?.classList.add("active");
    }
  }
  "use strict";

  const BUILD_VERSION = "20260819-3";

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
    { key: "demo-cz", name: "Demo CZ s.r.o.", id: "12345678", vatId: "CZ12345678", address: "", legalForm: "", dataBox: "", establishedAt: "" },
    { key: "alfa-cz", name: "Alfa Services CZ a.s.", id: "87654321", vatId: "CZ87654321", address: "", legalForm: "", dataBox: "", establishedAt: "" }
  ];
  let activePayerKey = "demo-cz";
  const PROFILE_STORAGE_KEY = "taxtreat-workspace-profiles-v1";

  function saveWorkspaceProfiles() {
    try {
      localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify({
        payers,
        activePayerKey,
        recipient
      }));
    } catch (_problem) {
      // Profile persistence is a convenience layer; calculation must keep working.
    }
  }

  function restoreWorkspaceProfiles() {
    try {
      const raw = localStorage.getItem(PROFILE_STORAGE_KEY);
      if (!raw) return;
      const stored = JSON.parse(raw);
      if (Array.isArray(stored?.payers) && stored.payers.length) {
        payers = stored.payers.filter((item) => item && item.key && item.name);
      }
      if (stored?.recipient && typeof stored.recipient === "object") {
        recipient = {
          ...recipient,
          ...stored.recipient,
          relationships: {
            ...(recipient.relationships || {}),
            ...(stored.recipient.relationships || {})
          }
        };
      }
      if (stored?.activePayerKey && payers.some((item) => item.key === stored.activePayerKey)) {
        activePayerKey = stored.activePayerKey;
      } else if (!payers.some((item) => item.key === activePayerKey)) {
        activePayerKey = payers[0]?.key || "demo-cz";
      }
    } catch (_problem) {
      // Ignore malformed/stale browser storage and retain safe demo defaults.
    }
  }

  restoreWorkspaceProfiles();

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
    payerForm.elements.payer_address.value = selected?.address || "";
    payerForm.elements.payer_legal_form.value = selected?.legalForm || "";
    payerForm.elements.payer_data_box.value = selected?.dataBox || "";
    payerForm.elements.payer_established_at.value = selected?.establishedAt || "";
    document.querySelector("#ares-lookup-status").className = "lookup-status";
    document.querySelector("#ares-lookup-status").textContent = "Po zadání 8 číslic TaxTreat načte identifikační údaje z ARES.";
    payerDialog.showModal();
  }
  document.querySelectorAll("[data-create-payer]").forEach((button) => button.addEventListener("click", () => openPayerDialog()));
  document.querySelectorAll("[data-close-payer]").forEach((button) => button.addEventListener("click", () => payerDialog.close()));

  let aresLookupTimer = null;
  async function lookupPayerFromAres() {
    const ico = String(payerForm.elements.payer_id.value || "").replace(/\D/g, "");
    const status = document.querySelector("#ares-lookup-status");
    if (ico.length !== 8) {
      status.className = "lookup-status error";
      status.textContent = "IČO musí obsahovat přesně 8 číslic.";
      return;
    }
    status.className = "lookup-status";
    status.textContent = "Načítám údaje z ARES…";
    try {
      const response = await fetch(`/company-registry/ares/${ico}`, { cache: "no-store" });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail?.message || "ARES lookup failed");
      payerForm.elements.payer_id.value = body.ico || ico;
      payerForm.elements.payer_name.value = body.name || payerForm.elements.payer_name.value;
      payerForm.elements.payer_vat_id.value = body.vat_id || payerForm.elements.payer_vat_id.value;
      payerForm.elements.payer_address.value = body.address || "";
      payerForm.elements.payer_legal_form.value = body.legal_form || "";
      payerForm.elements.payer_data_box.value = body.data_box || "";
      payerForm.elements.payer_established_at.value = body.established_at || "";
      status.className = "lookup-status success";
      status.textContent = "Údaje byly načteny z ARES. Před uložením je můžeš upravit.";
    } catch (_problem) {
      status.className = "lookup-status error";
      status.textContent = "Údaje se z ARES nepodařilo načíst. Pole můžeš vyplnit ručně.";
    }
  }
  document.querySelector("[data-ares-lookup]").addEventListener("click", lookupPayerFromAres);
  payerForm.elements.payer_id.addEventListener("input", () => {
    window.clearTimeout(aresLookupTimer);
    const ico = String(payerForm.elements.payer_id.value || "").replace(/\D/g, "");
    if (ico.length === 8) aresLookupTimer = window.setTimeout(lookupPayerFromAres, 450);
  });

  function savePayerProfile() {
    window.clearTimeout(aresLookupTimer);
    if (!payerForm.reportValidity()) return false;
    const data = new FormData(payerForm);
    const values = {
      name: String(data.get("payer_name")).trim(),
      id: String(data.get("payer_id")).trim(),
      vatId: String(data.get("payer_vat_id")).trim(),
      address: String(data.get("payer_address")).trim(),
      legalForm: String(data.get("payer_legal_form")).trim(),
      dataBox: String(data.get("payer_data_box")).trim(),
      establishedAt: String(data.get("payer_established_at")).trim()
    };
    if (editingPayerKey) {
      const existing = payers.find((item) => item.key === editingPayerKey);
      if (existing) Object.assign(existing, values);
    } else {
      const key = `payer-${Date.now()}`;
      payers.push({ key, ...values });
      activePayerKey = key;
    }
    saveWorkspaceProfiles();
    renderPayers();
    renderRecipient();
    if (payerDialog.open) payerDialog.close();
    return true;
  }

  payerForm.addEventListener("submit", (event) => {
    event.preventDefault();
    event.stopPropagation();
    window.setTimeout(savePayerProfile, 0);
  });
  document.querySelector("[data-save-payer]").addEventListener("click", (event) => {
    event.preventDefault();
    event.stopImmediatePropagation();
    window.setTimeout(savePayerProfile, 0);
  });

  function switchActivePayer(key) {
    if (!payers.some((item) => item.key === key)) return;
    activePayerKey = key;
    saveWorkspaceProfiles();
    renderPayers();
    renderRecipient();
  }

  activePayerSelect.addEventListener("change", () => {
    switchActivePayer(activePayerSelect.value);
  });

  document.addEventListener("change", (event) => {
    if (event.target?.id === "active-payer-select") {
      switchActivePayer(event.target.value);
    }
  }, true);

  function payerCard(item, compact = false) {
    const article = document.createElement("article");
    article.className = compact ? "card payer-choice" : "card entity-card payer-record";
    if (item.key === activePayerKey) article.classList.add("selected");
    const avatar = document.createElement("div"); avatar.className = "avatar"; avatar.textContent = item.name.slice(0, 1).toUpperCase();
    const copy = document.createElement("div");
    const title = document.createElement("h2"); title.textContent = item.name;
    const meta = document.createElement("p"); meta.textContent = `Česká republika · IČO ${item.id || "neuvedeno"}${item.vatId ? ` · DIČ ${item.vatId}` : ""}${item.address ? ` · ${item.address}` : ""}`;
    copy.append(title, meta);
    if (compact) {
      const label = document.createElement("label");
      const radio = document.createElement("input"); radio.type = "radio"; radio.name = "flow-payer"; radio.value = item.key; radio.checked = item.key === activePayerKey;
      radio.addEventListener("change", () => switchActivePayer(item.key));
      const state = document.createElement("em"); state.textContent = radio.checked ? "Vybráno" : "Vybrat";
      const edit = document.createElement("button"); edit.className = "secondary compact payer-choice-edit"; edit.type = "button"; edit.textContent = "Upravit plátce";
      edit.addEventListener("click", (event) => { event.preventDefault(); event.stopPropagation(); switchActivePayer(item.key); openPayerDialog(item.key); });
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
    activate.addEventListener("click", () => switchActivePayer(item.key));
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
    saveWorkspaceProfiles();
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
    saveWorkspaceProfiles();
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
      showFxStatus("Kurz ČNB se nepodařilo načíst. Po doplnění údajů bude možné zadat kurz ručně; rozhodné datum ani odkaz se znovu zadávat nebudou.", "warning");
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

  function setText(selector, value) {
    const element = document.querySelector(selector);
    if (!element) {
      const seen = window.__taxtreatMissingRuntimeIds || (window.__taxtreatMissingRuntimeIds = []);
      if (!seen.includes(selector)) {
        seen.push(selector);
        console.warn(`[TaxTreat] Missing runtime element ${selector}; the Step 4 result card was likely rewritten by a UI overlay.`);
      }
      return;
    }
    element.textContent = value;
  }

  function ensureRuntimeResultAnchors() {
    const step4 = document.querySelector('.flow-step[data-step="4"]');
    if (!step4) return;

    const ensure = (id, tag, parent) => {
      let element = document.getElementById(id);
      if (!element) {
        element = document.createElement(tag);
        element.id = id;
        parent.append(element);
      }
      return element;
    };

    const hero = step4.querySelector(".result-hero");
    if (hero) {
      ensure("workspace-result-status", "span", hero);
      ensure("workspace-tax-label", "p", hero);
      ensure("workspace-tax", "strong", hero);
      ensure("workspace-rate", "small", hero);
    }

    const reason = step4.querySelector(".reason");
    if (reason) ensure("workspace-reason", "p", reason);

    const summary = step4.querySelector(".summary") || step4.querySelector("article.summary") || step4.querySelector(".card.summary");
    if (summary) {
      const list = summary.querySelector("dl") || summary;
      if (!summary.querySelector("#workspace-gross")) ensure("workspace-gross", "dd", list);
      if (!summary.querySelector("#workspace-tax-row-label")) ensure("workspace-tax-row-label", "dt", list);
      if (!summary.querySelector("#workspace-tax-row")) ensure("workspace-tax-row", "dd", list);
      if (!summary.querySelector("#workspace-net")) ensure("workspace-net", "dd", list);
    }

    const actionsBlock = step4.querySelector("#workspace-actions") || step4.querySelector(".action-list");
    if (actionsBlock) {
      actionsBlock.id = actionsBlock.id || "workspace-actions";
      if (!actionsBlock.querySelector("#workspace-action-count")) {
        const count = document.createElement("span");
        count.id = "workspace-action-count";
        count.hidden = true;
        actionsBlock.parentElement?.querySelector(".card-head")?.append(count);
      }
    } else {
      const card = step4.querySelector(".card") || step4;
      if (!document.getElementById("workspace-actions")) {
        const actions = document.createElement("div");
        actions.id = "workspace-actions";
        card.append(actions);
      }
    }

    const sources = step4.querySelector(".result-sources") || step4.querySelector(".card.result-sources");
    if (sources) {
      if (!document.getElementById("workspace-citations")) {
        const citations = document.createElement("div");
        citations.id = "workspace-citations";
        citations.className = "citation-list";
        sources.append(citations);
      }
    }
  }

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
    setText("#workspace-submit", "Zobrazit pravidla a výpočet →");
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
    setText("#workspace-submit", pendingQuestions.length ? "Doplnit údaje a aktualizovat výpočet →" : "Zobrazit pravidla a výpočet →");
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
    if (analysis.candidate_rate !== null && analysis.candidate_rate !== undefined) return `Byla identifikována sazba ${analysis.candidate_rate} %. Její použití závisí na splnění právních a skutkových podmínek uvedených níže.`;
    return "Sazbu zatím nelze určit. Konkrétní důvod je uveden v části Podmínky a další kroky níže.";
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

  function decisiveLegalParagraph(fullText, citation) {
    const text = String(fullText || "")
      .replace(/\r/g, "")
      .trim();

    if (!text) return "";

    const reference = String(citation.paragraph || "").trim();
    const numberMatch = reference.match(
      /(?:odst(?:avec)?\.?\s*)?(\d+)/i
    );
    const paragraphNumber = numberMatch?.[1] || "";

    let candidate = text;

    if (paragraphNumber) {
      const escapedNumber = paragraphNumber.replace(
        /[.*+?^${}()|[\]\\]/g,
        "\\$&"
      );

      const startPattern = new RegExp(
        `(?:^|\\n)\\s*(?:\\(${escapedNumber}\\)|${escapedNumber}[.)])\\s+`,
        "m"
      );

      const match = startPattern.exec(text);

      if (match) {
        const contentStart = match.index + match[0].length;
        const tail = text.slice(contentStart);

        const next = /(?:^|\n)\s*(?:\(\d+\)|\d+[.)])\s+/m;
        const nextMatch = next.exec(tail);

        const paragraph = (
          nextMatch
            ? text.slice(match.index, contentStart + nextMatch.index)
            : text.slice(match.index)
        ).trim();

        if (paragraph) candidate = paragraph;
      }
    }

    // For rate rules, identify the precise clause containing
    // the selected rate. This mirrors the report's emphasis
    // on the operative percentage instead of marking the whole article.
    if (
      citation.rate !== null &&
      citation.rate !== undefined &&
      citation.rate !== ""
    ) {
      const numericRate = String(citation.rate)
        .replace(".", "[.,]");

      const ratePattern = new RegExp(
        `(?:^|[^0-9])${numericRate}\\s*(?:%|percent|per cent|procent)`,
        "i"
      );

      const clauses = candidate
        .split(/(?<=;)|(?<=\.)\s+(?=[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ0-9(])/)
        .map((item) => item.trim())
        .filter(Boolean);

      const rateClause = clauses.find(
        (item) => ratePattern.test(item)
      );

      if (
        rateClause &&
        rateClause.length < text.length * 0.9
      ) {
        return rateClause;
      }
    }

    const treatment = String(citation.tax_treatment || "");

    if (treatment === "exclusive_foreign_taxation") {
      const clauses = candidate
        .split(/(?<=\.)\s+/)
        .map((item) => item.trim())
        .filter(Boolean);

      const exclusive = clauses.find(
        (item) =>
          /\b(?:only|pouze|jen)\b/i.test(item) &&
          /tax|zdan/i.test(item)
      );

      if (exclusive && exclusive.length < text.length * 0.9) {
        return exclusive;
      }
    }

    if (
      candidate &&
      candidate !== text &&
      candidate.length < text.length * 0.9
    ) {
      return candidate;
    }

    const excerpt = String(citation.excerpt || "").trim();

    if (
      excerpt &&
      text.includes(excerpt) &&
      excerpt.length < text.length * 0.72
    ) {
      return excerpt;
    }

    return "";
  }

  function citationRole(citation, selected, position, analysis) {
    const layer = String(citation.legal_layer || "");
    const en = document.documentElement.lang === "en";
    const role = String(citation.path_role || "");
    const domesticExemptionSelected = (analysis?.tax_treatment || analysis?.candidate_tax_treatment) === "domestic_exemption";
    if (role === "domestic_exemption_basis") {
      return `${position}. ${en ? "APPLIED DOMESTIC EXEMPTION" : "POUŽITÉ VNITROSTÁTNÍ OSVOBOZENÍ"}`;
    }
    if (role === "domestic_starting_point") {
      return `${position}. ${en ? "GENERAL DOMESTIC RATE WITHOUT EXEMPTION" : "OBECNÁ VNITROSTÁTNÍ SAZBA BEZ OSVOBOZENÍ"}`;
    }
    if (layer === "domestic") return `${position}. ${en ? "DOMESTIC RULE" : "VNITROSTÁTNÍ PRAVIDLO"}`;
    if (["treaty", "protocol", "mli"].includes(layer)) {
      if (domesticExemptionSelected && !selected) {
        return `${position}. ${en ? "SECONDARY TREATY PROTECTION" : "SEKUNDÁRNÍ SMLUVNÍ OCHRANA"}`;
      }
      return `${position}. ${en ? (selected ? "APPLIED TREATY RULE" : "TREATY RULE") : (selected ? "POUŽITÉ SMLUVNÍ PRAVIDLO" : "SMLUVNÍ PRAVIDLO")}`;
    }
    if (layer === "eu_relief") {
      return `${position}. ${en ? (selected ? "APPLIED EXEMPTION" : "EXEMPTION RULE") : (selected ? "POUŽITÉ OSVOBOZENÍ" : "PRAVIDLO OSVOBOZENÍ")}`;
    }
    return `${position}. ${en ? (selected ? "APPLIED RULE" : "RELATED LEGAL RULE") : (selected ? "POUŽITÉ PRAVIDLO" : "SOUVISEJÍCÍ PRÁVNÍ PRAVIDLO")}`;
  }

  function citationParagraphLabel(value) {
    const raw = String(value || "").trim();
    if (!raw) return "";
    if (document.documentElement.lang === "en") {
      return raw
        .replace(/^odst\.\s*/i, "paragraph ")
        .replace(/^písm\.\s*/i, "point ");
    }
    return raw;
  }

  function citationCard(citation, analysis, position) {
    const card = document.createElement("article"); card.className = "citation-card";
    const selected = String(citation.rule_id || "") === selectedRuleId(analysis);
    const title = document.createElement("strong");
    const layer = String(citation.legal_layer || "");
    if (!selected) card.classList.add("context");
    const role = document.createElement("span"); role.className = "citation-role";
    role.textContent = citationRole(citation, selected, position, analysis);
    const pathRole = String(citation.path_role || "");
    const paragraph = citation.paragraph && pathRole !== "domestic_exemption_basis"
      ? ` · ${citationParagraphLabel(citation.paragraph)}`
      : "";
    const en = document.documentElement.lang === "en";
    title.textContent = ["treaty", "protocol", "mli"].includes(layer)
      ? `${en ? "Double Tax Treaty" : "Smlouva o zamezení dvojího zdanění"} · ${en ? "Article" : "článek"} ${citation.article || "—"}${paragraph}`
      : `${en ? "Czech Income Taxes Act (Act No. 586/1992 Coll.)" : "Zákon č. 586/1992 Sb., o daních z příjmů"} · § ${citation.article || "—"}${paragraph}`;
    const link = document.createElement("a"); link.href = citation.source_url; link.target = "_blank"; link.rel = "noreferrer noopener"; link.textContent = en ? "Open source ↗" : "Otevřít zdroj ↗";
    const detail = document.createElement("p");
    if (pathRole === "domestic_exemption_basis") {
      detail.textContent = en
        ? "The domestic exemption is the primary legal basis for this result."
        : "Vnitrostátní osvobození je primárním právním titulem tohoto výsledku.";
    } else if (pathRole === "domestic_starting_point") {
      detail.textContent = en
        ? "Without an applicable exemption or treaty limitation, the Czech domestic withholding tax rate is 15%."
        : "Pokud se neuplatní osvobození ani smluvní omezení, česká vnitrostátní sazba srážkové daně činí 15 %.";
    } else {
      detail.textContent = citationDetail(citation);
    }
    card.append(role, title, link, detail);

    const hasDomesticDisclosure = pathRole === "domestic_exemption_basis" || pathRole === "domestic_starting_point";
    if ((citation.official_text || citation.excerpt || hasDomesticDisclosure) && (layer !== "domestic" || hasDomesticDisclosure)) {
      const disclosure = document.createElement("details"); disclosure.className = "citation-excerpt"; disclosure.open = true;
      const summary = document.createElement("summary");
      summary.textContent = hasDomesticDisclosure
        ? (en ? "Relevant provisions" : "Relevantní ustanovení")
        : citation.official_text
          ? (en ? "Text of the applied provision" : "Znění použitého ustanovení")
          : (en ? "Recorded text of the applied provision" : "Evidované znění použitého ustanovení");
      const excerpt = document.createElement("blockquote");
      const fullText = pathRole === "domestic_exemption_basis"
        ? (en
            ? "Section 19(1)(ze), Section 19(3), Section 19(4), Section 19(6), Section 19(8) and Section 19(11) of the Czech Income Taxes Act."
            : "§ 19 odst. 1 písm. ze), § 19 odst. 3, § 19 odst. 4, § 19 odst. 6, § 19 odst. 8 a § 19 odst. 11 zákona o daních z příjmů.")
        : pathRole === "domestic_starting_point"
          ? (en
              ? "Section 36(1) of the Czech Income Taxes Act provides the general domestic withholding-tax rate applicable where no exemption or treaty limitation replaces it."
              : "§ 36 odst. 1 zákona o daních z příjmů stanoví obecnou vnitrostátní sazbu srážkové daně pro případy, kdy ji nenahrazuje osvobození ani smluvní omezení.")
          : displayLegalExcerpt(citation);
      const decisiveText = selected
        ? decisiveLegalParagraph(fullText, citation)
        : "";

      if (decisiveText && fullText.includes(decisiveText)) {
        const start = fullText.indexOf(decisiveText);

        excerpt.append(
          document.createTextNode(fullText.slice(0, start))
        );

        const mark = document.createElement("mark");
        mark.className = "legal-decisive-passage";
        mark.textContent = decisiveText;
        excerpt.append(mark);

        excerpt.append(
          document.createTextNode(
            fullText.slice(start + decisiveText.length)
          )
        );
      } else {
        excerpt.textContent = fullText;
      }

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
    const en = document.documentElement.lang === "en";
    setText("#workspace-reference-date", formatCzechDate(schedule.reference_date));
    const nonTaxing = ["exclusive_foreign_taxation", "domestic_exemption"].includes(analysis.tax_treatment);
    setText("#workspace-remittance-deadline", schedule.tax_remittance_deadline ? formatCzechDate(schedule.tax_remittance_deadline) : analysis.status === "FINAL" && nonTaxing ? (en ? "No tax remittance required" : "Daň se neodvádí") : (en ? "After completing the facts" : "Po doplnění údajů"));
    setText("#workspace-notification-deadline", schedule.notification_deadline ? formatCzechDate(schedule.notification_deadline) : schedule.notification_required === false ? (en ? "No notification required" : "Oznámení se nepodává") : (en ? "After completing the facts" : "Po doplnění údajů"));
    const note = document.querySelector("#workspace-deadline-note");
    if (schedule.status !== "READY") note.textContent = en
      ? "The deadlines cannot be finalized until the applicable rule or the monthly aggregate relevant for the notification obligation can be determined."
      : "Lhůty nelze uzavřít, dokud zadané údaje neumožní přiřadit příslušné pravidlo nebo měsíční úhrn rozhodný pro oznamovací povinnost.";
    else if (schedule.notification_regime === "exempt_or_treaty_non_taxable_annual") note.textContent = en
      ? "No Czech tax is remitted under this treatment. For dividends and royalties, the outbound-income notification under Section 38da of the Czech Income Taxes Act is due by 31 January of the following year."
      : "Česká daň se při tomto daňovém zacházení neodvádí. Oznámení podle § 38da zákona č. 586/1992 Sb., o daních z příjmů se u dividend a licenčních poplatků podává do 31. ledna následujícího roku.";
    else if (schedule.notification_regime === "non_taxing_interest_above_monthly_threshold_annual") note.textContent = en
      ? `No Czech tax is remitted. The monthly aggregate of interest of the same type is ${money(schedule.monthly_same_type_income_czk)} and exceeds CZK 300,000; the notification under Section 38da of the Czech Income Taxes Act is due by the date shown.`
      : `Česká daň se neodvádí. Měsíční úhrn úroků stejného druhu činí ${money(schedule.monthly_same_type_income_czk)} a přesáhl 300 000 Kč; oznámení podle § 38da zákona č. 586/1992 Sb., o daních z příjmů se podává do uvedeného data.`;
    else if (schedule.notification_regime === "non_taxing_interest_monthly_threshold_not_exceeded") note.textContent = en
      ? `No Czech tax is remitted. The monthly aggregate of interest of the same type is ${money(schedule.monthly_same_type_income_czk)} and does not exceed CZK 300,000; no notification obligation arises under Section 38da of the Czech Income Taxes Act.`
      : `Česká daň se neodvádí. Měsíční úhrn úroků stejného druhu činí ${money(schedule.monthly_same_type_income_czk)} a nepřesáhl 300 000 Kč; oznamovací povinnost podle § 38da zákona č. 586/1992 Sb., o daních z příjmů proto nevzniká.`;
    else note.textContent = en
      ? "The withholding tax remittance and outbound-income notification have the same deadline: the end of the following calendar month."
      : "Odvod sražené daně a oznámení o příjmu plynoucím do zahraničí mají shodnou lhůtu: konec následujícího kalendářního měsíce.";
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

  function informationalRuleStatement(analysis) {
    const selected = selectedRuleId(analysis);
    const en = document.documentElement.lang === "en";
    const citation = [...(analysis.legal_path || analysis.citations || [])]
      .find((item) => String(item.rule_id || "") === selected);
    let reference = en ? "the applied legal rule" : "použitého právního pravidla";
    if (citation) {
      const paragraph = citation.paragraph ? `, ${citation.paragraph}` : "";
      const layer = String(citation.legal_layer || "");
      reference = ["treaty", "protocol", "mli"].includes(layer)
        ? (en
            ? `Article ${citation.article || "—"}${paragraph} of the Double Tax Treaty`
            : `článku ${citation.article || "—"}${paragraph} smlouvy o zamezení dvojího zdanění`)
        : layer === "eu_relief" || String(citation.path_role || "") === "domestic_exemption_basis"
          ? (en ? "Section 19 of the Czech Income Taxes Act" : "§ 19 zákona č. 586/1992 Sb., o daních z příjmů")
          : (en
              ? `Section ${citation.article || "—"}${paragraph} of the Czech Income Taxes Act`
              : `§ ${citation.article || "—"}${paragraph} zákona č. 586/1992 Sb., o daních z příjmů`);
    }
    const treatment = analysis.tax_treatment || analysis.candidate_tax_treatment;
    if (treatment === "exclusive_foreign_taxation") {
      return en
        ? `Under ${reference}, the income is not taxable in the Czech Republic based on the entered facts.`
        : `Podle ${reference} se při zadaných údajích příjem v České republice nezdaňuje.`;
    }
    if (treatment === "domestic_exemption") {
      return en
        ? `Under ${reference}, the income is exempt from Czech withholding tax based on the entered facts.`
        : `Podle ${reference} je při zadaných údajích příjem v České republice osvobozen od srážkové daně.`;
    }
    const rate = analysis.rate ?? analysis.candidate_rate;
    if (rate !== null && rate !== undefined) {
      return en
        ? `Under ${reference}, the Czech withholding tax rate is ${new Intl.NumberFormat("en-GB", { maximumFractionDigits: 2 }).format(Number(rate))}% based on the entered facts.`
        : `Podle ${reference} činí při zadaných údajích sazba srážkové daně ${new Intl.NumberFormat("cs-CZ", { maximumFractionDigits: 2 }).format(Number(rate))} %.`;
    }
    return en
      ? "The entered facts do not yet allow TaxTreat to assign a specific legal rule and rate."
      : "Zadané údaje zatím neumožňují v TaxTreat přiřadit konkrétní právní pravidlo a sazbu.";
  }

  function renderResult(payload, response) {
    ensureRuntimeResultAnchors();
    const analysis = response.analysis;
    const calculation = analysis.withholding_tax_calculation;
    const professional = (response.intake?.questions || []).filter((question) => !question.client_answerable);
    const reviewReasons = response.intake?.review_reasons || [];
    const reviewItems = concreteReviewItems(analysis, payload, professional, reviewReasons);
    const status = document.querySelector("#workspace-result-status");
    status.textContent = analysis.status === "FINAL" ? "VÝPOČET DOKONČEN" : "CHYBÍ ÚDAJE PRO PŘIŘAZENÍ PRAVIDLA";
    status.className = analysis.status === "FINAL" ? "badge" : "badge warning";
    const grossCzk = calculationValue(calculation, "gross_amount_czk", "tax_base_czk");
    const taxCzk = calculationValue(calculation, "withholding_tax_czk", "withholding_tax_czk");
    const netCzk = calculationValue(calculation, "net_amount_czk", "net_amount_czk");
    const treatment = analysis.tax_treatment || analysis.candidate_tax_treatment;
    const candidateCitation = selectedCitation(analysis);
    const unresolvedDomesticExemption = analysis.status !== "FINAL" && (analysis.layer_results || []).some(
      (item) => item.layer === "eu_relief" && item.outcome === "unresolved"
    );
    const treatyFallback = unresolvedDomesticExemption
      && analysis.candidate_rate !== null
      && analysis.candidate_rate !== undefined
      && ["treaty", "protocol", "mli"].includes(String(candidateCitation?.legal_layer || ""));
    if (treatyFallback) {
      status.textContent = document.documentElement.lang === "en"
        ? "DOMESTIC EXEMPTION FACTS INCOMPLETE"
        : "NEÚPLNÉ ÚDAJE PRO VNITROSTÁTNÍ OSVOBOZENÍ";
    }
    const reasonCard = document.querySelector('.flow-step[data-step="4"] > article.reason');
    if (reasonCard) reasonCard.hidden = analysis.status !== "FINAL" && !treatyFallback;
    const nonTaxing = ["exclusive_foreign_taxation", "domestic_exemption"].includes(treatment);
    const en = document.documentElement.lang === "en";
    setText("#workspace-tax-label", treatyFallback
      ? (en ? "Treaty fallback withholding tax" : "Srážková daň podle smluvního fallbacku")
      : nonTaxing ? "Česká daň k odvodu" : "Srážková daň v CZK");
    setText("#workspace-tax-row-label", treatyFallback
      ? (en ? "Treaty fallback withholding tax" : "Srážková daň podle smluvního fallbacku")
      : nonTaxing ? "Česká daň k odvodu" : "Srážková daň");
    const fallbackGross = grossCzk !== null
      ? Number(grossCzk)
      : payload.transaction_amount.currency === "CZK"
        ? Number(payload.transaction_amount.amount)
        : null;
    const fallbackTax = treatyFallback && Number.isFinite(fallbackGross)
      ? fallbackGross * Number(analysis.candidate_rate) / 100
      : null;
    setText("#workspace-tax", calculation ? money(taxCzk) : fallbackTax !== null ? money(fallbackTax) : "—");
    const incomeTypeLabels = { dividend: "Dividendy", interest: "Úroky", royalty: "Licenční poplatky" };
    const resultStep = document.querySelector('.flow-step[data-step="4"]');
    if (resultStep) resultStep.dataset.incomeType = payload.income_type || "";
    setText("#workspace-income-type", `${document.documentElement.lang === "en" ? "Transaction" : "Transakce"}: ${incomeTypeLabels[payload.income_type] || payload.income_type || "—"}`);
    setText("#workspace-rate", treatyFallback
      ? (en
          ? `Treaty fallback: ${analysis.candidate_rate}% of the transaction value. The final Czech tax may be lower or zero if the domestic exemption applies.`
          : `Smluvní fallback: ${analysis.candidate_rate} % z hodnoty transakce. Konečná česká daň může být nižší nebo nulová, pokud se uplatní vnitrostátní osvobození.`)
      : treatment === "exclusive_foreign_taxation" ? `Zdanění pouze ve státě rezidence příjemce (${countryName(recipient.country)})`
      : treatment === "domestic_exemption" ? "Příjem je v České republice osvobozen"
      : analysis.rate === null ? analysis.candidate_rate === null ? "Sazbu nelze určit bez doplnění potřebných podmínek" : `Sazba přiřazená podle dostupných údajů: ${analysis.candidate_rate} %`
      : `${analysis.rate} % z hodnoty transakce`);
    setText("#workspace-gross", grossCzk !== null ? money(grossCzk) : payload.transaction_amount.currency === "CZK" ? money(payload.transaction_amount.amount) : `${payload.transaction_amount.amount} ${payload.transaction_amount.currency}`);
    setText("#workspace-tax-row", calculation ? money(taxCzk) : fallbackTax !== null ? money(fallbackTax) : "—");
    setText("#workspace-net", calculation ? money(netCzk) : fallbackTax !== null && fallbackGross !== null ? money(fallbackGross - fallbackTax) : "—");
    setText("#workspace-reason", treatyFallback
      ? (en
          ? `The domestic exemption cannot yet be concluded. If it is not available, the fallback treaty rule is ${candidateCitation?.article ? `Article ${candidateCitation.article}` : "the applicable treaty provision"} at ${analysis.candidate_rate}%.`
          : `Vnitrostátní osvobození zatím nelze uzavřít. Pokud se neuplatní, smluvním fallbackem je ${candidateCitation?.article ? `článek ${candidateCitation.article}` : "příslušné smluvní ustanovení"} se sazbou ${analysis.candidate_rate} %.`)
      : informationalRuleStatement(analysis));
    const actions = document.querySelector("#workspace-actions"); actions.replaceChildren();
    reviewItems.forEach((item) => actions.append(item));
    const actionCount = document.querySelector("#workspace-action-count");
    if (actionCount) {
      actionCount.textContent = String(reviewItems.length);
      actionCount.hidden = reviewItems.length === 0;
    }
    const conditionsCard = actions.closest("article.card");
    const resultGrid = conditionsCard?.closest(".dashboard-grid");
    const unresolved = analysis.status !== "FINAL";
    if (conditionsCard) conditionsCard.hidden = reviewItems.length === 0 || unresolved;
    if (resultGrid) resultGrid.classList.toggle("single-column", !conditionsCard || conditionsCard.hidden);
    const citations = document.querySelector("#workspace-citations"); citations.replaceChildren();
    decisiveCitations(analysis).forEach((citation, index) => citations.append(citationCard(citation, analysis, index + 1)));
    if (!citations.children.length) { const p = document.createElement("p"); p.textContent = "Pro tento informační výstup nebyl vrácen konkrétní odkaz na právní zdroj."; citations.append(p); }
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
      if (!response.ok) throw new Error(body.detail?.code || "Informační výpočet se nepodařilo dokončit.");
      const clientQuestions = (body.intake?.questions || []).filter((question) => question.client_answerable);
      lastPayload = payload;
      if (clientQuestions.length) renderClientQuestions(clientQuestions);
      else { renderClientQuestions([]); renderResult(payload, body); }
    } catch (problem) { error.textContent = problem.message; error.hidden = false; }
  });

  window.TaxTreatWorkspace = {
    ...(window.TaxTreatWorkspace || {}),
    openStoredResult(payload, response) {
      if (!payload || !response?.analysis) return false;

      const restoredPayload = structuredClone(payload);
      const restoredResponse = structuredClone(response);

      lastPayload = restoredPayload;
      renderClientQuestions([]);
      renderResult(restoredPayload, restoredResponse);
      return true;
    }
  };

  renderPayers();
  renderRecipient();
  loadJurisdictionCatalog();
  renderTransactionFacts();
  checkForNewBuild();
})();
