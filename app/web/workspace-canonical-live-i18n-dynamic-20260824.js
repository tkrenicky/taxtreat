(() => {
  "use strict";

  const CS_MARKER = /Daňová rezidence:|Typ subjektu:|Skutečný vlastník(?: příjmu)?:|Vazba (?:na|ke) stálou provozovnu(?: v ČR)?:|Podíl na plátci:|Datum nabytí podílu:|profilové údaje vyplněny|základní údaje vyplněny/;
  const EN_MARKER = /Tax residence:|Entity type:|Beneficial owner:|Permanent establishment connection:|Ownership in payer:|Share acquisition date:|profile details completed|basic details completed/;
  const originalTreatyText = new WeakMap();

  const AT_TREATY_EN = {
    "10": `Article 10\nDIVIDENDS\n\n(1) Dividends paid by a company which is a resident of a Contracting State to a resident of the other Contracting State may be taxed in that other State.\n\n(2) a) However, such dividends may also be taxed in the Contracting State of which the company paying the dividends is a resident and according to the laws of that State, but if the beneficial owner of the dividends is a resident of the other Contracting State, the tax so charged shall not exceed 10 per cent of the gross amount of the dividends.\n\nb) If the beneficial owner is a company which holds at least 10 per cent of the capital of the company paying the dividends, such dividends shall be taxable only in the Contracting State of which the beneficial owner of the dividends is a resident.\n\nThe competent authorities of the Contracting States shall by mutual agreement settle the mode of application of these limitations. This paragraph shall not affect the taxation of the company in respect of the profits out of which the dividends are paid.\n\n(3) The term “dividends” as used in this Article means income from shares, “jouissance” shares or “jouissance” rights or other rights, not being debt-claims, participating in profits, as well as other income which is subjected to the same taxation treatment as income from shares by the laws of the State of which the company paying the income is a resident.\n\n(4) The provisions of paragraphs 1 and 2 shall not apply if the beneficial owner of the dividends, being a resident of a Contracting State, carries on business in the other Contracting State of which the company paying the dividends is a resident through a permanent establishment situated therein and the holding in respect of which the dividends are paid is effectively connected with such permanent establishment. In such case the provisions of Article 7 shall apply.\n\n(5) Where a company which is a resident of a Contracting State derives profits or income from the other Contracting State, that other State may not impose any tax on the dividends paid by the company, except insofar as such dividends are paid to a resident of that other State or insofar as the holding in respect of which the dividends are paid is effectively connected with a permanent establishment situated in that other State, nor subject the company’s undistributed profits to a tax on the company’s undistributed profits, even if the dividends paid or the undistributed profits consist wholly or partly of profits or income arising in such other State.`,
    "11": `Article 11\nINTEREST\n\n(1) Interest arising in a Contracting State and beneficially owned by a resident of the other Contracting State shall be taxable only in that other State.\n\n(2) The term “interest” as used in this Article means income from debt-claims of every kind, whether or not secured by mortgage and whether or not carrying a right to participate in the debtor’s profits, and in particular, income from government securities and income from bonds or debentures, including premiums and prizes attaching to such securities, bonds or debentures. Penalty charges for late payment shall not be regarded as interest for the purposes of this Article. The term “interest” shall not include any item of income which is considered as a dividend under the provisions of paragraph 3 of Article 10.\n\n(3) The provisions of paragraph 1 shall not apply if the beneficial owner of the interest, being a resident of a Contracting State, carries on business in the other Contracting State in which the interest arises through a permanent establishment situated therein and the debt-claim in respect of which the interest is paid is effectively connected with such permanent establishment. In such case the provisions of Article 7 shall apply.\n\n(4) Interest shall be deemed to arise in a Contracting State when the payer is a resident of that State. Where, however, the person paying the interest, whether he is a resident of a Contracting State or not, has in a Contracting State a permanent establishment in connection with which the indebtedness on which the interest is paid was incurred, and such interest is borne by such permanent establishment, then such interest shall be deemed to arise in the State in which the permanent establishment is situated.\n\n(5) Where, by reason of a special relationship between the payer and the beneficial owner or between both of them and some other person, the amount of the interest, having regard to the debt-claim for which it is paid, exceeds the amount which would have been agreed upon by the payer and the beneficial owner in the absence of such relationship, the provisions of this Article shall apply only to the last-mentioned amount. In such case, the excess part of the payments shall remain taxable according to the laws of each Contracting State, due regard being had to the other provisions of this Convention.`,
    "12": `Article 12\nROYALTIES\n\n(1) Royalties arising in a Contracting State and paid to a resident of the other Contracting State may be taxed in that other State.\n\n(2) However, the royalties mentioned in sub-paragraph a) of paragraph 3 may also be taxed in the Contracting State in which they arise and according to the laws of that State, but if the beneficial owner of the royalties is a resident of the other Contracting State, the tax so charged shall not exceed 5 per cent of the gross amount of the royalties. The competent authorities of the Contracting States shall by mutual agreement settle the mode of application of these limitations.\n\n(3) The term “royalties” as used in this Article means payments of any kind received as a consideration for the use of, or the right to use:\n\na) any patent, trade mark, design or model, plan, secret formula or process, computer software, or industrial, commercial or scientific equipment, or for information concerning industrial, commercial or scientific experience;\n\nb) any copyright of literary, artistic or scientific work including cinematograph films and films or tapes for television or radio broadcasting.\n\n(4) The provisions of paragraphs 1 and 2 shall not apply if the beneficial owner of the royalties, being a resident of a Contracting State, carries on business in the other Contracting State in which the royalties arise through a permanent establishment situated therein and the right or property in respect of which the royalties are paid is effectively connected with such permanent establishment. In such case the provisions of Article 7 shall apply.\n\n(5) Royalties shall be deemed to arise in a Contracting State when the payer is a resident of that State. Where, however, the person paying the royalties, whether he is a resident of a Contracting State or not, has in a Contracting State a permanent establishment in connection with which the liability to pay the royalties was incurred, and such royalties are borne by such permanent establishment, then such royalties shall be deemed to arise in the State in which the permanent establishment is situated.\n\n(6) Where, by reason of a special relationship between the payer and the beneficial owner or between both of them and some other person, the amount of the royalties, having regard to the use, right or information for which they are paid, exceeds the amount which would have been agreed upon by the payer and the beneficial owner in the absence of such relationship, the provisions of this Article shall apply only to the last-mentioned amount. In such case, the excess part of the payments shall remain taxable according to the laws of each Contracting State, due regard being had to the other provisions of this Convention.`
  };

  const EXACT = new Map([
    ["Označuje povinný údaj.", "Indicates a required field."],
    ["ÚDAJE PODLE DRUHU PŘÍJMU", "INCOME-SPECIFIC FACTS"],
    ["Vyplň dostupné skutkové údaje před výpočtem. Údaje uložené v profilu příjemce jsou předvyplněny a lze je pro tuto platbu změnit.", "Complete the available transaction facts before calculation. Facts stored in the recipient profile are pre-filled and can be changed for this payment."],
    ["Ano, přímo", "Yes, directly"],
    ["K datu transakce alespoň 12 měsíců", "At least 12 months as of the transaction date"],
    ["Podíl, přímé držení, dobu držby, skutečné vlastnictví a vazbu ke stálé provozovně už TaxTreat používá z odpovědí výše.", "TaxTreat already uses the ownership percentage, direct holding, holding period, beneficial ownership and permanent-establishment connection from the answers above."],
    ["Je příjemce běžnou obchodní společností (např. GmbH, AG, Ltd. nebo S.A.), nikoli fyzickou osobou, fondem nebo daňově transparentním subjektem?", "Is the recipient an ordinary commercial company (e.g. GmbH, AG, Ltd. or S.A.), rather than an individual, fund or tax-transparent entity?"],
    ["Pokud si nejsi jistý právní formou příjemce, zvol raději „Ne“ nebo údaj ověř v korporátních podkladech.", "If you are unsure about the recipient’s legal form, select “No” or verify it in the corporate documentation."],
    ["Podléhá příjemce ve státě své daňové rezidence běžné dani z příjmů právnických osob a není od této daně osvobozen ani v režimu s nulovou sazbou?", "Is the recipient subject to ordinary corporate income tax in its state of tax residence and neither exempt from that tax nor subject to a zero-rate regime?"],
    ["Jde o faktické daňové postavení příjemce, nikoli o posouzení českého § 19.", "This concerns the recipient’s actual tax status, not the assessment under Section 19 of the Czech Income Taxes Act."],
    ["← Zpět k příjemci", "← Back to recipient"],
    ["Platby", "Payments"],
    ["Stav", "Status"],
    ["Aktivní", "Active"],
    ["Připraven", "Ready"],
    ["Nastavit jako aktivního", "Set as active"],
    ["Po dokončení prvního výpočtu se zde zobrazí výsledek a report.", "The result and report will appear here after the first calculation is completed."],
    ["1. POUŽITÉ PRAVIDLO", "1. APPLIED RULE"],
    ["2. OBECNÁ ČESKÁ SAZBA BEZ OSVOBOZENÍ", "2. GENERAL CZECH RATE WITHOUT EXEMPTION"],
    ["3. SEKUNDÁRNÍ SMLUVNÍ OCHRANA", "3. SECONDARY TREATY PROTECTION"],
    ["Pokud by se neuplatnilo osvobození podle § 19 ZDP ani příznivější smluvní pravidlo, česká vnitrostátní úprava stanoví u tohoto příjmu sazbu 15 %.", "If neither the exemption under Section 19 of the Czech Income Taxes Act nor a more favourable treaty rule applied, Czech domestic law would impose a 15% withholding tax rate on this income."],
    ["Česká daň se při tomto daňovém zacházení neodvádí. Oznámení podle § 38da ZDP se u dividend a licenčních poplatků podává do 31. ledna následujícího roku.", "No Czech tax is remitted under this tax treatment. For dividends and royalties, the outbound-income notification under Section 38da of the Czech Income Taxes Act is due by 31 January of the following year."],
    ["U dividend může povinnost srazit daň podle § 38d odst. 2 zákona č. 586/1992 Sb., o daních z příjmů vzniknout i před zadaným datem. Pro úplné určení je nutné zohlednit také schválení účetní závěrky a rozhodnutí o rozdělení zisku.", "For dividends, the obligation to withhold tax under Section 38d(2) of the Czech Income Taxes Act may arise before the entered date. A complete determination must also take into account approval of the financial statements and the decision on profit distribution."]
  ]);
  const REVERSE = new Map(Array.from(EXACT, ([cs, en]) => [en, cs]));

  function language() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
  }

  function translateDynamicLine(text, toEnglish) {
    if (toEnglish) {
      if (!CS_MARKER.test(text)) return text;
      return text
        .replace(/Daňová rezidence:\s*Rakouska/g, "Tax residence: Austria")
        .replace(/Daňová rezidence:/g, "Tax residence:")
        .replace(/Typ subjektu:/g, "Entity type:")
        .replace(/Skutečný vlastník(?: příjmu)?:/g, "Beneficial owner:")
        .replace(/Vazba (?:na|ke) stálou provozovnu(?: v ČR)?:/g, "Permanent establishment connection:")
        .replace(/Podíl na plátci:/g, "Ownership in payer:")
        .replace(/Datum nabytí podílu:/g, "Share acquisition date:")
        .replace(/profilové údaje vyplněny/g, "profile details completed")
        .replace(/základní údaje vyplněny/g, "basic details completed")
        .replace(/Rakouska|Rakousko/g, "Austria")
        .replace(/\bSpolečnost\b/g, "Company")
        .replace(/\bspolečnost\b/g, "company")
        .replace(/\bNevyplněno\b/g, "Not provided")
        .replace(/\bAno\b/g, "Yes")
        .replace(/\bNe\b/g, "No");
    }

    if (!EN_MARKER.test(text)) return text;
    return text
      .replace(/Tax residence:\s*Austria/g, "Daňová rezidence: Rakouska")
      .replace(/Tax residence:/g, "Daňová rezidence:")
      .replace(/Entity type:/g, "Typ subjektu:")
      .replace(/Beneficial owner:/g, "Skutečný vlastník:")
      .replace(/Permanent establishment connection:/g, "Vazba na stálou provozovnu:")
      .replace(/Ownership in payer:/g, "Podíl na plátci:")
      .replace(/Share acquisition date:/g, "Datum nabytí podílu:")
      .replace(/profile details completed/g, "profilové údaje vyplněny")
      .replace(/basic details completed/g, "základní údaje vyplněny")
      .replace(/\bAustria\b/g, "Rakousko")
      .replace(/\bCompany\b/g, "Společnost")
      .replace(/\bcompany\b/g, "společnost")
      .replace(/\bNot provided\b/g, "Nevyplněno")
      .replace(/\bYes\b/g, "Ano")
      .replace(/\bNo\b/g, "Ne");
  }

  function translateGeneralText(text, toEnglish) {
    const key = text.trim();
    if (!key) return text;

    if (toEnglish && /^Czech withholding tax is therefore 0\s*%; treaty protection is secondary\.$/i.test(key)) {
      return text.replace(key, "Czech withholding tax does not apply; treaty protection is secondary.");
    }
    if (!toEnglish && key === "Czech withholding tax does not apply; treaty protection is secondary.") {
      return text.replace(key, "Česká srážková daň se neuplatní; smluvní ochrana je sekundární.");
    }

    let translated = toEnglish ? EXACT.get(key) : REVERSE.get(key);
    if (translated) return text.replace(key, translated);

    if (toEnglish) {
      if (/^Příjemce je daňovým rezidentem státu\s+Austria\s+pro účely příslušné smlouvy\.?$/i.test(key)) {
        return text.replace(key, "The recipient is a tax resident of Austria for the purposes of the applicable treaty.");
      }
      if (/^DIČ\s+(.+)$/i.test(key)) return text.replace(key, `Tax ID ${key.replace(/^DIČ\s+/i, "")}`);
      if (/^-?[\d\s.,]+\s*Kč$/.test(key)) return text.replace(key, key.replace(/\s*Kč$/, " CZK"));
    } else {
      if (/^The recipient is a tax resident of Austria for the purposes of the applicable treaty\.$/i.test(key)) {
        return text.replace(key, "Příjemce je daňovým rezidentem státu Rakousko pro účely příslušné smlouvy.");
      }
      if (/^Tax ID\s+CZ/i.test(key)) return text.replace(key, key.replace(/^Tax ID\s+/i, "DIČ "));
      if (/^-?[\d\s.,]+\s+CZK$/.test(key)) return text.replace(key, key.replace(/\s+CZK$/, " Kč"));
    }
    return text;
  }

  function incomeType() {
    return document.querySelector('[name="income_type"]')?.value || "";
  }

  function correctPeQuestion() {
    const type = incomeType();
    if (!type) return;
    const toEnglish = language() === "en";
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    const marker = /specific interest, receivable or right giving rise to this payment|debt-claim giving rise to this interest|holding giving rise to this dividend|right or property giving rise to these royalties|konkrétní úrok|podíl, z něhož je dividenda|právo nebo majetek, za který jsou placeny licenční poplatky/i;
    nodes.forEach((node) => {
      const current = (node.nodeValue || "").trim();
      if (!marker.test(current)) return;
      let next;
      if (toEnglish) {
        next = type === "dividend"
          ? "The holding giving rise to this dividend is effectively connected with the recipient’s permanent establishment in the Czech Republic."
          : type === "interest"
          ? "The debt-claim giving rise to this interest is effectively connected with the recipient’s permanent establishment in the Czech Republic."
          : "The right or property giving rise to these royalties is effectively connected with the recipient’s permanent establishment in the Czech Republic.";
      } else {
        next = type === "dividend"
          ? "Podíl, z něhož je dividenda vyplácena, je skutečně spojen s činností stálé provozovny příjemce v České republice."
          : type === "interest"
          ? "Pohledávka, z níž plyne tento úrok, je skutečně spojena s činností stálé provozovny příjemce v České republice."
          : "Právo nebo majetek, za který jsou placeny licenční poplatky, je skutečně spojen s činností stálé provozovny příjemce v České republice.";
      }
      if (current !== next) node.nodeValue = (node.nodeValue || "").replace(current, next);
    });
  }

  function isAustriaContext() {
    const text = document.body?.textContent || "";
    return /\bAustria\b|Rakousk/i.test(text);
  }

  function articleNumber(card) {
    const text = card?.textContent || "";
    const match = text.match(/(?:Article|článek|Článek)\s*(10|11|12)\b/);
    return match?.[1] || null;
  }

  function switchTreatyExcerpts() {
    const toEnglish = language() === "en";
    document.querySelectorAll("#workspace-citations .citation-card").forEach((card) => {
      const title = card.textContent || "";
      if (!/Double Tax Treaty|Smlouva o zamezení dvojího zdanění/i.test(title)) return;
      const excerpt = card.querySelector(".legal-excerpt, blockquote");
      if (!excerpt) return;
      if (!originalTreatyText.has(excerpt)) originalTreatyText.set(excerpt, excerpt.textContent || "");
      const article = articleNumber(card);
      if (toEnglish && isAustriaContext() && article && AT_TREATY_EN[article]) {
        excerpt.textContent = AT_TREATY_EN[article];
        excerpt.setAttribute("lang", "en");
        excerpt.dataset.ttTreatyLanguage = "en-official";
      } else if (!toEnglish && originalTreatyText.has(excerpt)) {
        excerpt.textContent = originalTreatyText.get(excerpt);
        excerpt.setAttribute("lang", "cs");
        delete excerpt.dataset.ttTreatyLanguage;
      }
    });
  }

  function refresh() {
    const toEnglish = language() === "en";
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      if (node.parentElement?.closest("blockquote,.legal-excerpt,pre,code")) return;
      const current = node.nodeValue || "";
      let next = translateDynamicLine(current, toEnglish);
      next = translateGeneralText(next, toEnglish);
      if (next !== current) node.nodeValue = next;
    });
    correctPeQuestion();
    switchTreatyExcerpts();
  }

  function schedule() {
    [0, 50, 150, 400, 900].forEach((delay) => window.setTimeout(refresh, delay));
  }

  document.addEventListener("change", (event) => {
    if (event.target?.id === "taxtreat-ui-language" || event.target?.matches?.('[name="income_type"]')) schedule();
  }, true);
  document.addEventListener("click", () => window.setTimeout(schedule, 0), true);
  schedule();
})();
