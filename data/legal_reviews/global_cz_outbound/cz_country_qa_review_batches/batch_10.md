# CZ country legal-QA review batch 10

> Machine-prepared candidate evidence only. No country or scope in this file has been human reviewed, approved, verified, or released.

## TM — Turkmenistán (STANDARD)

Base treaty: **23/2018 Sb.m.s.** (`SRC-63B5FB533F1F8FAD`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 10.0% | 10.0%: beneficial_owner == true |
| interest | 11 | 0.0%, 10.0% | 10.0%: beneficial_owner == true; 0.0%: article_11_3_exemption == government_central_bank_government_owned_or_controlled_institution_or_qualifying_government_guaranteed_financing, beneficial_owner == true |
| royalty | 12 | 10.0% | 10.0%: beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `not_listed`; modification `None`; candidate WHT date `None`. Article 8 adds no overlay.

Language: authentic `['Czech', 'Turkmen', 'English']`; prevailing `english_prevails_all_text_divergences`; evidence `current_official_pdf_signature_clause_candidate`; signature clause `Dano v ASchabadu dne 18. b¥ezna 2016 ve dvou pivodnich vyhotovenich, kazdé v jazyce éeském, turkmenském a anglickém, pritemz vsechny texty jsou autentické. V pripadé jakéhokoliv rozdilu mezi texty bude rozhodujicim anglicky text.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: No current WHT-relevant MLI PPT effect record.

Official sources: [SRC-63B5FB533F1F8FAD](https://e-sbirka.gov.cz/sm/2018/23/0000-00-00).

Candidate excerpts:

- dividend Article 10: DIVIDENDY 1. Dividendy vyplácené společností, která je rezidentem jednoho smluvního státu, rezidentu druhého smluvního státu, mohou být zdaněny v tomto druhém státě. 2. Tyto dividendy však mohou být rovněž zdaněny ve smluvním státě, jehož je společnost, která je vyplácí, rezidentem, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník dividend je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 10 procent hrubé částky dividend. Příslušné úřady smluvních států upraví vzájemnou dohodou způsob aplikace tohoto omezení. Tento odstavec se nedotýká zdanění zisků společnosti, z nichž jsou dividendy vypláceny. 3. Výraz "dividendy" použitý v tomto článku označuje příjmy z akcií nebo jiných práv, s výjimkou pohledávek, s podílem na zisku, jakož i jiné příjmy, které jsou podrobeny stejnému daňovému režimu jako příjmy z akcií podle právních předpisů státu, jehož …
- interest Article 11: ÚROKY 1. Úroky mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu mohou být zdaněny v tomto druhém státě. 2. Tyto úroky však mohou být rovněž zdaněny ve smluvním státě, v němž mají zdroj, a to podle právních předpisů tohoto statu, avšak jestliže skutečný vlastník úroků je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 10 procent hrubé částky úroků. 3. Úroky mající zdroj v jednom smluvním státě a skutečně vlastněné rezidentem druhého smluvního státu podléhají bez ohledu na ustanovení odstavce 2 zdanění jen v tomto druhém státě, jestliže jsou tyto úroky vypláceny: a) vládě druhého smluvního státu, včetně jakéhokoliv územně-správního útvaru nebo místního úřadu tohoto státu, centrální bance druhého smluvního státu nebo jakékoli instituci, která je vlastněna nebo ovládána touto vládou; b) v souvislosti s jakoukoliv půjčkou nebo jakýmkoliv úvěr …
- royalty Article 12: LICENČNÍ POPLATKY 1. Licenční poplatky mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu mohou být zdanény v tomto druhém státě. 2. Tyto licenční poplatky však mohou být rovněž zdaněny ve smluvním státě, v němž mají zdroj, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník licenčních poplatků je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 10 procent hrubé částky licenčních poplatků. Příslušné úřady smluvních států upraví vzájemnou dohodou způsob aplikace tohoto omezení. 3. Výraz "licenční poplatky" použitý v tomto článku označuje platby jakéhokoliv druhu obdržené jako náhrada za užití nebo za právo na užití jakéhokoliv autorského práva k dílu literárnímu, uměleckému nebo vědeckému, včetně kinematografickych filmů a nahrávek pro televizní nebo rozhlasové vysílání, jakéhokoliv patentu, ochranné známky, návrhu ne …

Audit package hash: `42d2e58ef8988864c7625ac96078d1b8aad01c1fd0bc9fedbc1802eafee03510`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## TN — Tunisko (STANDARD)

Base treaty: **419/1992 Sb.** (`SRC-7CA3D6D0E3382934`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 10.0%, 15.0% | 10.0%: minimum_ownership >= 25, beneficial_owner == true; 15.0%: beneficial_owner == true |
| interest | 11 | 0.0%, 12.0% | 0.0%: loan_provider == contracting_state; 12.0%: fallback_case == other_interest_subject_to_source_state_taxation |
| royalty | 12 | 5.0%, 15.0% | 5.0%: royalty_category == copyright_literary_artistic_scientific_including_cinematographic_films_and_tv_or_radio_recordings; 15.0%: royalty_category == patent_trademark_design_model_plan_secret_formula_process_equipment_knowhow_technical_or_economic_studies_or_technical_assistance |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-TN-MLI-WHT-PPT`; candidate WHT date `2025-01-01`. Article 8 adds no overlay.

Language: authentic `None`; prevailing `None`; evidence `hash_bound_repository_signature_clause_candidate`; signature clause `Dáno v Praze dne 14. brezna 1990 ve dvojõm vy-
hotovenõ v jazyce francouzském.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-7CA3D6D0E3382934](https://e-sbirka.gov.cz/sb/1992/419/0000-00-00).

Candidate excerpts:

- dividend Article 10: DIVIDENDY 1. Dividendy vyplácené spolecnostõ, která je rezi- dentem v jednom smluvnõm státe, osobe, která je rezi- dentem v druhém smluvnõm státe, mohou být zdaneny v tomto druhém státe. 2. Takové dividendy vsak mohou být zdaneny ta- ké ve smluvnõm státe, v nemz je spolecnost, která je vy- plácõ, rezidentem, a to podle právnõch predpisu tohoto státu, avsak dan takto ukládaná nepresáhne: a) 10 % hrubé cástky dividend, jestlize skutecný vlastnõk dividend je spolecnost, která vlastnõ nej- méne 25 % podõlu na spolecnosti vyplácejõcõ divi- dendy; b) 15 % hrubé cástky dividend ve vsech jiných prõpa- dech. Tento odstavec se nedotkne zdanenõ zisku spolec- nosti, ze kterých jsou dividendy vypláceny. 3. Výraz 1dividendya, pouzitý v tomto clánku, oznacuje prõjmy z akciõ, pozitkových akciõ nebo pozit- kových listu , kuksu , zakladatelských podõlu nebo ji- ných práv ± s výjimkou pohledávek ± s podõle …
- interest Article 11: U roky 1. U roky majõcõ zdroj v jednom smluvnõm státe a placené osobe, která je rezidentem v druhém smluv- nõm státe, podléhajõ zdanenõ pouze v tomto druhém státe. 2. Avsak tyto úroky s výjimkou úroku z pu jcek poskytnutých jednõm ze smluvnõch státu , mohou být zdaneny ve smluvnõm státe, ve kterém je jejich zdroj, a to podle právnõch predpisu tohoto státu, ale dan takto ulozená nemu ze presáhnout 12 % jejich hrubé cástky. 3. Výraz 1úrokya pouzitý v tomto clánku ozna- cuje prõjmy z pohledávek jakéhokoli druhu, zajiste- ných i nezajistených zástavnõm právem nemovitosti, poskytujõcõch i neposkytujõcõch právo na úcast na zisku dluznõka a obzvláste prõjmy z verejných dluhopisu a obligacõ, vcetne prémiõ a výher spojených s temito cennými papõry. 4. Ustanovenõ odstavce 1 tohoto clánku se nepou- zije, jestlize skutecný prõjemce úroku , který je reziden- tem v jednom smluvnõm státe, vykonává v dr …
- royalty Article 12: LICENČ NI POPLATKY 1. Licencnõ poplatky majõcõ zdroj v jednom smluvnõm státe a placené osobe, která je rezidentem v druhém smluvnõm státe, mohou být zdaneny pouze v tomto druhém státe. 2. Na rozdõl od ustanovenõ odstavce 1 tohoto clánku mohou být licencnõ poplatky uvedené v odstav- ci 3 zdaneny také ve smluvnõm státe, ve kterém je jejich zdroj, a to podle právnõch predpisu tohoto státu, ale dan takto stanovená nemu ze presáhnout ± 5 % z hrubé cástky licencnõch poplatku uvede- ných v odstavci 3b); ± 15 % z hrubé cástky licencnõch poplatku uvede- ných v odstavci 3a). 3. Výraz 1licencnõ poplatkya pouzitý v tomto clánku oznacuje: a) náhrady jakéhokoli druhu placené za uzitõ nebo za privolenõ k uzitõ patentu, ochranné známky, ná- vrhu nebo modelu, plánu, tajného vzorce nebo vý- robnõho postupu nebo za uzitõ nebo privolenõ k uzitõ pru myslového, obchodnõho nebo vedecké- ho zarõzenõ nebo za inf …

Audit package hash: `14e9381645206c2c7d1aecf451bc42f0a430ad1ba0082aca147bf29480bb50a5`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## TR — Turecko (STANDARD)

Base treaty: **19/2004 Sb.m.s.** (`SRC-19BEE984FA392973`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 10.0% | 10.0%: beneficial_owner == true |
| interest | 11 | 0.0%, 10.0% | 10.0%: beneficial_owner == true; 0.0%: recipient_entity_type == government_subnational_local_authority_central_bank_eximbank_or_agreed_wholly_government_owned_institution, beneficial_owner == true |
| royalty | 12 | 10.0% | 10.0%: beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `signed_not_ratified_no_current_wht_effect`; modification `None`; candidate WHT date `None`. Article 8 adds no overlay.

Language: authentic `None`; prevailing `None`; evidence `hash_bound_repository_signature_clause_candidate`; signature clause `Dáno v Ankare dne 12. listopadu 1999 ve dvou puvodnõch vyhotovenõch v anglickém jazyce.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: No current WHT-relevant MLI PPT effect record.

Official sources: [SRC-19BEE984FA392973](https://e-sbirka.gov.cz/sm/2004/19/0000-00-00); `OECD-MLI-CZ-POSITION`; `OECD-MLI-PARTIES-2026-07`.

Candidate excerpts:

- dividend Article 10: Dividendy 1. Dividendy vyplácené spolecnostõ, která je rezidentem jednoho smluvnõho státu, rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto dividendy vsak mohou být rovnez zdaneny ve smluvnõm státe, jehoz je spolecnost, která je vyplácõ, rezidentem, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk dividend je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne 10 procent hrubé cástky dividend. Tento odstavec se nedotýká zdanenõ zisku spolecnosti, z nichz jsou dividendy vypláceny. 3. Výraz 1dividendya pouzitý v tomto clánku oznacuje prõjmy z akciõ, pozitkových akciõ nebo pozitkových práv, kuksu, zakladatelských podõlu nebo jiných práv, s výjimkou pohledávek, s podõlem na zisku, jakoz i prõjmy pobõrané z investicnõho fondu a investicnõho trustu a jiné prõjmy, které jsou podrobeny stejnému danovému rezimu jako prõjmy z …
- interest Article 11: Uroky 1. Uroky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto úroky vsak mohou být rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk úroku je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne 10 procent hrubé cástky úroku. 3. Uroky majõcõ zdroj v jednom smluvnõm státe jsou bez ohledu na ustanovenõ odstavce 2 osvobozeny od zdanenõ v tomto státe, pokud jsou pobõrány a skutecne vlastneny: a) vládou, nizsõm správnõm útvarem nebo mõstnõm úradem druhého smluvnõho státu; nebo b) (i) v prõpade Turecka Centrálnõ bankou Turecka a Eximbankou Turecka; a (ii) v prõpade České republiky Českou národnõ bankou a Českou exportnõ bankou; nebo c) jakoukoli jinou institucõ, která je zcela vlastnena vládou druhého smluvnõho státu, jak …
- royalty Article 12: Licencnõ poplatky 1. Licencnõ poplatky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto licencnõ poplatky vsak mohou být rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk licencnõch poplatku je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne 10 procent hrubé cástky licencnõch poplatku. 3. Výraz 1licencnõ poplatkya pouzitý v tomto clánku oznacuje platby jakéhokoliv druhu obdrzené jako náhrada za uzitõ nebo za právo na uzitõ jakéhokoliv autorského práva k dõlu literárnõmu, umeleckému nebo vedeckému, vcetne kinematografických filmu a nahrávek pro televiznõ nebo rozhlasové vysõlánõ, jakéhokoliv patentu, ochranné známky, návrhu nebo modelu, plánu, tajného vzorce nebo výrobnõho postupu nebo jakého- koliv prumyslového,  …

