(() => {
  "use strict";

  const form = document.querySelector("#payer-form");
  const dialog = document.querySelector("#payer-dialog");
  const activePayerSelect = document.querySelector("#active-payer-select");
  if (!form || !dialog || !activePayerSelect) return;

  const originalCountryInput = [...form.querySelectorAll("label")].find((label) =>
    label.querySelector("span")?.textContent.trim() === "Stát"
  );

  const label = originalCountryInput || document.createElement("label");
  label.id = "payer-country-field";
  label.innerHTML = `
    <span>Stát plátce *</span>
    <select name="payer_country" required>
      <option value="CZ">Česká republika</option>
      <option value="SK">Slovensko</option>
    </select>
    <small>Stát plátce určuje, která vnitrostátní pravidla srážkové daně TaxTreat použije. Nejde o samostatný přepínač režimu aplikace.</small>`;
  if (!originalCountryInput) form.querySelector(".flow-actions")?.before(label);

  const country = label.querySelector("select");
  const aresButton = form.querySelector("[data-ares-lookup]");
  const aresStatus = form.querySelector("#ares-lookup-status");

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

  function applyCountryUi() {
    const isSk = country.value === "SK";
    if (aresButton) {
      aresButton.hidden = isSk;
      aresButton.disabled = isSk;
    }
    if (aresStatus) {
      aresStatus.textContent = isSk
        ? "Pro slovenského plátce se údaje z českého registru ARES nenačítají; identifikační údaje vyplň ručně."
        : "Po zadání 8 číslic TaxTreat načte identifikační údaje z ARES.";
    }
    const vat = form.elements.payer_vat_id;
    if (vat && !vat.value) vat.placeholder = isSk ? "např. SK2020000000" : "např. CZ12345678";
  }

  function refreshPayerCountryCopy() {
    const cards = [...document.querySelectorAll(".payer-record,.payer-choice")];
    cards.forEach((card) => {
      const payerName = card.querySelector("h2")?.textContent?.trim() || card.querySelector("b")?.textContent?.trim() || "";
      const key = findPayerKeyByName(payerName);
      const code = countryForKey(key);
      const meta = card.querySelector("p");
      if (!meta) return;
      meta.textContent = meta.textContent
        .replace(/^Česká republika/, code === "SK" ? "Slovensko" : "Česká republika")
        .replace(/^Slovensko/, code === "CZ" ? "Česká republika" : "Slovensko");
    });
  }

  country.addEventListener("change", applyCountryUi);

  document.querySelectorAll("[data-create-payer]").forEach((button) => {
    button.addEventListener("click", () => window.setTimeout(() => {
      if (!form.elements.payer_name.value) country.value = "CZ";
      applyCountryUi();
    }, 0));
  });

  // openPayerDialog() is invoked by dynamically created edit buttons. Watching the
  // dialog's open state keeps the country field correct without requiring those
  // buttons to carry special data attributes.
  new MutationObserver(() => {
    if (!dialog.open) return;
    country.value = inferredEditorCountry();
    applyCountryUi();
  }).observe(dialog, { attributes: true, attributeFilter: ["open"] });

  form.addEventListener("submit", () => {
    const selectedCountry = country.value;
    const payerName = String(form.elements.payer_name?.value || "").trim();
    window.setTimeout(() => {
      const key = findPayerKeyByName(payerName);
      sourceApi()?.setPayerCountry?.(key, selectedCountry);
      refreshPayerCountryCopy();
    }, 0);
  });

  new MutationObserver(() => refreshPayerCountryCopy()).observe(
    document.querySelector("main") || document.body,
    { subtree: true, childList: true }
  );

  // Default demo payers are Czech unless a payer-specific country is later saved.
  [...activePayerSelect.options].forEach((option) => {
    if (!sourceApi()?.getPayerCountry?.(option.value)) sourceApi()?.setPayerCountry?.(option.value, "CZ");
  });
  country.value = inferredEditorCountry();
  applyCountryUi();
  refreshPayerCountryCopy();
})();