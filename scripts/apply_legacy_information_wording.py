from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

html = ROOT / 'app/web/index.html'
t = html.read_text(encoding='utf-8')
replacements = [
    ('Výsledek uvádí použitou sazbu, výpočet a podmínky, které je vhodné ověřit s daňovým poradcem.', 'Výstup zobrazuje právní pravidla přiřazená k zadaným údajům a mechanický výpočet; neposkytuje doporučení ani individuální daňové posouzení.'),
    ('TaxTreat je výpočetní nástroj. Výstup není právním ani daňovým poradenstvím ani závazným stanoviskem.\n               Splnění podmínek pro použití sazby a konečný postup ověřte s daňovým poradcem.', 'TaxTreat je informační výpočetní nástroj. Automatizovaně zobrazuje informace z uvedených právních zdrojů a zadaných údajů. Neposkytuje individuální daňové nebo právní poradenství, doporučení ani závazné stanovisko a neurčuje postup uživatele.'),
    ('TaxTreat je porovná s evidovanými\n         pravidly, zobrazí odpovídající sazbu a vypočte srážkovou daň v CZK.', 'TaxTreat je porovná s evidovanými\n         pravidly, zobrazí pravidlo přiřazené k zadaným údajům a provede mechanický výpočet v CZK.'),
    ('<strong>101</strong><span>smluvních partnerů</span>', '<strong>101</strong><span>podporovaných jurisdikcí</span>'),
    ('<span><b>i</b> Výsledek ověřte s daňovým poradcem</span>', '<span><b>i</b> Informační výstup bez individuálního daňového doporučení</span>'),
    ('Pokud některý z těchto předpokladů neplatí nebo si nejste jistí, výsledek ověřte s daňovým poradcem.', 'Pokud některý z těchto předpokladů neplatí, upravte vstupní údaje; TaxTreat podle nich znovu přiřadí relevantní pravidla.'),
    ('Podmínky označené ve výsledku doporučujeme projednat s daňovým poradcem.', 'TaxTreat nezobrazuje doporučení ani individuální daňové posouzení; výstup pouze propojuje zadané údaje s evidovanými pravidly.'),
    ('<h2>Výsledek výpočtu</h2>', '<h2>Informace podle zadaných údajů</h2>'),
    ('Po odeslání údajů se zobrazí sazba, výpočet daně v CZK a podmínky,\n             které je třeba doložit nebo ověřit s daňovým poradcem.', 'Po odeslání údajů se zobrazí přiřazené právní pravidlo, mechanický výpočet v CZK a údaje, které vstupují do přiřazení pravidla.'),
    ('<h3>Podmínky k ověření s daňovým poradcem</h3>', '<h3>Podmínky, které nelze určit z dostupných údajů</h3>'),
    ('<span>Požadované podklady</span>', '<span>Související podklady</span>'),
    ('Přehled podkladů, které mohou být vyžadovány k doložení skutkových okolností a právních podmínek.', 'Přehled podkladů souvisejících se skutkovými údaji a právními podmínkami zobrazenými ve výstupu.'),
    ('<h3>Výsledek a ověření</h3>', '<h3>Pravidla a výpočet</h3>'),
    ('Výstup uvádí sazbu, výpočet v CZK, použité předpoklady a samostatně podmínky k ověření s daňovým poradcem.', 'Výstup uvádí přiřazené právní pravidlo, mechanický výpočet v CZK, použité vstupní údaje a samostatně podmínky, které nelze určit z dostupných údajů.'),
    ('<b>Ověřte s poradcem</b> – použití sazby závisí na podmínce, kterou aplikace nemůže potvrdit z klientského vstupu.', '<b>Chybí údaj pro přiřazení pravidla</b> – z dostupných vstupních údajů nelze konkrétní pravidlo automatizovaně přiřadit.'),
    ('Výstup není právním ani daňovým poradenstvím ani závazným stanoviskem.', 'TaxTreat je informační nástroj; neposkytuje individuální právní ani daňové poradenství, doporučení ani závazné stanovisko.'),
]
for old, new in replacements:
    t = t.replace(old, new)
