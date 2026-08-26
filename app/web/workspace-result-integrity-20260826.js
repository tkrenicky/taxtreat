(() => {
  "use strict";

  let latest = null;
  const previousFetch = window.fetch.bind(window);

  function uiLanguage() {
    const pressed = document.querySelector('#taxtreat-language-controls .tt-lang-mini button[aria-pressed="true"]')?.dataset.lang;
    if (pressed === "en" || pressed === "cs") return pressed;
    const active = document.querySelector('#taxtreat-language-controls .tt-lang-mini button[data-active="true"]')?.dataset.lang;
    if (active === "en" || active === "cs") return active;
    const stored = localStorage.getItem("taxtreat-ui-language");
    return stored === "en" ? "en" : "cs";
  }

  const EN_TEXT = [
    [/CHYBÍ ÚDAJE PRO PŘIŘAZENÍ PRAVIDLA/g, "FACTS REQUIRED TO ASSIGN A RULE"],
    [/Srážková daň v CZK/g, "Withholding tax in CZK"],
    [/Sazbu nelze určit bez doplnění potřebných podmínek/g, "The rate cannot be determined until the required facts are completed"],
    [/Zadané údaje zatím neumožňují v TaxTreat přiřadit konkrétní právní pravidlo a sazbu\./g, "The entered facts do not yet allow TaxTreat to assign a specific legal rule and rate."],
    [/Po doplnění údajů/g, "After completing the facts"],
    [/Lhůty nelze uzavřít, dokud zadané údaje neumožní přiřadit příslušné pravidlo nebo měsíční úhrn rozhodný pro oznamovací povinnost\./g, "The deadlines cannot be finalized until the entered facts allow the applicable rule to be assigned or the monthly aggregate relevant for the notification obligation to be determined."],
    [/VÝCHOZÍ VNITROSTÁTNÍ PRAVIDLO/g, "BASE DOMESTIC RULE"],
    [/POUŽITÉ SMLUVNÍ PRAVIDLO/g, "APPLIED TREATY RULE"],
    [/SMLUVNÍ PRAVIDLO/g, "TREATY RULE"],
    [/POUŽITÉ PRAVIDLO/g, "APPLIED DOMESTIC RULE"],
    [/OBECNÁ ČESKÁ SAZBA BEZ OSVOBOZENÍ/g, "GENERAL CZECH RATE WITHOUT EXEMPTION"],
    [/SEKUNDÁRNÍ SMLUVNÍ OCHRANA/g, "SECONDARY TREATY PROTECTION"],
    [/Výše úroku mezi spojenými osobami/g, "Interest amount between associated enterprises"],
    [/Zadané údaje nepotvrzují, že výše úroku odpovídá obvyklým podmínkám\./g, "The entered facts do not confirm that the interest amount is consistent with arm's length conditions."],
    [/Oznámení se nepodává/g, "No notification required"],
    [/Česká daň se neodvádí\./g, "No Czech tax is remitted."],
    [/\b([0-9][0-9\s.,]*)\s*Kč\b/g, "$1 CZK"],
    [/\bKč\b/g, "CZK"]
  ];

  function translateEnglish(root) {
    if (!root || uiLanguage() !== "en") return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      let value = node.nodeValue || "";
      EN_TEXT.forEach(([pattern, replacement]) => { value = value.replace(pattern, replacement); });
      if (value !== node.nodeValue) node.nodeValue = value;
    });
  }

  function forceLegalSourceRoles(step) {
    if (uiLanguage() !== "en") return;
    step.querySelectorAll('.citation-role').forEach((role) => {
      const raw = String(role.textContent || "").trim();
      const position = raw.match(/^\s*(\d+)\./)?.[1] || "";
      const prefix = position ? `${position}. ` : "";
      if (/VÝCHOZÍ VNITROSTÁTNÍ PRAVIDLO/i.test(raw)) role.textContent = `${prefix}BASE DOMESTIC RULE`;
      else if (/POUŽITÉ SMLUVNÍ PRAVIDLO/i.test(raw)) role.textContent = `${prefix}APPLIED TREATY RULE`;
      else if (/SMLUVNÍ PRAVIDLO/i.test(raw)) role.textContent = `${prefix}TREATY RULE`;
      else if (/POUŽITÉ PRAVIDLO/i.test(raw)) role.textContent = `${prefix}APPLIED DOMESTIC RULE`;
      else if (/OBECNÁ ČESKÁ SAZBA BEZ OSVOBOZENÍ/i.test(raw)) role.textContent = `${prefix}GENERAL CZECH RATE WITHOUT EXEMPTION`;
      else if (/SEKUNDÁRNÍ SMLUVNÍ OCHRANA/i.test(raw)) role.textContent = `${prefix}SECONDARY TREATY PROTECTION`;
    });
  }

  function reasonItems() {
    if (!latest) return [];
    const items = [];
    const seen = new Set();
    const push = (title, detail) => {
      const t = String(title || "").trim();
      const d = String(detail || "").trim();
      const key = `${t}|${d}`;
      if ((!t && !d) || seen.has(key)) return;
      seen.add(key);
      items.push({ title:t, detail:d });
    };
    (latest.intake?.review_reasons || []).forEach((item) => push(item.title, item.detail));
    (latest.intake?.questions || []).forEach((q) => push(q.prompt, q.why));
    return items;
  }

  function enReason(value) {
    let text = String(value || "");
    EN_TEXT.forEach(([pattern, replacement]) => { text = text.replace(pattern, replacement); });
    return text;
  }

  function renderWhyUnresolved(step) {
    let card = step.querySelector("#tt-unresolved-reasons");
    const unresolved = latest?.analysis && latest.analysis.status !== "FINAL";
    if (!unresolved) {
      if (card) card.remove();
      return;
    }
    if (!card) {
      card = document.createElement("article");
      card.id = "tt-unresolved-reasons";
      card.className = "card";
      card.style.cssText = "margin-top:14px;border-left:4px solid #9b6a20";
      const reason = step.querySelector(".reason");
      (reason || step.querySelector(".result-hero"))?.after(card);
    }
    const en = uiLanguage() === "en";
    const items = reasonItems();
    const title = en ? "Why the result cannot be finalized" : "Proč výsledek zatím nelze uzavřít";
    const fallback = en
      ? "TaxTreat is missing at least one fact needed to determine the applicable legal rule. Return to the payment step and complete the missing factual item(s)."
      : "TaxTreat chybí alespoň jeden skutkový údaj potřebný k určení použitelného právního pravidla. Vrať se ke kroku platby a doplň chybějící údaj(e).";
    let html = `<h2>${title}</h2>`;
    if (!items.length) html += `<p>${fallback}</p>`;
    else html += "<ul>" + items.map((item) => {
      const heading = en ? enReason(item.title || "Missing condition") : (item.title || "Chybějící podmínka");
      const detailText = en ? enReason(item.detail) : item.detail;
      const detail = detailText ? `<br><small>${detailText}</small>` : "";
      return `<li><strong>${heading}</strong>${detail}</li>`;
    }).join("") + "</ul>";
    card.innerHTML = html;
  }

  function fixExemptionNotice(step) {
    const notice = step.querySelector("#cz-ir-exemption-notice");
    if (!notice) return;
    const final = latest?.analysis?.status === "FINAL";
    notice.hidden = !final;
    if (!final) return;
    if (uiLanguage() === "en") {
      notice.innerHTML = '<h2>Potential domestic exemption — not assessed in this calculation</h2><p>This calculation does not test the statutory conditions for the Czech interest/royalty exemption. A separate exemption may be available only if all statutory conditions are met and an effective Czech tax authority decision under Section 38nb is obtained.</p><p><strong>Eligibility snapshot:</strong> qualifying company and jurisdiction; qualifying 25% direct relationship; 24-month holding period; beneficial ownership; relevant tax/legal status; no disqualifying PE attribution; and the Section 38nb decision.</p>';
    } else {
      notice.innerHTML = '<h2>Možné vnitrostátní osvobození — v tomto výpočtu neposuzováno</h2><p>Tento výpočet neposuzuje zákonné podmínky českého osvobození úroků/licenčních poplatků. Samostatné osvobození může být dostupné pouze při splnění všech zákonných podmínek a po získání účinného rozhodnutí správce daně podle § 38nb ZDP.</p><p><strong>Orientační podmínky:</strong> kvalifikovaná společnost a jurisdikce; kvalifikované přímé 25% propojení; doba držby 24 měsíců; skutečné vlastnictví; příslušné daňové/právní postavení; žádná diskvalifikující vazba ke stálé provozovně; a rozhodnutí podle § 38nb ZDP.</p>';
    }
  }

  function patch() {
    const step = document.querySelector('.flow-step[data-step="4"].active');
    if (!step) return;
    renderWhyUnresolved(step);
    fixExemptionNotice(step);
    translateEnglish(step);
    forceLegalSourceRoles(step);
  }

  function patchBurst() {
    [0, 25, 75, 160, 350, 700].forEach((delay) => window.setTimeout(patch, delay));
  }

  window.fetch = async function taxTreatResultIntegrityFetch(resource, options = {}) {
    const url = typeof resource === "string" ? resource : resource?.url || "";
    const response = await previousFetch(resource, options);
    if (url.endsWith("/analysis/intake") && response.ok) {
      try { latest = await response.clone().json(); } catch (_problem) {}
      patchBurst();
    }
    return response;
  };

  document.addEventListener("click", (event) => {
    if (event.target?.closest?.('[data-next-step], #taxtreat-language-controls, button[type="submit"]')) patchBurst();
  }, true);
  document.addEventListener("change", (event) => {
    if (event.target?.id === "taxtreat-ui-language") patchBurst();
  }, true);

  let observerTimer = 0;
  new MutationObserver((mutations) => {
    if (!mutations.some((m) => m.type === "characterData" || m.addedNodes?.length)) return;
    clearTimeout(observerTimer);
    observerTimer = window.setTimeout(() => {
      patch();
      window.setTimeout(patch, 60);
    }, 10);
  }).observe(document.documentElement, { childList:true, subtree:true, characterData:true });

  patchBurst();
})();