Audit package hash: `8bea9d47230d5e903f1df47519486a611aea1741f0da8ba7854f63941a141549`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## TW — Tchaj-wan (ELEVATED)

Base treaty: **zákon č. 45/2020 Sb. (příloha – Ustanovení ve vztahu k Tchaj-wanu)** (`CZ-TW-LAW-45-2020`).

Risk focus: special_statutory_double_taxation_arrangement, effective_notice_309_2020.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 10.0% | 10.0%: beneficial_owner == true |
| interest | 11 | 0.0%, 10.0% | 0.0%: special_article_11_3_exemption == credit_sale_of_goods_or_equipment_or_government_subnational_local_authority_central_bank_or_government_controlled_or_wholly_owned_financial_institution_or_loan_or_credit_guaranteed_or_insured_by_such_public_body, beneficial_owner == true; 10.0%: fallback_case == all_other_cases, beneficial_owner == true |
| royalty | 12 | 5.0%, 10.0% | 5.0%: royalty_category == industrial_commercial_scientific_equipment, beneficial_owner == true; 10.0%: royalty_category == other, beneficial_owner == true |

Protocol/status: `official_effective_notice_identified_needs_human_review` / `in_force_use_start_confirmed_needs_human_review`.

MLI (WHT only): `not_applicable_special_statutory_arrangement`; modification `None`; candidate WHT date `None`. Article 8 adds no overlay.

