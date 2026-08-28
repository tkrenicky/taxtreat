(() => {
  "use strict";

  const UI_KEY = "taxtreat-ui-language";
  const REGISTRY_URL = "/ui-assets/treaty-excerpt-locales-20260824.json?v=20260824-1";
  const COUNTRY_REGISTRY_ROOT = "/ui-assets/treaty-excerpt-locales";
  const originalExcerpt = new WeakMap();
  const countryRegistryPromises = new Map();
  let recipientCountry = null;
  let selectedRuleId = null;
  let selectedTreatyArticle = null;
  let selectedTreatyCitation = null;
  let registryPromise = null;
  let jurisdictionsPromise = null;

  function language() {
    const htmlLang = String(document.documentElement.lang || "").toLowerCase();
    if (htmlLang.startsWith("en")) return "en";
    if (htmlLang.startsWith("cs") || htmlLang.startsWith("cz")) return "cs";
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem(UI_KEY) || "cs";
  }

  const STATUS_UI = {
    official_treaty_text: null,
    official_protocol_text: null,
    official_translation_non_authentic: {
      level: "info",
      label: "Official English translation — non-authentic",
      detail: "This English wording is published by an official source but is not the authentic treaty text."
    },
    official_synthesised_text: {
      level: "info",
      label: "Official-source synthesised English text",
      detail: "This English wording is synthesised from official treaty materials and is not presented as authentic treaty wording."
    },
    official_synthesised_excerpt: {
      level: "info",
      label: "Official-source synthesised English excerpt",
      detail: "This English excerpt is synthesised from official treaty materials and is not presented as authentic treaty wording."
    },
    machine_translation_from_official_text: {
      level: "warning",
      label: "Machine translation of official text",
      detail: "This is a machine translation of official treaty text. Consult the official-language source for authoritative wording."
    },
    verified_stage6_rule_summary: {
      level: "info",
      label: "Verified English rule summary",
      detail: "This is a verified English summary of the legal rule, not authentic treaty wording."
    },
    current_application_suspended: {
      level: "danger",
      label: "Application currently suspended",
      detail: "This provision is currently suspended. The wording below is shown for legal context only and must not be treated as an operative treaty rule."
    }
  };

  function removeStatusNotice(card) {
    card.querySelector(".tt-treaty-status")?.remove();
  }

  function renderStatusNotice(card, locale) {
    removeStatusNotice(card);
    const status = String(locale?.status || "");
    const meta = STATUS_UI[status];
    if (!meta) return;

    const note = document.createElement("div");
    note.className = `tt-treaty-status tt-treaty-status-${meta.level}`;
    note.dataset.treatyStatus = status;

    const strong = document.createElement("strong");
    strong.textContent = meta.label;
    const small = document.createElement("small");
    small.textContent = meta.detail;
    note.append(strong, small);

    const details = card.querySelector("details.citation-excerpt");
    if (details) card.insertBefore(note, details);
    else card.append(note);
  }

  function installStatusStyles() {
    if (document.querySelector("#tt-treaty-status-styles")) return;
    const style = document.createElement("style");
    style.id = "tt-treaty-status-styles";
    style.textContent = `
      .tt-treaty-status{margin:10px 0 8px;padding:10px 12px;border-radius:8px;border:1px solid #d8e3df;display:grid;gap:3px;font-size:.82rem;line-height:1.4}
      .tt-treaty-status strong{font-size:.82rem}
      .tt-treaty-status small{font-size:.78rem;color:#566662}
      .tt-treaty-status-info{background:#f4f8f7}
      .tt-treaty-status-warning{background:#fff8e8;border-color:#ead7a3}
      .tt-treaty-status-danger{background:#fff1ef;border-color:#dfb4ae}
      .tt-treaty-status-danger strong{color:#8b2f25}
    `;
    document.head.append(style);
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

  function loadCountryRegistry(country) {
    const iso2 = String(country || "").toUpperCase();
    if (!iso2) return Promise.resolve(null);
    if (!countryRegistryPromises.has(iso2)) {
      const url = `${COUNTRY_REGISTRY_ROOT}/${iso2}.json?v=20260824-3`;
      countryRegistryPromises.set(iso2, fetch(url, { cache: "no-store" })
        .then((response) => response.ok ? response.json() : null)
        .catch(() => null));
    }
    return countryRegistryPromises.get(iso2);
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
    originalExcerpt.set(excerpt, Array.from(excerpt.childNodes).map((node) => node.cloneNode(true)));
  }

  function restoreOriginal(excerpt) {
    const nodes = originalExcerpt.get(excerpt);
    if (!nodes) return;
    excerpt.replaceChildren(...nodes.map((node) => node.cloneNode(true)));
  }

  function captureAnalysis(analysis) {
    selectedRuleId = String(analysis?.selected_rule_id || analysis?.candidate_rule_id || "") || null;
    selectedTreatyArticle = null;
    selectedTreatyCitation = null;
    if (!selectedRuleId) return;
    const citations = analysis?.legal_path || analysis?.citations || [];
    const selected = citations.find((citation) => String(citation?.rule_id || "") === selectedRuleId);
    if (selected && ["treaty", "protocol", "mli"].includes(String(selected.legal_layer || ""))) {
      selectedTreatyArticle = String(selected.article || "") || null;
      selectedTreatyCitation = selected;
    }
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

  function localeFor(registry, countryRegistry, country, article, cardRuleId = "") {
    const exactRuleId = String(cardRuleId || "");
    const exactEntry = exactRuleId ? countryRegistry?.rules?.[exactRuleId] : null;
    const exactLocale = exactEntry && (!exactEntry.article || String(exactEntry.article) === String(article))
      ? exactEntry.en
      : null;
    if (exactLocale?.text) return { locale: exactLocale, specificity: "rule" };

    const selectedEntry = selectedRuleId && String(selectedTreatyArticle || "") === String(article)
      ? countryRegistry?.rules?.[selectedRuleId]
      : null;
    const selectedLocale = selectedEntry && (!selectedEntry.article || String(selectedEntry.article) === String(article))
      ? selectedEntry.en
      : null;
    if (selectedLocale?.text) return { locale: selectedLocale, specificity: "rule" };

    const articleLocale = registry?.entries?.[country]?.[String(article)]?.en
      || countryRegistry?.articles?.[String(article)]?.en
      || null;
    if (articleLocale?.text) return { locale: articleLocale, specificity: "article" };

    // Last-resort verified rule summary for this article. This is especially
    // important when the treaty is displayed as secondary protection and
    // therefore is not the selected rule, but a verified EN rule summary is
    // already present in the country registry.
    const matchingRule = Object.values(countryRegistry?.rules || {}).find((entry) =>
      String(entry?.article || "") === String(article) && entry?.en?.text
    );
    return matchingRule?.en?.text
      ? { locale: matchingRule.en, specificity: "rule" }
      : null;
  }

  function candidateSegments(text) {
    const normalized = String(text || "").replace(/\r/g, "").trim();
    if (!normalized) return [];
    const paragraphs = normalized.split(/\n{2,}/).map((part) => part.trim()).filter(Boolean);
    const segments = [];
    paragraphs.forEach((paragraph) => {
      segments.push(paragraph);
      paragraph.split(/(?<=\.)\s+(?=[A-Z0-9(])/).forEach((sentence) => {
        const trimmed = sentence.trim();
        if (trimmed && trimmed !== paragraph) segments.push(trimmed);
      });
    });
    return [...new Set(segments)];
  }

  function ratePattern(rate) {
    const numeric = Number(rate);
    if (!Number.isFinite(numeric)) return null;
    const canonical = String(numeric).replace(".", "[.,]");
    return new RegExp(`(?:^|[^0-9])${canonical}(?:[.,]0+)?\\s*(?:%|percent|per cent)`, "i");
  }

  function decisiveArticlePassage(text, citation) {
    if (!citation) return "";
    const segments = candidateSegments(text);
    if (!segments.length) return "";

    const numericRate = citation.rate === null || citation.rate === undefined || citation.rate === ""
      ? null
      : Number(citation.rate);
    if (numericRate !== null && Number.isFinite(numericRate) && numericRate > 0) {
      const pattern = ratePattern(numericRate);
      const matches = pattern ? segments.filter((segment) => pattern.test(segment)) : [];
      const minimal = matches.filter((segment) => !matches.some((other) => other !== segment && segment.includes(other)));
      if (minimal.length === 1) return minimal[0];
      return "";
    }

    const treatment = String(citation.tax_treatment || citation.resolve_tax_treatment || "");
    if (numericRate === 0 || treatment === "exclusive_foreign_taxation") {
      const explicitPatterns = [
        /\btaxable only\b/i,
        /\bshall be taxable only\b/i,
        /\bexempt from tax\b/i,
        /\bshall be exempt\b/i,
        /\bonly in (?:that|the) other (?:Contracting )?State\b/i,
      ];
      const matches = segments.filter((segment) => explicitPatterns.some((pattern) => pattern.test(segment)));
      const minimal = matches.filter((segment) => !matches.some((other) => other !== segment && segment.includes(other)));
      if (minimal.length === 1) return minimal[0];
    }

    return "";
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

  function appendWithMark(excerpt, text, decisive) {
    const start = decisive ? text.indexOf(decisive) : -1;
    if (start < 0) {
      excerpt.textContent = text;
      return false;
    }
    excerpt.append(document.createTextNode(text.slice(0, start)));
    const mark = document.createElement("mark");
    mark.className = "legal-decisive-passage";
    mark.textContent = decisive;
    excerpt.append(mark, document.createTextNode(text.slice(start + decisive.length)));
    return true;
  }

  function renderEnglishLocale(card, excerpt, resolved, article) {
    const { locale, specificity } = resolved;
    excerpt.replaceChildren();
    let decisive = "";
    if (specificity === "rule") {
      decisive = locale.text;
    } else if (String(selectedTreatyArticle || "") === String(article)) {
      decisive = decisiveArticlePassage(locale.text, selectedTreatyCitation);
    }
    const highlighted = appendWithMark(excerpt, locale.text, decisive);
    excerpt.setAttribute("lang", "en");
    excerpt.dataset.ttTreatyLanguage = "en";
    excerpt.dataset.ttTreatyLocaleStatus = locale.status || "registered";
    excerpt.dataset.ttTreatyLocaleSource = locale.source_url || "";
    excerpt.dataset.ttTreatyLocaleSpecificity = specificity;
    excerpt.dataset.ttTreatyDecisivePassage = highlighted ? "resolved" : "not-isolated";
    renderStatusNotice(card, locale);
    const details = card.querySelector("details.citation-excerpt");
    if (details && locale.status === "current_application_suspended") {
      const summary = details.querySelector("summary");
      if (summary) summary.textContent = "Treaty wording — application currently suspended";
    }
  }

  async function refreshTreatyExcerpts() {
    const targetLanguage = language();
    const cards = treatyCards();
    if (!cards.length) return;
    const [registry, jurisdictions] = await Promise.all([loadRegistry(), loadJurisdictions()]);
    const country = inferRecipientCountry(jurisdictions);
    const countryRegistry = targetLanguage === "en" && country
      ? await loadCountryRegistry(country)
      : null;

    cards.forEach((card) => {
      const excerpt = excerptNode(card);
      const article = articleNumber(card);
      if (!excerpt || !article) return;
      ensureOriginal(excerpt);

      if (targetLanguage !== "en") {
        restoreOriginal(excerpt);
        excerpt.setAttribute("lang", "cs");
        delete excerpt.dataset.ttTreatyLanguage;
        delete excerpt.dataset.ttTreatyLocaleStatus;
        delete excerpt.dataset.ttTreatyLocaleSource;
        delete excerpt.dataset.ttTreatyLocaleSpecificity;
        delete excerpt.dataset.ttTreatyDecisivePassage;
        removeMissingNote(card);
        removeStatusNotice(card);
        return;
      }

      const resolved = localeFor(registry, countryRegistry, country, article, card.dataset.ruleId || "");
      if (!country || !resolved?.locale?.text) {
        restoreOriginal(excerpt);
        excerpt.setAttribute("lang", "cs");
        excerpt.dataset.ttTreatyLanguage = "cs-fallback";
        delete excerpt.dataset.ttTreatyLocaleSpecificity;
        delete excerpt.dataset.ttTreatyDecisivePassage;
        showMissingNote(card, country || "?", article);
        removeStatusNotice(card);
        return;
      }

      renderEnglishLocale(card, excerpt, resolved, article);
      removeMissingNote(card);
    });
  }

  function schedule() {
    [0, 60, 180, 450, 900].forEach((delay) => window.setTimeout(refreshTreatyExcerpts, delay));
  }

  function installStoredResultHook() {
    const workspace = window.TaxTreatWorkspace;
    if (!workspace?.openStoredResult || workspace.openStoredResult.__ttTreatyLocaleWrapped) return;
    const original = workspace.openStoredResult;
    const wrapped = function treatyLocaleStoredResult(payload, response) {
      recipientCountry = String(payload?.recipient_country || "").toUpperCase() || recipientCountry;
      captureAnalysis(response?.analysis);
      const result = original.call(this, payload, response);
      schedule();
      return result;
    };
    wrapped.__ttTreatyLocaleWrapped = true;
    workspace.openStoredResult = wrapped;
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
    if (url.endsWith("/analysis/intake") && response.ok) {
      response.clone().json()
        .then((body) => {
          captureAnalysis(body?.analysis);
          schedule();
        })
        .catch(() => schedule());
    }
    return response;
  };

  document.addEventListener("change", (event) => {
    if (event.target?.id === "taxtreat-ui-language") schedule();
  }, true);
  document.addEventListener("click", (event) => {
    if (event.target?.closest?.('[data-next-step],[data-flow-step],[data-nav],#workspace-submit,#taxtreat-language-controls')) {
      window.setTimeout(schedule, 0);
    }
  }, true);

  installStatusStyles();
  installStoredResultHook();
  schedule();
})();
