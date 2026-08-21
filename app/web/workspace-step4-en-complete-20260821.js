(() => {
  "use strict";

  const AT_EN_TREATY_URL = "https://www.bmf.gv.at/dam/jcr:8100aa41-e177-4705-8b4b-5f1178ffc0b1/MLI%20Tschechien%20englisch.pdf";

  function isEn() {
    return (document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs") === "en";
  }

  function step4() {
    return document.querySelector('.flow-step[data-step="4"]');
  }

  function exact(root, from, to) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      if (node.nodeValue.trim() === from) node.nodeValue = node.nodeValue.replace(from, to);
    });
  }

  function regex(root, pattern, replacement) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      if (pattern.test(node.nodeValue)) node.nodeValue = node.nodeValue.replace(pattern, replacement);
      pattern.lastIndex = 0;
    });
  }

  function translateProgress() {
    const flow = document.querySelector('[data-view="flow"]');
    if (!flow) return;
    const labels = ["Payer", "Recipient", "Payment", "Result"];
    flow.querySelectorAll('[data-flow-step] span').forEach((el, i) => {
      if (labels[i]) el.textContent = labels[i];
    });
    const back = flow.querySelector(':scope > button.back');
    if (back) back.textContent = "← Exit calculation";
  }

  function translateStaticStep4(root) {
    const pairs = [
      ["KROK 4 ZE 4", "STEP 4 OF 4"],
      ["Výsledek", "Result"],
      ["ČEKÁ NA VÝPOČET", "WAITING FOR CALCULATION"],
      ["VÝPOČET DOKONČEN", "CALCULATION COMPLETE"],
      ["Srážková daň v CZK", "Withholding tax in CZK"],
      ["Použité právní pravidlo", "Applied legal rule"],
      ["Souhrn platby", "Payment summary"],
      ["Hrubá částka", "Gross amount"],
      ["Srážková daň", "Withholding tax"],
      ["Čistá částka", "Net amount"],
      ["Podmínky použitého pravidla", "Conditions of the applied rule"],
      ["Všechny údaje potřebné pro výpočet jsou zadány", "All facts required for the calculation are entered"],
      ["Výsledek vychází z uvedených údajů a zobrazeného právního základu.", "The result is based on the entered facts and the legal basis shown."],
      ["DAŇOVÝ KALENDÁŘ", "TAX CALENDAR"],
      ["Rozhodné datum a navazující lhůty", "Relevant date and deadlines"],
      ["Rozhodné datum zadané pro výpočet", "Relevant date entered for the calculation"],
      ["Odvod srážkové daně", "Remittance of withholding tax"],
      ["Oznámení příjmu plynoucího do zahraničí", "Notification of income paid abroad"],
      ["Lhůty se zobrazí po dokončení výpočtu.", "Deadlines will be shown after the calculation is completed."],
      ["Právní podklady", "Legal sources"],
      ["Po výpočtu se zobrazí smluvní článek a evidované zdroje.", "The applicable treaty article and recorded legal sources will be shown after the calculation."],
      ["← Upravit platbu", "← Edit payment"],
      ["Tisk / PDF reportu", "Print / PDF report"],
      ["Sekundární smluvní ochrana", "Secondary treaty protection"],
      ["Výchozí vnitrostátní pravidlo", "Default domestic rule"],
      ["Použité smluvní pravidlo", "Applied treaty rule"],
      ["Související právní pravidlo", "Related legal rule"],
      ["Otevřít zdroj ↗", "Open source ↗"],
      ["Znění použitého ustanovení", "Text of the applied provision"],
    ];
    pairs.forEach(([cs, en]) => exact(root, cs, en));

    regex(root, /§ 38d a § 38da zákona č\. 586\/1992 Sb\., o daních z příjmů/g, "Sections 38d and 38da of Act No. 586/1992 Coll., on Income Taxes");
    regex(root, /Based on článku\s*(\d+)\s*smlouvy o zamezení dvojího zdanění,?/gi, "Based on Article $1 of the applicable double tax treaty,");
    regex(root, /Podle článku\s*(\d+)\s*smlouvy o zamezení dvojího zdanění se při zadaných údajích sazba srážkové daně uplatní ve výši\s*([^\.]+)\./gi, "Under Article $1 of the applicable double tax treaty, the withholding tax rate for the entered facts is $2.");
    regex(root, /U dividend může povinnost srazit daň podle § 38d odst\. 2 zákona č\. 586\/1992 Sb\., o daních z příjmů vzniknout i před zadaným datem\. Pro úplné určení je nutné zohlednit také schválení účetní závěrky a rozhodnutí o rozdělení zisku\./g, "For dividends, the obligation to withhold tax under Section 38d(2) of Act No. 586/1992 Coll., on Income Taxes may arise before the date entered above. A complete determination also requires consideration of the approval of the financial statements and the decision on profit distribution.");
  }

  function simplifySection19English(root) {
    const box = root.querySelector("#cz-section19-result");
    if (!box) return;
    const text = box.textContent || "";
    const failedItems = [...box.querySelectorAll("li")].map((li) => li.textContent.trim()).filter(Boolean);

    if (/Section 19 does not apply|§\s*19 ZDP se neuplatní/i.test(text)) {
      const reasons = failedItems.length ? failedItems : ["At least one statutory condition is not met."];
      box.className = "card tt-section19-not-applicable tt-s19-summary-only";
      box.innerHTML = `<div class="tt-legal-status">Section 19 of the Czech Income Taxes Act — exemption not available</div><p><strong>Reason:</strong></p><ul>${reasons.map((r) => `<li>${r}</li>`).join("")}</ul>`;
      return;
    }

    if (/Section 19 applies|§\s*19 ZDP se použije/i.test(text)) {
      box.className = "card tt-section19-applicable tt-s19-summary-only";
      box.innerHTML = `<div class="tt-legal-status">Section 19 of the Czech Income Taxes Act — exemption applies</div><p>Czech withholding tax does not apply because the statutory exemption conditions are satisfied.</p>`;
      return;
    }

    if (/cannot be confirmed|unresolved|nelze potvrdit|zatím nelze uzavřít/i.test(text)) {
      const reasons = failedItems.length ? failedItems : ["A required factual condition has not been verified."];
      box.className = "card tt-s19-summary-only";
      box.innerHTML = `<div class="tt-legal-status">Section 19 of the Czech Income Taxes Act — exemption cannot be confirmed</div><p><strong>Missing verification:</strong></p><ul>${reasons.map((r) => `<li>${r}</li>`).join("")}</ul>`;
    }
  }

  function translateTreatyCards(root) {
    const citations = root.querySelector("#workspace-citations");
    if (!citations) return;

    citations.querySelectorAll(".citation-card").forEach((card) => {
      const text = card.textContent || "";
      const link = card.querySelector("a[href]");

      if (/Smlouva o zamezení dvojího zdanění|Článek\s*10|DIVIDENDY/i.test(text)) {
        const sourceHref = link?.href || AT_EN_TREATY_URL;
        card.innerHTML = `
          <strong>Applied treaty rule</strong>
          <p><b>Czech Republic–Austria double tax treaty · Article 10</b></p>
          <small>The treaty rule is shown in English for the English-language interface.</small>
          <div class="tt-en-treaty-excerpt">
            <b>Article 10 — Dividends</b>
            <p>Dividends paid by a company resident in one Contracting State to a resident of the other Contracting State may be taxed in that other State.</p>
            <p>Such dividends may also be taxed in the State of which the paying company is a resident. Where the recipient is the beneficial owner, the source-state tax is limited by Article 10, including the applicable participation threshold.</p>
          </div>
          <a href="${AT_EN_TREATY_URL}" target="_blank" rel="noopener">Official English synthesised treaty text ↗</a>
          ${sourceHref && sourceHref !== AT_EN_TREATY_URL ? `<a href="${sourceHref}" target="_blank" rel="noopener">Recorded official source ↗</a>` : ""}`;
        return;
      }

      exact(card, "Výchozí vnitrostátní pravidlo", "Default domestic rule");
      exact(card, "Otevřít zdroj ↗", "Open source ↗");
      regex(card, /Zákon č\. 586\/1992 Sb\., o daních z příjmů/g, "Act No. 586/1992 Coll., on Income Taxes");
      regex(card, /Výchozí vnitrostátní sazba činí\s*([^\.]+)\./g, "The default domestic rate is $1.");
    });
  }

  function translateResultReason(root) {
    const reason = root.querySelector("#workspace-reason");
    if (!reason) return;
    const text = reason.textContent || "";
    if (/článku|smlouvy o zamezení dvojího zdanění/i.test(text)) {
      const article = text.match(/(?:článku|Article)\s*(\d+)/i)?.[1] || "10";
      const rate = text.match(/(\d+(?:[.,]\d+)?\s*%)/)?.[1];
      reason.textContent = rate
        ? `Based on Article ${article} of the applicable double tax treaty, the withholding tax rate for the entered facts is ${rate}.`
        : `The result is based on Article ${article} of the applicable double tax treaty.`;
    }
  }

  function refresh() {
    if (!isEn()) return;
    translateProgress();
    const root = step4();
    if (!root) return;
    translateStaticStep4(root);
    simplifySection19English(root);
    translateResultReason(root);
    translateTreatyCards(root);
  }

  document.addEventListener("change", (event) => {
    if (event.target?.id === "taxtreat-ui-language") {
      window.setTimeout(refresh, 0);
      window.setTimeout(refresh, 120);
    }
  }, true);

  document.addEventListener("click", (event) => {
    if (event.target?.closest("[data-nav],[data-next-step],[data-flow-step],[data-start-flow],#taxtreat-language-controls")) {
      window.setTimeout(refresh, 0);
      window.setTimeout(refresh, 120);
    }
  }, true);

  const previousFetch = window.fetch.bind(window);
  window.fetch = async function taxTreatStep4EnglishFetch(resource, options = {}) {
    const response = await previousFetch(resource, options);
    const url = typeof resource === "string" ? resource : resource?.url || "";
    if (url.endsWith("/analysis/intake")) {
      window.setTimeout(refresh, 0);
      window.setTimeout(refresh, 120);
    }
    return response;
  };

  refresh();
})();
