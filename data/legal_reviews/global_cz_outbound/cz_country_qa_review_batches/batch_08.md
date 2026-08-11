# CZ country legal-QA review batch 08

> Machine-prepared candidate evidence only. No country or scope in this file has been human reviewed, approved, verified, or released.

## PA — Panama (STANDARD)

Base treaty: **91/2013 Sb.m.s.** (`SRC-82F15B2AF261EB4D`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 10.0% | 10.0%: beneficial_owner == true |
| interest | 11 | 0.0%, 5.0%, 10.0% | 5.0%: recipient_entity_type == bank, beneficial_owner == true; 10.0%: fallback_case == all_other_cases, beneficial_owner == true; 0.0%: article_11_3_exemption == credit_sale_or_government_central_bank_government_owned_or_controlled_financial_institution_or_qualifying_government_guaranteed_financing_minimum_4_years, beneficial_owner == true |
| royalty | 12 | 10.0% | 10.0%: beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-PA-MLI-WHT-PPT`; candidate WHT date `2025-01-01`. Article 8 adds no overlay.

Language: authentic `['Czech', 'Spanish', 'English']`; prevailing `english_prevails_all_text_divergences`; evidence `current_official_pdf_signature_clause_candidate`; signature clause `Dano v Panamé dne 4. éervence 2012 ve dvou pivodnich vyhotovenich, v Ceském, Spanélském a anglickém jazyce, pritemzZ vsechny texty jsou autentické. V pripadé jakéhokoliv rozdilu bude rozhodujicim anglicky text.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-82F15B2AF261EB4D](https://e-sbirka.gov.cz/sm/2013/91/0000-00-00).

Candidate excerpts:

- dividend Article 10: DIVIDENDY 1. Dividendy vyplácené společností, která je rezidentem jednoho smluvního státu, rezidentu druhého smluvního státu, mohou být zdaněny v tomto druhém státě. 2. Tyto dividendy však mohou být rovněž zdaněny ve smluvním státě, jehož je společnost, která je vyplácí, rezidentem, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník dividend je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 10 procent hrubé částky dividend. Příslušné úřady smluvních států upraví vzájemnou dohodou způsob aplikace tohoto omezení. Tento odstavec se nedotýká zdanění zisků společnosti, z nichž jsou dividendy vypláceny. 3. Výraz „dividendy“ použitý v tomto článku označuje příjmy z akcií nebo jiných práv, s výjimkou pohledávek, s podílem na zisku, jakož i jiné příjmy, které jsou podrobeny stejnému daňovému režimu jako příjmy zakcií podle právních předpisů statu, jehož  …
- interest Article 11: ÚROKY 1. Úroky mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu mohou být zdaněny v tomto druhém státě. 2. Tyto úroky však mohou být rovněž zdaněny ve smluvním státě, v němž mají zdroj, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník úroků je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne: a) 5 procent hrubé částky úroků, jestliže skutečným vlastníkem je banka, která je rezidentem druhého smluvního státu; a b) 10 procent hrubé částky úroků ve všech ostatních případech. 3. Úroky mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu, který je jejich skutečným vlastníkem, podléhají bez ohledu na ustanovení odstavce 2 zdanění jen v tomto druhém státě, jestliže jsou tyto úroky vypláceny: a) v souvislosti s prodejem jakéhokoliv zboží nebo zařízení na úvěr; b) vládě druhého smluvního stá …
- royalty Article 12: LICENČNÍ POPLATKY 1. Licenční poplatky mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu mohou být zdaněny v tomto druhém státě., 2. Tyto licenční poplatky však mohou být rovněž zdaněny ve smluvním státě, v němž mají zdroj, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník licenčních poplatků je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 10 procent hrubé částky licenčních poplatků. Příslušné úřady smluvních států upraví vzájemnou dohodou způsob aplikace tohoto omezení. 3. Výraz „licenční poplatky“ použitý v tomto článku označuje platby jakéhokoliv druhu obdržené jako náhrada za užití nebo za právo na užití jakéhokoliv autorského práva k dílu literárnímu, uměleckému nebo vědeckému, včetně kinematografických filmů, a filmů nebo pásek pro televizní nebo rozhlasové vysílání, jakéhokoliv patentu, ochranné známky, …

Audit package hash: `c189607db309ca777db82320f63f1459ef59c64d69c071324b579fcb81be1e22`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## PH — Filipíny (STANDARD)