html.write_text(t, encoding='utf-8')

js = ROOT / 'app/web/app.js'
t = js.read_text(encoding='utf-8')
replacements = [
    ('["Příjem se v České republice nezdaňuje", "Podle použitého smluvního pravidla se příjem zdaňuje pouze ve státě daňové rezidence příjemce. Česká daň k odvodu činí 0 Kč."]', '["Pravidlo přiřazené k zadaným údajům", "Podle použitého smluvního pravidla je v TaxTreat při zadaných údajích přiřazeno pravidlo bez českého zdanění; jde o automatizované informační přiřazení, nikoli individuální daňové posouzení."]'),
    ('["Příjem je v České republice osvobozen", "Podmínky použitého vnitrostátního osvobození byly podle zadaných údajů splněny. Česká daň k odvodu činí 0 Kč."]', '["Pravidlo přiřazené k zadaným údajům", "Podle použitého vnitrostátního pravidla je v TaxTreat při zadaných údajích přiřazeno pravidlo osvobození; jde o automatizované informační přiřazení, nikoli individuální daňové posouzení."]'),
    ('FINAL: ["Výpočet dokončen", "Sazba a daň byly vypočteny podle zadaných údajů a uvedených předpokladů."]', 'FINAL: ["Výpočet dokončen", "TaxTreat podle zadaných údajů přiřadil evidované právní pravidlo a provedl mechanický výpočet."]'),
    ('REVIEW_REQUIRED: ["Je třeba doplnit údaje", "Níže doplňte konkrétní informace nebo ověřte označené podmínky s daňovým poradcem."]', 'REVIEW_REQUIRED: ["Je třeba doplnit údaje", "Doplňte konkrétní vstupní informace, aby TaxTreat mohl automatizovaně přiřadit relevantní pravidlo."]'),
    ('return copies[status] || ["Ověřte s daňovým poradcem", "Použití sazby závisí na podmínce, kterou aplikace nemůže potvrdit ze zadaných údajů."];', 'return copies[status] || ["Chybí údaj pro přiřazení pravidla", "Z dostupných vstupních údajů nelze konkrétní právní pravidlo automatizovaně přiřadit."];'),
    ('}[status] || "OVĚŘIT S PORADCEM";', '}[status] || "CHYBÍ ÚDAJ";'),
    ('tag.textContent = "Ověřit s poradcem";', 'tag.textContent = "Nelze určit z dostupných údajů";'),
    ('const values = documents.length ? documents : ["V této fázi nejsou vyžadovány další podklady."];', 'const values = documents.length ? documents : ["K tomuto informačnímu výstupu nejsou evidovány další související podklady."];'),
    ('submitButton.firstChild.textContent = "Vyhodnocuji… ";', 'submitButton.firstChild.textContent = "Přiřazuji pravidla… ";'),
]
for old, new in replacements:
    t = t.replace(old, new)
# Space-separated Czech number formatting in the legacy result too.
marker = '  function renderCalculation(calculation) {\n'
helper = '''  function formatCzk(value) {\n    const numeric = Number(value);\n    if (!Number.isFinite(numeric)) return "—";\n    return new Intl.NumberFormat("cs-CZ", { maximumFractionDigits: 2 }).format(numeric) + " Kč";\n  }\n\n'''
if helper not in t:
    t = t.replace(marker, helper + marker, 1)
t = t.replace('calculation.gross_amount_czk + " Kč"', 'formatCzk(calculation.gross_amount_czk)')
t = t.replace('calculation.withholding_tax_czk + " Kč"', 'formatCzk(calculation.withholding_tax_czk)')
t = t.replace('calculation.net_amount_czk + " Kč"', 'formatCzk(calculation.net_amount_czk)')
js.write_text(t, encoding='utf-8')

print('Legacy public UI wording aligned')
