# CZ country legal-QA review batch 04

> Machine-prepared candidate evidence only. No country or scope in this file has been human reviewed, approved, verified, or released.

## FR — Francie (STANDARD)

Base treaty: **79/2005 Sb.m.s.** (`SRC-903074BA6B9910C5`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 0%, 10% | 0%: recipient_entity_type == company, direct_ownership == true, ownership_percent >= 25, beneficial_owner == true; 10%: fallback_case == all_other_cases, beneficial_owner == true |
| interest | 11 | 0.0% | 0.0%: beneficial_owner == true |
| royalty | 12 | 0.0%, 5.0%, 10.0% | 0.0%: royalty_category == copyright_literary_artistic_scientific_excluding_computer_program_including_films_and_broadcast_media, beneficial_owner == true; 5.0%: royalty_category == industrial_commercial_or_scientific_equipment, beneficial_owner == true; 10.0%: royalty_category == patent_trademark_design_model_plan_secret_formula_process_computer_program_or_knowhow, beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-FR-MLI-WHT-PPT`; candidate WHT date `2021-01-01`. Article 8 adds no overlay.

Language: authentic `None`; prevailing `None`; evidence `hash_bound_repository_signature_clause_candidate`; signature clause `Dáno v Praze dne 28. dubna roku 2003 ve dvou puvodnõch vyhotovenõch, kazdé v jazyce ceském a francouz-
ském, pricemz oba texty majõ stejnou platnost.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-903074BA6B9910C5](https://e-sbirka.gov.cz/sm/2005/79/0000-00-00).

Candidate excerpts:

- dividend Article 10: DIVIDENDY 1. Dividendy vyplácené spolecnostõ, která je rezidentem jednoho smluvnõho státu, rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto dividendy vsak mohou být rovnez zdaneny ve smluvnõm státe, jehoz je spolecnost, která je vyplácõ, rezidentem, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk dividend je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne: a) 0 procent hrubé cástky dividend, jestlize skutecným vlastnõkem je spolecnost, která prõmo drzõ nejméne 25 procent kapitálu spolecnosti vyplácejõcõ dividendy; b) 10 procent hrubé cástky dividend ve vsech ostatnõch prõpadech. Tento odstavec se nedotýká zdanenõ zisku spolecnosti, z nichz jsou dividendy vypláceny. 3. Rezident České republiky, který dostává dividendy vyplácené spolecnostõ, která je rezidentem Francie, muze zõskat refundaci zálohy do té mõry, ze …
- interest Article 11: UROKY 1. Uroky majõcõ zdroj v jednom smluvnõm státe a skutecne vlastnené rezidentem druhého smluvnõho státu podléhajõ zdanenõ jen v tomto druhém státe. 2. Výraz 1úrokya oznacuje prõjmy z pohledávek jakéhokoliv druhu, at' zajistených ci nezajistených zá- stavnõm právem na nemovitosti nebo majõcõch ci nemajõcõch právo úcasti na zisku dluznõka, a zvláste, prõjmy z vládnõch cenných papõru a prõjmy z obligacõ nebo dluhopisu, vcetne prémiõ a výher, které se vázou k temto cenným papõrum, obligacõm nebo dluhopisum. Penále ukládané za pozdnõ platbu se nepovazuje za úroky pro úcely tohoto clánku. Výraz 1úrokya nezahrnuje zádnou cást prõjmu, která je povazována za dividendu podle ustanovenõ clánku 10. 3. Ustanovenõ odstavce 1 se nepouzijõ, jestlize skutecný vlastnõk úroku, který je rezidentem jednoho smluv- nõho státu, vykonává v druhém smluvnõm státe, ve kterém majõ úroky zdroj, prumyslovou nebo o …
- royalty Article 12: LICENČNI POPLATKY 1. Licencnõ poplatky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto licencnõ poplatky vsak mohou být, vyjma prõpadu druhu plateb, který je uveden v põsmenu a) odstavce 3, rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk licencnõch poplatku je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne: a) 5 procent hrubé cástky licencnõch poplatku, a to v prõpade druhu plateb, který je uveden v põsmenu b) odstavce 3; b) 10 procent hrubé cástky licencnõch poplatku, a to v prõpade druhu plateb, který je uveden v põsmenu c) odstavce 3. 3. Výraz 1licencnõ poplatkya oznacuje platby jakéhokoliv druhu obdrzené jako náhrada za uzitõ nebo za právo na uzitõ: a) jakéhokoliv autorského práva k dõlu literárnõmu, umel …

Audit package hash: `844708cccc4d51d154767c32e27574a10684b6c7450f9de0ff761737634f1bd9`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## GB — Velká Británie (Spojené království Velké Británie a Severního Irska) (ELEVATED)

Base treaty: **89/1992 Sb.** (`SRC-4253A70D066D161D`).

