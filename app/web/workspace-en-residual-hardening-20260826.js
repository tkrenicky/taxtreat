(() => {
  "use strict";

  const PAIRS = [
    ["PRACOVNÍ PROSTOR", "WORKSPACE"],
    ["Přehled", "Overview"],
    ["Platby, příjemci a informace navázané na zadané údaje.", "Payments, recipients and information linked to the entered data."],
    ["Úkoly", "Tasks"],
    ["Doklad k případnému smluvnímu nároku není evidován", "No supporting document for a potential treaty claim is recorded."],
    ["Otevřít profil →", "Open profile →"],
    ["Příjemce je daňovým rezidentem státu", "The recipient is a tax resident of"],
    ["pro účely příslušné smlouvy.", "for the purposes of the applicable treaty."],
    ["Jaký podíl na základním kapitálu českého plátce příjemce drží?", "What percentage of the Czech payer's registered capital does the recipient hold?"],
    ["Drží příjemce tento podíl přímo?", "Does the recipient hold this interest directly?"],
    ["Jak dlouho příjemce podíl drží?", "How long has the recipient held this interest?"],
    ["Jaký podíl na hlasovacích právech českého plátce příjemce drží?", "What percentage of the Czech payer's voting rights does the recipient hold?"],
    ["Předvyplněno podle podílu na základním kapitálu. Uprav, pokud se podíl na hlasovacích právech liší.", "Pre-filled based on the registered-capital percentage. Adjust if the voting-rights percentage differs."],
    ["Podíl, přímé držení, dobu držby, skutečné vlastnictví a vazbu ke stálé provozovně už TaxTreat používá z odpovědí výše.", "TaxTreat already uses the answers above for ownership percentage, direct holding, holding period, beneficial ownership and permanent-establishment connection."],
    ["Je příjemce běžnou obchodní společností (např. GmbH, AG, Ltd. nebo S.A.), nikoli fyzickou osobou, fondem nebo daňově transparentním subjektem?", "Is the recipient an ordinary commercial company (e.g. GmbH, AG, Ltd. or S.A.), rather than an individual, fund or tax-transparent entity?"],
    ["Pokud si nejsi jistý právní formou příjemce, zvol raději „Ne“ nebo údaj ověř v korporátních podkladech.", "If you are unsure about the recipient's legal form, select “No” or verify it in the corporate documentation."],
    ["Podléhá příjemce ve státě své daňové rezidence běžné dani z příjmů právnických osob a není od této daně osvobozen ani v režimu s nulovou sazbou?", "Is the recipient subject to ordinary corporate income tax in its state of tax residence and neither exempt from that tax nor subject to a zero-rate regime?"],
    ["Jde o faktické daňové postavení příjemce, nikoli o posouzení českého § 19.", "This concerns the recipient's actual tax status, not the assessment under Section 19 of the Czech Income Taxes Act."],
    ["Ještě dva údaje pro možné osvobození podle § 19 ZDP", "Additional facts for potential domestic exemption"],
    ["Vyber odpověď", "Select answer"],
    ["Ano, přímo", "Yes, directly"],
    ["Ne, nepřímo", "No, indirectly"],
    ["Znám datum nabytí podílu", "I know the acquisition date"],
    ["K datu transakce alespoň 12 měsíců", "At least 12 months as of the transaction date"],
    ["K datu transakce méně než 12 měsíců", "Less than 12 months as of the transaction date"],
    ["Datum nabytí podílu", "Share acquisition date"],
    ["Doba držby se vypočte automaticky k datu transakce.", "The holding period is calculated automatically as of the transaction date."],
    ["VÝPOČET DOKONČEN", "CALCULATION COMPLETE"],
    ["Česká daň k odvodu", "Czech withholding tax payable"],
    ["Daň se neodvádí", "No withholding tax remittance required"],
    ["Souhrn platby", "Payment summary"],
    ["Hrubá částka", "Gross amount"],
    ["Čistá částka", "Net amount"],
    ["1. VÝCHOZÍ VNITROSTÁTNÍ PRAVIDLO", "1. BASE DOMESTIC RULE"],
    ["2. POUŽITÉ SMLUVNÍ PRAVIDLO", "2. APPLIED TREATY RULE"],
    ["3. SEKUNDÁRNÍ SMLUVNÍ OCHRANA", "3. SECONDARY TREATY PROTECTION"],
    ["Otevřít zdroj ↗", "Open source ↗"],
    ["Otevřít zdroj", "Open source"],
    ["Oficiální zdroj e-Sbírka ↗", "Official e-Sbírka source ↗"],
    ["Oficiální zdroj e-Sbírka", "Official e-Sbírka source"],
    ["Znění použitého ustanovení", "Text of the applied provision"],
    ["Použité právní pravidlo", "Applied legal rule"],
    ["Smlouva o zamezení dvojího zdanění", "Double Tax Treaty"],
    ["Česká daň se při tomto daňovém zacházení neodvádí. Oznámení podle § 38da zákona č. 586/1992 Sb., o daních z příjmů se u dividend a licenčních poplatků podává do 31. ledna následujícího roku.", "No Czech tax is remitted under this tax treatment. For dividends and royalties, the outbound-income notification under Section 38da of the Czech Income Taxes Act is due by 31 January of the following year."],
    ["U dividend může povinnost srazit daň podle § 38d odst. 2 zákona č. 586/1992 Sb., o daních z příjmů vzniknout i před zadaným datem. Pro úplné určení je nutné zohlednit také schválení účetní závěrky a rozhodnutí o rozdělení zisku.", "For dividends, the obligation to withhold tax under Section 38d(2) of the Czech Income Taxes Act may arise before the entered date. A complete determination must also take into account approval of the financial statements and the decision on profit distribution."],
    ["Ano", "Yes"],
    ["Ne", "No"]
  ];

  const PLACEHOLDERS = [["např. 25", "e.g. 25"], ["např. Example GmbH", "e.g. Example GmbH"]];
  const ORDERED = [...PAIRS].sort((a, b) => Math.max(b[0].length, b[1].length) - Math.max(a[0].length, a[1].length));

  function language() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
  }

  function swap(value, from, to) {
    if (!value.includes(from)) return value;
    if (from.length <= 4) {
      const key = value.trim();
      return key === from ? value.replace(key, to) : value;
    }
    return value.split(from).join(to);
  }

  function translate(value) {
    const en = language() === "en";
    let next = String(value || "");
    for (const [cs, english] of ORDERED) next = swap(next, en ? cs : english, en ? english : cs);
    if (en) {
      next = next
        .replace(/Smlouva o zamezení dvojího zdanění\s*·\s*(?:Č|č)lánek\s*(\d+)/g, "Double Tax Treaty · Article $1")
        .replace(/(\d[\d\s.,]*)\s*Kč\b/g, "$1 CZK");
    } else {
      next = next
        .replace(/Double Tax Treaty\s*·\s*Article\s*(\d+)/g, "Smlouva o zamezení dvojího zdanění · článek $1")
        .replace(/(\d[\d\s.,]*)\s*CZK\b/g, "$1 Kč");
    }
    return next;
  }

  function translateText(root) {
    if (!root) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
      if (node.parentElement?.closest("blockquote,.legal-excerpt,pre,code")) continue;
      const next = translate(node.nodeValue || "");
      if (next !== node.nodeValue) node.nodeValue = next;
    }
  }

  function translateAttributes(root) {
    const all = [];
    if (root?.nodeType === Node.ELEMENT_NODE) all.push(root);
    if (root?.querySelectorAll) all.push(...root.querySelectorAll("[placeholder],[title],[aria-label]"));
    const en = language() === "en";
    for (const element of all) {
      for (const attr of ["placeholder", "title", "aria-label"]) {
        if (!element.hasAttribute?.(attr)) continue;
        let value = element.getAttribute(attr) || "";
        for (const [cs, english] of PLACEHOLDERS) value = swap(value, en ? cs : english, en ? english : cs);
        value = translate(value);
        if (value !== element.getAttribute(attr)) element.setAttribute(attr, value);
      }
    }
  }

  function fixTreatyResidence() {
    document.querySelectorAll(".assumption-row > span").forEach((span) => {
      const text = (span.textContent || "").trim();
      if (!/^(?:Příjemce je daňovým rezidentem státu|The recipient is a tax resident of)\s+/i.test(text)) return;
      const countryNode = span.querySelector("[data-recipient-country-name]");
      const current = (countryNode?.textContent || "").trim() || (/Austria|Rakousko/i.test(text) ? "Austria" : "");
      const country = language() === "en" ? current.replace(/^Rakousko$/i, "Austria") : current.replace(/^Austria$/i, "Rakousko");
      const desired = language() === "en"
        ? `The recipient is a tax resident of ${country} for the purposes of the applicable treaty.`
        : `Příjemce je daňovým rezidentem státu ${country} pro účely příslušné smlouvy.`;
      if (text === desired) return;
      const b = document.createElement("b");
      b.textContent = country;
      b.setAttribute("data-recipient-country-name", "");
      span.replaceChildren(
        document.createTextNode(language() === "en" ? "The recipient is a tax resident of " : "Příjemce je daňovým rezidentem státu "),
        b,
        document.createTextNode(language() === "en" ? " for the purposes of the applicable treaty." : " pro účely příslušné smlouvy.")
      );
    });
  }

  function resultRoot() {
    return document.querySelector('.flow-step[data-step="4"].active');
  }

  function section19Active() {
    const root = resultRoot();
    if (!root) return false;
    const text = root.textContent || "";
    return /Section 19 applies|Domestic exemption under Section 19|§\s*19\s+se\s+uplatn[ií]|vnitrostátní osvobození[^.\n]*§\s*19/i.test(text);
  }

  function fixSection19Presentation() {
    if (!section19Active()) return;
    const root = resultRoot();
    const heading = [...root.querySelectorAll("h1,h2,h3,h4,strong,b")].find((el) => /^(Applied legal rule|Použité právní pravidlo)$/i.test((el.textContent || "").trim()));
    const card = heading?.closest(".card") || heading?.parentElement;
    const body = card?.querySelector("p") || heading?.nextElementSibling;
    if (body) {
      const desired = language() === "en"
        ? "Section 19 of the Czech Income Taxes Act applies. The domestic exemption means that no Czech withholding tax is due based on the entered facts."
        : "Uplatní se § 19 zákona o daních z příjmů. Na základě zadaných údajů vnitrostátní osvobození znamená, že česká srážková daň není splatná.";
      if ((body.textContent || "").trim() !== desired) body.textContent = desired;
    }
    root.querySelectorAll("h1,h2,h3,h4,strong,b,div,p,span").forEach((el) => {
      if (el.children.length) return;
      const text = (el.textContent || "").trim();
      const match = text.match(/^(\d+)\.\s*(?:POUŽITÉ SMLUVNÍ PRAVIDLO|APPLIED TREATY RULE|SEKUNDÁRNÍ SMLUVNÍ OCHRANA|SECONDARY TREATY PROTECTION)$/i);
      if (!match) return;
      const desired = `${match[1]}. ${language() === "en" ? "SECONDARY TREATY PROTECTION" : "SEKUNDÁRNÍ SMLUVNÍ OCHRANA"}`;
      if (text !== desired) el.textContent = desired;
    });
  }

  function fixQuestionTypography() {
    const reference = document.querySelector('.fact-question[data-dividend-step="2"] > span') || document.querySelector('.fact-question[data-dividend-step="1"] > span');
    const target = document.querySelector('.fact-question[data-dividend-step="3"] > span');
    if (!reference || !target) return;
    const style = getComputedStyle(reference);
    for (const prop of ["font-size", "font-weight", "line-height", "font-family"]) target.style.setProperty(prop, style.getPropertyValue(prop), "important");
  }

  function refresh(root = document.body) {
    document.documentElement.lang = language() === "en" ? "en" : "cs";
    translateText(root);
    translateAttributes(root);
    fixTreatyResidence();
    fixSection19Presentation();
    fixQuestionTypography();
  }

  let timer = 0;
  function schedule(root = document.body) {
    clearTimeout(timer);
    timer = setTimeout(() => refresh(root), 20);
  }

  document.addEventListener("change", () => schedule(document.body), true);
  document.addEventListener("click", () => schedule(document.body), true);
  new MutationObserver((records) => {
    const added = records.flatMap((record) => [...record.addedNodes]).find((node) => node.nodeType === Node.ELEMENT_NODE);
    schedule(added || document.body);
  }).observe(document.documentElement, { childList: true, subtree: true, characterData: true });
  [0, 50, 150, 400, 900, 1600].forEach((delay) => setTimeout(() => refresh(document.body), delay));
})();
