# TaxTreat Roadmap

Status date: **4 August 2026**

## 🟡 Phase 1 — Source ingestion and identity

Completed:

- Czech treaty-partner registry
- official-document discovery and download
- deterministic source IDs and official URL candidates
- JSON source manifest
- SQLite source registry
- country and legal-act identity validation
- safe handling of shared and multi-act publications

## ✅ Phase 2 — Base-treaty parser and QA

Closed on **3 August 2026**.

Completed:

- correct treaty-sequence selection
- protection against unrelated and parallel-language content
- identification of dividend, interest and royalty articles
- validation of 100 parsed treaty-country datasets
- validation of 300 relevant article extracts
- all base-act comparisons at least 99.5%
- zero missing relevant article blocks
- zero structural parser issues
- 600 passing automated tests
- repository cleanup and removal of obsolete implementation paths

Still blocked:

- 100/100 raw artifacts are unavailable in a clean clone;
- full source SHA-256 evidence is therefore not yet reproducible;
- 89/100 datasets retain a publication-reference warning.

## 🟡 Phase 3 — Legal consolidation and effective dates

Current phase.

Required work:

- identify and assign protocols and amending instruments
- record signature, entry-into-force and effective dates
- represent treaty replacement, termination and historical validity
- process Czech and counterparty MLI positions
- determine bilateral MLI effects
- consolidate date-sensitive legal rules
- retain legal provenance for every resulting rule

AT/CH pilot completed as review-ready candidate data:

- official Czech, Austrian, Swiss and EU source registry;
- treaty/protocol effective dates for all three WHT income types;
- bilateral MLI/PPT withholding dates (AT 2021-01-01, CH 2022-01-01);
- source excerpt hashes and immutable dataset release identifier;
- independent legal approval still required before any rule becomes `verified`.

All-country scope baseline completed:

- canonical ISO-like registry for all 100 Czech treaty partners;
- all 300 country-income scopes registered with their parsed base-treaty source;
- six AT/CH scopes marked `review_ready` and 294 scopes marked
  `pending_consolidation`;
- pending scopes return `REVIEW_REQUIRED` without a candidate rate and list the
  missing legal layers;
- no automatically extracted base-treaty rate is promoted into the canonical
  decision engine before protocol/effective-date review.

Remaining-294 consolidation baseline completed:

- official MF treaty inventory captured for all 100 partners as at 4 February
  2026, including base publications, protocols, corrections and MLI notices;
- all 294 non-pilot Articles 10-12 stored as hashed review candidates;
- rate candidates extracted for 293/294 scopes; Greek dividends correctly
  remain without a treaty rate cap;
- known semantic false positives are quarantined (including the Chilean 50%
  financing condition) and cannot enter the active rule engine;
- 62 official Czech MLI WHT effect notices captured with hashed excerpts and
  dates, including 60 partners outside the AT/CH pilot;
- all 294 scopes remain `pending_consolidation` until protocol, special-rule,
  domestic/EU relief and independent-review gates are completed.

Protocol candidate consolidation completed:

- all 12 protocol instruments for the 11 non-pilot protocol partners captured
  from official publications and hashed;
- all 33 affected country-income scopes classified as rate replacement,
  conditional exemption, definition/scope change or confirmed no WHT change;
- known BY, RU, SG and UZ rate effects represented as structured candidates;
- later Belarus and Russia status instruments are represented as
  article-specific suspension overlays, resolving the former blocker without
  presenting a historical protocol rate as current;
- all 33 scopes remain `pending_consolidation` pending MLI/status,
  domestic/EU relief and independent legal approval.

Czech domestic and section 19 relief candidate consolidation completed:

- all 300 country-income scopes contain structured Czech domestic-rate
  candidates, with the standard 15% and protective 35% paths kept separate;
- current ZDP provenance and pilot effective-date anchors corrected to the
  official expression effective from 1 April 2026;
