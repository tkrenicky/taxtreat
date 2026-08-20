(() => {
  "use strict";

  const form = document.querySelector("#payer-form");
  const activePayerSelect = document.querySelector("#active-payer-select");
  if (!form || !activePayerSelect) return;

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

  country.addEventListener("change", applyCountryUi);

  document.querySelectorAll("[data-create-payer]").forEach((button) => {
    button.addEventListener("click", () => window.setTimeout(() => {
      country.value = "CZ";
      applyCountryUi();
    }, 0));
  });

  document.querySelectorAll("[data-edit-payer]").forEach((button) => {
    button.addEventListener("click", () => window.setTimeout(() => {
      country.value = inferredEditorCountry();
      applyCountryUi();
    }, 0));
  });

  form.addEventListener("submit", () => {
    const selectedCountry = country.value;
    const payerName = String(form.elements.payer_name?.value || "").trim();
    window.setTimeout(() => {
      const key = findPayerKeyByName(payerName);
      sourceApi()?.setPayerCountry?.(key, selectedCountry);
    }, 0);
  });

  // Default demo payers are Czech unless a payer-specific country is later saved.
  [...activePayerSelect.options].forEach((option) => {
    sourceApi()?.setPayerCountry?.(option.value, "CZ");
  });
  country.value = inferredEditorCountry();
  applyCountryUi();
})();