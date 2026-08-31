# CZ country legal-QA review batch 02

> Machine-prepared candidate evidence only. No country or scope in this file has been human reviewed, approved, verified, or released.

## BE — Belgie (ELEVATED)

Base treaty: **95/2000 Sb.m.s.** (`SRC-E16828A7660D9797`).

Risk focus: material_protocol_overlay, multiple_historical_instruments.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 5%, 15% | 5%: recipient_entity_type == company, ownership_percent >= 25, beneficial_owner == true; 15%: fallback_case == all_other_cases, beneficial_owner == true |
| interest | 11 | 0.0%, 10.0% | 10.0%: beneficial_owner == true; 0.0%: article_11_3_exemption == trade_receivable_or_public_export_credit_or_bank_loan_or_bank_deposit_or_government_subnational_or_local_authority, beneficial_owner == true |
| royalty | 12 | 0.0%, 5.0% | 0.0%: royalty_category == copyright_literary_artistic_scientific_including_cinematographic_films_and_broadcast_media, beneficial_owner == true; 5.0%: royalty_category == software_patent_trademark_design_model_plan_secret_formula_process_knowhow_or_industrial_commercial_scientific_equipment, beneficial_owner == true |

Protocol/status: `protocol_effect_candidate_consolidated` / `not_listed`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-BE-MLI-WHT-PPT`; candidate WHT date `2021-01-01`. Article 8 adds no overlay.

Language: authentic `['English']`; prevailing `sole_english`; evidence `official_source_candidate_evidence`; signature clause `Dáno v Bruselu dne 16. prosince 1996 ve dvou puvodnõch vyhotovenõch v anglickém jazyce.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-E16828A7660D9797](https://e-sbirka.gov.cz/sm/2000/95/0000-00-00); `CZ-MF-BE-D0E145875613`.

Candidate excerpts:

- dividend Article 10: DIVIDENDY 1. Dividendy vyplácené spolecnostõ, která je rezidentem jednoho smluvnõho státu, rezidentu druhého smluvnõho státu mohou být zdaneny v tomo druhém státe. 2. Tyto dividendy vsak mohou být rovnez zdaneny ve smluvnõm státe, jehoz je spolecnost, která je vyplácõ, rezidentem, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk dividend je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne: a) 5 procent hrubé cástky dividend, jestlize skutecným vlastnõkem je spolecnost, vcetne osobnõ spolecnosti, která prõmo nebo neprõmo vlastnõ nejméne 25 procent jmenõ spolecnosti vyplácejõcõ dividendy; b) 15 procent hrubé cástky dividend ve vsech ostatnõch prõpadech. Tento odstavec se nedotýká zdanenõ zisku spolecnosti, z nichz jsou dividendy vypláceny. 3. Výraz 1dividendya pouzitý v tomto clánku oznacuje prõjmy z akciõ, pozitkových akciõ nebo pozitkových práv, …
- interest Article 11: UROKY 1. Uroky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto úroky vsak mohou být rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk úroku je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne 10 procent hrubé cástky úroku. 3. Bez ohledu na ustanovenõ odstavce 2 budou úroky osvobozeny od zdanenõ ve smluvnõm státe, v nemz majõ zdroj, jestlize to jsou: a) úroky z obchodnõch pohledávek ± vcetne pohledávek predstavovaných obchodnõmi cennými papõry ± vy- plývajõcõ z odlozených plateb za zbozõ nebo sluzby poskytované podnikem; b) úroky placené z duvodu pujcky nebo úveru, které jsou poskytovány, garantovány nebo pojist'ovány ve- rejnými subjekty, jejichz cõlem je podpora exportu; c) úroky z pujcek jakéhokoliv druhu ± nep …
- royalty Article 12: LICENČNI POPLATKY 1. Licencnõ poplatky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto licencnõ poplatky vsak mohou být rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk licencnõch poplatku je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne: a) 5 procent hrubé cástky licencnõch poplatku placených za uzitõ nebo za právo na uzitõ jakéhokoliv pru- myslového, obchodnõho nebo vedeckého zarõzenõ; b) 10 procent hrubé cástky licencnõch poplatku placených za uzitõ nebo za právo na uzitõ jakéhokoliv autor- ského práva k dõlu literárnõmu, umeleckému nebo vedeckému, vcetne kinematografických filmu a filmu nebo nahrávek pro televiznõ nebo rozhlasové vysõlánõ, jakéhokoliv softwaru, patentu, ochranné známky, návrhu nebo modelu …

Audit package hash: `c8e49524ffd637ad72745f2c7785231542196d428fba39a8a48bb36e4acebcaa`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## BG — Bulharsko (STANDARD)

