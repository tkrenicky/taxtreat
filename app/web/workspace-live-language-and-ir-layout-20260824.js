(() => {
  "use strict";

  const UI_LANGUAGE_KEY = "taxtreat-ui-language";
  const EXTRA_TRANSLATIONS = new Map([
    ["Odpovídá výše úroku běžným tržním podmínkám?", "Is the amount of interest consistent with arm's length conditions?"],
    ["Posuzuje se, zda úrok není kvůli vztahu mezi stranami vyšší než obvyklá tržní částka.", "This checks whether the interest is higher than an arm's length amount because of the relationship between the parties."],
    ["Ostatní úroky stejného druhu připadající tomuto příjemci ve stejném kalendářním měsíci (Kč)", "Other interest of the same type attributable to this recipient in the same calendar month (CZK)"],
    ["Uveď souhrn bez právě zadávané platby. Aktuální platba se po přepočtu kurzem ČNB přičte automaticky pro posouzení limitu podle § 38da zákona č. 586/1992 Sb., o daních z příjmů.", "Enter the total excluding the payment currently being entered. The current payment will be added automatically after conversion using the CNB exchange rate for the assessment of the threshold under Section 38da of the Czech Income Taxes Act."],
    ["Jaký podíl na základním kapitálu českého plátce příjemce drží?", "What percentage of the Czech payer's registered capital does the recipient hold?"],
    ["Drží příjemce tento podíl přímo?", "Does the recipient hold this interest directly?"],
    ["Při nepřímém držení je podíl vlastněn prostřednictvím jiné společnosti. TaxTreat dále posoudí pravidla, která nepřímou účast připouštějí; pravidlo vyžadující přímé držení nebude bez dalšího použito.", "With an indirect holding, the interest is held through another company. TaxTreat will assess rules that permit indirect ownership; a rule requiring direct ownership will not be applied without further support."],
    ["Jak dlouho příjemce podíl drží?", "How long has the recipient held the interest?"],
    ["Jaký podíl na hlasovacích právech českého plátce příjemce drží?", "What percentage of the voting rights in the Czech payer does the recipient hold?"],
    ["Předvyplněno podle podílu na základním kapitálu. Uprav, pokud se podíl na hlasovacích právech liší.", "Pre-filled based on the registered-capital interest. Change it if the voting-rights percentage differs."],
    ["Příjemce je daňovým rezidentem státu Rakousko pro účely příslušné smlouvy.", "The recipient is a tax resident of Austria for the purposes of the applicable treaty."],
    ["Konkrétní podíl, pohledávka nebo právo, ze kterého plyne tato platba, je součástí činnosti stálé provozovny příjemce v České republice.", "The specific interest, receivable or right giving rise to this payment is effectively connected with the activities of the recipient's permanent establishment in the Czech Republic."],
    ["Zvol „Ano“ pouze tehdy, pokud zahraniční příjemce podniká v České republice prostřednictvím stálé provozovny a právě tento podíl, pohledávku nebo licenční právo používá v její činnosti. Pokud příjemce v ČR stálou provozovnu nemá nebo s ní tato platba nesouvisí, ponech „Ne“. Samotná pobočka, kancelář nebo zaměstnanec v ČR tuto vazbu automaticky neznamená.", "Select “Yes” only if the foreign recipient carries on business in the Czech Republic through a permanent establishment and this specific interest, receivable or royalty right is used in its activities. If the recipient has no Czech permanent establishment or the payment is not connected with it, leave “No” selected. A branch, office or employee in the Czech Republic does not by itself establish this connection."],
    ["Uveď dřívější z těchto dvou dat: datum úhrady nebo datum zaúčtování závazku.", "Enter the earlier of these two dates: the payment date or the date on which the liability was recorded."],
    ["Osvobození podle § 19 ZDP se uplatní", "Exemption under Section 19 of the Czech Income Taxes Act applies"],
    ["Vnitrostátní osvobození podle § 19 ZDP", "Domestic exemption under Section 19 of the Czech Income Taxes Act"],
    ["Při zadaných údajích jsou splněny podmínky osvobození podle § 19 ZDP. Příjem proto nepodléhá české srážkové dani.", "Based on the entered facts, the conditions for the exemption under Section 19 of the Czech Income Taxes Act are met. The income is therefore not subject to Czech withholding tax."],
    ["Posouzení vnitrostátního osvobození", "Assessment of the domestic exemption"],
    ["Možnost vnitrostátního osvobození byla posouzena před použitím smluvního pravidla.", "The potential domestic exemption was assessed before applying the treaty rule."],
    ["Použité pravidlo", "Applied rule"],
    ["Obecná česká sazba bez osvobození", "General Czech rate without the exemption"],
    ["Sekundární smluvní ochrana", "Secondary treaty protection"],
    ["Relevantní ustanovení", "Relevant provisions"],
    ["Otevřít zdroj ↗", "Open source ↗"],
    ["Znění použitého ustanovení", "Text of the applied provision"],
    ["Evidované znění použitého ustanovení", "Recorded text of the applied provision"],
    ["Vnitrostátní osvobození podílu na zisku použité pro tento výsledek.", "Domestic exemption for a profit distribution applied to this result."],
    ["Smluvní pravidlo přiznává právo zdanit příjem pouze státu daňové rezidence příjemce.", "The treaty rule grants the taxing right exclusively to the recipient's state of tax residence."],
    ["Vnitrostátní pravidlo stanoví osvobození příjmu při splnění všech kvalifikačních podmínek.", "The domestic rule provides an exemption where all qualifying conditions are met."],
    ["Pravidlo vnitrostátního osvobození se použije při splnění všech kvalifikačních podmínek.", "The domestic exemption rule applies where all qualifying conditions are met."],
    ["Právní ustanovení použité při výpočtu.", "Legal provision used in the calculation."],
    ["Možné vnitrostátní osvobození", "Potential domestic exemption"],
    ["Úroky nebo licenční poplatky mohou být při splnění zákonných podmínek § 19 ZDP osvobozeny od české srážkové daně. Pro neuplatnění WHT je nutné účinné rozhodnutí správce daně podle § 38nb ZDP.", "Interest or royalties may be exempt from Czech withholding tax if the statutory conditions under Section 19 of the Czech Income Taxes Act are met. Non-application of WHT requires an effective Czech tax authority decision under Section 38nb."],
    ["Základní podmínky:", "Key conditions:"],
    ["kvalifikovaná společnost a jurisdikce; kvalifikované přímé 25% propojení; doba držby 24 měsíců; skutečné vlastnictví; příslušné daňové/právní postavení; žádná diskvalifikující vazba ke stálé provozovně; a rozhodnutí podle § 38nb ZDP.", "qualifying company and jurisdiction; qualifying 25% direct relationship; 24-month holding period; beneficial ownership; relevant tax/legal status; no disqualifying permanent-establishment attribution; and a decision under Section 38nb."],
    ["§ 19 odst. 1 písm. ze) – stanoví osvobození podílu na zisku při splnění zákonných podmínek.", "Section 19(1)(ze) – provides the exemption for a profit distribution where the statutory conditions are met."],
    ["§ 19 odst. 3 – vymezuje podmínky vztahující se ke kvalifikovaným společnostem a jejich daňovému postavení.", "Section 19(3) – defines conditions relating to qualifying companies and their tax status."],
    ["§ 19 odst. 6 – upravuje podmínky účasti a časového testu držby.", "Section 19(6) – sets out the ownership and holding-period conditions."],
    ["§ 19 odst. 11 – obsahuje navazující podmínky a vymezení relevantní pro osvobození.", "Section 19(11) – contains further conditions and definitions relevant to the exemption."],
  ]);

  const REVERSE_TRANSLATIONS = new Map([...EXTRA_TRANSLATIONS].map(([cs, en]) => [en, cs]));
  let scheduled = false;

  function currentLanguage() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem(UI_LANGUAGE_KEY) || "cs";
  }

  function installStyles() {
    let style = document.querySelector("#tt-ir-layout-20260824");
    if (!style) {
      style = document.createElement("style");
      style.id = "tt-ir-layout-20260824";
      document.head.append(style);
    }
    style.textContent = `
      #interest-facts,
      #royalty-facts{
        display:grid!important;
        grid-template-columns:1fr!important;
        gap:18px!important;
      }
      #interest-facts > label,
      #royalty-facts > label{
        width:100%!important;
        max-width:none!important;
        min-width:0!important;
        margin:0!important;
      }
      #interest-facts > label > select,
      #interest-facts > label > input,
      #royalty-facts > label > select,
      #royalty-facts > label > input{
        width:100%!important;
        max-width:none!important;
      }
      #cz-ir-exemption-notice{
        margin:30px 0 0!important;
        padding:22px 24px!important;
        border:1px solid #cadad4!important;
        border-top:4px solid #28584f!important;
        border-left:1px solid #cadad4!important;
        border-radius:12px!important;
        background:#f8fbf9!important;
      }
      #cz-ir-exemption-notice h2{margin-top:0!important}
    `;
  }

  function preserveWhitespace(original, replacement) {
    const start = original.match(/^\s*/)?.[0] || "";
    const end = original.match(/\s*$/)?.[0] || "";
    return `${start}${replacement}${end}`;
  }

  function translatePattern(text, target) {
    if (target === "en") {
      return text
        .replace(/^Česká republika · IČO /, "Czech Republic · Company ID ")
        .replace(/ · DIČ /g, " · Tax ID ")
        .replace(/^Zákon č\. 586\/1992 Sb\., o daních z příjmů · §\s*(.+)$/i, "Czech Income Taxes Act (Act No. 586/1992 Coll.) · Section $1")
        .replace(/^Smlouva o zamezení dvojího zdanění · článek\s*(.+)$/i, "Double Tax Treaty · Article $1")
        .replace(/^Výchozí vnitrostátní sazba činí ([0-9.,]+) %\. V následujícím kroku je zohledněno pravidlo, které tuto sazbu omezuje nebo nahrazuje\.$/i, "The general Czech domestic rate is $1%. The next legal layer then applies any rule that limits or replaces that rate.")
        .replace(/^Pravidlo příslušné smlouvy stanoví sazbu ([0-9.,]+) % při splnění jeho podmínek\.$/i, "The applicable treaty rule provides a $1% rate where its conditions are met.")
        .replace(/^Vnitrostátní pravidlo stanoví sazbu ([0-9.,]+) %\.$/i, "The domestic rule provides a $1% rate.")
        .replace(/^Podle článku ([^ ]+) smlouvy o zamezení dvojího zdanění se při zadaných údajích příjem v České republice nezdaňuje\.$/i, "Under Article $1 of the double tax treaty, the income is not taxable in the Czech Republic based on the entered facts.")
        .replace(/^Podle článku ([^ ]+) smlouvy o zamezení dvojího zdanění činí při zadaných údajích sazba srážkové daně ([0-9.,]+) %\.$/i, "Under Article $1 of the double tax treaty, the withholding tax rate is $2% based on the entered facts.")
        .replace(/^Zdanění pouze ve státě rezidence příjemce \(Rakousko\)$/i, "Taxation only in the recipient's state of residence (Austria)")
        .replace(/^Zdanění pouze ve státě rezidence příjemce \((.+)\)$/i, "Taxation only in the recipient's state of residence ($1)");
    }
    return text
      .replace(/^Czech Republic · Company ID /, "Česká republika · IČO ")
      .replace(/ · Tax ID /g, " · DIČ ")
      .replace(/^Czech Income Taxes Act \(Act No\. 586\/1992 Coll\.\) · Section\s*(.+)$/i, "Zákon č. 586/1992 Sb., o daních z příjmů · § $1")
      .replace(/^Double Tax Treaty · Article\s*(.+)$/i, "Smlouva o zamezení dvojího zdanění · článek $1")
      .replace(/^The general Czech domestic rate is ([0-9.,]+)%\. The next legal layer then applies any rule that limits or replaces that rate\.$/i, "Výchozí vnitrostátní sazba činí $1 %. V následujícím kroku je zohledněno pravidlo, které tuto sazbu omezuje nebo nahrazuje.")
      .replace(/^The applicable treaty rule provides a ([0-9.,]+)% rate where its conditions are met\.$/i, "Pravidlo příslušné smlouvy stanoví sazbu $1 % při splnění jeho podmínek.")
      .replace(/^The domestic rule provides a ([0-9.,]+)% rate\.$/i, "Vnitrostátní pravidlo stanoví sazbu $1 %.")
      .replace(/^Under Article ([^ ]+) of the double tax treaty, the income is not taxable in the Czech Republic based on the entered facts\.$/i, "Podle článku $1 smlouvy o zamezení dvojího zdanění se při zadaných údajích příjem v České republice nezdaňuje.")
      .replace(/^Under Article ([^ ]+) of the double tax treaty, the withholding tax rate is ([0-9.,]+)% based on the entered facts\.$/i, "Podle článku $1 smlouvy o zamezení dvojího zdanění činí při zadaných údajích sazba srážkové daně $2 %.")
      .replace(/^Taxation only in the recipient's state of residence \((.+)\)$/i, "Zdanění pouze ve státě rezidence příjemce ($1)");
  }

  function supplementLanguage(root = document.body) {
    if (!root) return;
    const target = currentLanguage();
    document.documentElement.lang = target;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      if (node.parentElement?.closest("blockquote,pre,code,.legal-excerpt")) return;
      const raw = node.nodeValue || "";
      const text = raw.trim();
      if (!text) return;
      const exact = target === "en" ? EXTRA_TRANSLATIONS.get(text) : REVERSE_TRANSLATIONS.get(text);
      const patterned = exact || translatePattern(text, target);
      if (patterned && patterned !== text) node.nodeValue = preserveWhitespace(raw, patterned);
    });
  }

  function moveIrNoticeToEnd() {
    const step = document.querySelector('.flow-step[data-step="4"]');
    const notice = step?.querySelector("#cz-ir-exemption-notice");
    if (!step || !notice || notice.hidden) return;
    const citations = step.querySelector("#workspace-citations");
    const sourcesCard = citations?.closest("article.card,.card,.result-sources") || citations?.parentElement;
    const actions = step.querySelector(".flow-actions");
    if (sourcesCard && sourcesCard.nextElementSibling !== notice) {
      sourcesCard.after(notice);
    } else if (!sourcesCard && actions && notice.nextElementSibling !== actions) {
      actions.before(notice);
    }
  }

  function refresh() {
    installStyles();
    moveIrNoticeToEnd();
    supplementLanguage(document.body);
  }

  function scheduleRefresh() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      refresh();
      [80, 220, 600].forEach((delay) => window.setTimeout(refresh, delay));
    });
  }

  function setLanguage(lang) {
    if (!["cs", "en"].includes(lang)) return;
    const select = document.querySelector("#taxtreat-ui-language");
    localStorage.setItem(UI_LANGUAGE_KEY, lang);
    if (select) {
      select.value = lang;
      select.dispatchEvent(new Event("change", { bubbles:true }));
    }
    scheduleRefresh();
  }

  document.addEventListener("click", (event) => {
    const button = event.target?.closest?.("#taxtreat-language-controls .tt-lang-mini button[data-lang]");
    if (button) {
      setLanguage(button.dataset.lang);
      return;
    }
    if (event.target?.closest?.("[data-nav],[data-next-step],[data-flow-step],[data-start-flow],#workspace-submit")) scheduleRefresh();
  }, true);

  document.addEventListener("change", (event) => {
    if (event.target?.id === "taxtreat-ui-language") {
      localStorage.setItem(UI_LANGUAGE_KEY, event.target.value);
      scheduleRefresh();
      return;
    }
    if (event.target?.closest?.("#workspace-payment")) scheduleRefresh();
  }, true);

  const previousFetch = window.fetch.bind(window);
  window.fetch = async function taxTreatLiveLanguageFetch(resource, options = {}) {
    const response = await previousFetch(resource, options);
    const url = typeof resource === "string" ? resource : resource?.url || "";
    if (url.endsWith("/analysis/intake") || url.includes("/exchange-rates/cnb")) scheduleRefresh();
    return response;
  };

  refresh();
})();
