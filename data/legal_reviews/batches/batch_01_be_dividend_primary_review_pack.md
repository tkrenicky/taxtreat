# Primary legal review – CZ → BE / dividendy

**Packet:** `CZ-BE-DIV-LEGAL-REVIEW`

**Review hash:** `f445a97fff44b14aedd291b6d8693f36553095b51c632c2d289959ad09d283c6`

## 1. Základní smlouva

- Publikace: 95/2000 Sb.m.s.
- Článek: 10 – DIVIDENDY
- Source ID: `SRC-E16828A7660D9797`
- Stav: `needs_review`

### Kandidátní smluvní sazby

- **5.0 %** — Article 10 — minimum_ownership >= 25; beneficial_owner == true
- **15.0 %** — Article 10 — beneficial_owner == true

## 2. České domácí právo

```json
{
  "effective_from": "2026-04-01",
  "income_scope_reference": "section 22(1)(g)(3)",
  "protective_rate": 35.0,
  "protective_rate_condition": "recipient is outside the EU/EEA and no qualifying treaty or tax-information-exchange instrument is applied",
  "protective_rate_reference": "section 36(1)(c)",
  "source_id": "CZ-ZDP-2026-04-01-OPEN-DATA",
  "standard_rate": 15.0,
  "standard_reference": "section 36(1)(b)(1), referring to section 22(1)(g)(3)"
}
```

## 3. EU osvobození

```json
{
  "all_of": [
    {
      "fact": "recipient_is_qualifying_company_form",
      "operator": "==",
      "value": true
    },
    {
      "fact": "recipient_is_tax_resident_in_eligible_jurisdiction",
      "operator": "==",
      "value": true
    },
    {
      "fact": "recipient_subject_to_qualifying_corporate_tax",
      "operator": "==",
      "value": true
    },
    {
      "fact": "recipient_has_no_tax_exemption_or_zero_rate_option",
      "operator": "==",
      "value": true
    },
    {
      "fact": "ownership_percent",
      "operator": ">=",
      "value": 10
    },
    {
      "fact": "recipient_is_parent_company",
      "operator": "==",
      "value": true
    }
  ],
  "anti_abuse_review_required": true,
  "directive_source_id": "EU-PSD-2011-96-CONSOLIDATED",
  "holding_period_one_of": [
    {
      "fact": "holding_period_months",
      "operator": ">=",
      "value": 12
    },
    {
      "all_of": [
        {
          "fact": "holding_period_will_reach_months",
          "operator": ">=",
          "value": 12
        },
        {
          "fact": "statutory_clawback_acknowledged",
          "operator": "==",
          "value": true
        }
      ]
    }
  ],
  "legal_reference": "section 19(1)(ze), (3), (4), (6), (8) and (11)",
  "rate": 0.0,
  "regime": "eu_directive_domestic_implementation"
}
```

## 4. Protokoly

- Protokol č. 17/2015 Sb.m.s.
  - Source ID: `CZ-MF-BE-D0E145875613`
  - Účinnost kandidáta: 2016-01-01
  - Stav: `needs_review`

## 5. MLI

```json
[
  {
    "applies_to_income_types": [
      "dividend",
      "interest",
      "royalty"
    ],
    "effect_id": "CZ-BE-MLI-WHT-PPT",
    "effective_from": "2021-01-01",
    "mli_article": "Article 7(1) PPT",
    "recipient_country": "BE",
    "recipient_country_name": "Belgie",
    "source_country": "CZ",
    "source_excerpt": "Článek 2 Výše uvedené změny Smlouvy se v obou smluvních státech provádějí následovně: 1) pokud jde o daně vybírané srážkou u zdroje z částek vyplácených nebo připisovaných nerezidentům, jestliže skutečnost dávající vzniknout takovým daním nastala k 1. lednu 2021 nebo později; 2) pokud jde o všechny ostatní daně, na daně ukládané za zdaňovací období začínající",
    "source_excerpt_sha256": "514b559c36618b0160d8cb64a3c5dd1a73ec669da0ea1c6ca9cc2a8f600af51a",
    "source_page_id": "CZ-MF-BE-FC7B1E3B8535",
    "source_page_url": "https://mf.gov.cz/cs/dane-a-ucetnictvi/financni-zpravodaj/2020/financni-zpravodaj-cislo-23-2020-39686",
    "source_pdf_url": "https://mf.gov.cz/assets/cs/media/Financni-zpravodaj_2020-c-23.pdf",
    "verification_status": "needs_review"
  }
]
```

## 6. Otázky pro primary review

### 1. Does the 5% rate require direct or direct/indirect ownership of at least 25%?

- Odpověď: `[ANO / NE]`
- Právní odůvodnění:
- Supporting source IDs:

### 2. Is the 15% rate the residual rate for all other beneficial owners?

- Odpověď: `[ANO / NE]`
- Právní odůvodnění:
- Supporting source IDs:

### 3. Does the protocol leave Article 10 unchanged?

- Odpověď: `[ANO / NE]`
- Právní odůvodnění:
- Supporting source IDs:

### 4. Are the Czech PSD conditions correctly represented, including the 12-month holding-period rule?

- Odpověď: `[ANO / NE]`
- Právní odůvodnění:
- Supporting source IDs:

## 7. Výsledek primary review

- Treaty rates confirmed:
- Beneficial owner requirement confirmed:
- Protocol effects confirmed:
- MLI effects confirmed:
- Czech domestic rate confirmed:
- EU relief confirmed:
- Effective dates confirmed:
- Anti-abuse review completed:
- Proposed rule snapshot:
- Reviewer ID:
- Reviewed at:
- Review outcome:

> Tento dokument nepředstavuje schválené právní pravidlo. Packet zůstává fail-closed až do nezávislého schválení.