Base treaty: **132/2003 Sb.m.s.** (`SRC-1E2D0264FEB4040D`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 10.0%, 15.0% | 10.0%: recipient_entity_type == company, direct_ownership >= 10%, beneficial_owner == true; 15.0%: fallback_case == all_other_cases, beneficial_owner == true |
| interest | 11 | 0.0%, 10.0% | 10.0%: beneficial_owner == true; 0.0%: recipient_entity_type == government_subnational_local_authority_central_bank_wholly_government_owned_financial_institution_or_qualifying_government_guaranteed_financing, beneficial_owner == true |
| royalty | 12 | 10.0%, 15.0% | 10.0%: beneficial_owner == true; 15.0%: beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `not_listed`; modification `None`; candidate WHT date `None`. Article 8 adds no overlay.

Language: authentic `None`; prevailing `None`; evidence `hash_bound_repository_signature_clause_candidate`; signature clause `Dáno v Manile dne 13. listopadu roku 2000 ve dvou puvodnõch vyhotovenõch v anglickém jazyce.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-1E2D0264FEB4040D](https://e-sbirka.gov.cz/sm/2003/132/0000-00-00).

Candidate excerpts:

- dividend Article 10: DIVIDENDY 1. Dividendy vyplácené spolecnostõ, která je rezidentem jednoho smluvnõho státu, rezidentu druhého smluvnõho státu, mohou být zdaneny v tomto druhém státe. 2. Tyto dividendy vsak mohou být rovnez zdaneny ve smluvnõm státe, jehoz je spolecnost, která je vyplácõ, rezidentem, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk dividend je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne: a) 10 procent hrubé cástky dividend, jestlize skutecným vlastnõkem je spolecnost, která prõmo vlastnõ nejméne 10 procent kapitálu spolecnosti vyplácejõcõ dividendy; b) 15 procent hrubé cástky dividend ve vsech ostatnõch prõpadech. Přõslusné úrady smluvnõch státu upravõ vzájemnou dohodou zpusob aplikace techto omezenõ. Tento odstavec se nedotýká zdanenõ zisku spolecnosti, z nichz jsou dividendy vypláceny. 3. Výraz 1dividendya pouzitý v tomto clánku oznacuje p …
- interest Article 11: UROKY 1. Uroky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto úroky vsak mohou být rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk úroku je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne 10 procent hrubé cástky úroku. 3. Bez ohledu na ustanovenõ odstavce 2 budou úroky osvobozené od zdanenõ ve smluvnõm státe, v nemz majõ zdroj, pokud jsou pobõrané a skutecne vlastnené: a) vládou druhého smluvnõho státu, vcetne jakéhokoliv nizsõho správnõho útvaru nebo mõstnõho úradu tohoto státu, centrálnõ bankou nebo jakoukoli financnõ institucõ, která je zcela vlastnena touto vládou; nebo b) rezidentem druhého smluvnõho státu v souvislosti s pujckou nebo úverem zarucenou vládou tohoto druhého státu. Přõslusné úrady smluvnõc …
- royalty Article 12: LICENČNI POPLATKY 1. Licencnõ poplatky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto licencnõ poplatky vsak mohou být rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk licencnõch poplatku je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne: a) 10 procent hrubé cástky licencnõch poplatku plynoucõch z uzitõ nebo z práva na uzitõ jakéhokoliv autorského práva k dõlu literárnõmu, umeleckému nebo vedeckému, jiného nez, které je uvedeno v põsmenu b), jaké- hokoliv patentu, ochranné známky, návrhu nebo modelu, plánu, tajného vzorce nebo výrobnõho postupu nebo z uzitõ nebo z práva na uzitõ prumyslového, obchodnõho nebo vedeckého zarõzenõ nebo za informace, které se vztahujõ na zkusenosti nabyté v oblasti prumyslové, obc …

Audit package hash: `1a385625bd2000bef394e680dedbc90075d133fcbd66b7c3541821df267ad3ce`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## PK — Pákistán (STANDARD)

Base treaty: **58/2015 Sb.m.s.** (`SRC-017BDD519C89EE7E`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 5.0%, 15.0% | 5.0%: minimum_ownership >= 25, beneficial_owner == true; 15.0%: beneficial_owner == true |
| interest | 11 | 0.0%, 10.0% | 10.0%: beneficial_owner == true; 0.0%: article_11_3_exemption == government_subnational_local_authority_central_bank_government_owned_or_controlled_financial_institution_or_qualifying_guaranteed_or_insured_financing, beneficial_owner == true |
| royalty | 12 | 10.0% | 10.0%: beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-PK-MLI-WHT-PPT`; candidate WHT date `2022-01-01`. Article 8 adds no overlay.

Language: authentic `['English']`; prevailing `sole_english`; evidence `current_official_pdf_signature_clause_candidate`; signature clause `DONE in duplicate at Prague this 2" day of May 2014 in the English language.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-017BDD519C89EE7E](https://e-sbirka.gov.cz/sm/2015/58/0000-00-00).

Candidate excerpts:

- dividend Article 10: DIVIDENDY 1. Dividendy vyplácené společností, která je rezidentem jednoho smluvního státu, rezidentu druhého smluvního státu, mohou být zdaněny v tomto druhém státě. 2. Tyto dividendy však mohou být rovněž zdaněny ve smluvním státě, jehož je společnost, která je vyplácí, rezidentem, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník dividend je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne: a) 5 procent hrubé částky dividend, jestliže skutečným vlastníkem je společnost (jiná než osobní společnost), která přímo drží alespoň 25 procent kapitálu společnosti, která dividendy vyplácí; b) 15 procent hrubé částky dividend ve všech ostatních případech. Tento odstavec se nedotýká zdanění zisků společnosti, z nichž jsou dividendy vypláceny. 3. Výraz „dividendy“ použitý v tomto článku označuje příjmy z akcií, požitkových akcií nebo požitkových práv, kuksů …
- interest Article 11: ÚROKY 1. Úroky mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu mohou být zdaněny v tomto druhém státě. 2. Tyto úroky však mohou být rovněž zdaněny ve smluvním státě, v němž mají zdroj, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník úroků je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 10 procent hrubé částky úroků. 3. Bez ohledu na ustanovení odstavce 2 jsou úroky mající zdroj v jednom smluvním státě osvobozeny od zdanění v tomto státě, pokud jsou skutečně vlastněny: a) vládou, nižším správním útvarem nebo místním úřadem druhého smluvního státu; nebo b) centrální bankou tohoto druhého státu; nebo c) jakoukoli finanční institucí, která je vlastněna nebo ovládána vládou tohoto druhého státu; nebo d) rezidentem druhého smluvního státu, a to v souvislosti s půjčkou nebo úvěrem, která je zaručena nebo pojištěn …
- royalty Article 12: LICENČNÍ POPLATKY A POPLATKY ZA SLUŽBY 1. Licenční poplatky a poplatky za služby mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu mohou být zdaněny v tomto druhém státě. 2. Tyto licenční poplatky a poplatky za služby však mohou být rovněž zdaněny ve smluvním státě, v němž mají zdroj, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník licenčních poplatků nebo poplatků za služby je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 10 procent hrubé částky licenčních poplatků nebo poplatků za služby. 3. a) Výraz „licenční poplatky“ použitý v tomto článku označuje platby jakéhokoliv druhu obdržené jako náhrada za užití nebo za právo na užití jakéhokoliv autorského práva k dílu literárnímu, uměleckému nebo vědeckému, včetně kinematografických filmů, a filmů nebo pásek pro televizní nebo rozhlasové vysílání, jakéhokoliv p …

Audit package hash: `5d361dc54d8dcfae38b172b20aa54b7ff311df243a06831b1f213070cea6a481`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## PL — Polsko (STANDARD)

Base treaty: **102/2012 Sb.m.s.** (`SRC-6449FD410AC2BC33`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 5.0% | 5.0%: beneficial_owner == true |
| interest | 11 | 0.0%, 5.0% | 5.0%: beneficial_owner == true; 0.0%: article_11_3_exemption == bank_loan_or_government_central_bank_government_owned_or_controlled_financial_institution_or_qualifying_government_guaranteed_financing, beneficial_owner == true |
| royalty | 12 | 10.0% | 10.0%: beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-PL-MLI-WHT-PPT`; candidate WHT date `2021-01-01`. Article 8 adds no overlay.

Language: authentic `['Czech', 'Polish', 'English']`; prevailing `english_prevails_all_text_divergences`; evidence `current_official_pdf_signature_clause_candidate`; signature clause `Dano ve VarSavé dne 13. zA¥i 2011 ve dvou ptivodnich vyhotovenich, v éeském, polském a anglickém jazyce, priéemz vSechny texty jsou autentické. V pripadé jakéhokoliv rozdilu bude rozhodujicim anglicky text.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-6449FD410AC2BC33](https://e-sbirka.gov.cz/sm/2012/102/0000-00-00).

Candidate excerpts:

- dividend Article 10: DIVIDENDY 1. Dividendy vyplácené společností, která je rezidentem jednoho smluvního státu, rezidentu druhého smluvního státu, mohou být zdaněny v tomto druhém státě. 2. Tyto dividendy však mohou být rovněž zdaněny ve smluvním státě, jehož je společnost, která je vyplácí, rezidentem, a to podle právních předpisů tohoto statu, avšak jestliže skutečný vlastník dividend je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 5 procent hrubé částky dividend. Tento odstavec se nedotýká zdanění zisků společnosti, z nichž jsou dividendy vypláceny. 3. Výraz „dividendy“ použitý v tomto článku označuje příjmy z akcií nebo jiných práv, s výjimkou pohledávek, s podílem na zisku, jakož i jiné příjmy, které jsou podrobeny stejnému daňovému režimu jako příjmy z akcií podle právních předpisů státu, jehož je společnost, která provádí platbu, rezidentem. 4. Ustanovení odstavců 1 a 2 se nepoužij …
- interest Article 11: ÚROKY 1. Úroky mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu mohou být zdaněny v tomto druhém státě. 2. Tyto úroky však mohou být rovněž zdaněny ve smluvním státě, v němž mají zdroj, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník úroků je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 5 procent hrubé částky úroků. 3. Úroky mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu, který je jejich skutečným vlastníkem, podléhají bez ohledu na ustanovení odstavce 2 zdanění jen v tomto druhém státě, jestliže jsou tyto úroky vypláceny: a) z jakékoliv půjčky nebo úvěru jakéhokoliv druhu, kterou nebo který poskytla banka; b) vládě druhého smluvního státu, včetně jakéhokoliv nižšího správního útvaru nebo místního úřadu tohoto státu, centrální bance nebo jakékoli finanční instituci, která …
- royalty Article 12: LICENČNÍ POPLATKY 1. Licenční poplatky mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu mohou být zdaněny v tomto druhém státě. 2. Tyto licenční poplatky však mohou být rovněž zdaněny ve smluvním státě, v němž mají zdroj, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník licenčních poplatků je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 10 procent hrubé částky licenčních poplatků. 3. Výraz „licenční poplatky“ použitý v tomto článku označuje platby jakéhokoliv druhu obdržené jako náhrada za užití nebo za právo na užití jakéhokoliv autorského práva, filmů nebo pásek užívaných pro rozhlasové nebo televizní vysílání, patentu, ochranné známky, návrhu nebo modelu, plánu, tajného vzorce nebo postupu nebo jakéhokoliv průmyslového, obchodního nebo vědeckého zařízení nebo za informace, které se vztahují na zkušenosti  …

Audit package hash: `25458a66fc68e66aed3b2366be04336b4e62a4410195145a0383022ac6b747b1`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## PT — Portugalsko (STANDARD)

Base treaty: **275/1997 Sb.** (`SRC-12128F81E027CFFF`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 10.0%, 15.0% | 10.0%: recipient_entity_type == company, direct_ownership >= 25%, holding_period_years >= 2, beneficial_owner == true; 15.0%: fallback_case == all_other_cases, beneficial_owner == true |
| interest | 11 | 0.0%, 10.0% | 0.0%: article_11_3_exemption == source_state_government_or_local_authority_debtor_or_other_state_government_local_authority_or_supported_financing_under_intergovernmental_agreement_or_named_public_financial_institution_loan_or_credit; 10.0%: fallback_case == all_other_cases, beneficial_owner == true |
| royalty | 12 | 10.0% | 10.0%: beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-PT-MLI-WHT-PPT`; candidate WHT date `2021-01-01`. Article 8 adds no overlay.

Language: authentic `None`; prevailing `None`; evidence `hash_bound_repository_signature_clause_candidate`; signature clause `Dáno v Lisabonu dne 24. kvetna 1994 ve dvou
vyhotovenõch, kazdé v jazyce ceském, portugalském
a anglickém, pricemz vsechny texty jsou autentické.
V prõpade rozdõlnosti ve výkladu je rozhodujõcõ znenõ
v jazyce anglickém.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-12128F81E027CFFF](https://e-sbirka.gov.cz/sb/1997/275/0000-00-00).

Candidate excerpts:

- dividend Article 10: Dividendy 1. Dividendy vyplácené spolecnostõ, která je rezi- dentem v jednom smluvnõm státe, rezidentovi druhého smluvnõho státu, mohou být zdaneny v tomto druhém státe. 2. Tyto dividendy vsak mohou být rovnez zda- neny ve smluvnõm státe, v nemz je spolecnost, která je vyplácõ, rezidentem, a to podle právnõch predpisu tohoto státu, avsak jestlize prõjemce je skutecným vlastnõkem dividend, dan takto stanovená nepresáhne 15 % hrubé cástky dividend. Tento odstavec se nedotýká zdanenõ zisku spolecnosti, ze kterých jsou divideny vypláceny. 3. Bez ohledu na ustanovenõ odstavce 2, jestlize skutecným vlastnõkem dividend je spolecnost, která po nepretrzité obdobõ dvou let predcházejõcõch výplate dividend vlastnõ prõmo nejméne 25 % základnõho jmenõ spolecnosti dividendy vyplácejõcõ, dan takto stanovená nepresáhne, pokud jde o dividendy vyplácené po 31. prosinci 1996, 10 % hrubé cástky dividend. 4. …
- interest Article 11: U roky 1. U roky majõcõ zdroj v jednom smluvnõm státe, které pobõrá rezident druhého smluvnõho státu, mohou být zdaneny v tomto druhém státe. 2. Tyto úroky vsak mohou být rovnez zdaneny ve smluvnõm státe, ve kterém je jejich zdroj, a to podle právnõch predpisu tohoto státu, avsak je-li prõjemce úroku jejich skutecným vlastnõkem, dan takto vyme- rená nepresáhne 10 % hrubé cástky úroku . 3. Bez ohledu na ustanovenõ odstavce 2 úroky, které majõ zdroj v jednom smluvnõm státe, budou vy- jmuty ze zdanenõ v tomto státe: a) pokud dluznõkem tohoto úroku je vláda tohoto státu nebo jeho mõstnõ úrad; nebo b) pokud je úrok placen vláde druhého smluvnõho státu nebo jeho mõstnõmu úradu nebo jiné instituci (vcetne financnõ instituce) ve spojenõ s jimi pod- porovaným financovánõm na základe dohody mezi vládami smluvnõch státu ; nebo c) pro pu jcky nebo úvery poskytnuté: (i) v prõpade České republiky ± Č  …
- royalty Article 12: Licencnõ poplatky 1. Licencnõ poplatky majõcõ zdroj v jednom smluvnõm státe vyplácené rezidentu druhého smluv- nõho státu mohou být zdaneny v tomto druhém státe. 2. Takové licencnõ poplatky vsak mohou být také zdaneny ve smluvnõm státe, ve kterém je jejich zdroj, a v souladu s právnõmi predpisy tohoto státu, avsak je-li prõjemce skutecným vlastnõkem licencnõch po- platku , cástka dane takto stanovená nepresáhne 10 % hrubé cástky licencnõch poplatku . 3. Výraz 1licencnõ poplatkya pouzitý v tomto clánku oznacuje platby jakéhokoliv druhu obdrzené jako náhrada za uzitõ nebo za poskytnutõ práva na uzitõ autorského práva k dõlu literárnõmu, umeleckému nebo vedeckému vcetne kinematografických filmu a filmu nebo nahrávek pro televiznõ nebo rozhlasové vysõlánõ, jakéhokoliv patentu, ochranné známky, návrhu nebo modelu, plánu, tajného vzorce nebo výrobnõho po- stupu nebo jakéhokoliv pru myslového,  …

Audit package hash: `86e03d81fa93e4431facc262bb2623414c0004f1ae8e8abfd17d4b151a19dbe4`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## QA — Katar (STANDARD)

Base treaty: **45/2022 Sb.m.s.** (`SRC-A4B3C2125350DA5C`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 0.0%, 5.0%, 10.0% | 0.0%: beneficial_owner == other_state_government_subnational_local_authority_central_bank_other_public_law_body_or_entity_directly_or_indirectly_wholly_owned_by_such_public_body; 5.0%: recipient_entity_type == company, direct_ownership >= 10%, beneficial_owner == true; 10.0%: fallback_case == all_other_cases, beneficial_owner == true |
| interest | 11 | 0.0% | 0.0%: recipient_is_treaty_resident == true, beneficial_owner == true, claim_not_effectively_connected_to_czech_pe == true |
| royalty | 12 | 10.0% | 10.0%: beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `not_listed`; modification `None`; candidate WHT date `None`. Article 8 adds no overlay.

Language: authentic `['cs', 'ar', 'en']`; prevailing `english`; evidence `existing_repository_language_record`; signature clause `None`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-A4B3C2125350DA5C](https://e-sbirka.gov.cz/sm/2022/45/0000-00-00).

Candidate excerpts:

- dividend Article 10: 1. Dividendy vyplácené společností, která je rezidentem jednoho smluvního státu, rezidentu druhého smluvního státu, mohou být zdaněny v tomto druhém státě. 2. Tyto dividendy však mohou být rovněž zdaněny ve smluvním státě, jehož je společnost, která je vyplácí, rezidentem, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník dividend je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne: a) 5 procent hrubé částky dividend, jestliže skutečným vlastníkem je společnost, která přímo drží alespoň 10 procent kapitálu společnosti, která dividendy vyplácí; b) 10 procent hrubé částky dividend ve všech ostatních případech. Příslušné úřady smluvních států upraví vzájemnou dohodou způsob aplikace těchto omezení. Tento odstavec se nedotýká zdanění zisků společnosti, z nichž jsou dividendy vypláceny. 3. Dividendy vyplácené společností, která je rezidentem jednoho s …
- interest Article 11: 1. Úroky mající zdroj v jednom smluvním státě a skutečně vlastněné rezidentem druhého smluvního státu podléhají zdanění jen v tomto druhém státě. 2. Výraz „úroky“ použitý v tomto článku označuje příjmy z pohledávek jakéhokoliv druhu, ať zajištěných či nezajištěných zástavním právem na nemovitosti a majících či nemajících právo účasti na zisku dlužníka, a zvláště, příjmy z vládních cenných papírů a příjmy z obligací nebo dluhopisů, včetně prémií a výher, které se vážou k těmto cenným papírům, obligacím nebo dluhopisům. Penále ukládané za pozdní platbu se nepovažuje za úroky pro účely tohoto článku. Výraz „úroky“ nezahrnuje žádnou část příjmu, která je považována za dividendu podle ustanovení článku 10 odstavce 4. 3. Ustanovení odstavce I se nepoužijí, jestliže skutečný vlastník úroků, který je rezidentem jednoho smluvního státu, vykonává v druhém smluvním státě, ve kterém mají úroky zdroj …
- royalty Article 12: 1. Licenční poplatky mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu mohou být zdaněny v tomto druhém státě. 2. Tyto licenční poplatky však mohou být rovněž zdaněny ve smluvním státě, v němž mají zdroj, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník licenčních poplatků je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 10 procent hrubé částky licenčních poplatků. Příslušné úřady smluvních států upraví vzájemnou dohodou způsob aplikace tohoto omezení. 3. Výraz „licenční poplatky“ použitý v tomto článku označuje platby jakéhokoliv druhu obdržené jako náhrada za užití nebo za právo na užití jakéhokoliv autorského práva k dílu literárnímu, uměleckému nebo vědeckému, jakéhokoliv patentu, ochranné známky, návrhu nebo modelu, plánu, tajného vzorce nebo postupu, nebo za užití nebo za právo na užití jakéhokoliv průmy …

Audit package hash: `955712e070ef76d5a0d6c1c9ff9e3349d11e2892412ff7d6aa23d6a3186cb424`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## RO — Rumunsko (STANDARD)

Base treaty: **180/1994 Sb.** (`SRC-AD6B58C75FA89A97`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 10.0% | 10.0%: beneficial_owner == true |
| interest | 11 | 0.0%, 7.0% | 0.0%: recipient_or_financing == government_local_authority_territorial_administrative_unit_government_agency_bank_or_body_or_claim_guaranteed_secured_or_directly_or_indirectly_financed_by_wholly_government_owned_financial_institution, loan_is_noncommercial == true, beneficial_owner == true; 7.0%: fallback_case == all_other_cases, beneficial_owner == true |
| royalty | 12 | 10.0% | 10.0%: beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-RO-MLI-WHT-PPT`; candidate WHT date `2024-01-01`. Article 8 adds no overlay.

Language: authentic `None`; prevailing `None`; evidence `hash_bound_repository_signature_clause_candidate`; signature clause `Dáno ve dvojõm vyhotovenõ v Bukuresti dne
8. listopadu 1993 v ceském, rumunském a anglickém
jazyce, pricemz vsechny texty jsou autentické. V prõ-
pade jakýchkoliv rozdõlnostõ výkladu bude rozhodujõcõ
anglický text.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-AD6B58C75FA89A97](https://e-sbirka.gov.cz/sb/1994/180/0000-00-00).

Candidate excerpts:

- dividend Article 10: Dividendy 1. Dividendy vyplácené spolecnostõ, která je rezi- dentem v jednom smluvnõm státe, osobe, která je rezi- dentem v druhém smluvnõm státe, mohou být zdaneny v tomto druhém státe. 2. Tyto dividendy vsak mohou být rovnez zda- neny ve smluvnõm státe, v nemz je spolecnost, která je vyplácõ, rezidentem, a to podle právnõch predpisu tohoto státu, avsak jestlize prõjemce je skutecným vlastnõkem dividend, dan takto stanovená nepresáhne 10 procent hrubé cástky dividend. Tento odstavec se nedotýká zdanenõ zisku spolecnosti, ze kterých jsou dividendy vypláceny. 3. Výraz 1dividendya, pouzitý v tomto clánku, oznacuje prõjmy z akciõ nebo jiných práv s podõlem na zisku, s výjimkou pohledávek, jakoz i prõjmy z práv na spolecnosti, které jsou podle dan ových pred- pisu státu, v nemz je spolecnost, která rozdõlõ zisk, rezidentem, postaveny na roven prõjmu z akciõ. 4. Ustanovenõ odstavcu 1 a 2 se n …
- interest Article 11: U roky 1. U roky majõcõ zdroj v jednom smluvnõm státe, které pobõrá rezident druhého smluvnõho státu, mohou být zdaneny v tomto druhém státe. 2. Avsak takové úroky mohou být zdaneny rov- nez ve smluvnõm státe, v nemz majõ zdroj, a podle právnõch predpisu tohoto státu, ale pokud prõjemce je skutecným vlastnõkem úroku , dan takto ulozená nepre- sáhne 7 procent hrubé cástky úroku . 3. Bez ohledu na ustanovenõ odstavce 2 úroky, majõcõ zdroj v jednom smluvnõm státe, budou osvobo- zeny od danõ v tomto státe, jestlize je pobõrá a skutecne vlastnõ vláda druhého smluvnõho státu, mõstnõ úrad nebo územne správnõ jednotka tohoto státu nebo jaká- koliv agentura nebo banka nebo orgán této vlády nebo jestlize pohledávky rezidenta druhého smluvnõho státu jsou zaruceny, zajisteny nebo prõmo nebo neprõmo financovány financnõ institucõ zcela vlastnenou vládou druhého smluvnõho státu, za predpokladu, ze pu  …
- royalty Article 12: Licencnõ poplatky 1. Licencnõ poplatky, majõcõ zdroj v jednom smluvnõm státe, vyplácené rezidentu druhého smluv- nõho státu, mohou být zdaneny v tomto druhém státe. 2. Avsak takové licencnõ poplatky mohou být také zdaneny ve smluvnõm státe, ve kterém je jejich zdroj, a v souladu s právnõmi predpisy tohoto státu, avsak je-li prõjemce skutecným vlastnõkem licencnõch poplatku , cástka dane takto stanovená nepresáhne 10 procent hrubé cástky licencnõch poplatku . 3. Výraz 1licencnõ poplatkya pouzitý v tomto clánku oznacuje platby jakéhokoliv druhu obdrzené jako náhrada za uzitõ nebo za právo na uzitõ autor- ského práva k dõlu literárnõmu, umeleckému nebo ve- deckému vcetne kinematografických filmu a filmu nebo nahrávek pro televiznõ nebo rozhlasové vysõlánõ, satelitnõho nebo kabelového prenosu za úcelem vysõ- lánõ pro verejnost prostrednictvõm jakékoliv formy elektronických médiõ; nebo jakého …

Audit package hash: `3b446ca6671dc35bdf9483cb2cb80ff53c04803840afbd80523173e8ab9b1fe6`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## RS — Srbsko (ELEVATED)

Base treaty: **88/2005 Sb.m.s.** (`SRC-1AFA5CABE7CE078F`).

Risk focus: material_protocol_overlay.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 10.0% | 10.0%: beneficial_owner == true |
| interest | 11 | 0.0%, 10.0% | 10.0%: beneficial_owner == true; 0.0%: recipient_entity_type == government_subnational_local_authority_central_bank_or_wholly_government_owned_financial_institution, beneficial_owner == true |
| royalty | 12 | 5.0%, 10.0% | 5.0%: royalty_category == copyright_literary_artistic_or_scientific_excluding_computer_program_including_films_and_broadcast_media, beneficial_owner == true; 10.0%: royalty_category == patent_trademark_design_model_plan_secret_formula_process_computer_program_equipment_or_knowhow, beneficial_owner == true |

Protocol/status: `protocol_effect_candidate_consolidated` / `not_listed`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-RS-MLI-WHT-PPT`; candidate WHT date `2021-01-01`. Article 8 adds no overlay.

Language: authentic `None`; prevailing `None`; evidence `hash_bound_repository_signature_clause_candidate`; signature clause `Dáno v Praze dne 11. listopadu 2004 ve dvou puvodnõch vyhotovenõch v anglickém jazyce.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-1AFA5CABE7CE078F](https://e-sbirka.gov.cz/sm/2005/88/0000-00-00); `CZ-MF-RS-7987A53E3798`.

Candidate excerpts:

- dividend Article 10: DIVIDENDY 1. Dividendy vyplácené spolecnostõ, která je rezidentem jednoho smluvnõho státu, rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto dividendy vsak mohou být rovnez zdaneny ve smluvnõm státe, jehoz je spolecnost, která je vyplácõ, rezidentem, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk dividend je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne 10 procent hrubé cástky dividend. Přõslusné úrady smluvnõch státu upravõ vzájemnou dohodou zpusob aplikace tohoto omezenõ. Tento odstavec se nedotýká zdanenõ zisku spolecnosti, z nichz jsou dividendy vypláceny. 3. Výraz 1dividendya pouzitý v tomto clánku oznacuje prõjmy z akciõ nebo jiných práv, s výjimkou pohle- dávek, s podõlem na zisku, jakoz i jiné prõjmy, které jsou podrobeny stejnému danovému rezimu jako prõjmy z akciõ podle právnõch predpisu státu, jeho …
- interest Article 11: UROKY 1. Uroky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto úroky vsak mohou být rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk úroku je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne 10 procent hrubé cástky úroku. Přõslusné úrady smluvnõch státu upravõ vzájemnou dohodou zpusob aplikace tohoto omezenõ. 3. Bez ohledu na ustanovenõ odstavce 2 budou úroky osvobozeny od zdanenõ ve smluvnõm státe, ve kterém majõ zdroj, pokud jsou pobõrané a skutecne vlastnené vládou druhého smluvnõho státu, vcetne jakéhokoliv nizsõho správnõho útvaru nebo mõstnõho úradu tohoto státu, centrálnõ bankou nebo jakoukoli financnõ institucõ, která je zcela vlastnena touto vládou. 4. Výraz 1úrokya pouzitý v tomto clánku oznacuje prõjm …
- royalty Article 12: LICENČNI POPLATKY 1. Licencnõ poplatky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto licencnõ poplatky vsak mohou být rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk licencnõch poplatku je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne: (1) 5 procent hrubé cástky licencnõch poplatku uvedených v odstavci 3 bode (1); (2) 10 procent hrubé cástky licencnõch poplatku uvedených v odstavci 3 bode (2). Přõslusné úrady smluvnõch státu upravõ vzájemnou dohodou zpusob aplikace techto omezenõ. 3. Výraz 1licencnõ poplatkya pouzitý v tomto clánku oznacuje platby jakéhokoliv druhu obdrzené jako náhrada za uzitõ nebo za právo na uzitõ: (1) jakéhokoliv autorského práva k dõlu literárnõmu, umeleckému nebo vedeckému, s výjimk …

Audit package hash: `cb35714bbf57a360ea80e606f4afe2d75304073cb5504c9b9c5f6830d83fa5d9`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## RU — Rusko (ELEVATED)

Base treaty: **278/1997 Sb.** (`SRC-5B60ADE50F43E63E`).

Risk focus: material_protocol_overlay, multiple_historical_instruments.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 10.0% | 10.0%: beneficial_owner == true |
| interest | 11 | 0.0% | 0.0%: beneficial_owner == true |
| royalty | 12 | 10.0% | 10.0%: beneficial_owner == true |

Protocol/status: `protocol_effect_candidate_consolidated` / `article_application_suspended`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-RU-MLI-WHT-PPT`; candidate WHT date `2021-01-01`. Article 8 adds no overlay.

Language: authentic `None`; prevailing `None`; evidence `hash_bound_repository_signature_clause_candidate`; signature clause `Dáno ve dvojõm vyhotovenõ v Praze dne 17. listo-
padu 1995 v ceském, ruském a anglickém jazyce, pri-
cemz vsechny texty jsou autentické. V prõpade jakých-
koliv rozdõlnostõ výkladu mezi ceským a ruským tex-
tem bude rozhodujõcõm anglický text.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-5B60ADE50F43E63E](https://e-sbirka.gov.cz/sb/1997/278/0000-00-00); `CZ-MF-RU-2647E9E83753`; `CZ-MF-RU-4F72F907462B`.

Candidate excerpts:

- dividend Article 10: Dividendy 1. Dividendy vyplácené společností, které je rezidentem jednoho smluvního státu, rezidentu druhého smluvního státu, mohou být zdaněny v tomto druhém státě. 2. Tyto dividendy však mohou být rovněž zdaněny ve smluvním státě, jehož je společnost, která je vyplácí, rezidentem, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník dividend je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 10 procent hrubé částky dividend. Příslušné úřady smluvních států upraví vzájemnou dohodou způsob aplikace tohoto omezení. Tento odstavec se nedotýká zdanění zisků společnosti, ze kterých jsou dividendy vypláceny. 3. Výraz „dividendy“ použitý v tomto článku označuje příjmy z akcií nebo jiných práv, s výjimkou pohledávek, s podílem na zisku, jakož i jiné příjmy, které jsou podrobeny stejnému daňovému režimu jako příjmy z akcií podle daňových zákonů státu, jeho …
- interest Article 11: Úroky 1. Úroky mající zdroj v jednom smluvním státě a skutečně vlastněné rezidentem druhého smluvního státu podléhají zdanění jen v tomto druhém státě. 2. Výraz „úroky" použitý v tomto článku označuje příjmy z pohledávek jakéhokoliv druhu, ať zajištěných či nezajištěných zástavním právem na nemovitosti nebo majících či nemajících právo účasti na zisku dlužníka a obzvláště příjmy z vládních cenných papírů a příjmy z obligací nebo dluhopisů vřetně prémií a výher spojených s těmito cennými papíry, obligacemi nebo dluhopisy. Výraz „úroky“ nezahrnuje žádnou část příjmu, která je považována za dividendu podle ustanovení článku 10 odstavce 3. 3. Ustanovení odstavce 1 se nepoužije, jestliže skutečný vlastník úroků, který je rezidentem v jednom smluvním státě, vykonává v druhém smluvním státě, v němž mají úroky zdroj, průmyslovou nebo obchodní činnost prostřednictvím stálé provozovny, která je ta …
- royalty Article 12: Licenční poplatky 1. Licenční poplatky mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu mohou být zdaněny v tomto druhém státě. 2. Tyto licenční poplatky však mohou být rovněž zdaněny ve smluvním státě, v němž mají zdroj, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník licenčních poplatků je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 10 procent hrubé částky licenčních poplatků. Příslušné úřady smluvních států upraví vzájemnou dohodou způsob aplikace tohoto omezení. 3. Výraz „licenční poplatky" použity v tomto článku označuje platby jakéhokoliv druhu obdržené jako náhrada za užití nebo za právo na užití jakéhokoliv autorského práva k dílu literárnímu, uměleckému nebo vědeckému včetně kinematografických filmů a filmů nebo nahrávek pro televizní nebo rozhlasové vysílání, jakéhokoliv patentu, ochranné známky, …

Audit package hash: `b291eea5bb76aba2eef984369b8b8143a91a36f0536260e75f33d76f2d9f49c9`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## RW — Rwanda (STANDARD)

Base treaty: **482/2024 Sb.** (`SRC-511CFDDE4F94358B`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 10.0% | 10.0%: beneficial_owner == true |
| interest | 11 | 0.0%, 10.0% | 10.0%: beneficial_owner == true; 0.0%: article_11_3_exemption == government_central_bank_export_or_investment_promotion_institution_or_qualifying_government_guaranteed_financing, beneficial_owner == true |
| royalty | 12 | 10.0% | 10.0%: beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `not_listed`; modification `None`; candidate WHT date `None`. Article 8 adds no overlay.

Language: authentic `None`; prevailing `None`; evidence `hash_bound_repository_signature_clause_candidate`; signature clause `Dáno v Kigali dne 2. května​ 2023 ve dvou původních vyhotoveních v anglickém jazyce.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-511CFDDE4F94358B](https://e-sbirka.gov.cz/sb/2024/482/0000-00-00).

Candidate excerpts:

- dividend Article 10: DIVIDENDY 1. Dividendy vyplácené společností, která je rezidentem jednoho smluvního státu, rezidentu druhého smluvního státu, mohou být zdaněny v tomto druhém státě. 2. Dividendy vyplácené společností, která je rezidentem jednoho smluvního státu, však mohou být rovněž zdaněny v tomto státě, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník dividend je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 10 procent hrubé částky dividend. Tento odstavec se nedotýká zdanění zisků společnosti, z nichž jsou dividendy vypláceny. 3. Výraz „dividendy“ použitý v tomto článku označuje příjmy z akcií nebo jiných práv (s výjimkou pohledávek) s podílem na zisku, jakož i jiné příjmy, které jsou podrobeny stejnému daňovému režimu jako příjmy z akcií podle právních předpisů smluvního státu, jehož je společnost, která rozdílí zisk nebo provádí platbu, rezidentem. 4.  …
- interest Article 11: ÚROKY 1. Úroky mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu mohou být zdaněny v tomto druhém státě. 2. Úroky mající zdroj v jednom smluvním státě však mohou být rovněž zdaněny v tomto státě, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník úroků je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 10 procent hrubé částky úroků. 3. Úroky mající zdroj v jednom smluvním státě podléhají bez ohledu na ustanovení odstavce 2 zdanění jen ve druhém smluvním státě, jestliže jsou tyto úroky skutečně vlastněny: a) vládou druhého státu, včetně jakéhokoliv nižšího správního útvaru nebo místního úřadu tohoto státu, centrální bankou druhého státu nebo jakoukoli institucí, která je vlastněna nebo ovládána touto vládou, jestliže smyslem existence takové instituce je podpora investic nebo exportu; b) rezidentem druhého státu v  …
- royalty Article 12: LICENČNÍ POPLATKY A POPLATKY ZA TECHNICKÉ SLUŽBY 1. Licenční poplatky a poplatky za technické služby mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu mohou být zdaněny v tomto druhém státě. 2. Licenční poplatky a poplatky za technické služby mající zdroj v jednom smluvním státě však mohou být rovněž zdaněny v tomto státě, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník licenčních poplatků nebo poplatků za technické služby je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 10 procent hrubé částky licenčních poplatků nebo poplatků za technické služby. 3. ​ a) Výraz „licenční poplatky“ použitý v tomto článku označuje platby jakéhokoliv druhu obdržené jako náhrada za užití nebo za právo na užití jakéhokoliv autorského práva k dílu literárnímu, uměleckému nebo vědeckému, včetně kinematografických filmů, nebo filmů, …

Audit package hash: `7b4c632b04eb4d46e1083871e66fee636d94c0e2976ac7cb17f770cfee54efdd`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____