Base treaty: **203/1999 Sb.** (`SRC-0E071DC9C81B5E19`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 10.0% | 10.0%: beneficial_owner == true |
| interest | 11 | 0.0%, 10.0% | 10.0%: beneficial_owner == true; 0.0%: article_11_3_exemption == government_local_authority_central_bank_or_wholly_government_owned_financial_institution_or_other_article_11_3_qualifying_case, beneficial_owner == true |
| royalty | 12 | 10.0% | 10.0%: beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-BG-MLI-WHT-PPT`; candidate WHT date `2023-01-01`. Article 8 adds no overlay.

Language: authentic `None`; prevailing `None`; evidence `hash_bound_repository_signature_clause_candidate`; signature clause `Dáno v Sofii dne 9. dubna 1998 ve dvou pu vod-
nõch vyhotovenõch, kazdé v jazyce ceském, bulharském
a anglickém, pricemz vsechny texty jsou autentické.
V prõpade jakéhokoliv rozdõlu bude rozhodujõcõm ang-
lický text.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-0E071DC9C81B5E19](https://e-sbirka.gov.cz/sb/1999/203/0000-00-00).

Candidate excerpts:

- dividend Article 10: Dividendy 1. Dividendy vyplácené spolecnostõ, která je rezi- dentem jednoho smluvnõho státu, rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto dividendy vsak mohou být rovnez zda- neny ve smluvnõm státe, jehoz je spolecnost, která je vyplácõ, rezidentem, a to podle právnõch predpisu to- hoto státu, avsak jestlize skutecný vlastnõk dividend je rezidentem druhého smluvnõho státu, dan takto ulo- zená nepresáhne 10 procent hrubé cástky dividend. Přõslusné úrady smluvnõch státu upravõ vzájemnou do- hodou zpu sob aplikace tohoto omezenõ. Tento odstavec se nedotýká zdanenõ zisku spolecnosti, z nichz jsou dividendy vypláceny. 3. Výraz 1dividendya pouzitý v tomto clánku oznacuje prõjmy z akciõ nebo jiných práv, s výjimkou pohledávek, s podõlem na zisku, jakoz i jiné prõjmy, které jsou podrobeny stejnému dan ovému rezimu jako prõjmy z akciõ podle právnõch predpisu s …
- interest Article 11: U roky 1. U roky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto úroky vsak mohou být rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk úroku je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne 10 procent hrubé cástky úroku . Přõslusné úrady smluvnõch státu upravõ vzájemnou do- hodou zpu sob aplikace tohoto omezenõ a omezenõ uve- dených v odstavci 3. 3. Bez ohledu na ustanovenõ odstavce 2 jsou úroky osvobozeny od zdanenõ ve smluvnõm státe, ve kterém majõ zdroj, jestlize jsou: a) pobõrané a skutecne vlastnené: (i) vládou druhého smluvnõho státu, vcetne jaké- hokoliv mõstnõho úradu tohoto státu, cen- trálnõ banky nebo jakékoliv financnõ instituce, kterou zcela vlastnõ tato vláda; nebo (ii) rezidentem druhého smluvn …
- royalty Article 12: Licencnõ poplatky 1. Licencnõ poplatky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluv- nõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto licencnõ poplatky vsak mohou být rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk licencnõch poplatku je rezidentem druhého smluvnõho státu, dan takto ulozená nepre- sáhne 10 procent hrubé cástky licencnõch poplatku . Přõslusné úrady smluvnõch státu upravõ vzájemnou do- hodou zpu sob aplikace tohoto omezenõ. 3. Výraz 1licencnõ poplatkya pouzitý v tomto clánku oznacuje platby jakéhokoliv druhu obdrzené jako náhrada za uzitõ nebo za právo na uzitõ jakéhoko- liv autorského práva k dõlu literárnõmu, umeleckému nebo vedeckému, vcetne kinematografických filmu a filmu , nahrávek nebo disku pro televiznõ nebo roz- hlasové vysõlánõ, jakéhokoliv pate …

Audit package hash: `4bc8a0b96d972d6ef9b0f4269daab55374bb888081dc4d3df98953270ef1757d`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## BH — Bahrajn (STANDARD)

