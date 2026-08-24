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

  function localeFor(registry, countryRegistry, country, article) {
    const ruleEntry = selectedRuleId && String(selectedTreatyArticle || "") === String(article)
      ? countryRegistry?.rules?.[selectedRuleId]
      : null;
    const ruleLocale = ruleEntry && (!ruleEntry.article || String(ruleEntry.article) === String(article))
      ? ruleEntry.en
      : null;
    if (ruleLocale?.text) return { locale: ruleLocale, specificity: "rule" };

    const articleLocale = registry?.entries?.[country]?.[String(article)]?.en
      || countryRegistry?.articles?.[String(article)]?.en
      || null;
    return articleLocale?.text ? { locale: articleLocale, specificity: "article" } : null;
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

  function renderEnglishLocale(excerpt, resolved, article) {
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
        return;
      }

      const resolved = localeFor(registry, countryRegistry, country, article);
      if (!country || !resolved?.locale?.text) {
        restoreOriginal(excerpt);
        excerpt.setAttribute("lang", "cs");
        excerpt.dataset.ttTreatyLanguage = "cs-fallback";
        delete excerpt.dataset.ttTreatyLocaleSpecificity;
        delete excerpt.dataset.ttTreatyDecisivePassage;
        showMissingNote(card, country || "?", article);
        return;
      }

      renderEnglishLocale(excerpt, resolved, article);
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
  document.addEventListener("click", () => window.setTimeout(schedule, 0), true);

  installStoredResultHook();
  schedule();
})();