Risk focus: multiple_historical_instruments.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 5%, 15% | 5%: recipient_entity_type == company, voting_ownership >= 25, beneficial_owner == true; 15%: fallback_case == all_other_cases, beneficial_owner == true |
| interest | 11 | 0.0% | 0.0%: beneficial_owner == true |
| royalty | 12 | 0.0%, 10.0% | 0.0%: royalty_category == copyright_literary_artistic_or_scientific_including_films_and_broadcast_recordings, beneficial_owner == true; 10.0%: royalty_category == patent_trademark_design_model_plan_secret_formula_process_equipment_or_industrial_commercial_technical_technological_scientific_knowhow, beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-GB-MLI-WHT-PPT`; candidate WHT date `2021-01-01`. Article 8 adds no overlay.

Language: authentic `['cs', 'en']`; prevailing `equal`; evidence `existing_repository_language_record`; signature clause `None`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-4253A70D066D161D](https://e-sbirka.gov.cz/sb/1992/89/0000-00-00).

Candidate excerpts:

- dividend Article 10: Dividendy 1. Dividendy vyplácené společností, která je rezidentem v jednom smluvním státě, osobě, která je rezidentem v druhém smluvním státě, mohou být zdaněny v tomto druhém smluvním státě. 2. Tyto dividendy však mohou být rovněž zdaněny ve smluvním státě, v němž je společnost, která je vyplácí, rezidentem, a to podle právních předpisů tohoto státu, avšak jestliže příjemce je skutečným vlastníkem dividend, daň takto stanovená nepřesáhne: (a) 5 % hrubé částky dividend, jestliže příjemce je společnost, která spravuje nejméně 25 % podílů s hlasovacím právem na společnosti vyplácející dividendy; (b) 15 % hrubé částky dividend ve všech ostatních případech. 3. Výraz „dividendy“, použitý v tomto článku, označuje příjmy z akcií nebo jiných práv - s výjimkou pohledávek - s podílem na zisku, jakož i příjmy z práv na společnosti, které jsou podle daňových předpisů státu, v němž je společnost, kte …
- interest Article 11: Úroky 1. Úroky mající zdroj v jednom smluvním státě, které pobírá rezident druhého smluvního státu, a který je jejich skutečným vlastníkem, budou zdaněny pouze v tomto druhém státě. 2. Výraz „úroky“, použitý v tomto článku, označuje příjmy z vládních cenných papírů, obligací nebo dluhopisů zajištěných i nezajištěných zástavním právem na nemovitosti nebo doložkou o účasti na zisku a z pohledávek jakéhokoliv druhu, stejně jako všechny ostatní příjmy, mající charakter příjmů z půjček, podle daňového práva státu, ve kterém je zdroj příjmu. 3. Ustanovení odstavce 1 tohoto článku se nepoužije, jestliže skutečný vlastník úroků, který je rezidentem v jednom smluvním státě, vykonává v druhém smluvním státě, ve kterém mají úroky zdroj, průmyslovou nebo obchodní činnost prostřednictvím stálé provozovny, která je tam umístěna, nebo nezávislé povolání prostřednictvím stálé základny tam umístěné a jes …
- royalty Article 12: Licenční poplatky 1. Licenční poplatky, mající zdroj v jednom smluvním státě, který pobírá rezident druhého smluvního státu, a který je jejich skutečným vlastníkem, budou zdaněny pouze v tomto druhém státě. 2. Licenční poplatky uvedené v pododstavci 3 (a), mohou být bez ohledu na ustanovení odstavce 1 tohoto článku, zdaněny také ve smluvním státě, ve kterém je jejich zdroj, a v souladu s právními předpisy tohoto státu, avšak je-li příjemce skutečným vlastníkem licenčních poplatků, částka daně takto stanovená nepřesáhne 10 % hrubé částky z licenčních poplatků. 3. Výraz „licenční poplatky“ použitý v tomto článku označuje platby jakéhokoliv druhu obdržené jako náhrada za: (a) užití nebo za právo na užití patentu, ochranné známky, návrhu nebo modelu, plánu, tajného vzorce nebo výrobního postupu nebo za užití nebo za právo na užití průmyslového, obchodního nebo vědeckého zařízení, nebo za inf …

Audit package hash: `3d0fafa71a4e8299cf1c18d62c0e152e5de7a0b216c3dbbc1cd93dd2ff510f8c`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## GE — Gruzie (STANDARD)

Base treaty: **40/2007 Sb.m.s.** (`SRC-424DC2CFCDF8B32E`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 5%, 10% | 5%: recipient_entity_type == company_other_than_partnership, direct_ownership == true, ownership_percent >= 25, beneficial_owner == true; 10%: fallback_case == all_other_cases, beneficial_owner == true |
| interest | 11 | 0.0%, 8.0% | 8.0%: beneficial_owner == true; 0.0%: article_11_3_exemption == government_subnational_local_authority_central_bank_wholly_government_owned_financial_institution_or_government_guaranteed_financing_or_credit_sale_of_industrial_commercial_or_scientific_equipment, beneficial_owner == true |
| royalty | 12 | 0.0%, 5.0%, 10.0% | 0.0%: royalty_category == copyright_literary_artistic_scientific_excluding_computer_program_including_films_and_broadcast_media, beneficial_owner == true; 5.0%: royalty_category == industrial_commercial_or_scientific_equipment, beneficial_owner == true; 10.0%: royalty_category == patent_trademark_design_model_plan_secret_formula_process_computer_program_or_knowhow, beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-GE-MLI-WHT-PPT`; candidate WHT date `2021-01-01`. Article 8 adds no overlay.

