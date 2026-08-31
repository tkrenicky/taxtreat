(() => {
  "use strict";

  const OPTIONS = [
    ["", "Vyber možnost", "Select option"],
    [
      "copyright_literary_artistic_scientific_nonfilm_nonsoftware",
      "Autorská práva k literárnímu, uměleckému nebo vědeckému dílu (mimo film/TV/rozhlas a software)",
      "Copyright in a literary, artistic or scientific work (excluding film/TV/radio and software)",
    ],
    [
      "cinematographic_films_or_broadcast_media",
      "Filmová, televizní nebo rozhlasová práva",
      "Film, television or radio rights",
    ],
    [
      "computer_software",
      "Software / počítačový program",
      "Software / computer program",
    ],
    [
      "patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
      "Patent, ochranná známka, design, model, plán, tajný vzorec, postup nebo know-how",
      "Patent, trademark, design, model, plan, secret formula, process or know-how",
    ],
    [
      "financial_lease_of_equipment",
      "Finanční leasing průmyslového, obchodního nebo vědeckého zařízení",
      "Financial lease of industrial, commercial or scientific equipment",
    ],
    [
      "operating_lease_or_other_use_of_equipment",
      "Jiné užití nebo pronájem průmyslového, obchodního nebo vědeckého zařízení",
      "Other use or lease of industrial, commercial or scientific equipment",
    ],
    ["other", "Jiný předmět licence", "Other royalty subject"],
  ];

  const LEGACY_SAFE_MAP = new Map([
    ["other", "other"],
  ]);

  function language() {
    return document.querySelector("#taxtreat-ui-language")?.value ||
      localStorage.getItem("taxtreat-ui-language") || "cs";
  }

  function rebuild() {
    const select = document.querySelector('[name="royalty_category"]');
    if (!select) return;

    const english = language() === "en";
    const previous = select.value;
    const supported = new Set(OPTIONS.map(([value]) => value));
    const nextValue = supported.has(previous)
      ? previous
      : LEGACY_SAFE_MAP.get(previous) || "";

    const fragment = document.createDocumentFragment();
    for (const [value, cs, en] of OPTIONS) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = english ? en : cs;
      fragment.appendChild(option);
    }
    select.replaceChildren(fragment);
    select.value = nextValue;

    if (previous && !nextValue) {
      select.dataset.taxonomyReset = "true";
    } else {
      delete select.dataset.taxonomyReset;
    }
  }

  function refreshHint() {
    const select = document.querySelector('[name="royalty_category"]');
    const label = select?.closest("label");
    if (!select || !label) return;

    let hint = label.querySelector(".tt-royalty-taxonomy-hint");
    if (!hint) {
      hint = document.createElement("small");
      hint.className = "tt-royalty-taxonomy-hint";
      label.appendChild(hint);
    }

    if (select.dataset.taxonomyReset === "true") {
      hint.textContent = language() === "en"
        ? "The royalty classification has been refined. Select the precise subject of the royalty before calculation."
        : "Klasifikace licenčních plateb byla zpřesněna. Před výpočtem zvol přesný předmět licenční platby.";
      return;
    }

    hint.textContent = language() === "en"
      ? "The categories distinguish treaty branches that may carry different withholding tax rates."
      : "Kategorie rozlišují smluvní větve, pro které mohou platit rozdílné sazby srážkové daně.";
  }

  function refresh() {
    rebuild();
    refreshHint();
  }

  function schedule() {
    [0, 50, 150].forEach((delay) => window.setTimeout(refresh, delay));
  }

  document.addEventListener("change", (event) => {
    if (event.target?.id === "taxtreat-ui-language" || event.target?.name === "income_type") {
      schedule();
    }
  }, true);
  document.addEventListener("click", (event) => {
    if (event.target?.closest?.("#taxtreat-language-controls,[data-next-step],[data-start-flow]")) {
      schedule();
    }
  }, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", schedule, { once: true });
  } else {
    schedule();
  }
})();
