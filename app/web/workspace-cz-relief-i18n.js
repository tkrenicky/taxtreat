(() => {
  "use strict";

  const state = {
    uiLanguage: localStorage.getItem("taxtreat-ui-language") || "cs",
    reportLanguage: localStorage.getItem("taxtreat-report-language") || "cs",
    lastIncomeType: null,
    lastAnalysis: null,
  };

  const EN = new Map([
    ["PRACOVNÍ PROSTOR", "WORKSPACE"], ["Přehled", "Overview"], ["Plátci", "Payers"], ["Příjemci", "Recipients"], ["Výsledky", "Results"], ["Zdroje", "Sources"],
    ["Aktivní plátce", "Active payer"], ["Platby, příjemci a informace navázané na zadané údaje.", "Payments, recipients and information linked to the entered facts."],
    ["Nový výpočet →", "New calculation →"], ["Pokračovat v práci", "Continue working"], ["Plátce je připraven. Můžeš zkontrolovat příjemce nebo zahájit nový výpočet.", "The payer is ready. You can review the recipient or start a new calculation."],
    ["Plátce založen", "Payer created"], ["Příjemce zkontrolován", "Recipient reviewed"], ["První výpočet dokončen", "First calculation completed"],
    ["Úkoly", "Tasks"], ["Poslední výsledky", "Latest results"], ["Zatím bez výsledků", "No results yet"], ["Po dokončení výpočtu se zde zobrazí poslední výsledky.", "The latest results will appear here after a calculation is completed."],
    ["← Ukončit průvodce", "← Exit wizard"], ["KROK 1 ZE 4", "STEP 1 OF 4"], ["KROK 2 ZE 4", "STEP 2 OF 4"], ["KROK 3 ZE 4", "STEP 3 OF 4"], ["KROK 4 ZE 4", "STEP 4 OF 4"],
    ["Která společnost platbu provádí?", "Which company makes the payment?"], ["Vyber českého plátce, ke kterému bude výpočet přiřazen.", "Select the payer to which the calculation will be assigned."],
    ["Komu je placeno?", "Who receives the payment?"], ["Vyber existujícího příjemce nebo založ nový profil.", "Select an existing recipient or create a new profile."],
    ["Vybráno", "Selected"], ["Vybrat", "Select"], ["Upravit plátce", "Edit payer"], ["+ Přidat plátce", "+ Add payer"], ["Pokračovat k příjemci →", "Continue to recipient →"],
    ["Upravit příjemce", "Edit recipient"], ["+ Založit nového příjemce", "+ Create new recipient"], ["Pokračovat k platbě →", "Continue to payment →"],
    ["Údaje o platbě", "Payment details"], ["Druh příjmu *", "Income type *"], ["Vyber druh", "Select type"], ["Dividendy", "Dividends"], ["Úroky", "Interest"], ["Licenční poplatky", "Royalties"],
    ["Datum transakce *", "Transaction date *"], ["Hrubá částka *", "Gross amount *"], ["Měna *", "Currency *"], ["Výpočet vychází z níže uvedených předpokladů", "The calculation is based on the assumptions below"],
    ["Ano", "Yes"], ["Ne", "No"], ["Vyber odpověď", "Select answer"], ["Vyber možnost", "Select option"], ["Doplňující údaje o transakci", "Additional transaction facts"],
    ["Výsledek", "Result"], ["Použité právní pravidlo", "Applied legal rule"], ["Souhrn platby", "Payment summary"], ["Hrubá částka", "Gross amount"], ["Srážková daň", "Withholding tax"], ["Čistá částka", "Net amount"],
    ["Podmínky použitého pravidla", "Conditions of the applied rule"], ["Právní podklady", "Legal sources"], ["Rozhodné datum a navazující lhůty", "Reference date and compliance deadlines"],
    ["Rozhodné datum zadané pro výpočet", "Reference date used for the calculation"], ["Odvod srážkové daně", "Withholding tax remittance"], ["Oznámení příjmu plynoucího do zahraničí", "Outbound income notification"],
    ["← Upravit platbu", "← Edit payment"], ["Tisk / PDF reportu", "Print / PDF report"], ["ČEKÁ NA VÝPOČET", "WAITING FOR CALCULATION"], ["Srážková daň v CZK", "Withholding tax in CZK"],
    ["Česká daň k odvodu", "Czech tax payable"], ["Příjem je v České republice osvobozen", "Income is exempt from Czech withholding tax"], ["Daň se neodvádí", "No tax remittance"],
    ["Informační nástroj:", "Information tool:"], ["DOKONČENO", "COMPLETED"], ["VYŽADUJE DOPLNĚNÍ", "ADDITIONAL INFORMATION REQUIRED"],
    ["Otevřít výsledek", "Open result"], ["Tisk / PDF", "Print / PDF"],
  ]);

  const ORIGINAL_TEXT = new WeakMap();

  function t(text) {
    const value = String(text || "").trim();
    if (state.uiLanguage !== "en") return value;
    if (EN.has(value)) return EN.get(value);
    return value
      .replace(/^KROK (\d+) ZE 4$/, "STEP $1 OF 4")
      .replace(/^Sazba přiřazená podle dostupných údajů: ([0-9.,]+) %$/, "Rate assigned from available facts: $1%")
      .replace(/^([0-9.,]+) % z daňového základu$/, "$1% of the tax base")
      .replace(/^Česká srážková daň je ([0-9.,]+) %\./, "Czech withholding tax is $1%.")
      .replace(/^Podle (.+) činí při zadaných údajích sazba srážkové daně ([0-9.,]+) %\.$/, "Based on $1, the withholding tax rate for the entered facts is $2%.");
  }

  function applyUiLanguage(root = document.body) {
    document.documentElement.lang = state.uiLanguage;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      const current = node.nodeValue;
      const trimmed = current.trim();
      if (!trimmed) return;
      if (!ORIGINAL_TEXT.has(node)) ORIGINAL_TEXT.set(node, current);
      const original = ORIGINAL_TEXT.get(node);
      const originalTrimmed = original.trim();
      const translated = state.uiLanguage === "en" ? t(originalTrimmed) : originalTrimmed;
      node.nodeValue = original.replace(originalTrimmed, translated);
    });
  }

  function addLanguageControl() {
    if (document.querySelector("#taxtreat-ui-language")) return;
    const header = document.querySelector(".app-header");
    if (!header) return;
    const label = document.createElement("label");
    label.id = "taxtreat-language-controls";
    label.className = "payer-context";
    label.innerHTML = '<span>Language</span><select id="taxtreat-ui-language" aria-label="Website language"><option value="cs">CZ</option><option value="en">EN</option></select>';
    const account = header.querySelector(".account");
    if (account) header.insertBefore(label, account); else header.append(label);
    const select = label.querySelector("select");
    select.value = state.uiLanguage;
    select.addEventListener("change", () => {
      state.uiLanguage = select.value;
      localStorage.setItem("taxtreat-ui-language", state.uiLanguage);
      applyUiLanguage();
      renderSection19Result();
      renderIrExemptionNotice();
    });
  }

  function addReportLanguageControl() {
    const actions = document.querySelector('.flow-step[data-step="4"] .flow-actions');
    if (!actions || document.querySelector("#taxtreat-report-language")) return;
    const label = document.createElement("label");
    label.className = "report-language-control";
    label.style.cssText = "display:flex;align-items:center;gap:8px;margin-left:auto";
    label.innerHTML = '<span>Report</span><select id="taxtreat-report-language" aria-label="Report language"><option value="cs">CZ</option><option value="en">EN</option></select>';
    const primary = actions.querySelector(".primary");
    if (primary) actions.insertBefore(label, primary); else actions.append(label);
    const select = label.querySelector("select");
    select.value = state.reportLanguage;
    select.addEventListener("change", () => {
      state.reportLanguage = select.value;
      localStorage.setItem("taxtreat-report-language", state.reportLanguage);
    });
  }

  function isCzechDividend() {
    return String(document.body.dataset.sourceCountry || "CZ").toUpperCase() === "CZ" && state.lastIncomeType === "dividend";
  }

  function section19Layer(analysis) {
    const layers = analysis?.layer_results || [];
    return layers.find((item) => item.layer === "eu_relief" && String(item.rule_id || "").includes("DIVIDEND")) || null;
  }

  function renderSection19Result() {
    const step = document.querySelector('.flow-step[data-step="4"]');
    const reason = step?.querySelector(".reason");
    if (!step || !reason) return;
    let box = step.querySelector("#cz-section19-result");
    if (!box) {
      box = document.createElement("article");
      box.id = "cz-section19-result";
      box.className = "card";
      box.style.cssText = "margin-top:14px;border-left:4px solid #28584f";
      reason.before(box);
    }
    box.hidden = !isCzechDividend();
    if (box.hidden) return;

    const analysis = state.lastAnalysis;
    const treatment = analysis?.tax_treatment || analysis?.candidate_tax_treatment;
    const layer = section19Layer(analysis);
    const finalExemption = analysis?.status === "FINAL" && treatment === "domestic_exemption";
    const failed = layer?.outcome === "not_applicable" || layer?.outcome === "failed";

    if (state.uiLanguage === "en") {
      if (finalExemption) {
        box.innerHTML = '<h2>Domestic exemption under Section 19</h2><p><strong>Applicable – Czech withholding tax is not due.</strong> The domestic exemption under Section 19 of the Czech Income Taxes Act is the primary legal basis for this result. Treaty treatment is supplementary.</p>';
      } else if (failed) {
        box.innerHTML = '<h2>Domestic exemption under Section 19</h2><p>The domestic exemption was assessed first and is not available based on the facts used in this calculation. The treaty analysis therefore determines the applicable withholding tax treatment.</p>';
      } else {
        box.innerHTML = '<h2>Domestic exemption under Section 19</h2><p><strong>Professional verification required.</strong> Section 19 is assessed before treaty relief. Any unresolved legal qualification (for example qualifying company form or tax status) is an internal professional assessment and is not a question for the payer. The treaty rate shown below is secondary until this domestic exemption layer is resolved.</p>';
      }
    } else if (finalExemption) {
      box.innerHTML = '<h2>Vnitrostátní osvobození podle § 19 ZDP</h2><p><strong>Osvobození se použije – česká srážková daň se neodvádí.</strong> Primárním právním titulem výsledku je osvobození podle § 19 ZDP; smluvní režim je pouze doplňkový.</p>';
    } else if (failed) {
      box.innerHTML = '<h2>Vnitrostátní osvobození podle § 19 ZDP</h2><p>Osvobození bylo posouzeno jako první a podle údajů použitých ve výpočtu se neuplatní. Výsledné daňové zacházení proto určuje smluvní analýza.</p>';
    } else {
      box.innerHTML = '<h2>Vnitrostátní osvobození podle § 19 ZDP</h2><p><strong>Vyžaduje odborné ověření.</strong> § 19 se posuzuje před smluvní úlevou. Neuzavřená právní kvalifikace (např. kvalifikovaná právní forma nebo daňové postavení příjemce) je interním odborným posouzením TaxTreatu, nikoli otázkou pro plátce. Smluvní sazba uvedená níže je do uzavření této vrstvy sekundární.</p>';
    }
  }

  function renderIrExemptionNotice() {
    const step = document.querySelector('.flow-step[data-step="4"]');
    const reason = step?.querySelector(".reason");
    if (!step || !reason) return;
    let notice = step.querySelector("#cz-ir-exemption-notice");
    if (!notice) {
      notice = document.createElement("article");
      notice.id = "cz-ir-exemption-notice";
      notice.className = "card";
      notice.style.cssText = "margin-top:14px;border-left:4px solid #28584f";
      reason.after(notice);
    }
    const show = String(document.body.dataset.sourceCountry || "CZ").toUpperCase() === "CZ" && ["interest", "royalty"].includes(state.lastIncomeType);
    notice.hidden = !show;
    if (!show) return;
    if (state.uiLanguage === "en") {
      notice.innerHTML = '<h2>Potential domestic exemption</h2><p>Interest or royalties may be exempt from Czech withholding tax if the statutory conditions of Section 19 are met. Non-application of WHT requires an effective Czech tax authority decision under Section 38nb.</p><p><strong>Key conditions:</strong> qualifying company and jurisdiction; qualifying 25% direct relationship; 24-month holding period; beneficial ownership; relevant tax/legal status; no disqualifying PE attribution; and the Section 38nb decision.</p>';
    } else {
      notice.innerHTML = '<h2>Možné vnitrostátní osvobození</h2><p>Úroky nebo licenční poplatky mohou být při splnění zákonných podmínek § 19 ZDP osvobozeny od české srážkové daně. Pro neuplatnění WHT je nutné účinné rozhodnutí správce daně podle § 38nb ZDP.</p><p><strong>Základní podmínky:</strong> kvalifikovaná společnost a jurisdikce; kvalifikované přímé 25% propojení; doba držby 24 měsíců; skutečné vlastnictví; příslušné daňové/právní postavení; žádná diskvalifikující vazba ke stálé provozovně; a rozhodnutí podle § 38nb ZDP.</p>';
    }
  }

  function translateReportHtml(html) {
    if (state.reportLanguage !== "en" || !html) return html;
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    doc.documentElement.lang = "en";
    doc.title = "TaxTreat · Withholding tax report";
    const replacements = new Map([
      ["Informace k české srážkové dani", "Czech withholding tax information"], ["Informační výstup", "Information output"], ["Výpočet daně", "Tax calculation"],
      ["Použité právní pravidlo", "Applied legal rule"], ["Zadané podmínky a související podklady", "Entered conditions and supporting documentation"], ["Daňový kalendář", "Tax calendar"], ["Právní základ", "Legal basis"],
      ["Hrubá částka", "Gross amount"], ["Daňový základ", "Tax base"], ["Srážková daň", "Withholding tax"], ["Česká daň k odvodu", "Czech tax payable"], ["Oficiální zdroj ↗", "Official source ↗"],
    ]);
    const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      if (node.parentElement?.closest("blockquote")) return;
      const original = node.nodeValue;
      const trimmed = original.trim();
      if (!trimmed) return;
      let translated = replacements.get(trimmed) || EN.get(trimmed) || trimmed;
      translated = translated
        .replace("Automatizovaný přehled právních pravidel a výpočtu vycházejícího z údajů zadaných uživatelem.", "Automated overview of legal rules and the calculation based on facts entered by the user.")
        .replace("TaxTreat automatizovaně přiřadil právní pravidlo k údajům zadaným uživatelem; nejde o individuální daňové posouzení.", "TaxTreat automatically matched a legal rule to the facts entered by the user; this is not an individual tax assessment.");
      if (translated !== trimmed) node.nodeValue = original.replace(trimmed, translated);
    });
    return "<!doctype html>\n" + doc.documentElement.outerHTML;
  }

  const nativeFetch = window.fetch.bind(window);
  window.fetch = async function taxTreatCzReliefFetch(resource, options = {}) {
    const url = typeof resource === "string" ? resource : resource?.url || "";
    const response = await nativeFetch(resource, options);
    if (url.endsWith("/analysis/intake") && response.ok) {
      try {
        const body = await response.clone().json();
        state.lastIncomeType = body?.analysis?.scope?.income_type || body?.scope?.income_type || state.lastIncomeType;
        state.lastAnalysis = body?.analysis || null;
        window.setTimeout(() => { renderSection19Result(); renderIrExemptionNotice(); }, 0);
      } catch (_problem) {}
    }
    if (url.endsWith("/analysis/report") && state.reportLanguage === "en" && response.ok) {
      try {
        const body = await response.clone().json();
        if (body?.html) body.html = translateReportHtml(body.html);
        return new Response(JSON.stringify(body), { status: response.status, statusText: response.statusText, headers: { "Content-Type": "application/json" } });
      } catch (_problem) { return response; }
    }
    return response;
  };

  function boot() {
    addLanguageControl();
    addReportLanguageControl();
    const income = document.querySelector('#workspace-payment [name="income_type"]');
    state.lastIncomeType = income?.value || null;
    income?.addEventListener("change", () => {
      state.lastIncomeType = income.value || null;
      renderSection19Result();
      renderIrExemptionNotice();
    });
    applyUiLanguage();
    new MutationObserver((mutations) => {
      if (state.uiLanguage !== "en") return;
      mutations.forEach((mutation) => mutation.addedNodes.forEach((node) => {
        if (node.nodeType === Node.ELEMENT_NODE) applyUiLanguage(node);
      }));
    }).observe(document.body, { subtree: true, childList: true });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once: true });
  else boot();
})();