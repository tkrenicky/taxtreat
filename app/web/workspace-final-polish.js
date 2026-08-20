(() => {
  "use strict";

  const translations = new Map([
    ["Jazyk", "Language"], ["Jazyk webu", "Website language"], ["Jazyk reportu", "Report language"],
    ["Stát plátce *", "Payer country *"], ["Česká republika", "Czech Republic"], ["Slovensko", "Slovakia"],
    ["Stát plátce určuje, která vnitrostátní pravidla srážkové daně TaxTreat použije. Nejde o samostatný přepínač režimu aplikace.", "The payer country determines which domestic withholding tax rules TaxTreat applies. It is not a separate application-mode switch."],
    ["Pro slovenského plátce se údaje z českého registru ARES nenačítají; identifikační údaje vyplň ručně.", "For a Slovak payer, data are not retrieved from the Czech ARES register; enter the identification details manually."],
    ["Po zadání 8 číslic TaxTreat načte identifikační údaje z ARES.", "After entering 8 digits, TaxTreat retrieves identification details from ARES."],
    ["Údaje byly načteny z ARES. Před uložením je můžeš upravit.", "The data were retrieved from ARES. You can edit them before saving."],
    ["Údaje se z ARES nepodařilo načíst. Pole můžeš vyplnit ručně.", "The data could not be retrieved from ARES. You can complete the fields manually."],
    ["Načítám údaje z ARES…", "Retrieving data from ARES…"], ["Načíst z ARES", "Retrieve from ARES"],
    ["IČO *", "Company ID *"], ["IČO", "Company ID"], ["Název *", "Name *"], ["DIČ", "Tax ID"], ["Sídlo", "Registered office"], ["Právní forma", "Legal form"], ["Datová schránka", "Data box"], ["Datum vzniku", "Date of incorporation"],
    ["Načte se z ARES", "Retrieved from ARES"], ["Zrušit", "Cancel"], ["Uložit změny", "Save changes"], ["PŘÍJEMCE", "RECIPIENT"], ["PLÁTCE", "PAYER"],
    ["Skutečný vlastník příjmu", "Beneficial owner of the income"], ["Daňový rezident vybraného státu pro účely smlouvy", "Tax resident of the selected country for treaty purposes"], ["Přímé držení podílu", "Direct ownership"],
    ["Vazba účasti, pohledávky nebo práva ke stálé provozovně v ČR", "Connection of the participation, receivable or right to a Czech permanent establishment"],
    ["Ještě dva údaje pro možné osvobození podle § 19 ZDP", "Two more facts for the potential Section 19 exemption"],
    ["Podíl, přímé držení, dobu držby, skutečné vlastnictví a vazbu ke stálé provozovně už TaxTreat používá z odpovědí výše.", "TaxTreat already uses the ownership percentage, direct holding, holding period, beneficial ownership and permanent-establishment connection from the answers above."],
    ["Je příjemce běžnou obchodní společností (např. GmbH, AG, Ltd. nebo S.A.), nikoli fyzickou osobou, fondem nebo daňově transparentním subjektem?", "Is the recipient an ordinary corporate entity (for example GmbH, AG, Ltd. or S.A.), rather than an individual, fund or tax-transparent entity?"],
    ["Pokud si nejsi jistý právní formou příjemce, zvol „Nevím / potřebuji ověřit“. TaxTreat pak osvobození neuzavře, dokud nebude údaj ověřen.", "If you are unsure about the recipient's legal form, select “I don't know / needs verification”. TaxTreat will not finalise the exemption until the fact is verified."],
    ["Podléhá příjemce ve státě své daňové rezidence běžné dani z příjmů právnických osob a není od této daně osvobozen ani v režimu s nulovou sazbou?", "Is the recipient subject to ordinary corporate income tax in its state of tax residence and not exempt from that tax or subject to a zero-rate regime?"],
    ["Jde o faktické daňové postavení příjemce. Pokud jej neznáš, zvol „Nevím / potřebuji ověřit“.", "This asks about the recipient's factual tax status. If you do not know it, select “I don't know / needs verification”."],
    ["Nevím / potřebuji ověřit", "I don't know / needs verification"],
    ["Potvrzení o daňovém rezidentství je důkazním podkladem pro uplatnění smluvní výhody. Samotný výpočet lze provést i bez něj; ve výsledku bude uvedeno, že rezidentství nebylo doloženo.", "A tax residence certificate is supporting evidence for a treaty benefit. The calculation can be performed without it, but the result will state that residence has not been evidenced."],
    ["+ Evidovat potvrzení o daňovém rezidentství", "+ Record tax residence certificate"], ["Datum vystavení *", "Issue date *"], ["Platnost do *", "Valid until *"], ["Teď ne", "Not now"], ["Uložit evidenci", "Save record"],
    ["Základní údaje", "Basic details"], ["Daňová rezidence", "Tax residence"], ["Typ subjektu", "Entity type"], ["Vazba ke stálé provozovně v ČR", "Connection to a Czech permanent establishment"], ["Podíl na plátci", "Ownership in payer"], ["Datum nabytí podílu", "Share acquisition date"],
    ["Potvrzení o daňovém rezidentství", "Tax residence certificate"], ["Zatím nebylo bezpečně uloženo.", "It has not yet been securely recorded."], ["Spusť první výpočet pro tohoto příjemce.", "Start the first calculation for this recipient."],
    ["Předvyplněno podle podílu na základním kapitálu. Uprav, pokud se podíl na hlasovacích právech liší.", "Pre-filled from the share-capital ownership. Change it if the voting-rights percentage differs."],
    ["Doba držby se vypočte automaticky k datu transakce.", "The holding period is calculated automatically as of the transaction date."],
    ["Odpovídá výše úroku běžným tržním podmínkám?", "Is the amount of interest consistent with ordinary market conditions?"],
    ["Posuzuje se, zda úrok není kvůli vztahu mezi stranami vyšší než obvyklá tržní částka.", "This checks whether the interest is higher than an ordinary arm's-length amount because of the relationship between the parties."],
    ["Ostatní úroky stejného druhu připadající tomuto příjemci ve stejném kalendářním měsíci (Kč)", "Other interest of the same type attributable to this recipient in the same calendar month (CZK)"],
    ["Odpovídá výše licenční platby běžným tržním podmínkám?", "Is the royalty amount consistent with ordinary market conditions?"],
    ["Výsledek vychází z uvedených údajů a zobrazeného právního základu.", "The result is based on the entered facts and the legal basis shown."],
    ["Podmínky případného osvobození", "Conditions for a potential exemption"], ["Dodatečné splnění doby držby", "Subsequent fulfilment of the holding period"], ["Podmínky vnitrostátního osvobození", "Domestic exemption conditions"], ["Zvláštní smluvní podmínka úroku", "Special treaty condition for interest"], ["Zvláštní smluvní podmínka licenční platby", "Special treaty condition for royalties"], ["Podmínka vyžadující odborné posouzení", "Condition requiring professional review"],
    ["Sazbu zatím nelze určit. Konkrétní důvod je uveden v části Podmínky a další kroky níže.", "The rate cannot yet be determined. The specific reason is shown under Conditions and next steps below."],
    ["Zadané údaje směřují k osvobození příjmu v České republice. Před uzavřením výsledku je třeba ověřit konkrétní podmínky uvedené níže.", "The entered facts point to an exemption in the Czech Republic. The specific conditions shown below must be verified before the result can be finalised."],
    ["Zadané údaje směřují k použití smluvního pravidla, podle něhož se příjem zdaňuje pouze ve státě rezidence příjemce. Před uzavřením výsledku je třeba ověřit konkrétní podmínky uvedené níže.", "The entered facts point to a treaty rule under which the income is taxable only in the recipient's state of residence. The conditions shown below must be verified before the result can be finalised."],
    ["Lhůty se zobrazí po dokončení výpočtu.", "Deadlines will be shown after the calculation is completed."], ["Po doplnění údajů", "After completing the facts"], ["Daň se neodvádí", "No tax remittance"], ["Oznámení se nepodává", "No notification required"],
    ["Právní ustanovení použité při výpočtu.", "Legal provision used in the calculation."], ["Vnitrostátní pravidlo stanoví osvobození příjmu při splnění všech kvalifikačních podmínek.", "The domestic rule provides an exemption when all qualifying conditions are met."], ["Pravidlo vnitrostátního osvobození se použije při splnění všech kvalifikačních podmínek.", "The domestic exemption rule applies when all qualifying conditions are met."],
    ["Zásady ochrany dat", "Data protection"], ["Podmínky použití", "Terms of use"],
  ]);

  const originals = new WeakMap();

  function language() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
  }

  function dynamicEnglish(key) {
    let value = translations.get(key) || key;
    value = value
      .replace(/^Česká republika · IČO /, "Czech Republic · Company ID ")
      .replace(/^Slovensko · IČO /, "Slovakia · Company ID ")
      .replace(/ · DIČ /g, " · Tax ID ")
      .replace(/^Podle (.+) činí při zadaných údajích sazba srážkové daně ([0-9.,]+) %\.$/, "Based on $1, the withholding tax rate for the entered facts is $2%.")
      .replace(/^Podle (.+) je při zadaných údajích příjem v České republice osvobozen od srážkové daně\.$/, "Based on $1, the income is exempt from Czech withholding tax for the entered facts.")
      .replace(/^Podle (.+) se při zadaných údajích příjem v České republice nezdaňuje\.$/, "Based on $1, the income is not taxable in the Czech Republic for the entered facts.")
      .replace(/^Česká srážková daň je ([0-9.,]+) %\. Výsledek vychází z (.+) příslušné smlouvy ve znění použitelných změn\. Rozhodující byly podmínky konkrétního pravidla uvedené v právních podkladech\.$/, "Czech withholding tax is $1%. The result is based on $2 of the relevant treaty as amended. The conditions of the specific rule shown in the legal sources were decisive.")
      .replace(/^Česká srážková daň je ([0-9.,]+) %\. Výsledek vychází z (.+) zákona č\. 586\/1992 Sb\., o daních z příjmů, protože nebylo použito pravidlo s nižší sazbou\.$/, "Czech withholding tax is $1%. The result is based on $2 of the Czech Income Taxes Act because no rule with a lower rate applied.")
      .replace(/^Použitá sazba ([0-9.,]+) % byla určena na základě zadaných údajů a vybraného právního pravidla uvedeného níže\.$/, "The $1% rate was determined from the entered facts and the selected legal rule shown below.")
      .replace(/^Byla identifikována sazba ([0-9.,]+) %\. Její použití závisí na splnění právních a skutkových podmínek uvedených níže\.$/, "A $1% rate was identified. Its application depends on the legal and factual conditions shown below.")
      .replace(/^Smlouva o zamezení dvojího zdanění · článek /, "Double Tax Treaty · Article ")
      .replace(/^Zákon č\. 586\/1992 Sb\., o daních z příjmů · § /, "Czech Income Taxes Act · Section ")
      .replace(/^Vnitrostátní pravidlo stanoví sazbu ([0-9.,]+) %\.$/, "The domestic rule provides a $1% rate.")
      .replace(/^Pravidlo příslušné smlouvy stanoví sazbu ([0-9.,]+) % při splnění jeho podmínek\.$/, "The relevant treaty rule provides a $1% rate when its conditions are met.")
      .replace(/^Pravidlo stanoví sazbu ([0-9.,]+) % při podílu alespoň ([0-9.,]+) % a při splnění ostatních uvedených podmínek\.$/, "The rule provides a $1% rate for ownership of at least $2% when the other stated conditions are met.");
    return value;
  }

  function translateNode(node) {
    if (!node || node.nodeType !== Node.TEXT_NODE) return;
    if (node.parentElement?.closest("blockquote,pre,code,.legal-excerpt")) return;
    const current = node.nodeValue;
    const trimmed = current.trim();
    if (!trimmed) return;
    if (!originals.has(node)) originals.set(node, current);
    const original = originals.get(node);
    const key = original.trim();
    const value = language() === "en" ? dynamicEnglish(key) : key;
    node.nodeValue = original.replace(key, value);
  }

  function applyPayerAndReliefTranslations(root = document.body) {
    if (!root) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(translateNode);
    const ui = document.querySelector("#taxtreat-ui-language");
    if (ui) ui.setAttribute("aria-label", language() === "en" ? "Website language" : "Jazyk webu");
    const report = document.querySelector("#taxtreat-report-language");
    if (report) report.setAttribute("aria-label", language() === "en" ? "Report language" : "Jazyk reportu");
  }

  function ensureUnknownOption(select) {
    if (!select || [...select.options].some((option) => option.value === "unknown")) return;
    const option = document.createElement("option");
    option.value = "unknown";
    option.textContent = "Nevím / potřebuji ověřit";
    select.append(option);
  }

  function polishSection19Questions() {
    const formSelect = document.querySelector('[name="section19_company_form"]');
    const taxSelect = document.querySelector('[name="section19_taxable_company"]');
    ensureUnknownOption(formSelect);
    ensureUnknownOption(taxSelect);
    const formLabel = formSelect?.closest("label");
    const taxLabel = taxSelect?.closest("label");
    if (formLabel?.querySelector("small")) formLabel.querySelector("small").textContent = "Pokud si nejsi jistý právní formou příjemce, zvol „Nevím / potřebuji ověřit“. TaxTreat pak osvobození neuzavře, dokud nebude údaj ověřen.";
    if (taxLabel?.querySelector("small")) taxLabel.querySelector("small").textContent = "Jde o faktické daňové postavení příjemce. Pokud jej neznáš, zvol „Nevím / potřebuji ověřit“.";
  }

  function boot() {
    polishSection19Questions();
    applyPayerAndReliefTranslations();
    document.querySelector("#taxtreat-ui-language")?.addEventListener("change", () => window.setTimeout(() => applyPayerAndReliefTranslations(), 0));
    new MutationObserver((mutations) => {
      polishSection19Questions();
      mutations.forEach((mutation) => mutation.addedNodes.forEach((node) => {
        if (node.nodeType === Node.ELEMENT_NODE) applyPayerAndReliefTranslations(node);
      }));
    }).observe(document.body, { subtree: true, childList: true });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once: true });
  else boot();
})();