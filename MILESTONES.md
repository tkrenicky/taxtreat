# TaxTreat Roadmap

Status date: **3 August 2026**

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

## 🟡 Phase 4 — Deterministic WHT engine

Initial framework and pilot country rules exist.

Reliability baseline completed:

- one canonical decision service and API path;
- mandatory transaction date in canonical core;
- transaction facts separated from legal facts;
- fail-closed unverified rules and legal facts;
- explicit `FINAL`, `REVIEW_REQUIRED` and `OUT_OF_SCOPE` states;
- executable CZ–CH golden case;
- deterministic source, legal-scope and release manifests.

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
