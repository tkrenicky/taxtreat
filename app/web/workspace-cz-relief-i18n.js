(() => {
  "use strict";

  const state = {
    uiLanguage: localStorage.getItem("taxtreat-ui-language") || "cs",
    reportLanguage: localStorage.getItem("taxtreat-report-language") || "cs",
    lastIncomeType: null,
  };

  const EN = new Map([
    ["Přehled", "Overview"], ["Plátci", "Payers"], ["Příjemci", "Recipients"], ["Výsledky", "Results"], ["Zdroje", "Sources"],
    ["Aktivní plátce", "Active payer"], ["Nový výpočet →", "New calculation →"], ["Pokračovat v práci", "Continue working"],
    ["Úkoly", "Tasks"], ["Poslední výstupy", "Latest outputs"], ["Poslední výsledky", "Latest results"],
    ["Přidat plátce", "Add payer"], ["Přidat příjemce", "Add recipient"], ["Upravit příjemce", "Edit recipient"],
    ["Nový výpočet", "New calculation"], ["Plátce", "Payer"], ["Příjemce", "Recipient"], ["Platba", "Payment"], ["Výsledek", "Result"],
    ["KROK 1 ZE 4", "STEP 1 OF 4"], ["KROK 2 ZE 4", "STEP 2 OF 4"], ["KROK 3 ZE 4", "STEP 3 OF 4"], ["KROK 4 ZE 4", "STEP 4 OF 4"],
    ["Která společnost platbu provádí?", "Which company makes the payment?"], ["Komu je placeno?", "Who receives the payment?"],
    ["Údaje o platbě", "Payment details"], ["Druh příjmu *", "Income type *"], ["Vyber druh", "Select type"],
    ["Dividendy", "Dividends"], ["Úroky", "Interest"], ["Licenční poplatky", "Royalties"],
    ["Datum transakce *", "Transaction date *"], ["Hrubá částka *", "Gross amount *"], ["Měna *", "Currency *"],
    ["Ano", "Yes"], ["Ne", "No"], ["Vyber odpověď", "Select answer"], ["Vyber možnost", "Select option"],
    ["Doplňující údaje o transakci", "Additional transaction facts"], ["Použité právní pravidlo", "Applied legal rule"],
    ["Souhrn platby", "Payment summary"], ["Hrubá částka", "Gross amount"], ["Srážková daň", "Withholding tax"], ["Čistá částka", "Net amount"],
    ["Podmínky použitého pravidla", "Conditions of the applied rule"], ["Právní podklady", "Legal sources"],
    ["Daňový kalendář", "Tax calendar"], ["Rozhodné datum zadané pro výpočet", "Reference date used for the calculation"],
    ["Odvod srážkové daně", "Withholding tax remittance"], ["Oznámení příjmu plynoucího do zahraničí", "Outbound income notification"],
    ["← Upravit platbu", "← Edit payment"], ["Tisk / PDF reportu", "Print / PDF report"],
    ["ČEKÁ NA VÝPOČET", "WAITING FOR CALCULATION"], ["Srážková daň v CZK", "Withholding tax in CZK"],
    ["Česká daň k odvodu", "Czech tax payable"], ["Příjem je v České republice osvobozen", "Income is exempt from Czech withholding tax"],
    ["Daň se neodvádí", "No tax remittance"], ["Oznámení se nepodává", "No notification required"],
    ["Zatím bez výsledků", "No results yet"], ["DOKONČENO", "COMPLETED"], ["VYŽADUJE DOPLNĚNÍ", "ADDITIONAL INFORMATION REQUIRED"],
    ["Otevřít výsledek", "Open result"], ["Tisk / PDF", "Print / PDF"], ["právě vytvořeno", "just created"],
    ["Informační nástroj:", "Information tool:"], ["Právní základ", "Legal basis"], ["Právní stav", "Legal status"],
    ["Informační výstup", "Information output"], ["Informace k české srážkové dani", "Czech withholding tax information"],
    ["Výpočet daně", "Tax calculation"], ["Zadané podmínky a související podklady", "Entered conditions and supporting documentation"],
    ["Otevřené skutkové údaje", "Open factual items"], ["Související podklady", "Supporting documentation"],
    ["Oficiální zdroj ↗", "Official source ↗"], ["Zdroj", "Source"], ["Příjem", "Income"], ["Datum", "Date"], ["Částka", "Amount"],
    ["Daňový základ", "Tax base"], ["Částka zadaná pro tuto transakci", "Amount entered for this transaction"], ["Hodnota po přepočtu do CZK", "Value converted to CZK"],
    ["Neuplatňuje se", "Not applicable"], ["Neuvedena", "Not provided"], ["Žádné otevřené skutkové údaje.", "No open factual items."],
    ["Smluvní dokumentace a doklad o platbě nebo zaúčtování závazku", "Contract documentation and evidence of payment or recognition of the liability"],
    ["Potvrzení daňové rezidence a podklady ke skutečnému vlastnictví", "Tax residence certificate and beneficial ownership documentation"],
    ["Podklady ke každému skutkovému údaji použitému ve výpočtu", "Documentation supporting each factual item used in the calculation"],
    ["Doklady vyžadované pro případné vnitrostátní osvobození", "Documentation required for any domestic exemption"],
  ]);

  const REVERSE = new Map([...EN.entries()].map(([cs, en]) => [en, cs]));

  function isCzechSource() {
    return String(document.body.dataset.sourceCountry || "CZ").toUpperCase() === "CZ";
  }

  function translateDynamic(text, language) {
    let value = String(text || "");
    if (language === "cs") {
      if (REVERSE.has(value)) return REVERSE.get(value);
      return value;
    }
    if (EN.has(value)) return EN.get(value);
    value = value
      .replace(/^KROK (\d+) ZE 4$/, "STEP $1 OF 4")
      .replace(/^Sazba přiřazená podle dostupných údajů: ([0-9.,]+) %$/, "Rate assigned from available facts: $1%")
      .replace(/^([0-9.,]+) % z daňového základu$/, "$1% of the tax base")
      .replace(/^sazba ([0-9.,]+) %$/, "rate $1%")
      .replace(/^Česká srážková daň je ([0-9.,]+) %\./, "Czech withholding tax is $1%.")
      .replace(/^Podle (.+) je při zadaných údajích příjem v České republice osvobozen od srážkové daně\.$/, "Based on $1, the income is exempt from Czech withholding tax for the entered facts.")
      .replace(/^Podle (.+) se při zadaných údajích příjem v České republice nezdaňuje\.$/, "Based on $1, the income is not taxable in the Czech Republic for the entered facts.")
      .replace(/^Podle (.+) činí při zadaných údajích sazba srážkové daně ([0-9.,]+) %\.$/, "Based on $1, the withholding tax rate for the entered facts is $2%.")
      .replace(/^Smlouva o zamezení dvojího zdanění · článek /, "Double Tax Treaty · Article ")
      .replace(/^Zákon č\. 586\/1992 Sb\., o daních z příjmů · § /, "Act No. 586/1992 Coll., on Income Taxes · Section ");
    return value;
  }

  function translateSubtree(root, language = state.uiLanguage) {
    if (!root || language !== "en") return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      const original = node.nodeValue;
      const trimmed = original.trim();
      if (!trimmed) return;
      const translated = translateDynamic(trimmed, "en");
      if (translated !== trimmed) node.nodeValue = original.replace(trimmed, translated);
    });
  }

  function applyUiLanguage() {
    document.documentElement.lang = state.uiLanguage;
    document.body.dataset.uiLanguage = state.uiLanguage;
    if (state.uiLanguage === "en") translateSubtree(document.body, "en");
    const selector = document.querySelector("#taxtreat-ui-language");
    if (selector) selector.value = state.uiLanguage;
  }

  function addLanguageControls() {
    if (document.querySelector("#taxtreat-language-controls")) return;
    const host = document.querySelector(".app-header") || document.body;
    const wrap = document.createElement("div");
    wrap.id = "taxtreat-language-controls";
    wrap.style.cssText = "display:flex;align-items:center;gap:8px;margin-left:auto;font-size:12px";
    wrap.innerHTML = `
      <label style="display:flex;align-items:center;gap:5px"><span data-lang-control-label>Web</span><select id="taxtreat-ui-language" aria-label="Website language"><option value="cs">CZ</option><option value="en">EN</option></select></label>
      <label style="display:flex;align-items:center;gap:5px"><span data-report-lang-label>Report</span><select id="taxtreat-report-language" aria-label="Report language"><option value="cs">CZ</option><option value="en">EN</option></select></label>`;
    const account = host.querySelector(".account");
    if (account) host.insertBefore(wrap, account); else host.append(wrap);
    const ui = wrap.querySelector("#taxtreat-ui-language");
    const report = wrap.querySelector("#taxtreat-report-language");
    ui.value = state.uiLanguage;
    report.value = state.reportLanguage;
    ui.addEventListener("change", () => {
      state.uiLanguage = ui.value;
      localStorage.setItem("taxtreat-ui-language", state.uiLanguage);
      if (state.uiLanguage === "cs") window.location.reload();
      else applyUiLanguage();
    });
    report.addEventListener("change", () => {
      state.reportLanguage = report.value;
      localStorage.setItem("taxtreat-report-language", state.reportLanguage);
    });
  }

  function addDividendSection19Inputs() {
    const dividendFacts = document.querySelector("#dividend-facts");
    if (!dividendFacts || document.querySelector("#cz-section19-dividend")) return;
    const section = document.createElement("div");
    section.id = "cz-section19-dividend";
    section.className = "fact-question";
    section.style.cssText = "display:grid;gap:10px;padding:16px;margin-top:12px;border:1px solid #d9e3de;border-radius:10px;background:#f7faf8";
    section.innerHTML = `
      <span><b>§19</b> Podmínky českého vnitrostátního osvobození dividend</span>
      <small>Pokud jsou splněny, TaxTreat vyhodnotí osvobození podle § 19 ZDP před smluvní sazbou. Potvrď pouze skutečnosti, které jsou pro příjemce ověřeny.</small>
      <label>Je příjemce kvalifikovanou společností v přípustné právní formě?<select name="section19_qualifying_company"><option value="">Vyber odpověď</option><option value="true">Ano</option><option value="false">Ne</option></select></label>
      <label>Je příjemce daňovým rezidentem způsobilé jurisdikce a podléhá příslušné dani bez možnosti osvobození nebo nulové sazby?<select name="section19_tax_status"><option value="">Vyber odpověď</option><option value="true">Ano</option><option value="false">Ne</option></select></label>
      <label>Splňuje příjemce postavení mateřské společnosti pro účely § 19 ZDP?<select name="section19_parent_company"><option value="">Vyber odpověď</option><option value="true">Ano</option><option value="false">Ne</option></select></label>`;
    dividendFacts.append(section);
  }

  function updateSection19Visibility() {
    const section = document.querySelector("#cz-section19-dividend");
    const income = document.querySelector("#workspace-payment [name=income_type]")?.value;
    if (section) section.hidden = !(isCzechSource() && income === "dividend");
  }

  function boolFromControl(name) {
    const value = document.querySelector(`#workspace-payment [name="${name}"]`)?.value;
    if (value === "true") return true;
    if (value === "false") return false;
    return null;
  }

  function enrichCzechDividendFacts(payload) {
    if (!payload || String(payload.source_country).toUpperCase() !== "CZ" || payload.income_type !== "dividend") return payload;
    payload.facts = payload.facts && typeof payload.facts === "object" ? payload.facts : {};
    const qualifyingCompany = boolFromControl("section19_qualifying_company");
    const taxStatus = boolFromControl("section19_tax_status");
    const parentCompany = boolFromControl("section19_parent_company");
    if (qualifyingCompany !== null) payload.facts.recipient_is_qualifying_company_form = qualifyingCompany;
    if (taxStatus !== null) {
      payload.facts.recipient_is_tax_resident_in_eligible_jurisdiction = taxStatus;
      payload.facts.recipient_subject_to_qualifying_corporate_tax = taxStatus;
      payload.facts.recipient_has_no_tax_exemption_or_zero_rate_option = taxStatus;
    }
    if (parentCompany !== null) payload.facts.recipient_is_parent_company = parentCompany;
    return payload;
  }

  function addIrExemptionNotice() {
    const resultStep = document.querySelector('.flow-step[data-step="4"]');
    const reason = resultStep?.querySelector(".reason");
    if (!resultStep || !reason) return;
    let notice = resultStep.querySelector("#cz-ir-exemption-notice");
    if (!notice) {
      notice = document.createElement("article");
      notice.id = "cz-ir-exemption-notice";
      notice.className = "card";
      notice.style.cssText = "margin-top:14px;border-left:4px solid #28584f";
      reason.after(notice);
    }
    const show = isCzechSource() && ["interest", "royalty"].includes(state.lastIncomeType);
    notice.hidden = !show;
    if (!show) return;
    const noun = state.lastIncomeType === "interest" ? "úroky" : "licenční poplatky";
    notice.innerHTML = `
      <h2>Možné vnitrostátní osvobození</h2>
      <p>Bez ohledu na výše uvedenou smluvní sazbu mohou být ${noun} při splnění podmínek § 19 ZDP osvobozeny od české srážkové daně. Pro neuplatnění WHT je nutné mít účinné rozhodnutí správce daně podle § 38nb ZDP.</p>
      <p><strong>Základní podmínky:</strong> kvalifikovaná společnost a jurisdikce; alespoň 25% kvalifikované přímé kapitálové propojení; doba držby 24 měsíců (případně následné splnění za zákonných podmínek); skutečné vlastnictví příjmu; příslušné daňové a právní postavení; platba není přičitatelná diskvalifikující stálé provozovně; a rozhodnutí podle § 38nb ZDP.</p>`;
    if (state.uiLanguage === "en") {
      notice.innerHTML = `
        <h2>Potential domestic exemption</h2>
        <p>Irrespective of the treaty rate shown above, ${state.lastIncomeType === "interest" ? "interest" : "royalties"} may be exempt from Czech withholding tax if the conditions of Section 19 of the Czech Income Taxes Act are met. An effective Czech tax authority decision under Section 38nb is required in order not to apply WHT.</p>
        <p><strong>Key conditions:</strong> qualifying company and jurisdiction; at least a 25% qualifying direct capital relationship; 24-month holding period (or subsequent fulfilment where permitted by law); beneficial ownership; qualifying tax and legal status; the payment is not attributable to a disqualifying permanent establishment; and a Section 38nb decision.</p>`;
    }
  }

  function translateReportHtml(html) {
    if (state.reportLanguage !== "en" || !html) return html;
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    doc.documentElement.lang = "en";
    doc.title = "TaxTreat · Withholding tax report";
    const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      if (node.parentElement?.closest("blockquote")) return;
      const original = node.nodeValue;
      const trimmed = original.trim();
      if (!trimmed) return;
      let translated = translateDynamic(trimmed, "en");
      translated = translated
        .replace("TaxTreat automatizovaně přiřadil právní pravidlo k údajům zadaným uživatelem; nejde o individuální daňové posouzení.", "TaxTreat automatically matched a legal rule to the facts entered by the user; this is not an individual tax assessment.")
        .replace("Sazba je zobrazena jako automatizované přiřazení pravidla k zadaným údajům, nikoli jako daňové doporučení nebo stanovisko.", "The rate is shown as an automated matching of a rule to the entered facts, not as tax advice or a tax opinion.")
        .replace("Automatizovaný přehled právních pravidel a výpočtu vycházejícího z údajů zadaných uživatelem.", "Automated overview of legal rules and the calculation based on facts entered by the user.")
        .replace("Pravidlo přiřazené k zadaným údajům", "Rule assigned to the entered facts")
        .replace("Částkový výpočet nebyl uzavřen.", "The amount calculation has not been finalized.")
        .replace("Navazující lhůty nejsou pro tento výsledek k dispozici.", "Compliance deadlines are not available for this result.")
        .replace("Pro tento informační výstup nebyl přiřazen konkrétní právní zdroj.", "No specific legal source was assigned to this information output.");
      if (translated !== trimmed) node.nodeValue = original.replace(trimmed, translated);
    });
    return "<!doctype html>\n" + doc.documentElement.outerHTML;
  }

  const originalFetch = window.fetch.bind(window);
  window.fetch = async function taxTreatCzReliefFetch(resource, options = {}) {
    const url = typeof resource === "string" ? resource : resource?.url || "";
    const mutable = { ...options };
    if (url.endsWith("/analysis/intake") && mutable.body) {
      try {
        const payload = enrichCzechDividendFacts(JSON.parse(String(mutable.body)));
        state.lastIncomeType = payload.income_type || null;
        mutable.body = JSON.stringify(payload);
      } catch (_problem) {}
    }
    const response = await originalFetch(resource, mutable);
    if (url.endsWith("/analysis/report") && state.reportLanguage === "en" && response.ok) {
      try {
        const body = await response.clone().json();
        if (body?.html) body.html = translateReportHtml(body.html);
        return new Response(JSON.stringify(body), {
          status: response.status,
          statusText: response.statusText,
          headers: { "Content-Type": "application/json" },
        });
      } catch (_problem) {
        return response;
      }
    }
    if (url.endsWith("/analysis/intake")) {
      response.clone().json().then(() => window.setTimeout(addIrExemptionNotice, 0)).catch(() => {});
    }
    return response;
  };

  function boot() {
    addLanguageControls();
    addDividendSection19Inputs();
    updateSection19Visibility();
    applyUiLanguage();
    const income = document.querySelector("#workspace-payment [name=income_type]");
    income?.addEventListener("change", () => {
      state.lastIncomeType = income.value || null;
      updateSection19Visibility();
    });
    new MutationObserver((mutations) => {
      if (state.uiLanguage === "en") mutations.forEach((mutation) => mutation.addedNodes.forEach((node) => {
        if (node.nodeType === Node.ELEMENT_NODE) translateSubtree(node, "en");
      }));
      updateSection19Visibility();
    }).observe(document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ["data-source-country"] });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once: true });
  else boot();
})();
