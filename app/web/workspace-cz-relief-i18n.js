(() => {
  "use strict";

  const state = {
    uiLanguage: localStorage.getItem("taxtreat-ui-language") || "cs",
    reportLanguage: localStorage.getItem("taxtreat-report-language") || "cs",
    lastIncomeType: null,
    lastAnalysis: null,
  };

  const SECTION19_ELIGIBLE = new Set([
    "AT","BE","BG","HR","CY","CZ","DK","EE","FI","FR","DE","GR","HU","IE","IT","LV","LT","LU","MT","NL","PL","PT","RO","SK","SI","ES","SE",
    "CH","NO","IS","LI"
  ]);

  const EN = new Map([
    ["PRACOVNÍ PROSTOR", "WORKSPACE"], ["Přehled", "Overview"], ["Plátci", "Payers"], ["Příjemci", "Recipients"], ["Výsledky", "Results"], ["Zdroje", "Sources"],
    ["Aktivní plátce", "Active payer"], ["Platby, příjemci a informace navázané na zadané údaje.", "Payments, recipients and information linked to the entered facts."],
    ["Nový výpočet →", "New calculation →"], ["Pokračovat v práci", "Continue working"], ["Plátce je připraven. Můžeš zkontrolovat příjemce nebo zahájit nový výpočet.", "The payer is ready. You can review the recipient or start a new calculation."],
    ["Plátce založen", "Payer created"], ["Příjemce zkontrolován", "Recipient reviewed"], ["První výpočet dokončen", "First calculation completed"],
    ["Úkoly", "Tasks"], ["Poslední výstupy", "Latest outputs"], ["Poslední výsledky", "Latest results"], ["Zatím bez výstupů", "No outputs yet"], ["Zatím bez výsledků", "No results yet"],
    ["Po dokončení výpočtu se zde zobrazí informační výstup podle zadaných údajů.", "An information output based on the entered facts will appear here after a calculation is completed."],
    ["Po dokončení výpočtu se zde zobrazí poslední výsledky.", "The latest results will appear here after a calculation is completed."],
    ["Doklad k případnému smluvnímu nároku není evidován", "Evidence supporting a potential treaty claim is not recorded"], ["Otevřít profil →", "Open profile →"],
    ["ORGANIZACE", "ORGANIZATIONS"], ["České subjekty, jejichž platby jsou v TaxTreat zpracovávány.", "Entities whose payments are processed in TaxTreat."], ["Přidat plátce", "Add payer"],
    ["PROFILY PRO OPAKOVANÉ POUŽITÍ", "REUSABLE PROFILES"], ["Skutkové údaje a podklady použitelné pro další platby stejnému příjemci.", "Facts and supporting documents reusable for future payments to the same recipient."], ["Přidat příjemce", "Add recipient"],
    ["Základní údaje vyplněny", "Basic details completed"], ["Doklad rezidentství neevidován", "Residence certificate not recorded"], ["Upravit", "Edit"], ["Otevřít →", "Open →"],
    ["← Zpět na příjemce", "← Back to recipients"], ["Základní profil", "Basic profile"], ["Údaje vyplněny", "Details completed"], ["Dokumenty", "Documents"], ["Historie plateb", "Payment history"], ["Zatím bez plateb", "No payments yet"],
    ["VÝSLEDKY A REPORTY", "RESULTS AND REPORTS"], ["Výsledek výpočtu a report pro každou dokončenou platbu.", "Calculation result and report for each completed payment."], ["Zatím bez výpočtů", "No calculations yet"],
    ["DŮKAZNÍ ZÁKLAD", "EVIDENCE BASE"], ["Smluvní texty a evidované zdroje použité v konkrétních výsledcích.", "Treaty texts and recorded sources used in individual results."], ["Podporované jurisdikce", "Supported jurisdictions"], ["Pokryté kombinace", "Covered combinations"], ["Příjmové kategorie", "Income categories"], ["Podklady použité ve výsledku", "Sources used in the result"],
    ["← Ukončit průvodce", "← Exit wizard"], ["KROK 1 ZE 4", "STEP 1 OF 4"], ["KROK 2 ZE 4", "STEP 2 OF 4"], ["KROK 3 ZE 4", "STEP 3 OF 4"], ["KROK 4 ZE 4", "STEP 4 OF 4"],
    ["Která společnost platbu provádí?", "Which company makes the payment?"], ["Vyber českého plátce, ke kterému bude výpočet přiřazen.", "Select the payer to which the calculation will be assigned."], ["Vybráno", "Selected"], ["Vybrat", "Select"], ["Upravit plátce", "Edit payer"], ["+ Přidat plátce", "+ Add payer"], ["Pokračovat k příjemci →", "Continue to recipient →"],
    ["Komu je placeno?", "Who receives the payment?"], ["Vyber existujícího příjemce nebo založ nový profil.", "Select an existing recipient or create a new profile."], ["Upravit příjemce", "Edit recipient"], ["+ Založit nového příjemce", "+ Create new recipient"], ["← Zpět k plátci", "← Back to payer"], ["Pokračovat k platbě →", "Continue to payment →"],
    ["Základní profil příjemce", "Recipient basic profile"], ["Název nebo jméno *", "Name *"], ["Stát daňové rezidence *", "Tax residence country *"], ["Vyber stát", "Select country"], ["Typ příjemce *", "Recipient type *"], ["Společnost", "Company"], ["Fyzická osoba", "Individual"], ["Fond", "Fund"], ["Jiný subjekt", "Other entity"], ["Použít příjemce v této kontrole →", "Use recipient in this calculation →"],
    ["Údaje o platbě", "Payment details"], ["Označuje povinný údaj.", "Required field."], ["Druh příjmu *", "Income type *"], ["Vyber druh", "Select type"], ["Dividendy", "Dividends"], ["Úroky", "Interest"], ["Licenční poplatky", "Royalties"], ["Datum transakce *", "Transaction date *"], ["Hrubá částka *", "Gross amount *"], ["Měna *", "Currency *"], ["Kurz v CZK za 1 jednotku měny", "CZK exchange rate per 1 unit of currency"],
    ["Výpočet vychází z níže uvedených předpokladů", "The calculation is based on the assumptions below"], ["Předvyplněné odpovědi zkontroluj a změň, pokud pro danou platbu neplatí.", "Review the pre-filled answers and change them if they do not apply to this payment."], ["Příjemce je skutečným vlastníkem příjmu.", "The recipient is the beneficial owner of the income."], ["Ano", "Yes"], ["Ne", "No"],
    ["ÚDAJE PODLE DRUHU PŘÍJMU", "INCOME-SPECIFIC FACTS"], ["Doplňující údaje o transakci", "Additional transaction facts"], ["Vyplň dostupné skutkové údaje před výpočtem. Údaje uložené v profilu příjemce jsou předvyplněny a lze je pro tuto platbu změnit.", "Complete the available transaction facts before calculation. Facts stored in the recipient profile are pre-filled and can be changed for this payment."],
    ["Vyber odpověď", "Select answer"], ["Ano, přímo", "Yes, directly"], ["Ne, nepřímo", "No, indirectly"], ["Znám datum nabytí podílu", "I know the acquisition date"], ["K datu transakce alespoň 12 měsíců", "At least 12 months as of the transaction date"], ["K datu transakce méně než 12 měsíců", "Less than 12 months as of the transaction date"], ["Datum nabytí podílu", "Share acquisition date"],
    ["Předmět licenční platby", "Royalty subject"], ["Vyber možnost", "Select option"], ["Autorské dílo", "Copyright work"], ["Software, patent, ochranná známka nebo know-how", "Software, patent, trademark or know-how"], ["Průmyslové, obchodní nebo vědecké zařízení", "Industrial, commercial or scientific equipment"], ["Jiný předmět licence", "Other royalty subject"],
    ["DOPLŇUJÍCÍ SKUTKOVÉ ÚDAJE", "ADDITIONAL FACTS"], ["Údaje potřebné pro dokončení výpočtu", "Facts needed to complete the calculation"], ["Zobrazit pravidla a výpočet →", "Show rules and calculation →"], ["Doplnit údaje a aktualizovat výpočet →", "Complete facts and update calculation →"], ["← Zpět k příjemci", "← Back to recipient"],
    ["Výsledek", "Result"], ["Použité právní pravidlo", "Applied legal rule"], ["Souhrn platby", "Payment summary"], ["Hrubá částka", "Gross amount"], ["Srážková daň", "Withholding tax"], ["Čistá částka", "Net amount"], ["Podmínky použitého pravidla", "Conditions of the applied rule"], ["Právní podklady", "Legal sources"],
    ["Rozhodné datum a navazující lhůty", "Reference date and compliance deadlines"], ["Rozhodné datum zadané pro výpočet", "Reference date used for the calculation"], ["Odvod srážkové daně", "Withholding tax remittance"], ["Oznámení příjmu plynoucího do zahraničí", "Outbound income notification"], ["← Upravit platbu", "← Edit payment"], ["Tisk / PDF reportu", "Print / PDF report"], ["ČEKÁ NA VÝPOČET", "WAITING FOR CALCULATION"], ["VÝPOČET DOKONČEN", "CALCULATION COMPLETED"], ["CHYBÍ ÚDAJE PRO PŘIŘAZENÍ PRAVIDLA", "FACTS REQUIRED TO ASSIGN A RULE"], ["Srážková daň v CZK", "Withholding tax in CZK"], ["Česká daň k odvodu", "Czech tax payable"], ["Příjem je v České republice osvobozen", "Income is exempt from Czech withholding tax"], ["Daň se neodvádí", "No tax remittance"], ["Oznámení se nepodává", "No notification required"], ["Po doplnění údajů", "After completing the facts"],
    ["Všechny údaje potřebné pro výpočet jsou zadány", "All facts required for the calculation are entered"], ["Výsledek vychází z uvedených údajů a zobrazeného právního základu.", "The result is based on the entered facts and the legal basis shown."], ["Oficiální zdroj ↗", "Official source ↗"], ["Informační nástroj:", "Information tool:"],
    ["Možné vnitrostátní osvobození", "Potential domestic exemption"], ["Vnitrostátní osvobození", "Domestic exemption"],
  ]);

  const ORIGINAL_TEXT = new WeakMap();
  const ORIGINAL_ATTR = new WeakMap();

  function translateDynamic(value) {
    const text = String(value || "").trim();
    if (state.uiLanguage !== "en") return text;
    if (EN.has(text)) return EN.get(text);
    return text
      .replace(/^KROK (\d+) ZE 4$/, "STEP $1 OF 4")
      .replace(/^([0-9]+) údaje?$/, "$1 facts")
      .replace(/^Sazba přiřazená podle dostupných údajů: ([0-9.,]+) %$/, "Rate assigned from available facts: $1%")
      .replace(/^([0-9.,]+) % z daňového základu$/, "$1% of the tax base")
      .replace(/^Česká srážková daň je ([0-9.,]+) %\./, "Czech withholding tax is $1%.")
      .replace(/^Podle (.+) činí při zadaných údajích sazba srážkové daně ([0-9.,]+) %\.$/, "Based on $1, the withholding tax rate for the entered facts is $2%.")
      .replace(/^Česká republika · IČO /, "Czech Republic · Company ID ")
      .replace(/ · DIČ /g, " · Tax ID ")
      .replace(/ · společnost · základní údaje vyplněny$/, " · company · basic details completed")
      .replace(/^Rakousko$/, "Austria")
      .replace(/^Německo$/, "Germany")
      .replace(/^Švýcarsko$/, "Switzerland")
      .replace(/^Singapur$/, "Singapore")
      .replace(/^Tchaj-wan$/, "Taiwan")
      .replace(/^společnost$/, "company")
      .replace(/^Nevyplněno$/, "Not provided");
  }

  function applyAttributes(root) {
    const elements = [root, ...(root?.querySelectorAll ? root.querySelectorAll("[placeholder],[aria-label],[title]") : [])].filter(Boolean);
    elements.forEach((element) => {
      ["placeholder", "aria-label", "title"].forEach((name) => {
        if (!element.hasAttribute?.(name)) return;
        let stored = ORIGINAL_ATTR.get(element);
        if (!stored) { stored = {}; ORIGINAL_ATTR.set(element, stored); }
        if (!(name in stored)) stored[name] = element.getAttribute(name);
        const original = stored[name];
        if (state.uiLanguage === "cs") element.setAttribute(name, original);
        else element.setAttribute(name, translateDynamic(original));
      });
    });
  }

  function applyUiLanguage(root = document.body) {
    if (!root) return;
    document.documentElement.lang = state.uiLanguage;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      if (node.parentElement?.closest("blockquote,pre,code,.legal-excerpt")) return;
      const current = node.nodeValue;
      const trimmed = current.trim();
      if (!trimmed) return;
      if (!ORIGINAL_TEXT.has(node)) ORIGINAL_TEXT.set(node, current);
      const original = ORIGINAL_TEXT.get(node);
      const originalTrimmed = original.trim();
      const translated = state.uiLanguage === "en" ? translateDynamic(originalTrimmed) : originalTrimmed;
      node.nodeValue = original.replace(originalTrimmed, translated);
    });
    applyAttributes(root);
  }

  function addLanguageControl() {
    if (document.querySelector("#taxtreat-ui-language")) return;
    const header = document.querySelector(".app-header");
    if (!header) return;
    const label = document.createElement("label");
    label.id = "taxtreat-language-controls";
    label.className = "payer-context";
    label.innerHTML = '<span>Jazyk</span><select id="taxtreat-ui-language" aria-label="Jazyk webu"><option value="cs">CZ</option><option value="en">EN</option></select>';
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
    label.innerHTML = '<span>Jazyk reportu</span><select id="taxtreat-report-language" aria-label="Jazyk reportu"><option value="cs">CZ</option><option value="en">EN</option></select>';
    const primary = actions.querySelector(".primary");
    if (primary) actions.insertBefore(label, primary); else actions.append(label);
    const select = label.querySelector("select");
    select.value = state.reportLanguage;
    select.addEventListener("change", () => {
      state.reportLanguage = select.value;
      localStorage.setItem("taxtreat-report-language", state.reportLanguage);
    });
  }

  function syncSection19Visibility() {
    const box = document.querySelector("#cz-section19-facts");
    if (!box) return;
    const isCz = String(document.body.dataset.sourceCountry || "CZ").toUpperCase() === "CZ";
    box.hidden = !isCz;
    box.querySelectorAll("select").forEach((field) => {
      field.required = isCz && document.querySelector('#workspace-payment [name="income_type"]')?.value === "dividend";
    });
  }

  function addSection19Questions() {
    const root = document.querySelector("#dividend-facts");
    if (!root || document.querySelector("#cz-section19-facts")) return;
    const box = document.createElement("section");
    box.id = "cz-section19-facts";
    box.className = "fact-question";
    box.style.cssText = "display:grid;gap:14px;padding:16px;margin-top:12px;border:1px solid #d9e3de;border-radius:10px;background:#f7faf8";
    box.innerHTML = `
      <div><strong>Ještě dva údaje pro možné osvobození</strong><small style="display:block;margin-top:5px">Podíl, přímé držení, dobu držby, skutečné vlastnictví a vazbu ke stálé provozovně už TaxTreat používá z odpovědí výše.</small></div>
      <label><span>Je příjemce běžnou obchodní společností (např. GmbH, AG, Ltd. nebo S.A.), nikoli fyzickou osobou, fondem nebo daňově transparentním subjektem?</span><select name="section19_company_form"><option value="">Vyber odpověď</option><option value="true">Ano</option><option value="false">Ne</option></select><small>Pokud si nejsi jistý právní formou příjemce, zvol raději „Ne“ nebo údaj ověř v korporátních podkladech.</small></label>
      <label><span>Podléhá příjemce ve státě své daňové rezidence běžné dani z příjmů právnických osob a není od této daně osvobozen ani v režimu s nulovou sazbou?</span><select name="section19_taxable_company"><option value="">Vyber odpověď</option><option value="true">Ano</option><option value="false">Ne</option></select><small>Jde o faktické daňové postavení příjemce, nikoli o posouzení českého § 19.</small></label>`;
    root.append(box);
    applyUiLanguage(box);
    syncSection19Visibility();
  }

  function boolField(name) {
    const value = document.querySelector(`#workspace-payment [name="${name}"]`)?.value;
    if (value === "true") return true;
    if (value === "false") return false;
    return null;
  }

  function enrichSection19Facts(payload) {
    if (!payload || String(payload.source_country || "").toUpperCase() !== "CZ" || payload.income_type !== "dividend") return payload;
    payload.facts = payload.facts && typeof payload.facts === "object" ? payload.facts : {};
    const companyForm = boolField("section19_company_form");
    const taxableCompany = boolField("section19_taxable_company");
    const recipientCountry = String(payload.recipient_country || "").toUpperCase();
    const ownership = Number(payload.facts.ownership_percent || 0);
    const direct = payload.facts.direct_ownership === true;
    const company = payload.facts.recipient_entity_type === "company";

    if (companyForm !== null) payload.facts.recipient_is_qualifying_company_form = companyForm;
    payload.facts.recipient_is_tax_resident_in_eligible_jurisdiction = SECTION19_ELIGIBLE.has(recipientCountry);
    if (taxableCompany !== null) {
      payload.facts.recipient_subject_to_qualifying_corporate_tax = taxableCompany;
      payload.facts.recipient_has_no_tax_exemption_or_zero_rate_option = taxableCompany;
    }
    payload.facts.recipient_is_parent_company = Boolean(company && direct && ownership >= 10);
    return payload;
  }

  function resultIncomeType() {
    return document.querySelector('.flow-step[data-step="4"]')?.dataset.incomeType || state.lastIncomeType || "";
  }

  function isCzechDividend() {
    return String(document.body.dataset.sourceCountry || "CZ").toUpperCase() === "CZ" && resultIncomeType() === "dividend";
  }

  function section19Layers(analysis) {
    return (analysis?.layer_results || []).filter((item) => item.layer === "eu_relief" && String(item.rule_id || "").includes("DIVIDEND"));
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
    const analysis = state.lastAnalysis;
    const treatment = analysis?.tax_treatment || analysis?.candidate_tax_treatment;
    const layers = section19Layers(analysis);
    const finalExemption = analysis?.status === "FINAL" && treatment === "domestic_exemption";
    box.hidden = !isCzechDividend() || (!finalExemption && !layers.length);
    if (box.hidden) return;
    const applicable = layers.some((item) => item.outcome === "applicable");
    const unresolved = layers.some((item) => item.outcome === "unresolved");
    const allNotApplicable = layers.length > 0 && layers.every((item) => ["not_applicable","failed"].includes(item.outcome));

    if (state.uiLanguage === "en") {
      if (finalExemption || applicable) box.innerHTML = '<h2>Domestic exemption</h2><p><strong>Applicable – Czech withholding tax is not due.</strong> The domestic exemption under Section 19 of the Czech Income Taxes Act is the primary legal basis. Treaty treatment is supplementary.</p>';
      else if (allNotApplicable) box.innerHTML = '<h2>Domestic exemption</h2><p>The domestic exemption was assessed first and is not available based on the entered facts. The treaty analysis therefore determines the withholding tax treatment.</p>';
      else if (unresolved || !analysis) box.innerHTML = '<h2>Domestic exemption</h2><p><strong>Not yet resolved.</strong> Complete the remaining factual items before the exemption can be concluded.</p>';
      else box.innerHTML = '<h2>Domestic exemption</h2><p>Section 19 was assessed before treaty relief. The treaty result shown below applies only if the domestic exemption is not available.</p>';
    } else {
      if (finalExemption || applicable) box.innerHTML = '<h2>Vnitrostátní osvobození</h2><p><strong>Osvobození se použije – česká srážková daň se neodvádí.</strong> Primárním právním titulem je § 19 ZDP; smluvní režim je pouze doplňkový.</p>';
      else if (allNotApplicable) box.innerHTML = '<h2>Vnitrostátní osvobození</h2><p>Osvobození bylo posouzeno jako první a podle zadaných údajů se neuplatní. Daňové zacházení proto určuje smluvní analýza.</p>';
      else if (unresolved || !analysis) box.innerHTML = '<h2>Vnitrostátní osvobození</h2><p><strong>Zatím nelze uzavřít.</strong> Pro uzavření osvobození je nutné doplnit zbývající skutkové údaje.</p>';
      else box.innerHTML = '<h2>Vnitrostátní osvobození</h2><p>§ 19 byl posouzen před smluvní úlevou. Smluvní výsledek uvedený níže se použije pouze tehdy, pokud vnitrostátní osvobození není dostupné.</p>';
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
    const show = String(document.body.dataset.sourceCountry || "CZ").toUpperCase() === "CZ" && ["interest", "royalty"].includes(resultIncomeType());
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
    const map = new Map([
      ["Informace k české srážkové dani", "Czech withholding tax information"], ["Informační výstup", "Information output"], ["Výpočet daně", "Tax calculation"], ["Použité právní pravidlo", "Applied legal rule"], ["Zadané podmínky a související podklady", "Entered conditions and supporting documentation"], ["Otevřené skutkové údaje", "Open factual items"], ["Související podklady", "Supporting documentation"], ["Daňový kalendář", "Tax calendar"], ["Právní základ", "Legal basis"], ["Právní stav", "Legal status"], ["Pravidlo přiřazené k zadaným údajům", "Rule assigned to the entered facts"], ["Zdroj", "Source"], ["Příjemce", "Recipient"], ["Příjem", "Income"], ["Datum", "Date"], ["Částka", "Amount"], ["Hrubá částka", "Gross amount"], ["Daňový základ", "Tax base"], ["Srážková daň", "Withholding tax"], ["Česká daň k odvodu", "Czech tax payable"], ["Kurz ČNB", "CNB exchange rate"], ["Oficiální zdroj ↗", "Official source ↗"], ["Žádné otevřené skutkové údaje.", "No open factual items."], ["Neuplatňuje se", "Not applicable"], ["Neuvedena", "Not provided"],
      ["Smluvní dokumentace a doklad o platbě nebo zaúčtování závazku", "Contract documentation and evidence of payment or recognition of the liability"], ["Potvrzení daňové rezidence a podklady ke skutečnému vlastnictví", "Tax residence certificate and beneficial ownership documentation"], ["Podklady ke každému skutkovému údaji použitému ve výpočtu", "Documentation supporting each factual item used in the calculation"], ["Doklady vyžadované pro případné vnitrostátní osvobození", "Documentation required for any domestic exemption"],
      ["Možné vnitrostátní osvobození", "Potential domestic exemption"],
      ["Úroky nebo licenční poplatky mohou být při splnění zákonných podmínek § 19 ZDP osvobozeny od české srážkové daně. Pro neuplatnění srážkové daně je nutné účinné rozhodnutí správce daně podle § 38nb ZDP.", "Interest or royalties may be exempt from Czech withholding tax if the statutory conditions of Section 19 are met. Non-application of withholding tax requires an effective Czech tax authority decision under Section 38nb."],
      ["Základní podmínky:", "Key conditions:"],

    ]);
    const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      if (node.parentElement?.closest("blockquote")) return;
      const original = node.nodeValue;
      const trimmed = original.trim();
      if (!trimmed) return;
      let translated = map.get(trimmed) || trimmed;
      translated = translated
        .replace("Automatizovaný přehled právních pravidel a výpočtu vycházejícího z údajů zadaných uživatelem.", "Automated overview of legal rules and the calculation based on facts entered by the user.")
        .replace("TaxTreat automatizovaně přiřadil právní pravidlo k údajům zadaným uživatelem; nejde o individuální daňové posouzení.", "TaxTreat automatically matched a legal rule to the facts entered by the user; this is not an individual tax assessment.")
        .replace("Sazba je zobrazena jako automatizované přiřazení pravidla k zadaným údajům, nikoli jako daňové doporučení nebo stanovisko.", "The rate is shown as an automated matching of a rule to the entered facts, not as tax advice or a tax opinion.")
        .replace("Částka zadaná pro tuto transakci", "Amount entered for this transaction")
        .replace("Hodnota po přepočtu do CZK", "Value converted to CZK")
        .replace("Částkový výpočet nebyl uzavřen.", "The amount calculation has not been finalized.")
        .replace("Navazující lhůty nejsou pro tento výsledek k dispozici.", "Compliance deadlines are not available for this result.")
        .replace("Pro tento informační výstup nebyl přiřazen konkrétní právní zdroj.", "No specific legal source was assigned to this information output.")
        .replace(/^Smlouva o zamezení dvojího zdanění · článek /, "Double Tax Treaty · Article ")
        .replace(/^Zákon č\. 586\/1992 Sb\., o daních z příjmů · § /, "Act No. 586/1992 Coll., on Income Taxes · Section ")
        .replace("kvalifikovaná společnost a jurisdikce; kvalifikované přímé 25% propojení; doba držby 24 měsíců; skutečné vlastnictví; příslušné daňové a právní postavení; žádná diskvalifikující vazba ke stálé provozovně; a účinné rozhodnutí podle § 38nb ZDP.", "qualifying company and jurisdiction; qualifying 25% direct relationship; 24-month holding period; beneficial ownership; relevant tax and legal status; no disqualifying PE attribution; and an effective Section 38nb decision.")
        .replace(/^Dividendy$/, "Dividends").replace(/^Úroky$/, "Interest").replace(/^Licenční poplatky$/, "Royalties");
      if (translated !== trimmed) node.nodeValue = original.replace(trimmed, translated);
    });
    return "<!doctype html>\n" + doc.documentElement.outerHTML;
  }

  const previousFetch = window.fetch.bind(window);
  window.fetch = async function taxTreatCzReliefFetch(resource, options = {}) {
    const url = typeof resource === "string" ? resource : resource?.url || "";
    let mutable = { ...options };
    if (url.endsWith("/analysis/intake") && mutable.body) {
      try {
        const payload = JSON.parse(String(mutable.body));
        state.lastIncomeType = payload.income_type || null;
        enrichSection19Facts(payload);
        mutable.body = JSON.stringify(payload);
      } catch (_problem) {}
    }
    const response = await previousFetch(resource, mutable);
    if (url.endsWith("/analysis/intake") && response.ok) {
      try {
        const body = await response.clone().json();
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

  window.addEventListener("taxtreat:source-country-change", () => {
    window.setTimeout(syncSection19Visibility, 0);
  });

  document.querySelector('#workspace-payment [name="income_type"]')?.addEventListener("change", () => {
    window.setTimeout(syncSection19Visibility, 0);
  });

  function boot() {
    addLanguageControl();
    addReportLanguageControl();
    addSection19Questions();
    const income = document.querySelector('#workspace-payment [name="income_type"]');
    state.lastIncomeType = income?.value || null;
    income?.addEventListener("change", () => {
      state.lastIncomeType = income.value || null;
      renderSection19Result();
      renderIrExemptionNotice();
    });
    applyUiLanguage();
    new MutationObserver((mutations) => {
      mutations.forEach((mutation) => mutation.addedNodes.forEach((node) => {
        if (node.nodeType === Node.ELEMENT_NODE) applyUiLanguage(node);
      }));
    }).observe(document.body, { subtree: true, childList: true });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once: true });
  else boot();
})();