Language: authentic `None`; prevailing `None`; evidence `hash_bound_repository_signature_clause_candidate`; signature clause `Dáno v TBILISI dne 23. kvetna 2006 ve dvou puvodnõch vyhotovenõch, kazdé v jazyce ceském, gruzõnském
a anglickém, pricemz vsechny texty jsou autentické.
V prõpade jakéhokoliv rozdõlu mezi ceským a gruzõnským textem bude rozhodujõcõm anglický text.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-424DC2CFCDF8B32E](https://e-sbirka.gov.cz/sm/2007/40/0000-00-00).

Candidate excerpts:

- dividend Article 10: DIVIDENDY 1. Dividendy vyplácené spolecnostõ, která je rezidentem jednoho smluvnõho státu, rezidentu druhého smluvnõho státu, mohou být zdaneny v tomto druhém státe. 2. Tyto dividendy vsak mohou být rovnez zdaneny ve smluvnõm státe, jehoz je spolecnost, která je vyplácõ, rezidentem, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk dividend je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne: a) 5 procent hrubé cástky dividend, jestlize skutecným vlastnõkem je spolecnost (jiná nez osobnõ spolecnost), která prõmo vlastnõ nejméne 25 procent kapitálu spolecnosti vyplácejõcõ dividendy; b) 10 procent hrubé cástky dividend ve vsech ostatnõch prõpadech. Přõslusné úrady smluvnõch státu upravõ vzájemnou dohodou zpusob aplikace techto omezenõ. Tento odstavec se nedotýká zdanenõ zisku spolecnosti, z nichz jsou dividendy vypláceny. 3. Výraz 1dividendya pouzi …
- interest Article 11: UROKY 1. Uroky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto úroky vsak mohou být rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk úroku je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne 8 procent hrubé cástky úroku. Přõslusné úrady smluvnõch státu upravõ vzájemnou dohodou zpusob aplikace tohoto omezenõ. 3. Bez ohledu na ustanovenõ odstavce 2 budou úroky osvobozeny od zdanenõ ve smluvnõm státe, ve kterém majõ zdroj, pokud jsou: a) pobõrané a skutecne vlastnené: (i) vládou druhého smluvnõho státu, vcetne jakéhokoliv nizsõho správnõho útvaru nebo mõstnõho úradu tohoto státu, centrálnõ bankou nebo jakoukoli financnõ institucõ, která je zcela vlastnena touto vládou; nebo (ii) rezidentem druhého smluvnõho státu v …
- royalty Article 12: LICENČNI POPLATKY 1. Licencnõ poplatky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto licencnõ poplatky vsak mohou být, vyjma prõpadu druhu plateb, který je uveden v põsmenu a) odstavce 3, rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk licencnõch poplatku je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne: a) 5 procent hrubé cástky licencnõch poplatku, a to v prõpade druhu plateb, který je uveden v põsmenu b) odstavce 3; b) 10 procent hrubé cástky licencnõch poplatku, a to v prõpade druhu plateb, který je uveden v põsmenu c) odstavce 3. Přõslusné úrady smluvnõch státu upravõ vzájemnou dohodou zpusob aplikace techto omezenõ. 3. Výraz 1licencnõ poplatkya oznacuje platby jakéhokoliv druhu obdrzené jako náhrada  …

Audit package hash: `e7cc8f3e3f728af10162cac79a3c734097f29dc907b3951efc4786fadf75699d`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## GH — Ghana (ELEVATED)

Base treaty: **38/2020 Sb.m.s.** (`SRC-0CAA69D6B9F619E5`).

Risk focus: unusual_language_or_prevailing_text.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 6.0% | 6.0%: beneficial_owner == true |
| interest | 11 | 0.0%, 10.0% | 10.0%: beneficial_owner == true; 0.0%: article_11_3_exemption == credit_sale_or_bank_loan_or_government_central_bank_government_owned_or_controlled_financial_institution_or_qualifying_government_guaranteed_financing, beneficial_owner == true |
| royalty | 12 | 8.0% | 8.0%: beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `not_listed`; modification `None`; candidate WHT date `None`. Article 8 adds no overlay.

Language: authentic `['Czech', 'English']`; prevailing `both_texts_authentic_no_prevailing_clause_stated`; evidence `current_official_pdf_signature_clause_candidate`; signature clause `Dano v Akk#e dne 11. dubna 2017 ve dvou piivodnich vyhotovenich, v éeském a anglickém jazyce, pri¢emZ oba texty jsou autentické.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: No current WHT-relevant MLI PPT effect record.

Official sources: [SRC-0CAA69D6B9F619E5](https://e-sbirka.gov.cz/sm/2020/38/0000-00-00).

Candidate excerpts:

- dividend Article 10: 1. Dividendy vyplácené společností, která je rezidentem jednoho smluvního státu, rezidentu druhého smluvního státu, mohou být zdaněny v tomto druhém státě. 2. Tyto dividendy však mohou být rovněž zdaněny ve smluvním státě, jehož je společnost, která je vyplácí, rezidentem, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník dividend je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 6 procent hrubé částky dividend. Příslušné úřady smluvních států upraví vzájemnou dohodou způsob aplikace tohoto omezení. Tento odstavec se nedotýká zdanění zisků společnosti, z nichž jsou dividendy vypláceny. 3. Výraz „dividendy“ použitý v tomto článku označuje příjmy z akcií nebo jiných práv, s výjimkou pohledávek, s podílem na zisku, jakož i příjmy z jiných práv na společnosti a jiné příjmy, které jsou podrobeny stejnému daňovému režimu jako příjmy z akcií podle prá …
- interest Article 11: 1. Úroky mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu mohou být zdaněny v tomto druhém státě. 2. Tyto úroky však mohou být rovněž zdaněny ve smluvním státě, v němž mají zdroj, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník úroků je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 10 procent hrubé částky úroků. Příslušné úřady smluvních států upraví vzájemnou dohodou způsob aplikace tohoto omezení. 3. Úroky mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu, který je jejich skutečným vlastníkem, podléhají bez ohledu na ustanovení odstavce 2 zdanění jen v tomto druhém státě, jestliže jsou tyto úroky vypláceny: a) v souvislosti s prodejem jakéhokoliv zboží nebo zařízení na úvěr; b) z jakékoliv půjčky nebo úvěru jakéhokoliv druhu, kterou nebo který poskytla banka; c) vládě druhé …
- royalty Article 12: 1. Licenční poplatky a poplatky za služby mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu mohou být zdaněny v tomto druhém státě. 2. Tyto licenční poplatky a poplatky za služby však mohou být rovněž zdaněny ve smluvním státě, v němž mají zdroj, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník licenčních poplatků nebo poplatků za služby je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 8 procent hrubé částky licenčních poplatků nebo poplatků za služby. Příslušné úřady smluvních států upraví vzájemnou dohodou způsob aplikace tohoto omezení. 3. a) Výraz „licenční poplatky“ použitý vtomto článku označuje platby jakéhokoliv druhu obdržené jako náhrada za užití nebo za právo na užití jakéhokoliv autorského práva k dílu literárnímu, uměleckému nebo vědeckému, včetně kinematografických filmů, a filmů nebo pásek pro t …