Language: authentic `['Czech statutory text']`; prevailing `not_applicable_special_statutory_arrangement`; evidence `official_czech_statutory_text`; signature clause `None`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: No current WHT-relevant MLI PPT effect record.

Official sources: [CZ-TW-LAW-45-2020](https://e-sbirka.gov.cz/sb/2020/45); [CZ-TW-NOTICE-309-2020](https://e-sbirka.gov.cz/sb/2020/309).

Candidate excerpts:

- dividend Article 10: Article 10(2): source-territory tax does not exceed 10% of the gross dividend where the beneficial owner is resident in the other territory. …
- interest Article 11: Article 11(2): 10% general ceiling for beneficial-owner interest; Article 11(3) provides source exemption for specified qualifying cases. …
- royalty Article 12: Article 12(2): 5% for industrial, commercial or scientific equipment; 10% in all other cases, subject to beneficial ownership. …

Audit package hash: `e769983fbe69a71759dc6056705e1773a5d54ad4298a7799e7691f32ce3fb778`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## UA — Ukrajina (ELEVATED)

Base treaty: **103/1999 Sb.** (`SRC-1D74C3BA794BFE66`).

Risk focus: material_protocol_overlay.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 5.0%, 15.0% | 5.0%: minimum_ownership >= 25, beneficial_owner == true; 15.0%: beneficial_owner == true |
| interest | 11 | 0.0%, 5.0% | 0.0%: recipient_or_financing == government_subnational_local_authority_central_bank_wholly_government_owned_financial_institution_or_government_guaranteed_loan, beneficial_owner == true; 5.0%: fallback_case == all_other_cases, beneficial_owner == true |
| royalty | 12 | 10.0% | 10.0%: beneficial_owner == true |

Protocol/status: `protocol_effect_candidate_consolidated` / `not_listed`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-UA-MLI-WHT-PPT`; candidate WHT date `2025-01-01`. Article 8 adds no overlay.

Language: authentic `None`; prevailing `None`; evidence `hash_bound_repository_signature_clause_candidate`; signature clause `Dáno v Kyjeve dne 30. cervna 1997 ve dvou pu -
vodnõch vyhotovenõch, kazdé v jazyce ceském, ukrajin-
ském a anglickém, pricemz vsechny texty jsou auten-
tické. V prõpade jakýchkoliv rozdõlnostõ bude rozho-
dujõcõm anglický text.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-1D74C3BA794BFE66](https://e-sbirka.gov.cz/sb/1999/103/0000-00-00); `CZ-MF-UA-5F98838DA169`.

Candidate excerpts:

- dividend Article 10: Dividendy 1. Dividendy vyplácené spolecnostõ, která je rezi- dentem jednoho smluvnõho státu, rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto dividendy vsak mohou být rovnez zda- neny ve smluvnõm státe, jehoz je spolecnost, která je vyplácõ, rezidentem, a to podle právnõch predpisu to- hoto státu, avsak jestlize skutecný vlastnõk dividend je rezidentem druhého smluvnõho státu, dan takto ulo- zená nepresáhne: a) 5 procent hrubé cástky dividend, jestlize skutec- ným vlastnõkem je spolecnost (jiná nez osobnõ spolecnost), která prõmo vlastnõ nejméne 25 pro- cent majetku spolecnosti vyplácejõcõ dividendy; b) 15 procent hrubé cástky dividend ve vsech ostat- nõch prõpadech. Přõslusné úrady smluvnõch státu upravõ vzájemnou do- hodou zpu sob aplikace techto omezenõ. Tento odstavec se nedotýká zdanenõ zisku spolecnosti, z nichz jsou dividendy vypláceny. 3. Výraz 1d …
- interest Article 11: U roky 1. U roky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto úroky vsak mohou být rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk úroku je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne 5 procent hrubé cástky úroku . Přõslusné úrady smluvnõch státu upravõ vzájemnou do- hodou zpu sob aplikace tohoto omezenõ. 3. Bez ohledu na ustanovenõ odstavce 2 budou úroky majõcõ zdroj v jednom smluvnõm státe a pobõrané a skutecne vlastnené vládou druhého smluvnõho státu, vcetne nizsõch správnõch útvaru a mõstnõch úradu to- hoto státu, centrálnõ bankou nebo jakoukoli financnõ institucõ zcela vlastnenou touto vládou nebo úroky po- bõrané z pu jcek garantovaných touto vládou osvobo- zeny od zdanenõ v prvne zmõneném smluvnõ …
- royalty Article 12: Licencnõ poplatky 1. Licencnõ poplatky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluv- nõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto licencnõ poplatky vsak mohou být rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk licencnõch poplatku je rezidentem druhého smluvnõho státu, dan takto ulozená nepre- sáhne 10 procent hrubé cástky licencnõch poplatku . Přõslusné úrady smluvnõch státu upravõ vzájemnou do- hodou zpu sob aplikace tohoto omezenõ. 3. Výraz 1licencnõ poplatkya pouzitý v tomto clánku oznacuje platby jakéhokoliv druhu obdrzené jako náhrada za uzitõ nebo za právo na uzitõ jakéhoko- liv autorského práva k dõlu literárnõmu, umeleckému nebo vedeckému (vcetne kinematografických filmu a filmu nebo nahrávek pro rozhlasové nebo televiznõ vysõlánõ), jakéhokoliv patentu, ochr …