Base treaty: **59/2012 Sb.m.s.** (`SRC-023262E3EBEE0E28`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 5.0% | 5.0%: beneficial_owner == true |
| interest | 11 | 0.0% | 0.0%: beneficial_owner == true |
| royalty | 12 | 10.0% | 10.0%: beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-BH-MLI-WHT-PPT`; candidate WHT date `2025-01-01`. Article 8 adds no overlay.

Language: authentic `['Czech', 'Arabic', 'English']`; prevailing `english_prevails_all_text_divergences`; evidence `current_official_pdf_signature_clause_candidate`; signature clause `Dano v Praze dne 24. kvétna 2011 ve dvou ptivodnich vyhotovenich, v éeském, arabském a anglickém jazyce, pYitemZ vSechny tii texty jsou autentické. V pripadé jakéhokoliv rozdilu bude rozhodujicim anglicky text.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-023262E3EBEE0E28](https://e-sbirka.gov.cz/sm/2012/59/0000-00-00).

Candidate excerpts:

- dividend Article 10: DIVIDENDY 1. Dividendy vyplácené společností, která je rezidentem jednoho smluvního státu, rezidentu druhého smluvního státu, mohou být zdaněny v tomto druhém státě. 2. Tyto dividendy však mohou být rovněž zdaněny ve smluvním státě, jehož je společnost, která je vyplácí, rezidentem, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník dividend je rezidentem druhého smluvního statu, daň takto uložená nepřesáhne pět procent hrubé částky dividend. Příslušné úřady smluvních států upraví vzájemnou dohodou způsob aplikace tohoto omezení. Tento odstavec se nedotýká zdanění zisků společnosti, z nichž jsou dividendy vypláceny. 3. Výraz „dividendy“ použitý v tomto článku označuje příjmy z akcií nebo jiných práv, s výjimkou pohledávek, s podílem na zisku, jakož i jiné příjmy, které jsou podrobeny stejnému daňovému režimu jako příjmy z akcií podle právních předpisů státu, jeho …
- interest Article 11: PŘÍJMY Z POHLEDÁVEK 1. Příjmy z pohledávek mající zdroj v jednom smluvním státě a skutečně vlastněné rezidentem druhého smluvního státu podléhají zdanění jen v tomto druhém státě. 2. Výraz „příjmy z pohledávek“ použitý v tomto článku označuje příjmy z pohledávek jakéhokoliv druhu, ať zajištěných či nezajištěných zástavním právem na nemovitosti a majících či nemajících právo účasti na zisku dlužníka, a zvláště, příjmy z vládních cenných papírů a příjmy z obligací nebo dluhopisů, včetně prémií a výher, které se vážou k těmto cenným papírům, obligacím nebo dluhopisům. Penále ukládané za pozdní platbu se nepovažuje za příjem z pohledávky pro účely tohoto článku. Výraz „příjmy z pohledávek“ nezahrnuje žádnou část příjmu, která je považována za dividendu podle ustanovení článku 10 odstavce 3. 3. Ustanovení odstavce 1 se nepoužijí, jestliže skutečný vlastník příjmů z pohledávky, který je rezide …
- royalty Article 12: LICENČNÍ POPLATKY 1. Licenční poplatky mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu mohou být zdaněny v tomto druhém státě. 2. Tyto licenční poplatky však mohou být rovněž zdaněny ve smluvním státě, v němž mají zdroj, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník licenčních poplatků je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne deset procent hrubé částky licenčních poplatků. Příslušné úřady smluvních států upraví vzájemnou dohodou způsob aplikace tohoto omezení. 3. Výraz „licenční poplatky“ použitý v tomto článku označuje platby jakéhokoliv druhu obdržené jako náhrada za užití nebo za právo na užití jakéhokoliv autorského práva k dílu literárnímu, uměleckému nebo vědeckému, včetně kinematografických filmů a filmů nebo pásek pro televizní nebo rozhlasové vysílání, jakéhokoliv patentu, ochranné známky …

Audit package hash: `0421757bc10a86c08d23b4901c18752b82bda416c1ddc2e59c6ea57ee6617afa`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## BR — Brazílie (STANDARD)

Base treaty: **200/1991 Sb.** (`SRC-49610CA90840987F`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 15.0% | 15.0%: beneficial_owner == true |
| interest | 11 | 0.0%, 10.0%, 15.0% | 0.0%: article_11_3a_exemption == interest_paid_to_other_state_government_political_subdivision_or_government_owned_agency_including_financial_institution_unless_11_3b_applies; 10.0%: loan_or_credit_provider == bank, minimum_term_years >= 10, purpose == industrial_equipment_sale_or_study_installation_furnishing_of_industrial_or_scientific_units_or_public_works, beneficial_owner == true; 15.0%: fallback_case == all_other_cases, beneficial_owner == true |
| royalty | 12 | 15.0%, 25.0% | 25.0%: royalty_category == trademark, beneficial_owner == true; 15.0%: fallback_case == all_other_royalties, beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `not_listed`; modification `None`; candidate WHT date `None`. Article 8 adds no overlay.

Language: authentic `None`; prevailing `None`; evidence `hash_bound_repository_signature_clause_candidate`; signature clause `Dáno v Brasõlii, dne 26. srpna 1986, ve dvou vyho-
tovenõch, kazdé v jazyce ceském, portugalském a an-
glickém, pricemz vsechna tri znenõ majõ stejnou plat-
nost. V prõpade jakýchkoliv rozdõlnostõ výkladu bude
rozhodujõcõ anglický text.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: No current WHT-relevant MLI PPT effect record.

Official sources: [SRC-49610CA90840987F](https://e-sbirka.gov.cz/sb/1991/200/0000-00-00).

Candidate excerpts:

- dividend Article 10: Dividendy 1. Dividendy vyplácené spolecnostõ, která je rezi- dentem v jednom smluvnõm státe, osobe, která je rezi- dentem ve druhém smluvnõm státe, mohou být zdane- ny v tomto druhém státe. 2. Tyto dividendy vsak mohou být zdaneny ve smluvnõm státe, v nemz má sõdlo spolecnost, která je vyplácõ, a to podle právnõch predpisu tohoto státu, avsak jestlize prõjemce je skutecným vlastnõkem divi- dend, dan takto stanovená nemu ze presáhnout 15 % hrubé cástky dividend. Tento odstavec se nedotýká zdanenõ zisku spolec- nosti, které slouzõ k výplate dividend. 3. Ustanovenõ odstavcu 1 a 2 se nepouzijõ, jestlize vlastnõk dividend, který je rezidentem v jednom smluv- nõm státe, vykonává ve druhém smluvnõm státe, v nemz je rezidentem spolecnost vyplácejõcõ dividendy, pru - myslovou nebo obchodnõ cinnost prostrednictvõm stálé provozovny, která je tam umõstena, nebo svobodné po- volánõ prostrednictvõm st …
- interest Article 11: U roky 1. U roky majõcõ zdroj v jednom smluvnõm státe a vyplácené osobe, která je rezidentem v druhém smluvnõm státe, mohou být zdaneny v tomto druhém státe. 2. Takové úroky vsak mohou být zdaneny také ve smluvnõm státe, ve kterém je jejich zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize prõjemce je skutecným vlastnõkem úroku , dan takto ukládaná nepresáhne: a) 10 %, pokud jde o pu jcky a úvery poskytované bankou na obdobõ nejméne 10 let ve spojenõ s pro- dejem pru myslového zarõzenõ nebo studie, instala- cõ nebo vybavenõm pru myslových nebo vedeckých jednotek a ve spojenõ s verejnými pracemi; b) 15 % hrubé cástky úroku ve vsech ostatnõch prõpa- dech. 3. Bez ohledu na ustanovenõ odstavcu 1 a 2: a) úroky plynoucõ z jednoho smluvnõho státu a pla- cené vláde druhého smluvnõho státu, jeho správnõ- mu útvaru nebo jiné instituci (vcetne financnõ) ná- lezejõcõ této vláde nebo s …
- royalty Article 12: Licencnõ poplatky 1. Licencnõ poplatky majõcõ zdroj v jednom smluv- nõm státe a placené osobe, která je rezidentem v dru- hém smluvnõm státe, mohou být zdaneny v tomto dru- hém státe. 2. Tyto licencnõ poplatky mohou vsak být zdane- ny ve smluvnõm státe, ve kterém je jejich zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize prõjemce je skutecným vlastnõkem licencnõch poplatku , dan takto stanovená nepresáhne: a) 25 % hrubé cástky licencnõch poplatku za uzitõ ne- bo za právo na uzitõ ochranných známek; b) 15 % hrubé cástky licencnõch poplatku ve vsech ostatnõch prõpadech. 3. Výraz 1licencnõ poplatkya pouzitý v tomto clánku oznacuje platy jakéhokoli druhu, placené za uzitõ nebo za právo na uzitõ autorských práv k dõlu lite- rárnõmu, umeleckému nebo vedeckému (vcetne kine- matografických filmu , televiznõch nebo rozhlasových záznamu ), patentu , ochranných známek, návrhu nebo m …

Audit package hash: `8a7225f77ae5078458a5a6d9d38597bc5151561cbf48b219de2aa2c99c85ca68`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## BW — Botswana (STANDARD)

Base treaty: **49/2020 Sb.m.s.** (`SRC-906AECF6EEA9F28C`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 5.0% | 5.0%: beneficial_owner == true |
| interest | 11 | 0.0%, 7.5% | 7.5%: beneficial_owner == true; 0.0%: article_11_3_exemption == credit_sale_or_bank_loan_or_government_or_subnational_or_local_authority_or_central_bank_or_other_specified_public_financing, beneficial_owner == true |
| royalty | 12 | 7.5% | 7.5%: beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `not_listed`; modification `None`; candidate WHT date `None`. Article 8 adds no overlay.

Language: authentic `['cs', 'en']`; prevailing `equal`; evidence `existing_repository_language_record`; signature clause `None`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: No current WHT-relevant MLI PPT effect record.

Official sources: [SRC-906AECF6EEA9F28C](https://e-sbirka.gov.cz/sm/2020/49/0000-00-00).

Candidate excerpts:

- dividend Article 10: 1. Dividendy vyplácené společností, která je rezidentem jednoho smluvního státu, rezidentu druhého smluvního státu, mohou být zdaněny v tomto druhém státě. 2. Tyto dividendy však mohou být rovněž zdaněny ve smluvním státě, jehož je společnost, která je vyplácí, rezidentem, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník dividend je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 5 procent hrubé částky dividend. Příslušné úřady smluvních států upraví vzájemnou dohodou způsob aplikace tohoto omezení. Tento odstavec se nedotýká zdanění zisků společnosti, z nichž jsou dividendy vypláceny. 3. Výraz „dividendy“ použitý v tomto článku označuje příjmy z akcií, požitkových akcií nebo požitkových práv, kuksů, zakladatelských podílů nebo jiných práv, s výjimkou pohledávek, s podílem na zisku, jakož i jiné příjmy, které jsou podrobeny stejnému daňovému re …
- interest Article 11: 1. Úroky mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu mohou být zdaněny v tomto druhém státě. 2. Tyto úroky však mohou být rovněž zdaněny ve smluvním státě, v němž mají zdroj, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník úroků je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 7,5 procent hrubé částky úroků. 3. Úroky mající zdroj v jednom smluvním státě a skutečně vlastněné rezidentem druhého smluvního státu podléhají bez ohledu na ustanovení odstavce 2 zdanění jen v tomto druhém státě, jestliže jsou tyto úroky vypláceny: a) v souvislosti s prodejem jakéhokoliv zboží nebo zařízení na úvěr, b) z jakékoliv půjčky nebo úvěru jakéhokoliv druhu, kterou nebo který poskytla banka; c) vládě druhého smluvního státu, včetně jakéhokoliv nižšího správního útvaru nebo místního úřadu tohoto státu; d) centrální bance  …
- royalty Article 12: 1. Licenční poplatky a poplatky za technické služby mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu mohou být zdaněny v tomto druhém státě. 2. Tyto licenční poplatky a poplatky za technické služby však mohou být rovněž zdaněny ve smluvním státě,"v němž mají zdroj, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník licenčních poplatků nebo poplatků za technické služby je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 7,5 procent hrubé částky licenčních poplatků nebo poplatků za technické služby. Příslušné úřady smluvních států upraví vzájemnou dohodou způsob aplikace tohoto omezení. 3. a) Výraz „licenční poplatky“ použitý v tomto článku označuje platby jakéhokoliv druhu obdržené jako náhrada za užití nebo za právo na užití jakéhokoliv autorského práva k dílu literárnímu, uměleckému nebo vědeckému, včetně kinemat …

Audit package hash: `42d8630e491ddc4a1490318b78d7322496c2a6e0a78e6a77b64ada7680a86398`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## BY — Bělorusko (ELEVATED)

Base treaty: **31/1998 Sb.** (`SRC-9A8D6161227A3BB3`).

Risk focus: material_protocol_overlay, multiple_historical_instruments.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 5.0%, 10.0% | 5.0%: recipient_entity_type == company, minimum_ownership >= 25%, beneficial_owner == true; 10.0%: fallback_case == all_other_cases, beneficial_owner == true |
| interest | 11 | 0.0%, 5.0% | 5.0%: beneficial_owner == true; 0.0%: recipient_entity_type == government_or_central_bank, beneficial_owner == true |
| royalty | 12 | 10.0% | 10.0%: beneficial_owner == true |

Protocol/status: `protocol_effect_candidate_consolidated` / `article_application_suspended`.

MLI (WHT only): `not_listed`; modification `None`; candidate WHT date `None`. Article 8 adds no overlay.

Language: authentic `['Czech', 'Belarusian', 'English']`; prevailing `english_prevails_all_text_divergences`; evidence `official_source_candidate_evidence`; signature clause `Dáno v Praze dne 14. rõjna 1996 ve dvou pu vod-
nõch vyhotovenõch, kazdé v jazyce ceském, beloruském
a anglickém, pricemz vsechna tri znenõ jsou autentická.
V prõpade rozdõlnosti výkladu bude rozhodujõcõ ang-
lický text.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: No current WHT-relevant MLI PPT effect record.

Official sources: [SRC-9A8D6161227A3BB3](https://e-sbirka.gov.cz/sb/1998/31/0000-00-00); `CZ-MF-BY-852FD44A9622`; `CZ-MF-BY-9FB15934EDD7`.

Candidate excerpts:

- dividend Article 10: Dividendy 1. Dividendy vyplácené spolecnostõ, která je rezi- dentem jednoho smluvnõho státu, rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto dividendy vsak mohou být rovnez zda- neny ve smluvnõm státe, jehoz je spolecnost, která je vyplácõ, rezidentem, a to podle právnõch predpisu to- hoto státu, avsak jestlize skutecný vlastnõk dividend je rezidentem druhého smluvnõho státu, dan takto ulo- zená nepresáhne 10 % hrubé cástky dividend. Přõslusné úrady smluvnõch státu upravõ vzájemnou do- hodou zpu sob aplikace tohoto omezenõ. Tento odstavec se nedotýká zdan ovánõ zisku spolec- nosti, z nichz jsou dividendy vypláceny. 3. Výraz 1dividendya pouzitý v tomto clánku oznacuje prõjmy z akciõ nebo jiných práv, s výjimkou pohledávek, s podõlem na zisku, jakoz i prõjmy z jiných práv, které jsou podrobeny stejnému dan ovému rezimu jako prõjmy z akciõ podle dan ových p …
- interest Article 11: U roky 1. U roky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto úroky vsak mohou být rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk úroku je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne 5 % hrubé cástky úroku . 3. Bez ohledu na ustanovenõ odstavce 2 budou úroky majõcõ zdroj v jednom smluvnõm státe, které pobõrá a skutecne vlastnõ vláda druhého smluvnõho státu nebo centrálnõ (národnõ) banka tohoto státu, osvobozeny od zdanenõ v prvne zmõneném státe. Přõslusné úrady smluvnõch státu upravõ vzájemnou do- hodou zpu sob aplikace techto omezenõ. 4. Výraz 1úrokya pouzitý v tomto clánku ozna- cuje prõjmy z pohledávek jakéhokoliv druhu, at' zajis- tených ci nezajistených zástavnõm právem na nemovi- tosti nebo majõc …
- royalty Article 12: Licencnõ poplatky 1. Licencnõ poplatky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluv- nõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto licencnõ poplatky vsak mohou být rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk licencnõch poplatku je rezidentem druhého smluvnõho státu, dan takto ulozená nepre- sáhne 10 % hrubé cástky licencnõch poplatku . Přõslusné úrady smluvnõch státu upravõ vzájemnou do- hodou zpu sob aplikace tohoto omezenõ. 3. Výraz 1licencnõ poplatkya pouzitý v tomto clánku oznacuje platby jakéhokoliv druhu obdrzené jako náhrada za uzitõ nebo za právo na uzitõ jakéhoko- liv autorského práva k dõlu literárnõmu, umeleckému nebo vedeckému, vcetne kinematografických filmu a filmu nebo nahrávek pro rozhlasové nebo televiznõ vysõlánõ, jakéhokoliv patentu, ochranné zn …

Audit package hash: `10f649d62261ab9079bd87f1ec777b09f8831bfac42977549129c8849b682ae9`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## CA — Kanada (STANDARD)

Base treaty: **83/2002 Sb.m.s.** (`SRC-2E74109BA863062F`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 5.0%, 15.0% | 5.0%: recipient_entity_type == company, voting_power_control >= 10%, beneficial_owner == true, canadian_non_resident_owned_investment_corporation_exception == false; 15.0%: fallback_case == all_other_cases, beneficial_owner == true |
| interest | 11 | 0.0%, 10.0% | 10.0%: beneficial_owner == true; 0.0%: article_11_3_exemption == source_state_government_debt_or_qualifying_government_owned_export_financing_or_arm_length_credit_sale, beneficial_owner == true |
| royalty | 12 | 10.0% | 10.0%: beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-CA-MLI-WHT-PPT`; candidate WHT date `2021-01-01`. Article 8 adds no overlay.

Language: authentic `None`; prevailing `None`; evidence `hash_bound_repository_signature_clause_candidate`; signature clause `Dáno v Praze dne 25. kvetna 2001 ve dvou puvodnõch vyhotovenõch, kazdé v jazyce ceském, anglickém
a francouzském, pricemz vsechny texty majõ stejnou platnost.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-2E74109BA863062F](https://e-sbirka.gov.cz/sm/2002/83/0000-00-00).

Candidate excerpts:

- dividend Article 10: Dividendy 1. Dividendy vyplácené spolecnostõ, která je rezidentem jednoho smluvnõho státu, rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto dividendy vsak mohou být rovnez zdaneny ve smluvnõm státe, jehoz je spolecnost, která je vyplácõ, rezidentem, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk dividend je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne: a) vyjma prõpadu dividend vyplácených nerezidentem vlastnenou investicnõ spolecnostõ, která je rezidentem Kanady, 5 procent hrubé cástky dividend, jestlize skutecným vlastnõkem je spolecnost, která ovládá prõmo nebo neprõmo nejméne 10 procent hlasovacõho práva na spolecnosti vyplácejõcõ dividendy; b) 15 procent hrubé cástky dividend ve vsech ostatnõch prõpadech. Ustanovenõ tohoto odstavce se nedotýkajõ zdanenõ zisku, z nichz jsou dividendy vypláceny. 3. Výraz …
- interest Article 11: Uroky 1. Uroky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto úroky vsak mohou být rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk úroku je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne 10 procent hrubé cástky úroku. 3. Bez ohledu na ustanovenõ odstavce 2 a) úroky majõcõ zdroj v jednom smluvnõm státe a vyplácené v souvislosti se zadluzenõm vlády tohoto smluvnõho státu nebo nizsõho správnõho útvaru nebo mõstnõho úradu tohoto státu podléhajõ zdanenõ, pokud jsou úroky skutecne vlastnené rezidentem druhého smluvnõho státu, jen v tomto druhém státe; b) úroky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu a skutecne vlastnené tõmto rezidentem podléhajõ zdanenõ jen v tomto druhé …
- royalty Article 12: Licencnõ poplatky 1. Licencnõ poplatky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto licencnõ poplatky vsak mohou být rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk licencnõch poplatku je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne 10 procent hrubé cástky licencnõch poplatku. 3. Výraz 1licencnõ poplatkya pouzitý v tomto clánku oznacuje platby jakéhokoliv druhu obdrzené jako náhrada za uzitõ nebo za právo na uzitõ jakéhokoliv autorského práva k dõlu literárnõmu, umeleckému nebo vedeckému, vcetne filmu a del na filmech, páskách nebo jiných prostredcõch reprodukce pro vyuzitõ v souvislosti s televiznõm nebo rozhlasovým vysõlánõm, jakéhokoliv patentu, ochranné známky, návrhu nebo modelu, plánu, tajného vzor …