Audit package hash: `a92130ea00be08ff6e9346298f277e085df4fe7bf230fac7c81b45f0979894b8`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## GR — Řecko (ELEVATED)

Base treaty: **98/1989 Sb.** (`SRC-C5ED2C206EB6D04B`).

Risk focus: preserved_historical_source_hash_difference.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | none | No extracted rate condition |
| interest | 11 | 0.0%, 10.0% | 10.0%: beneficial_owner == true; 0.0%: article_11_3_exemption == loan_granted_by_government_or_bank_or_institution_on_behalf_or_for_account_of_government, beneficial_owner == true |
| royalty | 12 | 0.0%, 10.0% | 0.0%: royalty_category == copyright_literary_artistic_or_scientific_including_cinematographic_and_television_films; 10.0%: royalty_category == patent_trademark_design_model_plan_secret_formula_process_equipment_or_industrial_commercial_scientific_knowhow |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-GR-MLI-WHT-PPT`; candidate WHT date `2022-01-01`. Article 8 adds no overlay.

Language: authentic `['English']`; prevailing `sole_english`; evidence `current_official_pdf_signature_clause_candidate`; signature clause `Dano ve dvojim vyhotoveni v Athénéch dne 23, Fijna 1986 v anglickém jazyce.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-C5ED2C206EB6D04B](https://e-sbirka.gov.cz/sb/1989/98/0000-00-00).

Candidate excerpts:

- dividend Article 10: Dividendy 1. Dividendy vyplácené společností, která je rezidentem v jednom smluvním státě, osobě, která je rezidentem v druhém smluvním státě, podléhají zdanění v obou smluvních státech, 2. Výraz „dividendy“, použitý v tomto článku, označuje příjmy z akcií, požitkových akcií nebo požitkových listů, kuksů, zakladatelských podílů nebo jiných práv — s výjimkou pohledávek — s podílem na zisku a příjmy z jiných podílů na společnosti, které jsou podle právních předpisů států, v němž je společnost, která dividendy vy- plácí rezidentem, postaveny na roveň příjmů z akcií. 3. Ustanovení odstavce 1 se nepoužije, jestliže skutečný příjemce dividend, který je rezidentem v jednom smluvním státě, vykonává v druhém smluvním státě, v němž je rezidentem společnost vyplácející dividendy, průmyslovou nebo obchodní činnost prostřednictvím stálé provozovny, která je tam umístěna, nebo nezávislé povolání prost …
- interest Article 11: Úroky 1. Úroky mající zdroj v jednom smluvním stá- tě a vyplácené osobě, která je rezidentem v dru- hém smluvním státě, mohou být zdaněny v tomto druhém státě, 2. Takové úroky však mohou být zdaněny také ve smluvním státě, ve kterém je jejich zdroj, a to podle právních předpisů tohoto státu, avšak jestli- že příjemce je skutečným vlastníkem úroků, daň takto ukládaná nepřesáhne 10 % hrubé částky úroků. Příslušné úřady smluvních států stanoví ve vzájemné dohodě způsob uplatnění tohoto omeze- ní. 3. Bez ohledu na ustanovení odstavce 2, úroky plynoucí z půjčky poskytnuté vládou jednoho smluvního státu, nebo bankou, nebo jakoukoli ji- nou institucí ve jménu nebo na účet této vlády, budou podléhat zdanění pouze ve smluvním státě, v němž je příjemce rezidentem. 4. Výraz „úroky“ použitý v tomto článku označuje příjmy z pohledávek jakéhokoli druhu, zajištěných i nezajištěných zástavním právem na  …
- royalty Article 12: Licenční poplatky 1. Licenční poplatky mající zdroj v jednom smluvním státě a placené osobě, která je rezidentem v druhém smluvním státě, mohou být zdaněny v tomto druhém státě. 2. Licenční poplatky uvedené v odstavci 3a) mohou být však zdaněny také ve smluvním státě, ve kterém je jejich zdroj, a to podle právních předpisů tohoto státu. Daň takto stanovená však nemůže přesáhnout 10 % z hrubé částky licenčních poplatků. Příslušné úřady smluvních států stanoví ve vzájemné dohodě způsob uplatnění tohoto omezení. 3. Výraz "licenční poplatky" použitý v tomto článku označuje náhrady jakéhokoli druhu placené za užití nebo za přivolení k užití: a) patentu, ochranné známky, vzoru nebo modelu, plánu, tajného vzorce nebo výrobního postupu nebo průmyslového, obchodního nebo vědeckého zařízení, nebo za informace, které se vztahují na zkušenosti nabyté v oblasti průmyslové, obchodní nebo vědecké; b) p …

Audit package hash: `8c479a06d46bb16470addfc0019418b59aa830b97d38ec9c6a8cdfe99e2454bc`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## HK — Hongkong (STANDARD)

