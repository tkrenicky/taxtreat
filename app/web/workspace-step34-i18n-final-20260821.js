(() => {
  "use strict";

  const PAIRS = [
    ["Jaký podíl na základním kapitálu českého plátce příjemce drží?", "What percentage of the Czech payer's share capital does the recipient hold?"],
    ["Drží příjemce tento podíl přímo?", "Does the recipient hold this interest directly?"],
    ["Jak dlouho příjemce podíl drží?", "How long has the recipient held the interest?"],
    ["Jaký podíl na hlasovacích právech českého plátce příjemce drží?", "What percentage of the Czech payer's voting rights does the recipient hold?"],
    ["Předvyplněno podle podílu na základním kapitálu.", "Pre-filled based on the share-capital interest."],
    ["Uprav, pokud se podíl na hlasovacích právech liší.", "Change this if the voting-rights percentage differs."],
    ["Je příjemce běžnou obchodní společností (např. GmbH, AG, Ltd. nebo S.A.), nikoli fyzickou osobou, fondem nebo daňově transparentním subjektem?", "Is the recipient an ordinary commercial company (e.g. GmbH, AG, Ltd. or S.A.), rather than an individual, fund or tax-transparent entity?"],
    ["Pokud si nejsi jistý právní formou příjemce, zvol raději „Ne“ nebo údaj ověř v korporátních podkladech.", "If you are unsure about the recipient's legal form, select ‘No’ or verify the fact in the corporate records."],
    ["Podléhá příjemce ve státě své daňové rezidence běžné dani z příjmů právnických osob a není od této daně osvobozen ani v režimu s nulovou sazbou?", "Is the recipient subject to ordinary corporate income tax in its state of tax residence and neither exempt from that tax nor subject to a zero-rate regime?"],
    ["Jde o faktické daňové postavení příjemce, nikoli o posouzení českého § 19.", "This asks about the recipient's factual tax status, not about the legal conclusion under Czech Section 19."],
    ["Ještě dva údaje pro možné osvobození podle § 19 ZDP", "Two additional facts for the potential Section 19 exemption"],
    ["Podíl, přímé držení, dobu držby, skutečné vlastnictví a vazbu ke stálé provozovně už TaxTreat používá z odpovědí výše.", "Ownership, direct holding, holding period, beneficial ownership and permanent-establishment attribution are already taken from the answers above."],
    ["Zobrazit pravidla a výpočet →", "Show rules and calculation →"],
    ["Doplnit údaje a aktualizovat výpočet →", "Complete facts and update calculation →"],
    ["← Zpět k příjemci", "← Back to recipient"],
    ["Použité právní pravidlo", "Applied legal rule"],
    ["Právní podklady", "Legal sources"],
    ["Vnitrostátní osvobození podle § 19 ZDP", "Domestic exemption under Section 19"],
    ["Použije se osvobození podle § 19 ZDP", "Section 19 exemption applies"],
    ["Primární právní titul: § 19 ZDP.", "Primary legal basis: Section 19 of the Czech Income Taxes Act."],
    ["Relevantní česká ustanovení", "Relevant Czech provisions"],
    ["Oficiální zdroj e-Sbírka ↗", "Official e-Sbírka source ↗"],
    ["Česká daň k odvodu", "Czech tax payable"],
    ["Neuplatňuje se", "Does not apply"],
    ["Smluvní ochrana", "Treaty protection"],
    ["Sekundární", "Secondary"],
    ["Daňový režim", "Tax treatment"],
    ["Osvobození podle § 19 ZDP", "Exempt under Section 19"],
  ];

  const CS_TO_EN = new Map(PAIRS);
  const EN_TO_CS = new Map(PAIRS.map(([cs, en]) => [en, cs]));

  function language() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
  }

  function translateDynamic(text, toEnglish) {
    if (toEnglish) {
      let match = text.match(/^Příjemce je daňovým rezidentem státu (.+) pro účely příslušné smlouvy\.$/);
      if (match) return `The recipient is a tax resident of ${match[1]} for the purposes of the applicable treaty.`;
      if (text === "Konkrétní podíl, pohledávka nebo právo, ze kterého plyne tato platba, je součástí činnosti stálé provozovny příjemce v České republice.") {
        return "The specific interest, receivable or right from which this payment arises is attributable to the activities of the recipient's permanent establishment in the Czech Republic.";
      }
    } else {
      let match = text.match(/^The recipient is a tax resident of (.+) for the purposes of the applicable treaty\.$/);
      if (match) return `Příjemce je daňovým rezidentem státu ${match[1]} pro účely příslušné smlouvy.`;
      if (text === "The specific interest, receivable or right from which this payment arises is attributable to the activities of the recipient's permanent establishment in the Czech Republic.") {
        return "Konkrétní podíl, pohledávka nebo právo, ze kterého plyne tato platba, je součástí činnosti stálé provozovny příjemce v České republice.";
      }
    }
    return text;
  }

  function translateTextNode(node, toEnglish) {
    const raw = node.nodeValue;
    const trimmed = raw.trim();
    if (!trimmed) return;
    const map = toEnglish ? CS_TO_EN : EN_TO_CS;
    let replacement = map.get(trimmed);
    if (!replacement) replacement = translateDynamic(trimmed, toEnglish);
    if (replacement !== trimmed) node.nodeValue = raw.replace(trimmed, replacement);
  }

  function refresh() {
    const root = document.querySelector('[data-view="flow"]');
    if (!root) return;
    const toEnglish = language() === "en";
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      if (node.parentElement?.closest("blockquote,pre,code,.legal-excerpt")) return;
      translateTextNode(node, toEnglish);
    });

    root.querySelectorAll("option").forEach((option) => {
      const text = option.textContent.trim();
      const map = toEnglish ? CS_TO_EN : EN_TO_CS;
      if (map.has(text)) option.textContent = map.get(text);
    });
  }

  document.addEventListener("change", (event) => {
    if (event.target?.id === "taxtreat-ui-language") window.setTimeout(refresh, 0);
  }, true);
  document.addEventListener("click", (event) => {
    if (event.target?.closest?.("[data-nav],[data-next-step],[data-flow-step],#taxtreat-language-controls")) window.setTimeout(refresh, 0);
  }, true);

  refresh();
})();
