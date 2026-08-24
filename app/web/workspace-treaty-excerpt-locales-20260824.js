(() => {
  "use strict";

  const UI_KEY = "taxtreat-ui-language";
  const REGISTRY_URL = "/ui-assets/treaty-excerpt-locales-20260824.json?v=20260824-1";
  const originalExcerpt = new WeakMap();
  let recipientCountry = null;
  let registryPromise = null;
  let jurisdictionsPromise = null;

  function language() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem(UI_KEY) || "cs";
  }

  function loadRegistry() {
    if (!registryPromise) {
      registryPromise = fetch(REGISTRY_URL, { cache: "no-store" })
        .then((response) => {
          if (!response.ok) throw new Error(`Treaty locale registry unavailable (${response.status})`);
          return response.json();
        })
        .catch((problem) => {
          console.error("TaxTreat treaty locale registry failed", problem);
          return { entries: {} };
        });
    }
    return registryPromise;
  }

  function loadJurisdictions() {
    if (!jurisdictionsPromise) {
      jurisdictionsPromise = fetch("/jurisdictions", { cache: "no-store" })
        .then((response) => response.ok ? response.json() : { jurisdictions: [] })
        .then((payload) => Array.isArray(payload?.jurisdictions) ? payload.jurisdictions : [])
        .catch(() => []);
    }
    return jurisdictionsPromise;
  }

  function articleNumber(card) {
    const text = card?.textContent || "";
    const match = text.match(/(?:Article|článek|Článek)\s*([0-9]+[A-Za-z]?)\b/);
    return match?.[1] || null;
  }

  function treatyCards() {
    return Array.from(document.querySelectorAll("#workspace-citations .citation-card")).filter((card) => {
      const text = card.textContent || "";
      return /Double Tax Treaty|Smlouva o zamezení dvojího zdanění/i.test(text);
    });
  }

  function excerptNode(card) {
    return card.querySelector(".legal-excerpt, blockquote");
  }

  function ensureOriginal(excerpt) {
    if (originalExcerpt.has(excerpt)) return;
    const declaredLanguage = String(excerpt.dataset.ttTreatyLanguage || excerpt.getAttribute("lang") || "").toLowerCase();
    if (declaredLanguage.startsWith("en")) return;
    originalExcerpt.set(excerpt, excerpt.textContent || "");
  }

  function inferRecipientCountry(jurisdictions) {
    const explicit = String(recipientCountry || "").toUpperCase();
    if (explicit) return explicit;

    const bodyText = document.body?.textContent || "";
    let englishNames;
    let czechNames;
    try {
      englishNames = new Intl.DisplayNames(["en"], { type: "region" });
      czechNames = new Intl.DisplayNames(["cs"], { type: "region" });
    } catch (_problem) {
      return null;
    }

    for (const item of jurisdictions || []) {
      const country = String(item?.iso2 || "").toUpperCase();
      if (!country) continue;
      const names = [englishNames.of(country), czechNames.of(country)].filter(Boolean);
      if (names.some((name) => bodyText.includes(name))) {
        recipientCountry = country;
        return country;
      }
    }
    return null;
  }

  function removeMissingNote(card) {
    card.querySelector(".tt-treaty-locale-missing")?.remove();
  }

  function showMissingNote(card, country, article) {
    let note = card.querySelector(".tt-treaty-locale-missing");
    if (!note) {
      note = document.createElement("p");
      note.className = "tt-treaty-locale-missing";
      note.style.margin = "10px 0";
      note.style.fontSize = "0.9rem";
      note.style.fontWeight = "600";
      const details = card.querySelector("details.citation-excerpt");
      if (details) card.insertBefore(note, details); else card.append(note);
    }
    note.textContent = `Official English treaty wording is not yet registered for CZ–${country}, Article ${article}. The Czech official excerpt is shown below.`;
  }

  async function refreshTreatyExcerpts() {
    const targetLanguage = language();
    const cards = treatyCards();
    if (!cards.length) return;
    const [registry, jurisdictions] = await Promise.all([loadRegistry(), loadJurisdictions()]);
    const country = inferRecipientCountry(jurisdictions);

    cards.forEach((card) => {
      const excerpt = excerptNode(card);
      const article = articleNumber(card);
      if (!excerpt || !article) return;
      ensureOriginal(excerpt);

      if (targetLanguage !== "en") {
        if (originalExcerpt.has(excerpt)) {
          excerpt.textContent = originalExcerpt.get(excerpt) || "";
        }
        excerpt.setAttribute("lang", "cs");
        delete excerpt.dataset.ttTreatyLanguage;
        delete excerpt.dataset.ttTreatyLocaleStatus;
        delete excerpt.dataset.ttTreatyLocaleSource;
        removeMissingNote(card);
        return;
      }

      const locale = registry?.entries?.[country]?.[String(article)]?.en;
      if (!country || !locale?.text) {
        if (originalExcerpt.has(excerpt)) {
          excerpt.textContent = originalExcerpt.get(excerpt) || "";
        }
        excerpt.setAttribute("lang", "cs");
        excerpt.dataset.ttTreatyLanguage = "cs-fallback";
        showMissingNote(card, country || "?", article);
        return;
      }

      excerpt.textContent = locale.text;
      excerpt.setAttribute("lang", "en");
      excerpt.dataset.ttTreatyLanguage = "en";
      excerpt.dataset.ttTreatyLocaleStatus = locale.status || "registered";
      excerpt.dataset.ttTreatyLocaleSource = locale.source_url || "";
      removeMissingNote(card);
    });
  }

  function schedule() {
    [0, 60, 180, 450, 900].forEach((delay) => window.setTimeout(refreshTreatyExcerpts, delay));
  }

  const previousFetch = window.fetch.bind(window);
  window.fetch = async function treatyLocaleFetch(resource, options = {}) {
    const url = typeof resource === "string" ? resource : resource?.url || "";
    if (url.endsWith("/analysis/intake") && options?.body) {
      try {
        const payload = JSON.parse(String(options.body));
        recipientCountry = String(payload?.recipient_country || "").toUpperCase() || recipientCountry;
      } catch (_problem) {}
    }
    const response = await previousFetch(resource, options);
    if (url.endsWith("/analysis/intake") && response.ok) schedule();
    return response;
  };

  document.addEventListener("change", (event) => {
    if (event.target?.id === "taxtreat-ui-language") schedule();
  }, true);
  document.addEventListener("click", () => window.setTimeout(schedule, 0), true);

  schedule();
})();