Base treaty: **49/2012 Sb.m.s.** (`SRC-D025022024F9F174`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 5.0% | 5.0%: beneficial_owner == true |
| interest | 11 | 0.0% | 0.0%: beneficial_owner == true |
| royalty | 12 | 10.0% | 10.0%: beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-HK-MLI-WHT-PPT`; candidate WHT date `2024-01-01`. Article 8 adds no overlay.

Language: authentic `['cs', 'zh', 'en']`; prevailing `english`; evidence `existing_repository_language_record`; signature clause `None`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-D025022024F9F174](https://e-sbirka.gov.cz/sm/2012/49/0000-00-00).

Candidate excerpts:

- dividend Article 10: DIVIDENDY 1. Dividendy vyplácené společností, která je rezidentem jedné smluvní strany, rezidentu druhé smluvní strany, mohou být zdaněny v této druhé straně. 2. Tyto dividendy však mohou být rovněž zdaněny ve smluvní straně, jejíž je společnost, která je vyplácí, rezidentem, a to podle právních předpisů této strany, avšak jestliže skutečný vlastník dividend je rezidentem druhé smluvní strany, daň takto uložená nepřesáhne 5 procent hrubé částky dividend. Příslušné úřady smluvních stran upraví vzájemnou dohodou způsob aplikace tohoto omezení. Tento odstavec se nedotýká zdanění zisků společnosti, z nichž jsou dividendy vypláceny. 3. Výraz „dividendy“ použitý v tomto článku označuje příjmy z akcií, požitkových akcií nebo požitkových práv, kuksů, zakladatelských podílů nebo jiných práv, s výjimkou pohledávek, s podílem na zisku, jakož i jiné příjmy, které jsou podrobeny stejnému daňovému rež …
- interest Article 11: ÚROKY 1. Úroky mající zdroj v jedné smluvní straně a skutečně vlastněné rezidentem druhé smluvní strany podléhají zdanění jen v této druhé straně. 2. Výraz „úroky“ použitý v tomto článku označuje příjmy z pohledávek jakéhokoliv druhu, ať zajištěných či nezajištěných zástavním právem na nemovitosti a majících či nemajících právo účasti na zisku dlužníka, a zvláště, příjmy z vládních cenných papírů a příjmy z obligací nebo dluhopisů, včetně prémií a výher, které se vážou k těmto cenným papírům, obligacím nebo dluhopisům. Penále ukládané za pozdní platbu se nepovažuje za úroky pro účely tohoto článku. Výraz „úroky“ nezahrnuje žádnou část příjmu, která je považována za dividendu podle ustanovení článku 10 odstavce 3. 3. Ustanovení odstavce 1 se nepoužijí, jestliže skutečný vlastník úroků, který je rezidentem jedné smluvní strany, vykonává v druhé smluvní straně, ve které mají úroky zdroj, sv …
- royalty Article 12: LICENČNÍ POPLATKY 1. Licenční poplatky mající zdroj v jedné smluvní straně a vyplácené rezidentu druhé smluvní strany mohou být zdaněny v této druhé straně. 2. Tyto licenční poplatky však mohou být rovněž zdaněny ve smluvní straně, ve které mají zdroj, a to podle právních předpisů této strany, avšak jestliže skutečný vlastník licenčních poplatků je rezidentem druhé smluvní strany, daň takto uložená nepřesáhne 10 procent hrubé částky licenčních poplatků. Příslušné úřady smluvních stran upraví vzájemnou dohodou způsob aplikace tohoto omezení. 3. Výraz „licenční poplatky“ použitý v tomto článku označuje platby jakéhokoliv druhu obdržené jako náhrada za užití nebo za právo na užití jakéhokoliv autorského práva k dílu literárnímu, uměleckému nebo vědeckému, včetně kinematografických filmů nebo filmů nebo pásek používaných pro rozhlasové nebo televizní vysílání, jakéhokoliv patentu, ochranné z …

Audit package hash: `b969e3015c947fa320292130036e5e8d10c96963473a0ad116a4662fa92450d8`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## HR — Chorvatsko (ELEVATED)

Base treaty: **42/2000 Sb.m.s.** (`SRC-2026EC8F5E96A9CC`).

Risk focus: material_protocol_overlay.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 5.0% | 5.0%: beneficial_owner == true |
| interest | 11 | 0.0% | 0.0%: beneficial_owner == true |
| royalty | 12 | 10.0% | 10.0%: beneficial_owner == true |

Protocol/status: `protocol_effect_candidate_consolidated` / `not_listed`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-HR-MLI-WHT-PPT`; candidate WHT date `2022-01-01`. Article 8 adds no overlay.

Language: authentic `['Czech', 'Croatian', 'English']`; prevailing `english_prevails_czech_croatian_divergence`; evidence `official_source_candidate_evidence`; signature clause `Dáno v Praze dne 22. 1. 1999 ve dvou puvodnõch vyhotovenõch, kazdé v jazyce ceském, chorvatském
a anglickém, pricemz vsechny texty jsou autentické. V prõpade jakéhokoliv rozdõlu mezi ceským a chorvatským
textem bude rozhodujõcõm anglický text.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-2026EC8F5E96A9CC](https://e-sbirka.gov.cz/sm/2000/42/0000-00-00); `CZ-MF-HR-FF7645967F85`.

Candidate excerpts:

- dividend Article 10: Dividendy 1. Dividendy vyplácené spolecnostõ, která je rezidentem jednoho smluvnõho státu, rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto dividendy vsak mohou být rovnez zdaneny ve smluvnõm státe, jehoz je spolecnost, která je vyplácõ, rezidentem, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk dividend je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne 5 procent hrubé cástky dividend. Přõslusné úrady smluvnõch státu upravõ vzájemnou dohodou zpusob aplikace tohoto omezenõ. Tento odstavec se nedotýká zdanenõ zisku spolecnosti, z nichz jsou dividendy vypláceny. 3. Výraz 1dividendya pouzitý v tomto clánku oznacuje prõjmy z akciõ nebo jiných práv, s výjimkou pohle- dávek, s podõlem na zisku, jakoz i jiné prõjmy, které jsou podrobeny stejnému danovému rezimu jako prõjmy z akciõ podle právnõch predpisu státu, jehoz …
- interest Article 11: Uroky 1. Uroky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu podléhajõ zdanenõ jen v tomto druhém státe, jestlize tento rezident je skutecným vlastnõkem úroku. 2. Výraz 1úrokya pouzitý v tomto clánku oznacuje prõjmy z pohledávek jakéhokoliv druhu, at' zajistených, ci nezajistených zástavnõm právem na nemovitosti nebo majõcõch, ci nemajõcõch právo úcasti na zisku dluznõka, a zvláste, prõjmy z vládnõch cenných papõru a prõjmy z obligacõ nebo dluhopisu, vcetne prémiõ a výher, které se vázou k temto cenným papõrum, obligacõm nebo dluhopisum. Penále ukládané za pozdnõ platbu se nepovazuje za úroky pro úcely tohoto clánku. 3. Ustanovenõ odstavce 1 se nepouzijõ, jestlize skutecný vlastnõk úroku, který je rezidentem jednoho smluv- nõho státu, vykonává v druhém smluvnõm státe, ve kterém majõ úroky zdroj, prumyslovou nebo obchodnõ cinnost prostrednictvõm stálé  …
- royalty Article 12: Licencnõ poplatky 1. Licencnõ poplatky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto licencnõ poplatky vsak mohou být rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk licencnõch poplatku je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne 10 procent hrubé cástky licencnõch poplatku. Přõslusné úrady smluvnõch státu upravõ vzájemnou dohodou zpusob aplikace tohoto omezenõ. 3. Výraz 1licencnõ poplatkya pouzitý v tomto clánku oznacuje platby jakéhokoliv druhu obdrzené jako náhrada za uzitõ nebo za právo na uzitõ jakéhokoliv autorského práva k dõlu literárnõmu, umeleckému nebo vedeckému, vcetne kinematografických filmu, filmu nebo pásek nebo jiných prostredku reprodukce pro roz- hlasové nebo televiznõ vysõlánõ, jaké …

Audit package hash: `1d7760be8da657cfbdc3ea0225601563acdd46143d33425b0128438e5a60b6cc`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## HU — Maďarsko (STANDARD)

Base treaty: **22/1995 Sb.** (`SRC-21BEA9C0DA4A502D`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 5%, 15% | 5%: recipient_entity_type == company, direct_ownership == true, ownership_percent >= 25, beneficial_owner == true; 15%: fallback_case == all_other_cases, beneficial_owner == true |
| interest | 11 | 0.0% | 0.0%: beneficial_owner == true |
| royalty | 12 | 10.0% | 10.0%: beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-HU-MLI-WHT-PPT`; candidate WHT date `2022-01-01`. Article 8 adds no overlay.

Language: authentic `['English']`; prevailing `sole_english`; evidence `current_official_pdf_signature_clause_candidate`; signature clause `Dano ve dvojim vyhotovenf v Praze dne 14. ledna 1993 v anglickém jazyce.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-21BEA9C0DA4A502D](https://e-sbirka.gov.cz/sb/1995/22/0000-00-00).

Candidate excerpts:

- dividend Article 10: Dividendy 1. Dividendy vyplácené spolecnostõ, která je rezi- dentem v jednom smluvnõm státe, osobe, která je rezi- dentem v druhém smluvnõm státe, mohou být zdaneny v tomto druhém smluvnõm státe. 2. Tyto dividendy vsak mohou být rovnez zda- neny ve smluvnõm státe, v nemz je spolecnost, která je vyplácõ, rezidentem, a to podle právnõch predpisu tohoto státu, avsak jestlize prõjemce je skutecným vlastnõkem dividend, dan takto stanovená nepresáhne: a) 5 % hrubé cástky dividend, jestlize prõjemce je spolecnost, která prõmo vlastnõ nejméne 25 % majetku spolecnosti vyplácejõcõ dividendy; b) 15 % hrubé cástky dividend ve vsech ostatnõch prõpadech. Přõslusné úrady smluvnõch státu upravõ vzájemnou do- hodou zpu sob aplikace techto omezenõ. Tento odstavec se nedotýká zdanenõ zisku spolec- nosti, ze kterých jsou dividendy vypláceny. 3. Výraz 1dividendya, pouzitý v tomto clánku, oznacuje prõjmy z ak …
- interest Article 11: U roky 1. U roky majõcõ zdroj v jednom smluvnõm státe, které pobõrá rezident druhého smluvnõho státu a který je jejich skutecným vlastnõkem, podléhajõ zdanenõ pou- ze v tomto druhém státe. 2. Výraz 1úrokya, pouzitý v tomto clánku, ozna- cuje prõjmy z pohledávek jakéhokoliv druhu zajiste- ných i nezajistených zástavnõm právem na nemovi- tosti nebo majõcõch nebo ne právo úcasti na zisku dluz- nõka, a zvláste, prõjmy z vládnõch cenných papõru a prõjmy z obligacõ nebo dluhopisu vcetne prémiõ a odmen spojených s temito cennými papõry, obliga- cemi nebo dluhopisy. 3. Ustanovenõ odstavce 1 se nepouzije, jestlize skutecný vlastnõk úroku , který je rezidentem v jed- nom smluvnõm státe, vykonává v druhém smluvnõm státe, ve kterém majõ úroky zdroj, pru myslovou nebo obchodnõ cinnost prostrednictvõm stálé provozovny, která je tam umõstena, nebo nezávislé povolánõ pro- strednictvõm stálé základny tam …
- royalty Article 12: Licencnõ poplatky 1. Licencnõ poplatky, majõcõ zdroj v jednom smluvnõm státe, vyplácené rezidentu druhého smluv- nõho státu, mohou být zdaneny v tomto druhém státe. 2. Avsak takové licencnõ poplatky mohou být také zdaneny ve smluvnõm státe, ve kterém je jejich zdroj, a v souladu s právnõmi predpisy tohoto státu, avsak je- -li prõjemce skutecným vlastnõkem licencnõch poplat- ku , cástka dane takto stanovená nepresáhne 10 % hrubé cástky z licencnõch poplatku . Přõslusné úrady smluvnõch státu upravõ vzájemnou dohodou zpu sob aplikace techto omezenõ. 3. Výraz 1licencnõ poplatkya pouzitý v tomto clánku oznacuje platby jakéhokoliv druhu obdrzené jako náhrada za uzitõ nebo za právo na uzitõ autor- ského práva k dõlu literárnõmu, umeleckému nebo ve- deckému vcetne kinematografických filmu , a filmu nebo nahrávek pro televiznõ nebo rozhlasové vysõlánõ, jakéhokoliv patentu, ochranné známky, návrhu …

Audit package hash: `337ec1fcd922a997bde36b07107349193f17e378137e7386d5b51fb6ffd329b2`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## ID — Indonésie (STANDARD)

Base treaty: **67/1996 Sb.** (`SRC-98C2BE2C9B6D6F49`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 10.0%, 15.0% | 10.0%: recipient_entity_type == company_other_than_partnership, direct_ownership >= 20%, beneficial_owner == true; 15.0%: fallback_case == all_other_cases, beneficial_owner == true |
| interest | 11 | 0.0%, 12.5% | 0.0%: recipient_entity_type == government_including_local_authority_central_bank_or_other_government_controlled_financial_institution, beneficial_owner == true; 12.5%: fallback_case == all_other_cases, beneficial_owner == true |
| royalty | 12 | 12.5% | 12.5%: beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-ID-MLI-WHT-PPT`; candidate WHT date `2027-01-01`. Article 8 adds no overlay.

Language: authentic `None`; prevailing `None`; evidence `hash_bound_repository_signature_clause_candidate`; signature clause `Dáno ve dvojõm vyhotovenõ v Jakarte dne 4. rõjna
1994 v anglickém jazyce.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-98C2BE2C9B6D6F49](https://e-sbirka.gov.cz/sb/1996/67/0000-00-00).

Candidate excerpts:

- dividend Article 10: Dividendy 1. Dividendy vyplácené spolecnostõ, která je rezi- dentem v jednom smluvnõm státe, osobe, která je rezi- dentem v druhém smluvnõm státe, mohou být zdaneny v tomto druhém smluvnõm státe. 2. Tyto dividendy vsak mohou být rovnez zda- neny ve smluvnõm státe, v nemz je spolecnost, která je vyplácõ, rezidentem, a to podle právnõch predpisu tohoto státu, avsak jestlize prõjemce je skutecným vlast- nõkem dividend, dan takto stanovená nepresáhne: a) 10 % hrubé cástky dividend, jestlize skutecným vlastnõkem je spolecnost (jiná nez osobnõ spolec- nost), která prõmo vlastnõ nejméne 20 % majetku spolecnosti vyplácejõcõ dividendy; b) 15 % hrubé cástky dividend ve vsech ostatnõch prõpadech. Přõslusné úrady smluvnõch státu stanovõ vzájemnou do- hodou zpu sob aplikace techto omezenõ. 3. Ustanovenõ odstavce 2 se nedotkne zdan ovánõ spolecnostõ ze zisku , z nichz jsou dividendy vypláceny. 4. Výra …
- interest Article 11: U roky 1. U roky majõcõ zdroj v jednom smluvnõm státe, které pobõrá rezident druhého smluvnõho státu, mohou být zdaneny v tomto druhém státe. 2. Avsak takovéto úroky mohou být zdaneny rovnez ve smluvnõm státe, v nemz majõ zdroj, podle právnõch predpisu tohoto státu, ale pokud prõjemce je skutecným vlastnõkem úroku , dan takto ulozená nepre- sáhne 12,5 % hrubé cástky úroku . Přõslusné úrady smluvnõch státu stanovõ vzájemnou do- hodou zpu sob aplikace tohoto omezenõ. 3. Bez ohledu na ustanovenõ odstavce 2 úroky, které majõ zdroj v jednom smluvnõm státe a které po- bõrá vláda druhého smluvnõho státu vcetne mõstnõch orgánu tohoto státu, centrálnõ banky nebo jakéhokoliv jiného financnõho ústavu kontrolovaného touto vládou, budou vyn aty ze zdanenõ v prvne zmõneném státe. 4. Pro úcely odstavce 3 výrazy 1centrálnõ bankaa a 1financnõ ústav kontrolovaný vládoua znamenajõ: a) V prõpade Indonésie:  …
- royalty Article 12: Licencnõ poplatky 1. Licencnõ poplatky majõcõ zdroj v jednom smluvnõm státe, vyplácené rezidentu druhého smluv- nõho státu, mohou být zdaneny v tomto druhém státe. 2. Avsak takové licencnõ poplatky mohou být také zdaneny ve smluvnõm státe, ve kterém je jejich zdroj, a v souladu s právnõmi predpisy tohoto státu, avsak je-li prõjemce skutecným vlastnõkem licencnõch poplatku , cástka dane takto stanovená nepresáhne 12,5 % hrubé cástky z licencnõch poplatku . Přõslusné úrady smluv- nõch státu upravõ vzájemnou dohodou zpu sob aplikace tohoto omezenõ. 3. Výraz 1licencnõ poplatkya, pouzitý v tomto clánku, oznacuje platby jakéhokoliv druhu obdrzené jako náhrada za uzitõ nebo za právo na uzitõ jakéhoko- liv autorského práva k literárnõmu, umeleckému nebo vedeckému dõlu vcetne kinematografických filmu nebo filmu a pásek pro rozhlasové a televiznõ vysõlánõ, jaké- hokoliv patentu, ochranné známky, n …

Audit package hash: `189c8e2574f58a59ebe1e82c13ac4879db09801d1fb0f58deabdf4e746ec8797`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## IE — Irsko (STANDARD)

Base treaty: **163/1996 Sb.** (`SRC-DC652FA09D142B61`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 5%, 15% | 5%: recipient_entity_type == company, direct_ownership == true, voting_ownership >= 25, beneficial_owner == true; 15%: fallback_case == all_other_cases, beneficial_owner == true |
| interest | 11 | 0.0% | 0.0%: beneficial_owner == true |
| royalty | 12 | 10.0% | 10.0%: beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-IE-MLI-WHT-PPT`; candidate WHT date `2021-01-01`. Article 8 adds no overlay.

Language: authentic `None`; prevailing `None`; evidence `hash_bound_repository_signature_clause_candidate`; signature clause `Dáno ve dvojõm vyhotovenõ v Praze dne 14. listo-
padu 1995 v ceském a anglickém jazyce, pricemz obe
znenõ majõ stejnou platnost.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-DC652FA09D142B61](https://e-sbirka.gov.cz/sb/1996/163/0000-00-00).

Candidate excerpts:

- dividend Article 10: Dividendy 1. Dividendy vyplácené spolecnostõ, která je rezi- dentem v jednom smluvnõm státe, osobe, která je rezi- dentem v druhém smluvnõm státe, mohou být zdaneny v tomto druhém státe. 2. Tyto dividendy vsak mohou být rovnez zda- neny ve smluvnõm státe, v nemz je spolecnost, která je vyplácõ, rezidentem, a to podle právnõch predpisu tohoto státu, avsak jestlize prõjemce je skutecným vlastnõkem dividend, dan takto stanovená nepresáhne: a) 5 % hrubé cástky dividend, jestlize prõjemce je spolecnost, která prõmo vlastnõ nejméne 25 % podõlu s hlasovacõm právem spolecnosti vypláce- jõcõ dividendy; b) 15 % hrubé cástky dividend ve vsech ostatnõch prõpadech. Přõslusné úrady smluvnõch státu upravõ vzájemnou do- hodou zpu sob aplikace techto omezenõ. Tento odstavec se nedotýká zdanenõ zisku spolecnosti, ze kterých jsou dividendy vypláceny. 3. Výraz 1dividendya pouzitý v tomto clánku oznacuje prõ …
- interest Article 11: U roky 1. U roky majõcõ zdroj v jednom smluvnõm státe a vyplácené osobe, která je rezidentem v druhém smluvnõm státe, budou zdaneny pouze v tomto dru- hém státe, pokud je tento rezident skutecným vlastnõ- kem úroku . 2. Výraz 1úrokya pouzitý v tomto clánku ozna- cuje prõjmy z pohledávek jakéhokoliv druhu, zajiste- ných i nezajistených zástavnõm právem na nemovitosti nebo dolozkou o úcasti na zisku dluznõka a obzvláste prõjmy z vládnõch cenných papõru a prõjem z obligacõ a dluhopisu vcetne prémiõ a výher spojených s temito cennými papõry, obligacemi nebo dluhopisy a rovnez veskerými dalsõmi prõjmy, které patrõ mezi prõjmy z pu jcených penez podle práva toho státu, v nemz je jejich zdroj, avsak nezahrnuje jakýkoli prõjem, který je povazován za dividendu podle clánku 10. 3. Ustanovenõ odstavce 1 se nepouzije, jestlize skutecný vlastnõk úroku , který je rezidentem v jed- nom smluvnõm státe,  …
- royalty Article 12: Licencnõ poplatky 1. Licencnõ poplatky majõcõ zdroj v jednom smluvnõm státe vyplácené rezidentu druhého smluv- nõho státu mohou být zdaneny v tomto druhém státe. 2. Takové licencnõ poplatky vsak mohou být rov- nez zdaneny ve smluvnõm státe, ve kterém je jejich zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize je prõjemce skutecným vlastnõkem licenc- nõch poplatu , nepresáhne dan takto stanovená 10 % z hrubé cástky licencnõch poplatku . Přõslusné úrady smluvnõch státu upravõ vzájemnou dohodou zpu sob aplikace tohoto omezenõ. 3. Výraz 1licencnõ poplatkya pouzitý v tomto clánku oznacuje platby jakéhokoli druhu obdrzené jako náhrada za uzitõ nebo právo na uzitõ jakéhokoli autorského práva k literárnõmu, umeleckému nebo ve- deckému dõlu (vcetne kinematografických filmu nebo filmu a pásek nebo jiných prostredku uzõvaných pro rozhlasové a televiznõ vysõlánõ), jakéhokoli patentu,  …

Audit package hash: `e8f00a9678ea77d9739fe137fb44f56fdaf735045ccc5b45079b2a53fec30531`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____