Audit package hash: `19550d5d7ca9fda5bd89a7aef6e33640a5f6c0c295af6c759163a7f0201c8396`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## CH — Švýcarsko (ELEVATED)

Base treaty: **281/1996 Sb.** (`SRC-773D5F8BD93AE73A`).

Risk focus: material_protocol_overlay, multiple_historical_instruments.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 5%, 15% | 5%: recipient_entity_type == company_other_than_partnership, direct_ownership == true, ownership_percent >= 25, beneficial_owner == true; 15%: fallback_case == all_other_cases, beneficial_owner == true |
| interest | 11 | 0.0% | 0.0%: recipient_is_treaty_resident == True, beneficial_owner == True, permanent_establishment_connection == False, arm_length_amount == True |
| royalty | 12 | 5.0%, 10.0% | 10.0%: recipient_is_treaty_resident == True, beneficial_owner == True, permanent_establishment_connection == False, arm_length_amount == True; 5.0%: recipient_is_treaty_resident == True, beneficial_owner == True, permanent_establishment_connection == False, arm_length_amount == True, recipient_country_imposes_royalty_wht_on_nonresidents == False |

Protocol/status: `official_protocol_relationship_evidence_located_needs_human_review` / `official_correction_inventory_reconciled_needs_human_review`.

MLI (WHT only): `official_matching_and_withholding_effect_candidate_needs_human_review`; modification `CZ-CH-MLI-WHT-PPT`; candidate WHT date `2022-01-01`. Article 8 adds no overlay.