Audit package hash: `571232f8866532f41ee1c700a998a0b3a5c3545e022b557efbfd189b4b3858f4`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## US — USA (Spojené státy americké) (STANDARD)

Base treaty: **32/1994 Sb.** (`SRC-EADD5B70920D588C`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 5.0%, 15.0% | 5.0%: minimum_ownership >= 10, beneficial_owner == true; 15.0%: beneficial_owner == true |
| interest | 11 | 0.0% | 0.0%: beneficial_owner == true |
| royalty | 12 | 0.0%, 10.0% | 0.0%: royalty_category == copyright_literary_artistic_scientific_including_films_tapes_or_other_audio_visual_reproduction, beneficial_owner == true; 10.0%: royalty_category == patent_trademark_design_model_plan_secret_formula_process_similar_right_or_property_equipment_or_knowhow_including_productivity_use_or_disposition_contingent_sales, beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `not_listed`; modification `None`; candidate WHT date `None`. Article 8 adds no overlay.

Language: authentic `None`; prevailing `None`; evidence `hash_bound_repository_signature_clause_candidate`; signature clause `Dáno v Praze ve dvojõm vyhotovenõ, v ceském
a anglickém jazyce, pricemz oba texty majõ stejnou
platnost, dne 16. zárõ 1993.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: No current WHT-relevant MLI PPT effect record.

Official sources: [SRC-EADD5B70920D588C](https://e-sbirka.gov.cz/sb/1994/32/0000-00-00).

Candidate excerpts:

- dividend Article 10: DIVIDENDY 1. Dividendy vyplácené spolecnostõ, která je rezi- dentem v jednom smluvnõm státe, osobe, která je rezi- dentem v druhém smluvnõm státe, mohou být zdaneny v tomto druhém státe. 2. Tyto dividendy vsak mohou být rovnez zda- neny ve smluvnõm státe, v nemz je spolecnost, která je vyplácõ, rezidentem, a to podle právnõch predpisu tohoto státu, avsak jestlize prõjemce, který je skutec- ným vlastnõkem dividend, je rezidentem druhého smluvnõho státu, dan takto stanovená nepresáhne: a) 5 % hrubé cástky dividend, jestlize skutecným vlastnõkem je spolecnost, která vlastnõ nejméne 10 % podõlu s hlasovacõm právem na spolecnosti vyplácejõcõ dividendy; b) 15 % hrubé cástky dividend ve vsech ostatnõch prõpadech. Tento odstavec se nedotkne zdanenõ zisku spolecnosti, ze kterých jsou dividendy vypláceny. 3. Pododstavec a) odstavce 2 se nepouzije v prõ- pade dividend, které vyplácõ United State Re …
- interest Article 11: U ROKY 1. U roky, které majõ zdroj v jednom smluvnõm státe a které skutecne vlastnõ rezident druhého smluv- nõho státu, podléhajõ zdanenõ pouze v tomto státe. 2. Spojené státy mohou, bez ohledu na ustanovenõ odstavce 1, zdanit cástku prevysujõcõ zbytkový úrok v Real Estate Mortgage Investment Conduit v souladu s vnitrostátnõmi právnõmi predpisy. 3. Výraz 1úrokya, pouzitý v tomto clánku, ozna- cuje prõjmy z pohledávek jakéhokoliv druhu, zajiste- ných i nezajistených zástavnõm právem na nemovitosti, a s výhradou odstavce 4 clánku 10 (Dividendy) posky- tujõcõch nebo neposkytujõcõch právo úcasti na zisku dluznõka, a zvláste, prõjem z vládnõch cenných papõru a prõjem z obligacõ nebo dluhopisu , vcetne prémiõ a výher vztahujõcõch se k temto cenným papõru m, ob- ligacõm nebo dluhopisu m, stejne jako jakýkoliv jiný prõjem, který je podle dan ových zákonu smluvnõho státu, v nemz prõjem vzniká, po …
- royalty Article 12: LICENČ NI POPLATKY 1. Licencnõ poplatky, majõcõ zdroj v jednom smluvnõm státe, které pobõrá rezident druhého smluv- nõho státu, mohou být zdaneny v tomto druhém státe. 2. Licencnõ poplatky uvedené v pododstavci a) odstavce 3, které skutecne vlastnõ rezident jednoho smluvnõho státu, mohou být zdaneny pouze v tomto státe. Licencnõ poplatky uvedené v pododstavci b) od- stavce 3 mohou být zdaneny také ve smluvnõm státe, ve kterém je jejich zdroj, a v souladu s právnõmi predpisy tohoto státu, avsak je-li prõjemce, který je skutecným vlastnõkem licencnõch poplatku , rezidentem druhého smluvnõho státu, cástka dane takto stanovená nepre- sáhne 10 % hrubé cástky licencnõch poplatku . 3. Výraz 1licencnõ poplatkya pouzitý v této smlouve oznacuje platby jakéhokoliv druhu obdrzené jako náhrada za uzitõ nebo za právo na uzitõ: a) autorského práva k dõlu literárnõmu, umeleckému nebo vedeckému vcetne ki …

Audit package hash: `d23c40dff9d1e0ac564b51af46b46296f22857fb9049271123c5d2e5bd1430dc`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## UZ — Uzbekistán (ELEVATED)

Base treaty: **28/2001 Sb.m.s.** (`SRC-93B80AB9D2395397`).

Risk focus: material_protocol_overlay.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 5.0%, 10.0% | 5.0%: recipient_entity_type == company_other_than_partnership, direct_ownership >= 25%, beneficial_owner == true; 10.0%: fallback_case == all_other_cases, beneficial_owner == true |
| interest | 11 | 0.0%, 5.0% | 5.0%: beneficial_owner == true; 0.0%: article_11_3_exemption == government_subnational_local_authority_central_bank_wholly_government_owned_financial_institution_or_government_guaranteed_financing_or_credit_sale_or_bank_loan, beneficial_owner == true |
| royalty | 12 | 10.0% | 10.0%: beneficial_owner == true |

Protocol/status: `protocol_effect_candidate_consolidated` / `not_listed`.

MLI (WHT only): `not_listed`; modification `None`; candidate WHT date `None`. Article 8 adds no overlay.

Language: authentic `['Czech', 'Uzbek', 'English']`; prevailing `english_prevails_all_text_divergences`; evidence `current_official_pdf_signature_clause_candidate`; signature clause `Dáno v Praze dne 2. brezna roku 2000 ve dvou puvodnõch vyhotovenõch, kazdé v jazyce ceském, uzbeckém a anglickém, pricemz vsechny texty jsou autentické. V prõpade jakéhokoliv rozdõlu bude rozhodujõcõm anglický text.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-93B80AB9D2395397](https://e-sbirka.gov.cz/sm/2001/28/0000-00-00); `CZ-MF-UZ-91E56630154D`.

Candidate excerpts:

- dividend Article 10: Dividendy 1. Dividendy vyplácené spolecnostõ, která je rezidentem jednoho smluvnõho státu, rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto dividendy vsak mohou být rovnez zdaneny ve smluvnõm státe, jehoz je spolecnost, která je vyplácõ, rezidentem, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk dividend je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne 10 procent hrubé cástky dividend. Tento odstavec se nedotýká zdanenõ zisku spolecnosti, z nichz jsou dividendy vypláceny. 3. Výraz 1dividendya pouzitý v tomto clánku oznacuje prõjmy z akciõ, pozitkových akciõ nebo pozitkových práv, kuksu, zakladatelských podõlu nebo jiných práv, s výjimkou pohledávek, s podõlem na zisku, jakoz i jiné prõjmy, které jsou podrobeny stejnému danovému rezimu jako prõjmy z akciõ podle právnõch predpisu státu, jehoz je spolecnost, kt …
- interest Article 11: Uroky 1. Uroky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto úroky vsak mohou být rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk úroku je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne 5 procent hrubé cástky úroku. 3. Bez ohledu na ustanovenõ odstavce 2, budou úroky osvobozené od zdanenõ ve smluvnõm státe, ve kterém majõ zdroj, pokud jsou: a) pobõrané a skutecne vlastnené: (i) vládou druhého smluvnõho státu, vcetne jakéhokoliv územne-správnõho útvaru nebo mõstnõho úradu tohoto státu, centrálnõ bankou nebo jakoukoli financnõ institucõ, která je zcela vlastnena touto vládou; nebo (ii) rezidentem druhého smluvnõho státu v souvislosti s pujckou nebo úverem zarucenými vládou tohoto druhého státu; b) vyplácené v …
- royalty Article 12: Licencnõ poplatky 1. Licencnõ poplatky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto licencnõ poplatky vsak mohou být rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk licencnõch poplatku je rezidentem druhého smluvnõho státu, dan takto ulozená nepresáhne 10 procent hrubé cástky licencnõch poplatku. 3. Výraz 1licencnõ poplatkya pouzitý v tomto clánku oznacuje platby jakéhokoliv druhu obdrzené jako náhrada za uzitõ nebo za právo na uzitõ jakéhokoliv autorského práva k dõlu literárnõmu, umeleckému nebo vedeckému, vcetne kinematografických filmu nebo filmu nebo pásek pouzõvaných pro rozhlasové nebo televiznõ vysõlánõ, videokazet, jakéhokoliv patentu, ochranné známky, návrhu nebo modelu, plánu, pocõtacového pro- gramu, tajného vzo …

