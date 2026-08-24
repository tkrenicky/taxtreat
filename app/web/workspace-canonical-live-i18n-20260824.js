(() => {
  "use strict";

  const UI_KEY = "taxtreat-ui-language";
  const state = { payload: null, analysis: null };

  const PAIRS = [
    ["Přehled", "Overview"], ["Plátci", "Payers"], ["Příjemci", "Recipients"], ["Výsledky", "Results"], ["Zdroje", "Sources"],
    ["Aktivní plátce", "Active payer"], ["Nový výpočet →", "New calculation →"], ["Přidat plátce", "Add payer"], ["Přidat příjemce", "Add recipient"],
    ["Upravit", "Edit"], ["Upravit plátce", "Edit payer"], ["Upravit příjemce", "Edit recipient"], ["Otevřít →", "Open →"], ["Otevřít profil →", "Open profile →"],
    ["ORGANIZACE", "ORGANIZATIONS"], ["PROFILY PRO OPAKOVANÉ POUŽITÍ", "REUSABLE PROFILES"], ["VÝSLEDKY A REPORTY", "RESULTS AND REPORTS"], ["DŮKAZNÍ ZÁKLAD", "EVIDENCE BASE"],
    ["České subjekty, jejichž platby jsou v TaxTreat zpracovávány.", "Czech entities whose payments are processed in TaxTreat."],
    ["Skutkové údaje a podklady použitelné pro další platby stejnému příjemci.", "Facts and supporting documents reusable for future payments to the same recipient."],
    ["Výsledek výpočtu a report pro každou dokončenou platbu.", "Calculation result and report for each completed payment."],
    ["Smluvní texty a evidované zdroje použité v konkrétních výsledcích.", "Treaty texts and recorded sources used in individual results."],
    ["Základní údaje vyplněny", "Basic details completed"], ["Doklad rezidentství neevidován", "Residence certificate not recorded"],
    ["← Zpět na příjemce", "← Back to recipients"], ["Základní profil", "Basic profile"], ["Údaje vyplněny", "Details completed"],
    ["Potvrzení o daňovém rezidentství je důkazním podkladem pro uplatnění smluvní výhody. Samotný výpočet lze provést i bez něj; ve výsledku bude uvedeno, že rezidentství nebylo doloženo.", "A tax residence certificate is supporting evidence for a treaty claim. The calculation can still be performed without it; the result will state that residence has not been evidenced."],
    ["+ Evidovat potvrzení o daňovém rezidentství", "+ Record tax residence certificate"], ["Datum vystavení *", "Issue date *"], ["Platnost do *", "Valid until *"], ["Teď ne", "Not now"], ["Uložit evidenci", "Save record"],
    ["Základní údaje", "Basic details"], ["Daňová rezidence", "Tax residence"], ["Typ subjektu", "Entity type"], ["Skutečný vlastník příjmu", "Beneficial owner of the income"],
    ["Vazba ke stálé provozovně v ČR", "Connection to a permanent establishment in the Czech Republic"], ["Podíl na plátci", "Ownership in payer"], ["Datum nabytí podílu", "Share acquisition date"],
    ["Dokumenty", "Documents"], ["Potvrzení o daňovém rezidentství", "Tax residence certificate"], ["Zatím nebylo bezpečně uloženo.", "It has not yet been securely recorded."],
    ["Historie plateb", "Payment history"], ["Zatím bez plateb", "No payments yet"], ["Spusť první výpočet pro tohoto příjemce.", "Start the first calculation for this recipient."],
    ["Podporované jurisdikce", "Supported jurisdictions"], ["Pokryté kombinace", "Covered combinations"], ["Příjmové kategorie", "Income categories"],
    ["Podklady použité ve výsledku", "Sources used in the result"], ["U každého dokončeného výpočtu jsou uvedeny konkrétní články příslušné smlouvy, použitá právní pravidla, odkazy na právní zdroje a právní stav použitý pro daný výpočet.", "Each completed calculation identifies the relevant treaty provisions, applied legal rules, links to legal sources and the legal status used for that calculation."],
    ["Plátce", "Payer"], ["Příjemce", "Recipient"], ["Platba", "Payment"], ["Výsledek", "Result"], ["← Ukončit průvodce", "← Exit wizard"],
    ["KROK 1 ZE 4", "STEP 1 OF 4"], ["KROK 2 ZE 4", "STEP 2 OF 4"], ["KROK 3 ZE 4", "STEP 3 OF 4"], ["KROK 4 ZE 4", "STEP 4 OF 4"],
    ["Která společnost platbu provádí?", "Which company makes the payment?"], ["Vyber českého plátce, ke kterému bude výpočet přiřazen.", "Select the Czech payer to which the calculation will be assigned."],
    ["Vybráno", "Selected"], ["Vybrat", "Select"], ["+ Přidat plátce", "+ Add payer"], ["Pokračovat k příjemci →", "Continue to recipient →"],
    ["Komu je placeno?", "Who receives the payment?"], ["Vyber existujícího příjemce nebo založ nový profil.", "Select an existing recipient or create a new profile."],
    ["+ Založit nového příjemce", "+ Create new recipient"], ["Základní profil příjemce", "Recipient basic profile"],
    ["Údaje se uloží do pracovního profilu a při dalších platbách je nebude nutné zadávat znovu.", "The data will be saved in the working profile and will not need to be entered again for future payments."],
    ["Název nebo jméno *", "Name *"], ["Stát daňové rezidence *", "Tax residence country *"], ["Vyber stát", "Select country"], ["Typ příjemce *", "Recipient type *"],
    ["Společnost", "Company"], ["Fyzická osoba", "Individual"], ["Fond", "Fund"], ["Jiný subjekt", "Other entity"],
    ["Další údaje a podklady doplníš v profilu příjemce. V tomto demu se nový profil po obnovení stránky odstraní.", "Additional facts and supporting documents can be completed in the recipient profile. In this demo, a newly created profile is removed after the page is refreshed."],
    ["Použít příjemce v této kontrole →", "Use recipient in this calculation →"], ["← Zpět k plátci", "← Back to payer"], ["Pokračovat k platbě →", "Continue to payment →"],
    ["Údaje o platbě", "Payment details"], ["Druh příjmu *", "Income type *"], ["Vyber druh", "Select type"], ["Dividendy", "Dividends"], ["Úroky", "Interest"], ["Licenční poplatky", "Royalties"],
    ["Datum transakce *", "Transaction date *"], ["Hrubá částka *", "Gross amount *"], ["Hrubá částka", "Gross amount"], ["Měna *", "Currency *"], ["Kurz v CZK za 1 jednotku měny", "CZK exchange rate per 1 unit of currency"],
    ["Výpočet vychází z níže uvedených předpokladů", "The calculation is based on the assumptions below"], ["Předvyplněné odpovědi zkontroluj a změň, pokud pro danou platbu neplatí.", "Review the pre-filled answers and change them if they do not apply to this payment."],
    ["Příjemce je skutečným vlastníkem příjmu.", "The recipient is the beneficial owner of the income."], ["Ano", "Yes"], ["Ne", "No"],
    ["DOPLŇUJÍCÍ ÚDAJE O TRANSAKCI", "ADDITIONAL TRANSACTION FACTS"], ["Doplňující údaje o transakci", "Additional transaction facts"],
    ["Doplňující údaje pro možné vnitrostátní osvobození", "Additional facts for potential domestic exemption"],
    ["Předmět licenční platby", "Royalty subject"], ["Vyber možnost", "Select option"], ["Autorské dílo", "Copyright work"], ["Software, patent, ochranná známka nebo know-how", "Software, patent, trademark or know-how"], ["Průmyslové, obchodní nebo vědecké zařízení", "Industrial, commercial or scientific equipment"], ["Jiný předmět licence", "Other royalty subject"],
    ["Odpovídá výše úroku běžným tržním podmínkám?", "Is the amount of interest consistent with arm's length conditions?"],
    ["Posuzuje se, zda úrok není kvůli vztahu mezi stranami vyšší než obvyklá tržní částka.", "This checks whether the interest is higher than an arm's length amount because of the relationship between the parties."],
    ["Zobrazit pravidla a výpočet →", "Show rules and calculation →"], ["Doplnit údaje a aktualizovat výpočet →", "Complete facts and update calculation →"],
    ["Použité právní pravidlo", "Applied legal rule"], ["Souhrn platby", "Payment summary"], ["Srážková daň", "Withholding tax"], ["Čistá částka", "Net amount"],
    ["Podmínky použitého pravidla", "Conditions of the applied rule"], ["Právní podklady", "Legal sources"], ["Rozhodné datum a navazující lhůty", "Reference date and compliance deadlines"],
    ["DAŇOVÝ KALENDÁŘ", "TAX CALENDAR"], ["Rozhodné datum zadané pro výpočet", "Reference date used for the calculation"], ["Odvod srážkové daně", "Withholding tax remittance"], ["Oznámení příjmu plynoucího do zahraničí", "Outbound income notification"],
    ["Odvod sražené daně a oznámení o příjmu plynoucího do zahraničí mají shodnou lhůtu: konec následujícího kalendářního měsíce.", "Withholding tax remittance and the outbound income notification have the same deadline: the end of the following calendar month."],
    ["1. VÝCHOZÍ VNITROSTÁTNÍ PRAVIDLO", "1. DEFAULT DOMESTIC RULE"], ["2. POUŽITÉ SMLUVNÍ PRAVIDLO", "2. APPLIED TREATY RULE"],
    ["VÝCHOZÍ VNITROSTÁTNÍ PRAVIDLO", "DEFAULT DOMESTIC RULE"], ["POUŽITÉ SMLUVNÍ PRAVIDLO", "APPLIED TREATY RULE"],
    ["← Upravit platbu", "← Edit payment"], ["Tisk / PDF reportu", "Print / PDF report"],
    ["Možné vnitrostátní osvobození", "Potential domestic exemption"], ["Základní podmínky:", "Key conditions:"],
    ["Relevantní ustanovení", "Relevant provisions"], ["Otevřít zdroj ↗", "Open source ↗"], ["Znění použitého ustanovení", "Text of the applied provision"], ["Evidované znění použitého ustanovení", "Recorded text of the applied provision"],
    ["Rakousko", "Austria"], ["Rakouska", "Austria"], ["Německo", "Germany"], ["Švýcarsko", "Switzerland"], ["Singapur", "Singapore"], ["Tchaj-wan", "Taiwan"], ["společnost", "company"], ["Nevyplněno", "Not provided"],
    ["Zásady ochrany dat", "Data protection"], ["Podmínky použití", "Terms of use"]
  ];

  const CS_EN = new Map(PAIRS);
  const EN_CS = new Map(PAIRS.map(([cs, en]) => [en, cs]));
  const MONTHS_CS_EN = new Map([["ledna", "January"], ["února", "February"], ["března", "March"], ["dubna", "April"], ["května", "May"], ["června", "June"], ["července", "July"], ["srpna", "August"], ["září", "September"], ["října", "October"], ["listopadu", "November"], ["prosince", "December"]]);
  const MONTHS_EN_CS = new Map(Array.from(MONTHS_CS_EN, ([cs, en]) => [en, cs]));

  function language() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem(UI_KEY) || "cs";
  }

  function translateDate(text, target) {
    if (target === "en") {
      return text.replace(/^(\d{1,2})\.\s+(ledna|února|března|dubna|května|června|července|srpna|září|října|listopadu|prosince)\s+(\d{4})$/i, (_m, day, month, year) => `${day} ${MONTHS_CS_EN.get(month.toLowerCase())} ${year}`);
    }
    return text.replace(/^(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})$/i, (_m, day, month, year) => `${day}. ${MONTHS_EN_CS.get(month[0].toUpperCase() + month.slice(1).toLowerCase())} ${year}`);
  }

  function translatePattern(text, target) {
    const dated = translateDate(text, target);
    if (dated !== text) return dated;
    if (target === "en") {
      return text
        .replace(/^Česká republika · IČO /, "Czech Republic · Company ID ")
        .replace(/ · DIČ /g, " · Tax ID ")
        .replace(/^TaxTreat\s*·\s*Zásady ochrany dat\s*·\s*Podmínky použití$/i, "TaxTreat · Data protection · Terms of use")
        .replace(/^Rakousko · společnost · základní údaje vyplněny$/i, "Austria · company · basic details completed")
        .replace(/^Rakousko · společnost · příjemce /i, "Austria · company · recipient of ")
        .replace(/^Daňová rezidence:\s*Rakouska$/i, "Tax residence: Austria")
        .replace(/^Typ subjektu:\s*Společnost$/i, "Entity type: Company")
        .replace(/^Podíl na plátci:\s*(.+)$/i, "Ownership in payer: $1")
        .replace(/^Datum nabytí podílu:\s*(.+)$/i, "Share acquisition date: $1")
        .replace(/^([0-9]+) údaje?$/i, "$1 facts")
        .replace(/^KROK ([1-4]) ZE 4$/i, "STEP $1 OF 4")
        .replace(/^Podle článku\s+([^\s]+)\s+smlouvy o zamezení dvojího zdanění,?\s*(.*)$/i, (_m, article, rest) => `Under Article ${article} of the double tax treaty, ${rest}`)
        .replace(/^Zákon č\. 586\/1992 Sb\., o daních z příjmů\s*·\s*§\s*([^·]+)\s*·\s*odst\.\s*([^·]+)$/i, "Czech Income Taxes Act (Act No. 586/1992 Coll.) · Section $1 · paragraph $2")
        .replace(/^Czech Income Taxes Act \(Act No\. 586\/1992 Coll\.\)\s*·\s*Section\s*([^·]+)\s*·\s*odst\.\s*([^·]+)$/i, "Czech Income Taxes Act (Act No. 586/1992 Coll.) · Section $1 · paragraph $2")
        .replace(/^§\s*38d\s+a\s+§\s*38da\s+zákona č\. 586\/1992 Sb\., o daních z příjmů$/i, "Sections 38d and 38da of the Czech Income Taxes Act")
        .replace(/^§\s*38d\s+a\s+§\s*38da\s+ZDP$/i, "Sections 38d and 38da of the Czech Income Taxes Act")
        .replace(/^odst\.\s*(\d+[a-z]?)$/i, "paragraph $1");
    }
    return text
      .replace(/^Czech Republic · Company ID /, "Česká republika · IČO ")
      .replace(/ · Tax ID /g, " · DIČ ")
      .replace(/^TaxTreat\s*·\s*Data protection\s*·\s*Terms of use$/i, "TaxTreat · Zásady ochrany dat · Podmínky použití")
      .replace(/^Austria · company · basic details completed$/i, "Rakousko · společnost · základní údaje vyplněny")
      .replace(/^Austria · company · recipient of /i, "Rakousko · společnost · příjemce ")
      .replace(/^Tax residence: Austria$/i, "Daňová rezidence: Rakouska")
      .replace(/^Entity type: Company$/i, "Typ subjektu: Společnost")
      .replace(/^Ownership in payer:\s*(.+)$/i, "Podíl na plátci: $1")
      .replace(/^Share acquisition date:\s*(.+)$/i, "Datum nabytí podílu: $1")
      .replace(/^([0-9]+) facts$/i, "$1 údaje")
      .replace(/^STEP ([1-4]) OF 4$/i, "KROK $1 ZE 4")
      .replace(/^Under Article\s+([^\s]+)\s+of the double tax treaty,?\s*(.*)$/i, (_m, article, rest) => `Podle článku ${article} smlouvy o zamezení dvojího zdanění, ${rest}`)
      .replace(/^Czech Income Taxes Act \(Act No\. 586\/1992 Coll\.\)\s*·\s*Section\s*([^·]+)\s*·\s*paragraph\s*([^·]+)$/i, "Zákon č. 586/1992 Sb., o daních z příjmů · § $1 · odst. $2")
      .replace(/^Sections 38d and 38da of the Czech Income Taxes Act$/i, "§ 38d a § 38da ZDP")
      .replace(/^paragraph\s*(\d+[a-z]?)$/i, "odst. $1");
  }

  function translateTextNode(node) {
    if (!node || node.nodeType !== Node.TEXT_NODE) return;
    if (node.parentElement?.closest("blockquote,.legal-excerpt,pre,code")) return;
    const raw = node.nodeValue || "";
    const key = raw.trim();
    if (!key) return;
    const target = language();
    let next = target === "en" ? CS_EN.get(key) : EN_CS.get(key);
    if (!next) {
      const patterned = translatePattern(key, target);
      if (patterned !== key) next = patterned;
    }
    if (next && next !== key) node.nodeValue = raw.replace(key, next);
  }

  function translateAttributes(root) {
    const nodes = [root, ...(root?.querySelectorAll?.("[placeholder],[aria-label],[title]") || [])].filter(Boolean);
    nodes.forEach((el) => {
      ["placeholder", "aria-label", "title"].forEach((name) => {
        if (!el.hasAttribute?.(name)) return;
        const raw = el.getAttribute(name) || "";
        const key = raw.trim();
        const direct = language() === "en" ? CS_EN.get(key) : EN_CS.get(key);
        const next = direct || translatePattern(key, language());
        if (next && next !== key) el.setAttribute(name, raw.replace(key, next));
      });
    });
  }

  function apply(root = document.body) {
    if (!root) return;
    document.documentElement.lang = language() === "en" ? "en" : "cs";
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(translateTextNode);
    translateAttributes(root);
    clarifyAustrianCopyrightRoyaltySource();
  }

  function isAtCopyrightExclusive() {
    if (String(state.payload?.recipient_country || "").toUpperCase() !== "AT") return false;
    if (state.payload?.income_type !== "royalty") return false;
    const category = state.payload?.facts?.royalty_category || document.querySelector('[name="royalty_category"]')?.value || "";
    const copyright = /copyright|literary|artistic|scientific/i.test(String(category));
    const treatment = state.analysis?.tax_treatment || state.analysis?.candidate_tax_treatment;
    return copyright && treatment === "exclusive_foreign_taxation";
  }

  function clarifyAustrianCopyrightRoyaltySource() {
    const step = document.querySelector('.flow-step[data-step="4"]');
    if (!step) return;
    const existing = step.querySelector(".tt-at-copyright-source-note");
    if (!isAtCopyrightExclusive()) {
      existing?.remove();
      return;
    }
    const selectedCard = step.querySelector("#workspace-citations .citation-card:not(.context)") || step.querySelector("#workspace-citations .citation-card");
    if (!selectedCard) return;
    selectedCard.querySelectorAll("mark.legal-decisive-passage").forEach((mark) => mark.replaceWith(document.createTextNode(mark.textContent || "")));
    const details = selectedCard.querySelector("details.citation-excerpt");
    if (details) details.open = false;
    let note = selectedCard.querySelector(".tt-at-copyright-source-note");
    if (!note) {
      note = document.createElement("p");
      note.className = "tt-at-copyright-source-note";
      const anchor = selectedCard.querySelector("details.citation-excerpt");
      if (anchor) selectedCard.insertBefore(note, anchor); else selectedCard.append(note);
    }
    note.textContent = language() === "en"
      ? "For the selected copyright category, the 5% source-state limitation in Article 12(2) does not apply. The result follows the residence-state-only branch applicable to this category. The full treaty article below also contains rules for other royalty categories."
      : "Pro zvolenou kategorii autorského díla se 5% omezení zdanění ve státě zdroje podle čl. 12 odst. 2 neuplatní. Výsledek vychází z větve použitelné pro tuto kategorii, podle níž se příjem zdaňuje pouze ve státě rezidence. Úplné znění článku níže obsahuje také pravidla pro jiné kategorie licenčních poplatků.";
  }

  function schedule() {
    [0, 40, 120, 300, 700].forEach((ms) => window.setTimeout(() => apply(document.body), ms));
  }

  const previousFetch = window.fetch.bind(window);
  window.fetch = async function canonicalI18nFetch(resource, options = {}) {
    const url = typeof resource === "string" ? resource : resource?.url || "";
    if (url.endsWith("/analysis/intake") && options?.body) {
      try { state.payload = JSON.parse(String(options.body)); } catch (_problem) {}
    }
    const response = await previousFetch(resource, options);
    if (url.endsWith("/analysis/intake") && response.ok) {
      try {
        const body = await response.clone().json();
        state.analysis = body?.analysis || null;
        schedule();
      } catch (_problem) {}
    }
    return response;
  };

  document.addEventListener("click", (event) => {
    const button = event.target?.closest?.("#taxtreat-language-controls .tt-lang-mini button[data-lang]");
    if (button) {
      const select = document.querySelector("#taxtreat-ui-language");
      const lang = button.dataset.lang;
      if (select && ["cs", "en"].includes(lang)) {
        select.value = lang;
        localStorage.setItem(UI_KEY, lang);
        select.dispatchEvent(new Event("change", { bubbles: true }));
      }
    }
    window.setTimeout(schedule, 0);
  }, true);

  document.addEventListener("change", (event) => {
    if (event.target?.id === "taxtreat-ui-language" || event.target?.matches?.('[name="income_type"],[name="royalty_category"]')) schedule();
  }, true);

  schedule();
})();