Language: authentic `['Czech', 'German', 'English']`; prevailing `english_prevails_czech_german_interpretive_divergence`; evidence `current_official_pdf_signature_clause_candidate`; signature clause `Dáno v Praze ve dvojõm vyhotovenõ dne 4. prosince 1995 v ceském, nemeckém a anglickém jazyce, pricemz vsechny texty jsou autentické. V prõpade jakýchkoliv rozdõlnostõ výkladu mezi ceským a nemeckým textem bude rozhodujõcõ anglický text.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-773D5F8BD93AE73A](https://e-sbirka.gov.cz/sb/1996/281/0000-00-00); `CZ-MF-CH-7AAD2491663B`; `CZ-MF-CH-8B6FA3FB70A3`; `CZ-MF-CH-A21BB0496B98`.

Candidate excerpts:

- dividend Article 10: Dividendy 1. Dividendy vyplácené spolecnostõ, která je rezi- dentem jednoho smluvnõho státu, rezidentu druhého smluvnõho státu, mohou být zdaneny v tomto druhém státe. 2. Tyto dividendy vsak mohou být rovnez zda- neny ve smluvnõm státe, v nemz je spolecnost, která dividendy vyplácõ, rezidentem, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk dividend je rezidentem druhého smluvnõho státu, dan takto stanovená nepresáhne: a) 5 procent hrubé cástky dividend, jestlize skutec- ným vlastnõkem je spolecnost (jiná nez osobnõ spolecnost), která prõmo vlastnõ nejméne 25 pro- cent majetku spolecnosti vyplácejõcõ dividendy; b) 15 procent hrubé cástky dividend ve vsech ostat- nõch prõpadech. Tento odstavec se nedotkne zdanenõ zisku spolecnosti, ze kterých jsou dividendy vypláceny. 3. Výraz 1dividendya pouzitý v tomto clánku oznacuje prõjmy z akciõ nebo jiných práv s podõle …
- interest Article 11: U roky 1. U roky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu podlé- hajõ zdanenõ pouze v tomto druhém státe, pokud je tento rezident skutecným vlastnõkem úroku . 2. Výraz 1úrokya pouzitý v tomto clánku ozna- cuje prõjmy z pohledávek jakéhokoliv druhu, zajiste- ných i nezajistených zástavnõm právem na nemovitosti nebo dolozkou o úcasti na zisku dluznõka, a obzvláste prõjmy z vládnõch cenných papõru a prõjmy z obligacõ nebo dluhopisu , vcetne prémiõ a výher spojených s temito cennými papõry, obligacemi nebo dluhopisy. 3. Ustanovenõ odstavce 1 se nepouzije, jestlize skutecný vlastnõk úroku , který je rezidentem v jed- nom smluvnõm státe, vykonává v druhém smluvnõm státe, v nemz majõ úroky zdroj, pru myslovou nebo obchodnõ cinnost prostrednictvõm stálé provozovny, která je tam umõstena, nebo vykonává v tomto dru- hém státe nezávislé povolánõ prostrednic …
- royalty Article 12: Licencnõ poplatky 1. Licencnõ poplatky majõcõ zdroj v jednom smluvnõm státe, vyplácené rezidentu druhého smluv- nõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto licencnõ poplatky vsak mohou být zda- neny také ve smluvnõm státe, ve kterém je jejich zdroj, a v souladu s právnõmi predpisy tohoto státu, ale jestlize skutecný vlastnõk licencnõch poplatku je rezidentem druhého smluvnõho státu, dan takto stano- vená nepresáhne 10 procent hrubé cástky licencnõch poplatku . 3. Výraz 1licencnõ poplatkya pouzitý v tomto clánku oznacuje platby jakéhokoliv druhu obdrzené jako náhrada za uzitõ nebo za právo na uzitõ jakéhoko- liv autorského práva k dõlu literárnõmu, umeleckému nebo vedeckému vcetne kinematografických filmu , ja- kéhokoliv patentu, ochranné známky, návrhu nebo modelu, plánu, tajného vzorce nebo výrobnõho po- stupu nebo za uzitõ nebo za právo na uzitõ pru myslo- vého, obchodnõ …

Audit package hash: `74d74f237a9fec8c47271c51279263d11075474d51b274f0b72514c3dfcbadbb`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## CL — Chile (ELEVATED)

Base treaty: **5/2017 Sb.m.s.** (`SRC-CE747E586B47529F`).

Risk focus: multiple_historical_instruments.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 15.0% | 15.0%: beneficial_owner == true |
| interest | 11 | 4.0%, 15.0% | 4.0%: beneficial_owner == true, qualifying_article_11_2a_case == bank_or_insurer_or_active_regular_unrelated_financing_business_or_credit_sale_of_machinery_or_equipment_or_financial_market_funding_enterprise, detailed_eligibility_review_required == true; 15.0%: fallback_case == all_other_cases, beneficial_owner == true |
| royalty | 12 | 5.0%, 10.0% | 5.0%: royalty_category == industrial_commercial_or_scientific_equipment, beneficial_owner == true; 10.0%: fallback_case == all_other_article_12_royalties, beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-CL-MLI-WHT-PPT`; candidate WHT date `2022-01-01`. Article 8 adds no overlay.

