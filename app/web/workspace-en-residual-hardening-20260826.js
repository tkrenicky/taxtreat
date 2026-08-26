(() => {
  "use strict";

  const translations = new Map([
    ["Příjemce je daňovým rezidentem státu", "The recipient is a tax resident of"],
    ["pro účely příslušné smlouvy.", "for the purposes of the applicable treaty."],
    ["Jaký podíl na základním kapitálu českého plátce příjemce drží?", "What percentage of the Czech payer's registered capital does the recipient hold?"],
    ["Drží příjemce tento podíl přímo?", "Does the recipient hold this interest directly?"],
    ["Jak dlouho příjemce podíl drží?", "How long has the recipient held this interest?"],
    ["Jaký podíl na hlasovacích právech českého plátce příjemce drží?", "What percentage of the Czech payer's voting rights does the recipient hold?"],
    ["Předvyplněno podle podílu na základním kapitálu. Uprav, pokud se podíl na hlasovacích právech liší.", "Pre-filled based on the registered-capital percentage. Adjust if the voting-rights percentage differs."],
    ["Podíl, přímé držení, dobu držby, skutečné vlastnictví a vazbu ke stálé provozovně už TaxTreat používá z odpovědí výše.", "TaxTreat already uses the answers above for ownership percentage, direct holding, holding period, beneficial ownership and permanent-establishment connection."],
    ["Je příjemce běžnou obchodní společností (např. GmbH, AG, Ltd. nebo S.A.), nikoli fyzickou osobou, fondem nebo daňově transparentním subjektem?", "Is the recipient an ordinary trading company (e.g. GmbH, AG, Ltd. or S.A.), rather than an individual, fund or tax-transparent entity?"],
    ["Pokud si nejsi jistý právní formou příjemce, zvol raději „Ne“ nebo údaj ověř v korporátních podkladech.", "If you are unsure about the recipient's legal form, choose 'No' or verify it in the corporate documents."],
    ["Podléhá příjemce ve státě své daňové rezidence běžné dani z příjmů právnických osob a není od této daně osvobozen ani v režimu s nulovou sazbou?", "Is the recipient subject to ordinary corporate income tax in its state of tax residence and not exempt from that tax, including under a zero-rate regime?"],
    ["Jde o faktické daňové postavení příjemce, nikoli o posouzení českého § 19.", "This concerns the recipient's actual tax position, not an assessment under Czech Section 19."],
    ["Ještě dva údaje pro možné osvobození podle § 19 ZDP", "Additional facts for potential domestic exemption"],
    ["Vyber odpověď", "Select answer"],
    ["Ano", "Yes"],
    ["Ne", "No"],
    ["Ano, přímo", "Yes, directly"],
    ["Ne, nepřímo", "No, indirectly"],
    ["Znám datum nabytí podílu", "I know the acquisition date"],
    ["K datu transakce alespoň 12 měsíců", "At least 12 months as of the transaction date"],
    ["K datu transakce méně než 12 měsíců", "Less than 12 months as of the transaction date"],
    ["Datum nabytí podílu", "Share acquisition date"],
    ["Doba držby se vypočte automaticky k datu transakce.", "The holding period is calculated automatically as of the transaction date."],
    ["Česká daň k odvodu", "Czech withholding tax payable"],
    ["Daň se neodvádí", "No tax remittance required"],
    ["Česká daň se při tomto daňovém zacházení neodvádí. Oznámení podle § 38da zákona č. 586/1992 Sb., o daních z příjmů se u dividend a licenčních poplatků podává do 31. ledna následujícího roku.", "No Czech tax is remitted under this tax treatment. For dividends and royalties, the outbound-income notification under Section 38da of the Czech Income Taxes Act is due by 31 January of the following year."],
    ["U dividend může povinnost srazit daň podle § 38d odst. 2 zákona č. 586/1992 Sb., o daních z příjmů vzniknout i před zadaným datem. Pro úplné určení je nutné zohlednit také schválení účetní závěrky a rozhodnutí o rozdělení zisku.", "For dividends, the obligation to withhold tax under Section 38d(2) of the Czech Income Taxes Act may arise before the entered date. A complete determination must also take into account approval of the financial statements and the decision on profit distribution."],
    ["VÝPOČET DOKONČEN", "CALCULATION COMPLETE"]
  ]);

  function language() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
  }

  function replaceTextNodes(root) {
    if (!root || language() !== "en") return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
      if (node.parentElement?.closest("blockquote,.legal-excerpt,pre,code")) continue;
      let value = node.nodeValue || "";
      for (const [cs, en] of translations) {
        if (value.includes(cs)) value = value.split(cs).join(en);
      }
      if (value !== node.nodeValue) node.nodeValue = value;
    }
  }

  function fixTreatyResidenceSentence() {
    if (language() !== "en") return;
    document.querySelectorAll(".assumption-row > span").forEach((span) => {
      const text = (span.textContent || "").trim();
      if (!/^Příjemce je daňovým rezidentem státu\s+/i.test(text) && !/^The recipient is a tax resident of\s+/i.test(text)) return;
      const countryNode = span.querySelector("[data-recipient-country-name]");
      const country = (countryNode?.textContent || "").trim() || "the recipient's jurisdiction";
      span.replaceChildren(
        document.createTextNode("The recipient is a tax resident of "),
        Object.assign(document.createElement("b"), { textContent: country }),
        document.createTextNode(" for the purposes of the applicable treaty.")
      );
      const b = span.querySelector("b");
      if (b) b.setAttribute("data-recipient-country-name", "");
    });
  }

  function refresh() {
    if (language() !== "en") return;
    replaceTextNodes(document.body);
    fixTreatyResidenceSentence();
  }

  let timer = 0;
  function schedule() {
    window.clearTimeout(timer);
    timer = window.setTimeout(refresh, 25);
  }

  document.addEventListener("change", schedule, true);
  document.addEventListener("click", schedule, true);
  const observer = new MutationObserver(schedule);
  observer.observe(document.documentElement, { childList: true, subtree: true, characterData: true });
  [0, 50, 150, 400, 900, 1600].forEach((delay) => window.setTimeout(refresh, delay));
})();
