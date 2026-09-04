(() => {
  "use strict";

  const form = document.querySelector("#payer-form");
  const dialog = document.querySelector("#payer-dialog");
  const activePayerSelect = document.querySelector("#active-payer-select");
  if (!form || !dialog || !activePayerSelect) return;

  const originalCountryInput = [...form.querySelectorAll("label")].find((label) =>
    label.querySelector("span")?.textContent.trim() === "Stát"
  );

  const en = String(document.documentElement.lang || "").toLowerCase().startsWith("en");
  const label = originalCountryInput || document.createElement("label");
  label.id = "payer-country-field";
  label.innerHTML = `
    <span>${en ? "Payer country *" : "Stát plátce *"}</span>
    <select name="payer_country" required>
      <option value="">${en ? "Select payer country" : "Vyber stát plátce"}</option>
      <option value="CZ">🇨🇿 ${en ? "Czech Republic" : "Česká republika"}</option>
      <option value="SK">🇸🇰 ${en ? "Slovakia" : "Slovensko"}</option>
    </select>
    <small>${en
      ? "The payer’s country determines which domestic withholding tax rules TaxTreat applies. This is not a separate application-mode switch."
      : "Stát plátce určuje, která vnitrostátní pravidla srážkové daně TaxTreat použije. Nejde o samostatný přepínač režimu aplikace."}</small>`;
  if (!originalCountryInput) form.querySelector(".flow-actions")?.before(label);

  const country = label.querySelector("select");
  const aresButton = form.querySelector("[data-ares-lookup]");
  const aresStatus = form.querySelector("#ares-lookup-status");
  const saveButton = form.querySelector("[data-save-payer]");
  const payerDetailLabels = [...form.querySelectorAll(":scope > label")].filter(
    (item) => item !== label
  );

  const payerContext = activePayerSelect.closest(".payer-context");
  const activeCountryBadge = document.createElement("div");
  activeCountryBadge.id = "active-payer-country-badge";
  activeCountryBadge.className = "active-payer-country-badge";
  activeCountryBadge.setAttribute("role", "status");
  activeCountryBadge.setAttribute("aria-live", "polite");
  payerContext?.after(activeCountryBadge);

  if (!document.querySelector("#payer-country-badge-style")) {
    const style = document.createElement("style");
    style.id = "payer-country-badge-style";
    style.textContent = `
      .active-payer-country-badge{display:flex;align-items:center;gap:9px;min-width:150px;padding:7px 11px;border:1px solid #dfe4ee;border-radius:10px;background:#f8faff;box-shadow:0 3px 10px rgba(28,43,81,.05);white-space:nowrap}
      .active-payer-country-badge[data-country="SK"]{background:#f7fbff;border-color:#d7e5f4}
      .active-payer-country-badge .payer-country-flag{font-size:1.5rem;line-height:1;filter:saturate(.92)}
      .active-payer-country-badge .payer-country-badge-copy{display:grid;gap:1px}
      .active-payer-country-badge small{font-size:.57rem;line-height:1.1;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:#778095}
      .active-payer-country-badge strong{font-size:.72rem;line-height:1.2;color:#172033}
      #payer-country-field select{font-weight:750}
      @media(max-width:1050px){.active-payer-country-badge{order:2}}
      @media(max-width:700px){.active-payer-country-badge{width:100%;order:3}.active-payer-country-badge strong{font-size:.78rem}}
    `;
    document.head.append(style);
  }

  function sourceApi() {
    return window.TaxTreatWorkspaceSourceCountry;
  }

  function findPayerKeyByName(name) {
    const normalized = String(name || "").trim();
    const option = [...activePayerSelect.options].find((item) => item.textContent.trim() === normalized);
    return option?.value || activePayerSelect.value;
  }

  function countryForKey(key) {
    return sourceApi()?.getPayerCountry?.(key) || "CZ";
  }

  function inferredEditorCountry() {
    const name = form.elements.payer_name?.value || "";
    const key = findPayerKeyByName(name);
    const explicit = sourceApi()?.getPayerCountry?.(key);
    if (explicit) return explicit;
    const vatId = String(form.elements.payer_vat_id?.value || "").toUpperCase();
    return vatId.startsWith("SK") ? "SK" : "CZ";
  }

  function updateActiveCountryBadge(code = sourceApi()?.getActiveCode?.() || countryForKey(activePayerSelect.value)) {
    const normalized = String(code || "CZ").toUpperCase() === "SK" ? "SK" : "CZ";
    const isSk = normalized === "SK";
    const flag = isSk ? "🇸🇰" : "🇨🇿";
    const countryName = isSk
      ? (en ? "Slovakia" : "Slovensko")
      : (en ? "Czech Republic" : "Česká republika");
    const labelText = en ? "Payer country" : "Stát plátce";
    activeCountryBadge.dataset.country = normalized;
    activeCountryBadge.innerHTML = `
      <span class="payer-country-flag" aria-hidden="true">${flag}</span>
      <span class="payer-country-badge-copy">
        <small>${labelText}</small>
        <strong>${countryName} · ${normalized}</strong>
      </span>`;
    activeCountryBadge.setAttribute(
      "aria-label",
      en ? `Active payer country: ${countryName}` : `Stát aktivního plátce: ${countryName}`
    );
  }

  function applyCountryUi() {
    const selected = country.value === "CZ" || country.value === "SK";
    const isSk = country.value === "SK";

    payerDetailLabels.forEach((item) => {
      item.hidden = !selected;
    });

    if (saveButton) {
      saveButton.hidden = !selected;
      saveButton.disabled = !selected;
    }

    if (aresButton) {
      aresButton.hidden = !selected || isSk;
      aresButton.disabled = !selected || isSk;
    }

    if (aresStatus) {
      if (!selected) {
        aresStatus.hidden = true;
      } else {
        aresStatus.hidden = false;
        const nextStatus = isSk
          ? (en
              ? "Slovak company-registry lookup will be offered here. Until it is connected, enter the identification details manually."
              : "Zde bude dostupné načtení ze slovenského registru. Do jeho napojení zadej identifikační údaje ručně.")
          : (en
              ? "After entering the Company ID, you can retrieve identification details from ARES."
              : "Po zadání IČO můžeš identifikační údaje načíst z ARES.");
        if (aresStatus.textContent !== nextStatus) aresStatus.textContent = nextStatus;
      }
    }

    const vat = form.elements.payer_vat_id;
    if (vat && !vat.value && selected) {
      vat.placeholder = isSk ? "např. SK2020000000" : "např. CZ12345678";
    }
  }

  function refreshPayerCountryCopy() {
    const cards = [...document.querySelectorAll(".payer-record,.payer-choice")];
    cards.forEach((card) => {
      const payerName = card.querySelector("h2")?.textContent?.trim() || card.querySelector("b")?.textContent?.trim() || "";
      const key = findPayerKeyByName(payerName);
      const code = countryForKey(key);
      const meta = card.querySelector("p");
      if (!meta) return;
      const current = meta.textContent.replace(/^🇨🇿\s*/, "").replace(/^🇸🇰\s*/, "");
      const nextCountry = code === "SK" ? "Slovensko" : "Česká republika";
      const flag = code === "SK" ? "🇸🇰" : "🇨🇿";
      const next = current
        .replace(/^Česká republika/, nextCountry)
        .replace(/^Slovensko/, nextCountry);
      meta.textContent = `${flag} ${next}`;
    });
    updateActiveCountryBadge();
  }

  country.addEventListener("change", () => {
    country.dataset.userSelected = "true";
    applyCountryUi();
  });
  activePayerSelect.addEventListener("change", () => window.setTimeout(refreshPayerCountryCopy, 0));

  document.querySelectorAll("[data-create-payer]").forEach((button) => {
    button.addEventListener("click", () => {
      country.dataset.userSelected = "false";
      if (!form.elements.payer_name.value) country.value = "";
      applyCountryUi();
    });
  });

  new MutationObserver(() => {
    if (!dialog.open) return;

    if (country.dataset.userSelected === "true") {
      applyCountryUi();
      return;
    }

    country.value = form.elements.payer_name?.value ? inferredEditorCountry() : "";
    applyCountryUi();
  }).observe(dialog, { attributes: true, attributeFilter: ["open"] });

  dialog.addEventListener("close", () => {
    country.dataset.userSelected = "false";
  });

  window.addEventListener("taxtreat:payer-saved", (event) => {
    const key = String(event.detail?.key || "");
    const selectedCountry = String(event.detail?.country || country.value || "CZ");
    if (key) sourceApi()?.setPayerCountry?.(key, selectedCountry);
    refreshPayerCountryCopy();
  });

  window.addEventListener("taxtreat:source-country-change", (event) => {
    updateActiveCountryBadge(event.detail?.code);
  });

  document.addEventListener("click", (event) => {
    if (event.target.closest("[data-nav],[data-flow-step],[data-next-step],[data-start-flow],[data-open-recipient]")) {
      window.setTimeout(refreshPayerCountryCopy, 0);
    }
  });

  [...activePayerSelect.options].forEach((option) => {
    if (!sourceApi()?.getPayerCountry?.(option.value)) sourceApi()?.setPayerCountry?.(option.value, "CZ");
  });
  country.value = inferredEditorCountry();
  applyCountryUi();
  refreshPayerCountryCopy();
})();