Audit package hash: `6d1a25b37b4a4848a8f43dd1ddca5ce542123c43ef7a5239aeb960ac60db21e4`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## VE — Venezuela (STANDARD)

Base treaty: **6/1998 Sb.** (`SRC-5C857626A8532345`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 5.0%, 10.0% | 5.0%: minimum_ownership >= 15, beneficial_owner == true; 10.0%: beneficial_owner == true |
| interest | 11 | 0.0%, 10.0% | 10.0%: beneficial_owner == true; 0.0%: article_11_3_exemption == recipient_government_central_bank_subnational_or_local_authority_or_interest_paid_by_such_public_person_or_qualifying_government_owned_foreign_trade_financing, beneficial_owner == true |
| royalty | 12 | 12.0% | 12.0%: beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `not_listed`; modification `None`; candidate WHT date `None`. Article 8 adds no overlay.

Language: authentic `None`; prevailing `None`; evidence `hash_bound_repository_signature_clause_candidate`; signature clause `Dáno v Praze dne 26. dubna 1996 ve dvojõm vy-
hotovenõ v ceském, spanelském a anglickém jazyce,
pricemz vsechny texty jsou autentické. V prõpade ja-
kýchkoli rozdõlnostõ ve výkladu mezi ceským a spanel-
ským textem bude rozhodujõcõm anglický text.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: No current WHT-relevant MLI PPT effect record.

Official sources: [SRC-5C857626A8532345](https://e-sbirka.gov.cz/sb/1998/6/0000-00-00).

Candidate excerpts:

- dividend Article 10: Dividendy 1. Dividendy vyplácené spolecnostõ, která je rezi- dentem jednoho smluvnõho státu, rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto dividendy vsak mohou být rovnez zda- neny ve smluvnõm státe, jehoz je spolecnost, která je vyplácõ, rezidentem, a to podle právnõch predpisu to- hoto státu, avsak jestlize skutecný vlastnõk dividend je rezidentem druhého smluvnõho státu, dan takto stano- vená nepresáhne: a) 5 procent hrubé cástky dividend, jestlize skutecný vlastnõk je spolecnost (jiná nez osobnõ spolecnost), která prõmo vlastnõ nejméne 15 procent majetku spolecnosti vyplácejõcõ dividendy; b) 10 procent hrubé cástky dividend ve vsech ostat- nõch prõpadech. Přõslusné úrady smluvnõch státu upravõ vzájemnou do- hodou zpu sob aplikace techto omezenõ. Tento odstavec se nedotýká zdanenõ zisku spolecnosti, ze kterých jsou dividendy vypláceny. 3. Výraz 1div …
- interest Article 11: U roky 1. U roky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto úroky vsak mohou být rovnez zdaneny ve smluvnõm státe, ve kterém majõ zdroj, a to podle práv- nõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk úroku je rezidentem druhého smluvnõho státu, dan takto stanovená nepresáhne 10 procent hrubé cástky úroku . Přõslusné úrady smluvnõch státu upravõ vzájemnou dohodou zpu sob aplikace tohoto omezenõ. 3. Bez ohledu na ustanovenõ odstavce 2 budou úroky uvedené v odstavci 1 zdaneny pouze ve smluv- nõm státe, jehoz je prõjemce úroku rezidentem, pokud je splnen jeden z následujõcõch pozadavku : a) prõjemcem úroku je vláda smluvnõho státu, cen- trálnõ banka smluvnõho státu nebo jeho nizsõ správnõ útvar nebo mõstnõ úrad; b) úroky jsou vyplácené jakoukoli osobou uvedenou v põsmenu a); c) úroky jsou v …
- royalty Article 12: Licencnõ poplatky a poplatky za technickou pomoc 1. Licencnõ poplatky a poplatky za technickou pomoc majõcõ zdroj v jednom smluvnõm státe a vyplá- cené rezidentu druhého smluvnõho státu mohou být zdaneny v tomto druhém státe. 2. Tyto licencnõ poplatky a poplatky za technic- kou pomoc vsak mohou být rovnez zdaneny ve smluvnõm státe, ve kterém je jejich zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize skutecný vlastnõk je rezidentem druhého smluvnõho státu, dan takto stanovená nepresáhne 12 procent hrubé cástky. 3. Výraz 1poplatky za technickou pomoca po- uzitý v této smlouve oznacuje platby jakéhokoli druhu obdrzené jako náhrada za uzitõ nebo za právo na uzitõ jakékoli technické vedomosti, zkusenosti, dovednosti, know-how nebo výrobnõch postupu nebo spocõvajõcõ v rozvoji a prevodu technického plánu nebo technic- kého vzoru. 4. Výraz 1licencnõ poplatkya pouzitý v tomto clán …

Audit package hash: `783d1f2aecf4362640d821698c6e5e31bfde20b25b73b2fc344aacad1cc4ac41`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## VN — Vietnam (STANDARD)

Base treaty: **108/1998 Sb.** (`SRC-937F596D6E57DC99`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 10.0% | 10.0%: beneficial_owner == true |
| interest | 11 | 0.0%, 10.0% | 10.0%: beneficial_owner == true; 0.0%: article_11_3_exemption == government_subnational_local_authority_or_central_bank_or_government_approved_transaction_to_approved_extent, beneficial_owner == true |
| royalty | 12 | 10.0% | 10.0%: beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `wht_effect_candidate_available`; modification `CZ-VN-MLI-WHT-PPT`; candidate WHT date `2025-01-01`. Article 8 adds no overlay.

Language: authentic `None`; prevailing `None`; evidence `hash_bound_repository_signature_clause_candidate`; signature clause `Dáno ve dvojõm vyhotovenõ v Praze dne
23. kvetna 1997 v ceském, vietnamském a anglickém
jazyce, pricemz vsechny texty jsou autentické. V prõ-
pade rozdõlnostõ výkladu bude rozhodujõcõ anglický
text.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: I confirm, for the purpose of this treaty research, that obtaining the treaty benefit was not one of the principal purposes of the transaction or arrangement in circumstances where granting that benefit would be contrary to the object and purpose of the relevant treaty provisions.

Official sources: [SRC-937F596D6E57DC99](https://e-sbirka.gov.cz/sb/1998/108/0000-00-00).

Candidate excerpts:

- dividend Article 10: Dividendy 1. Dividendy vyplácené spolecnostõ, která je rezi- dentem v jednom smluvnõm státe, osobe, která je rezi- dentem v druhém smluvnõm státe, mohou být zdaneny v tomto druhém státe. 2. Tyto dividendy vsak mohou být rovnez zda- neny ve smluvnõm státe, v nemz je spolecnost, která je vyplácõ, rezidentem, a to podle právnõch predpisu tohoto státu, avsak jestlize prõjemce je skutecným vlastnõkem dividend, dan takto stanovená nepresáhne 10 % hrubé cástky dividend. Přõslusné úrady smluvnõch státu upravõ vzájemnou do- hodou zpu sob aplikace tohoto omezenõ. Tento odstavec se nedotýká zdanenõ zisku spolecnosti, ze kterých jsou dividendy vypláceny. 3. Výraz 1dividendya pouzitý v tomto clánku oznacuje prõjmy z akciõ nebo jiných práv, s výjimkou pohledávek, s podõlem na zisku, jakoz i prõjmy z jiných práv na spolecnosti, které jsou podrobeny stejnému dan ovému rezimu jako prõjmy z akciõ podle pr …
- interest Article 11: U roky 1. U roky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluvnõho státu, mo- hou být zdaneny v tomto druhém státe. 2. Tyto úroky vsak mohou být rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize prõjemce je sku- tecným vlastnõkem úroku , dan takto stanovená nepre- sáhne 10 % hrubé cástky úroku . Přõslusné úrady smluvnõch státu upravõ vzájemnou dohodou zpu sob aplikace tohoto omezenõ. 3. Bez ohledu na ustanovenõ odstavce 2 a) úroky majõcõ zdroj v jednom smluvnõm státe bu- dou osvobozeny od zdanenõ v tomto státe, pokud jsou pobõrány a skutecne vlastneny: (i) vládou, nizsõm správnõm útvarem nebo mõst- nõm úradem druhého smluvnõho státu; nebo (ii) centrálnõ bankou druhého smluvnõho státu; b) úroky majõcõ zdroj v jednom smluvnõm státe bu- dou osvobozeny od zdanenõ v tomto státe do výse schválené vládou toh …
- royalty Article 12: Licencnõ poplatky 1. Licencnõ poplatky majõcõ zdroj v jednom smluvnõm státe a vyplácené rezidentu druhého smluv- nõho státu mohou být zdaneny v tomto druhém smluv- nõm státe. 2. Tyto licencnõ poplatky vsak mohou být rovnez zdaneny ve smluvnõm státe, v nemz majõ zdroj, a to podle právnõch predpisu tohoto státu, avsak jestlize prõjemce je skutecným vlastnõkem licencnõch poplatku a je rezidentem druhého smluvnõho státu, dan takto stanovená nepresáhne 10 % hrubé cástky licencnõch poplatku . Přõslusné úrady smluvnõch státu upravõ vzájemnou dohodou zpu sob aplikace tohoto omezenõ. 3. Výraz 1licencnõ poplatkya pouzitý v tomto clánku oznacuje platby jakéhokoli druhu obdrzené jako náhrada za uzitõ nebo za právo na uzitõ jakéhokoli autorského práva k dõlu literárnõmu, umeleckému nebo vedeckému, vcetne kinematografických filmu nebo filmu nebo nahrávek pro rozhlasové nebo televiznõ vy- sõlánõ, jakéh …

