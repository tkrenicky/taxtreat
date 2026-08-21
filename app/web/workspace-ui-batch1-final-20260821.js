(() => {
  "use strict";

  const lang = () => document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
  const en = () => lang() === "en";

  function addStyles() {
    if (document.querySelector("#tt-ui-batch1-final")) return;
    const style = document.createElement("style");
    style.id = "tt-ui-batch1-final";
    style.textContent = `
      .app-header nav{display:flex!important;align-items:center!important;gap:9px!important}
      .app-header nav button[data-nav]{min-height:48px!important;padding:0 19px!important;border-radius:9px!important;font-size:15px!important;font-weight:750!important;line-height:1!important}
      .app-header nav button[data-nav].active{background:rgba(255,255,255,.13)!important;box-shadow:inset 0 -2px 0 rgba(255,255,255,.95)!important}
      .app-header .payer-context{width:auto!important;min-width:0!important;max-width:205px!important;min-height:44px!important;padding:5px 9px 6px!important;margin-left:auto!important;border-radius:10px!important;background:#fbfaf5!important;border:1px solid rgba(12,60,53,.13)!important;box-shadow:none!important}
      .app-header .payer-context>span{font-size:9px!important;line-height:1!important;letter-spacing:.055em!important;margin-bottom:2px!important}
      #active-payer-select{width:170px!important;min-width:0!important;max-width:170px!important;height:24px!important;padding:0 20px 0 0!important;border:0!important;box-shadow:none!important;background:transparent!important;font-size:14px!important;font-weight:750!important}
      #taxtreat-language-controls{width:auto!important;min-width:0!important;max-width:none!important;height:auto!important;padding:0!important;margin-left:4px!important;border:0!important;border-radius:0!important;background:transparent!important;box-shadow:none!important}
      #taxtreat-language-controls .tt-lang-mini{display:flex!important;align-items:center!important;gap:7px!important}
      #taxtreat-language-controls .tt-lang-mini button{display:inline-flex!important;align-items:center!important;gap:5px!important;padding:3px!important;border:0!important;background:transparent!important;font-size:12px!important}
      .tt-flag{display:inline-block;width:18px;height:12px;border-radius:2px;overflow:hidden;box-shadow:0 0 0 1px rgba(255,255,255,.28);flex:0 0 auto}.tt-flag svg{display:block;width:100%;height:100%}
      #cz-section19-facts{padding:20px 24px!important}
      #cz-section19-facts>div:first-child{margin-bottom:8px!important}
      #cz-section19-facts>label{display:grid!important;grid-template-columns:minmax(0,1fr) minmax(260px,375px)!important;grid-template-areas:"question control" "help control"!important;column-gap:28px!important;row-gap:6px!important;align-items:center!important;padding:18px 0!important;border-top:1px solid #e1e7e4!important;margin:0!important}
      #cz-section19-facts>label>span{grid-area:question!important;max-width:none!important;font-size:14px!important;line-height:1.35!important;font-weight:700!important}
      #cz-section19-facts>label>select{grid-area:control!important;width:100%!important;max-width:none!important;min-height:50px!important;font-size:15px!important}
      #cz-section19-facts>label>small{grid-area:help!important;margin:0!important;font-size:12.5px!important;line-height:1.35!important}
      .income-specific-facts label,.income-specific-facts .question-row,.income-specific-facts .fact-row{font-size:14px!important;line-height:1.35!important}
      .income-specific-facts select,.income-specific-facts input{font-size:15px!important}
      @media(max-width:900px){.app-header nav button[data-nav]{min-height:43px!important;padding:0 11px!important}#active-payer-select{width:150px!important;max-width:150px!important}#cz-section19-facts>label{grid-template-columns:1fr!important;grid-template-areas:"question" "control" "help"!important}}
    `;
    document.head.append(style);
  }

  const flagCz = `<span class="tt-flag" aria-hidden="true"><svg viewBox="0 0 30 20" xmlns="http://www.w3.org/2000/svg"><rect width="30" height="10" fill="#fff"/><rect y="10" width="30" height="10" fill="#d7141a"/><path d="M0 0L13 10L0 20Z" fill="#11457e"/></svg></span>`;
  const flagEn = `<span class="tt-flag" aria-hidden="true"><svg viewBox="0 0 60 30" xmlns="http://www.w3.org/2000/svg"><rect width="60" height="30" fill="#012169"/><path d="M0 0L60 30M60 0L0 30" stroke="#fff" stroke-width="6"/><path d="M0 0L60 30M60 0L0 30" stroke="#c8102e" stroke-width="3"/><path d="M30 0V30M0 15H60" stroke="#fff" stroke-width="10"/><path d="M30 0V30M0 15H60" stroke="#c8102e" stroke-width="6"/></svg></span>`;

  const pairs = [
    ["Jaký podíl na základním kapitálu českého plátce příjemce drží?","What percentage of the Czech payer's share capital does the recipient hold?"],
    ["Drží příjemce tento podíl přímo?","Does the recipient hold this interest directly?"],
    ["Jak dlouho příjemce podíl drží?","How long has the recipient held the interest?"],
    ["Jaký podíl na hlasovacích právech českého plátce příjemce drží?","What percentage of the Czech payer's voting rights does the recipient hold?"],
    ["Předvyplněno podle podílu na základním kapitálu. Uprav, pokud se podíl na hlasovacích právech liší.","Pre-filled based on the share-capital interest. Change it if the voting-rights percentage differs."],
    ["Je příjemce běžnou obchodní společností (např. GmbH, AG, Ltd. nebo S.A.), nikoli fyzickou osobou, fondem nebo daňově transparentním subjektem?","Is the recipient an ordinary commercial company (e.g. GmbH, AG, Ltd. or S.A.), rather than an individual, fund or tax-transparent entity?"],
    ["Pokud si nejsi jistý právní formou příjemce, zvol raději „Ne“ nebo údaj ověř v korporátních podkladech.","If you are unsure about the recipient's legal form, verify it in the corporate documents before relying on the exemption."],
    ["Podléhá příjemce ve státě své daňové rezidence běžné dani z příjmů právnických osob a není od této daně osvobozen ani v režimu s nulovou sazbou?","Is the recipient subject to ordinary corporate income tax in its state of tax residence and neither exempt from that tax nor subject to a zero-rate regime?"],
    ["Jde o faktické daňové postavení příjemce, nikoli o posouzení českého § 19.","This asks about the recipient's actual tax status, not about the application of Czech Section 19."],
    ["Ještě dva údaje pro možné osvobození podle § 19 ZDP","Two additional facts for the potential Section 19 exemption"],
    ["Podíl, přímé držení, dobu držby, skutečné vlastnictví a vazbu ke stálé provozovně už TaxTreat používá z odpovědí výše.","Ownership, direct holding, holding period, beneficial ownership and permanent-establishment attribution are already taken from the answers above."],
    ["Zobrazit pravidla a výpočet →","Show rules and calculation →"],
    ["← Zpět k příjemci","← Back to recipient"],
    ["Použité právní pravidlo","Applied legal rule"],
    ["Právní podklady","Legal sources"],
    ["Výsledek","Result"]
  ];

  function translateKnown(root=document.body){
    const map = new Map(en()?pairs:pairs.map(([cs,enText])=>[enText,cs]));
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);const nodes=[];while(walker.nextNode())nodes.push(walker.currentNode);
    nodes.forEach(node=>{const raw=node.nodeValue;const key=raw.trim();const out=map.get(key);if(out)node.nodeValue=raw.replace(key,out)});
  }

  function polishHeader(){
    const mini=document.querySelector("#taxtreat-language-controls .tt-lang-mini");
    mini?.querySelectorAll("button").forEach(button=>{const code=button.dataset.lang||(/EN/.test(button.textContent)?"en":"cs");button.innerHTML=`${code==="en"?flagEn:flagCz}<span>${code==="en"?"EN":"CZ"}</span>`});
    const label=document.querySelector(".app-header .payer-context>span");if(label)label.textContent=en()?"ACTIVE PAYER":"AKTIVNÍ PLÁTCE";
  }

  function polishSection19Result(){
    const box=document.querySelector("#cz-section19-result.tt-section19-applicable");if(!box)return;
    box.querySelectorAll("p").forEach(p=>{
      p.innerHTML=p.innerHTML
        .replace(/Česká srážková daň je proto 0\s*%[^.;]*/gi,"Česká srážková daň se proto neuplatní z důvodu osvobození podle § 19 ZDP")
        .replace(/Czech withholding tax is therefore 0\s*%[^.;]*/gi,"Czech withholding tax therefore does not apply because the dividend is exempt under Section 19")
        .replace(/nulovou českou srážkovou daň/gi,"osvobození od české srážkové daně")
        .replace(/0% Czech withholding tax result/gi,"Czech domestic exemption");
    });
    const used=[...document.querySelectorAll(".flow-step[data-step='4'] article,.flow-step[data-step='4'] .card")].find(el=>/Použité právní pravidlo|Applied legal rule/i.test(el.textContent));
    if(used&&/čl\.\s*10|Article\s*10|smlouv|treaty/i.test(used.textContent)){
      used.innerHTML=en()?'<h2>Applied legal rule</h2><p><strong>Section 19 of the Czech Income Taxes Act – domestic dividend exemption.</strong> The treaty is secondary protection only.</p>':'<h2>Použité právní pravidlo</h2><p><strong>§ 19 ZDP – vnitrostátní osvobození podílu na zisku.</strong> SZDZ představuje pouze sekundární ochranu.</p>';
    }
  }

  function refresh(){addStyles();polishHeader();translateKnown();polishSection19Result()}
  document.addEventListener("change",e=>{if(e.target?.id==="taxtreat-ui-language")setTimeout(refresh,0)},true);
  document.addEventListener("click",e=>{if(e.target?.closest("[data-nav],[data-next-step],[data-flow-step],[data-start-flow]"))setTimeout(refresh,0)},true);
  refresh();
})();