- section 19 relief candidates captured for 30 partner jurisdictions and 90
  scopes, including 84 scopes outside the AT/CH pilot;
- dividend candidates retain the 10%/12-month conditions and interest/royalty
  candidates retain all three 25% association paths, the 24-month period and
  section 38nb decision requirement;
- all new records remain review-only and cannot enter the active engine before
  full-chain and independent legal approval.

Remaining instrument-chain assembly completed:

- all 294 non-pilot scopes deterministically join the official inventory,
  base-treaty, protocol, MLI, Czech domestic and section 19 candidate layers;
- all 294 scopes have every mechanically required candidate layer assembled;
- the former 34-scope blocker queue is resolved through two additional MLI WHT
  effect candidates, seven signed-but-unratified no-current-effect records,
  article-specific BY/RU suspension overlays and an explicit Greek dividend
  no-numeric-cap conclusion;
- layer-specific rates remain separate and no chain contains or selects a final
  rate;
- all 294 chains remain `needs_review`, outside active legal rules and subject
  to semantic and independent legal approval.

Legal-review queue baseline completed:

- deterministic review packets cover all 294 non-pilot country-income scopes;
- every packet is bound to the immutable instrument-chain candidate hash and
  records all evidence source IDs and scope-specific legal-review tasks;
- primary review, rule-snapshot binding and independent approval are modeled as
  separate states;
- approval fails closed if the candidate hash is stale, any evidence artifact
  hash is missing, no canonical rule snapshot exists, or reviewer and approver
  are the same person;
- all 294 packets currently await primary review and 0 are independently
  approved or promotable into active legal rules.

## 🟡 Phase 4 — Deterministic WHT engine

Layered engine and complete AT/CH pilot country rules exist.

The API recognizes every registered treaty partner. Legal calculation remains
enabled only for AT/CH; the other countries fail closed as pending legal
consolidation rather than being misclassified as out of scope.

Reliability baseline completed:

- one canonical decision service and API path;
- mandatory transaction date in canonical core;
- transaction facts separated from legal facts;
- fail-closed unverified rules and legal facts;
- explicit `FINAL`, `REVIEW_REQUIRED` and `OUT_OF_SCOPE` states;
- eight executable AT/CH golden cases;
- deterministic source, legal-scope and release manifests.

AT/CH pilot completed:

- all six country-income scopes have domestic, treaty/protocol, MLI and
  Czech/EU-relief paths;
- candidate and final rates are separate fields;
- MLI effective-date boundary and failed-PPT regressions are executable;
- every candidate result carries rule IDs, layer outcomes, citations and a
  legal dataset release;
- all candidate scopes remain fail-closed pending four-eyes approval.

Required work:

### Dividends

- multiple treaty rates and ownership thresholds
- holding-period requirements
- beneficial-owner requirements
- special entities and exemptions
- domestic-law interaction
- Parent–Subsidiary Directive

### Interest

- treaty rates and exemptions
- government, central-bank and financial-institution rules
- beneficial-owner requirements
- domestic-law interaction
- Interest and Royalties Directive

### Royalties

- treaty rates and royalty categories
- equipment and technical-service distinctions
- beneficial-owner requirements
- domestic-law interaction
- Interest and Royalties Directive

### Quality gates

- fail-closed handling of missing facts
- legal source for every result
- positive and negative golden cases
- transaction-date regression tests
- complete country-coverage audit

## ⚪ Phase 5 — Professional reports

- structured analysis
- legal basis and source links
- assumptions and unresolved facts
- risk assessment
- required documentation
- HTML and PDF reports
- saved report representation

## ⚪ Phase 6 — Demo application

- transaction input
- analysis page
- report preview
- saved analyses
- basic account layer
- deployment and monitoring

## ⚪ Phase 7 — Commercial SaaS

- credit packages
- usage controls
- billing
- administration
- user management
- production security and compliance