Audit package hash: `fa12fb67613e498386f392cb24d2ace5ffa8f7e5b12f24aa4425dc45841636b5`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____

## XK — Kosovo (STANDARD)

Base treaty: **38/2023 Sb.m.s.** (`SRC-CD01C24D2AD80F3A`).

Risk focus: high_level_three_income_sanity_check.

| Income | Article | Candidate rate(s) | Material candidate conditions |
|---|---:|---:|---|
| dividend | 10 | 5.0%, 15.0% | 5.0%: minimum_ownership >= 25, beneficial_owner == true; 15.0%: beneficial_owner == true |
| interest | 11 | 0.0% | 0.0%: beneficial_owner == true |
| royalty | 12 | 10.0% | 10.0%: beneficial_owner == true |

Protocol/status: `not_listed` / `not_listed`.

MLI (WHT only): `not_listed`; modification `None`; candidate WHT date `None`. Article 8 adds no overlay.

Language: authentic `['English']`; prevailing `sole_english`; evidence `current_official_pdf_signature_clause_candidate`; signature clause `DONE in duplicate at Pristina this 26 day of November 2013 in the English language.`.

Domestic/EU: Czech candidate standard/protective rates `15.0` / `35.0`; EU interaction is shown per income in the JSON audit package.

PPT: No current WHT-relevant MLI PPT effect record.