Language: authentic `['Czech', 'Spanish', 'English']`; prevailing `english_prevails_all_text_divergences`; evidence `current_official_pdf_signature_clause_candidate`; signature clause `Dano v Santiagu de Chile dne 2. prosince 2015 ve dvou piivodnich vyhotovenich, v éeském, Spanélském a anglickém jazyce, priéemZ vSechny texty jsou autentické. V pripadé jakéhokoliv rozdilu bude rozhodujicim anglicky text.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-CE747E586B47529F](https://e-sbirka.gov.cz/sm/2017/5/0000-00-00).

Candidate excerpts:

- dividend Article 10: DIVIDENDY 1. Dividendy vyplácené společností, která je rezidentem jednoho smluvního státu, rezidentu druhého smluvního státu, mohou být zdaněny v tomto druhém státě. 2. Tyto dividendy však mohou být rovněž zdaněny ve smluvním státě, jehož je společnost, která je vyplácí, rezidentem, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník dividend je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 15 procent hrubé částky dividend. Ustanovení tohoto odstavce se nedotýkají zdanění zisků společnosti, z nichž jsou dividendy vypláceny. Ustanovení tohoto odstavce neomezují aplikaci dodatečné daně splatné v Chilské republice za předpokladu, že daň první kategorie je zcela započitatelná při výpočtu částky daně dodatečné. 3. Výraz „dividendy“ použitý v tomto článku označuje příjmy z akcií nebo jiných práv, s výjimkou pohledávek, s podílem na zisku, jakož i jiné …
- interest Article 11: ÚROKY 1. Úroky mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu mohou být zdaněny v tomto druhém státě. 2. Tyto úroky vsak mohou být rovněž zdaněny ve smluvním státě, v němž mají zdroj, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník úroků je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne: a) 4 procenta hrubé částky úroků, jestliže skutečný vlastník úroků je buď: (i) banka; (ii) pojišťovací společnost; (iii) podnik dosahující v podstatné míře svůj hrubý příjem z aktivního a pravidelného uskutečňování činnosti spočívající v poskytování půjček nebo úvěrů či financování a zahrnující transakce s nespojenými osobami, kdy podnik je nespojený s plátcem úroků. Pro účely tohoto ustanovení výraz „činnost spočívající v poskytování půjček nebo úvěrů či financování“ zahrnuje činnost spočívající ve vystavování akreditivů,  …
- royalty Article 12: LICENČNÍ POPLATKY 1. Licenční poplatky mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu mohou být zdaněny v tomto druhém státě. 2. Tyto licenční poplatky však mohou být rovněž zdaněny ve smluvním státě, v němž mají zdroj, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník licenčních poplatků je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne: a) 5 procent hrubé částky licenčních poplatků za užití nebo za právo na užití jakéhokoliv průmyslového, obchodního nebo vědeckého zařízení; b) 10 procent hrubé částky licenčních poplatků ve všech ostatních případech. 3. Výraz „licenční poplatky“ použitý v tomto článku označuje platby jakéhokoliv druhu obdržené jako náhrada za užití nebo za právo na užití jakéhokoliv autorského práva k dílu literárnímu, uměleckému nebo vědeckému, včetně kinematografických filmů, nebo filmů, p …

Audit package hash: `9be7ae087dcf77e6eb21a42ab455e8c855987883f1b1840ea5e82832f65d6656`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## CM — Kamerun (STANDARD)

Base treaty: **415/2025 Sb.** (`SRC-C9A0B1B633A5AAD3`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 10.0% | 10.0%: beneficial_owner == true |
| interest | 11 | 0.0%, 10.0% | 10.0%: beneficial_owner == true; 0.0%: article_11_3_exemption == credit_sale_or_government_central_bank_export_promotion_institution_or_qualifying_government_guaranteed_financing, beneficial_owner == true |
| royalty | 12 | 10.0% | 10.0%: beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `not_listed`; modification `None`; candidate WHT date `None`. Article 8 adds no overlay.

Language: authentic `['cs', 'fr', 'en']`; prevailing `english`; evidence `existing_repository_language_record`; signature clause `None`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-C9A0B1B633A5AAD3](https://e-sbirka.gov.cz/sb/2025/415/0000-00-00).

Candidate excerpts:

- dividend Article 10: DIVIDENDY 1. Dividendy vyplácené společností, která je rezidentem jednoho smluvního státu, rezidentu druhého smluvního státu, mohou být zdaněny v tomto druhém státě. 2. Tyto dividendy však mohou být rovněž zdaněny ve smluvním státě, jehož je společnost, která je vyplácí, rezidentem, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník dividend je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 10 procent hrubé částky dividend. Příslušné úřady smluvních států upraví vzájemnou dohodou způsob aplikace tohoto omezení. Tento odstavec se nedotýká zdanění zisků společnosti, z nichž jsou dividendy vypláceny. 3. Výraz „dividendy“ použitý v tomto článku označuje příjmy z akcií, požitkových akcií nebo požitkových práv, kuksů, zakladatelských podílů nebo jiných práv, s výjimkou pohledávek, s podílem na zisku, jakož i jiné příjmy, které jsou podrobeny stejnému  …
- interest Article 11: ÚROKY 1. Úroky mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu mohou být zdaněny v tomto druhém státě. 2. Tyto úroky však mohou být rovněž zdaněny ve smluvním státě, v němž mají zdroj, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník úroků je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 10 procent hrubé částky úroků. Příslušné úřady smluvních států upraví vzájemnou dohodou způsob aplikace tohoto omezení. 3. Úroky mající zdroj v jednom smluvním státě a skutečně vlastněné rezidentem druhého smluvního státu podléhají bez ohledu na ustanovení odstavce 2 zdanění jen v tomto druhém státě, jestliže jsou tyto úroky vypláceny: a) v souvislosti s prodejem jakéhokoliv zboží nebo zařízení na úvěr; b) vládě druhého smluvního státu, včetně jakéhokoliv územně-správního útvaru nebo místního úřadu tohoto státu, centrální ba …
- royalty Article 12: LICENČNÍ POPLATKY A POPLATKY ZA TECHNICKÉ SLUŽBY 1. Licenční poplatky a poplatky za technické služby mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu mohou být zdaněny v tomto druhém státě. 2. Tyto licenční poplatky a poplatky za technické služby však mohou být rovněž zdaněny ve smluvním státě, v němž mají zdroj, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník licenčních poplatků nebo poplatků za technické služby je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 10 procent hrubé částky licenčních poplatků nebo poplatků za technické služby. Příslušné úřady smluvních států upraví vzájemnou dohodou způsob aplikace tohoto omezení. 3. a) Výraz „licenční poplatky“ použitý v tomto článku označuje platby jakéhokoliv druhu obdržené jako náhrada za užití nebo za právo na užití jakéhokoliv autorského práva k dílu literá …

Audit package hash: `33f0f9798c3c065b1807e49fd06f62e4dc35f1645cf0aee656aa40a838d2cea5`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____