Official sources: [SRC-CD01C24D2AD80F3A](https://e-sbirka.gov.cz/sm/2023/38/0000-00-00).

Candidate excerpts:

- dividend Article 10: DIVIDENDY 1. Dividendy vyplácené společností, která je rezidentem jednoho smluvního státu, rezidentu druhého smluvního státu, mohou být zdaněny v tomto druhém státě. 2. Tyto dividendy však mohou být rovněž zdaněny ve smluvním státě, jehož je společnost, která je vyplácí, rezidentem, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník dividend je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne: a) 5 procent hrubé částky dividend, jestliže skutečným vlastníkem je společnost (jiná než osobní společnost), která přímo drží alespoň 25 procent kapitálu společnosti, která dividendy vyplácí; b) 15 procent hrubé částky dividend ve všech ostatních případech. Příslušné úřady smluvních států upraví vzájemnou dohodou způsob aplikace těchto omezení. Tento odstavec se nedotýká zdanění zisků společnosti, z nichž jsou dividendy vypláceny. 3. Výraz „dividendy“ použi …
- interest Article 11: ÚROKY 1. Úroky mající zdroj v jednom smluvním státě a skutečně vlastněné rezidentem druhého smluvního státu podléhají zdanění jen v tomto druhém státě. 2. Výraz „úroky“ použitý v tomto článku označuje příjmy z pohledávek jakéhokoliv druhu, ať zajištěných či nezajištěných zástavním právem na nemovitosti a majících či nemajících právo účasti na zisku dlužníka, a zvláště, příjmy z vládních cenných papírů a příjmy z obligací nebo dluhopisů, včetně prémií a výher, které se vážou k těmto cenným papírům, obligacím nebo dluhopisům. Penále ukládané za pozdní platbu se nepovažuje za úroky pro účely tohoto článku. Výraz „úroky“ nezahrnuje žádnou část příjmu, která je považována za dividendu podle ustanovení článku 10 odstavce 3. 3. Ustanovení odstavce 1 se nepoužijí, jestliže skutečný vlastník úroků, který je rezidentem jednoho smluvního státu, vykonává v druhém smluvním státě, ve kterém mají úroky …
- royalty Article 12: LICENČNÍ POPLATKY 1. Licenční poplatky mající zdroj v jednom smluvním státě a vyplácené rezidentu druhého smluvního státu mohou být zdaněny v tomto druhém státě. 2. Licenční poplatky uvedené v odstavci 3 písmenu a) však mohou být rovněž zdaněny ve smluvním státě, v němž mají zdroj, a to podle právních předpisů tohoto státu, avšak jestliže skutečný vlastník licenčních poplatků je rezidentem druhého smluvního státu, daň takto uložená nepřesáhne 10 procent hrubé částky licenčních poplatků. Příslušné úřady smluvních států upraví vzájemnou dohodou způsob aplikace těchto omezení. 3. Výraz „licenční poplatky“ použitý v tomto článku označuje platby jakéhokoliv druhu obdržené jako náhrada za užití nebo za právo na užití: a) jakéhokoliv patentu, ochranné známky, návrhu nebo modelu, plánu, tajného vzorce nebo postupu, počítačového programu nebo jakéhokoliv průmyslového, obchodního nebo vědeckého za …

Audit package hash: `d283770fea3173eb68ed60141575ef06dd2dea373c5ba5b9b3f323f59b35660f`.

Human QA: **PENDING**. Reviewer: ____  Date: ____  Outcome: ____  Independent review (if required): ____
