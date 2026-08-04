# TaxTreat

TaxTreat is a deterministic withholding-tax analysis platform initially focused on payments from the Czech Republic to Czech treaty partners.

Supported transaction types:

- dividends,
- interest,
- royalties.

The intended product combines verified legal sources, date-sensitive legal rules, deterministic calculations and reviewable professional reports.

## Current reliability baseline

The structural base-treaty parser phase was completed on 3 August 2026. This
does not by itself establish source auditability or the correctness of a final
withholding-tax rate.

| Area | Status |
|---|---:|
| Parsed treaty-country datasets | 100/100 structurally complete |
| Dividend, interest and royalty article checks | 300/300 structurally present |
| Reproducible raw source artifacts and hashes | 0/100 available in a clean clone — blocked |
| Registered country-income scopes | 300/300 |
| Review-ready legal scopes | 6/300 (AT/CH; independent approval pending) |
| Pending legal consolidation | 294/300 |
| Official MF instrument inventory | 100/100 treaty partners |
| Remaining base-treaty review candidates | 294/294; 293 with rate candidates |
| Official MLI WHT effect candidates | 62 partners; 60 outside AT/CH |
| Fully approved legal scopes | 0/300 |
| Executable golden cases | 8 (all intentionally `REVIEW_REQUIRED`) |
| Production readiness | blocked by source and legal approval gates |

Zákony pro lidi is used as a readable verification mirror for the relevant published Czech act. It is not treated as the sole authoritative source for the current legal position.

## Canonical decision path

All new decisions run through `taxtreat.services.decision`. The API and golden
cases use that same public service. Legacy extraction engines remain only for
parser compatibility and must not be used to issue a final report.

The canonical path requires a transaction date, separates transaction facts
from date-sensitive legal facts, returns `REVIEW_REQUIRED` for a registered
scope whose legal consolidation is incomplete, returns `OUT_OF_SCOPE` only
outside the registered product scope, and fails closed whenever legal
provenance or approval is incomplete.

## Current development phase

Development now moves from reliable base-treaty extraction to legal consolidation and date-sensitive calculation.

The AT/CH pilot now covers:

- Czech domestic withholding and statutory exemptions;
- treaty and protocol rates for dividends, interest and royalties;
- AT MLI/PPT withholding effect from 2021-01-01;
- CH MLI/PPT withholding effect from 2022-01-01;
- Parent–Subsidiary and Interest–Royalties Directive paths;
- official-source registry, excerpt hashes and dataset release IDs;
- deterministic layered calculation and eight executable golden cases.

All pilot rules remain `needs_review`: the engine exposes a traceable candidate
rate but cannot publish a `FINAL` rate until independent approval metadata is
recorded. The remaining 98 treaty partners and their 294 country-income scopes
are registered and exposed by the API, but deliberately return no active
calculation rate until their complete instrument chains and independent legal
reviews are finished.

The remaining 294 scopes now have a separate pre-consolidation evidence layer.
It contains the official MF instrument chain, the complete hashed Article
10-12 text, quarantined extractor output and official Czech MLI WHT effective
dates where published. This layer is visible in release metrics but is not
loaded as active legal rules, so unfinished protocol or semantic review cannot
produce a client-facing candidate rate.

The protocol overlay is now consolidated as a review-only candidate layer for
all 11 non-pilot partners whose MF inventory lists a protocol: 12 official
protocol instruments and 33 country-income scopes. It records explicit rate,
exemption, definition and no-WHT-effect conclusions, with source-document
hashes and candidate effective dates. Later status instruments for Belarus and
Russia remain explicit blockers. No protocol candidate is loaded into the
active decision engine before MLI/status, domestic/EU and four-eyes review.

The Czech domestic-law layer now covers all 300 scopes as review-only
candidates. It distinguishes the standard 15% withholding rate from the
protective 35% rate and anchors the current rules to the official ZDP expression
effective from 1 April 2026. Section 19 relief candidates cover 30 eligible
partner jurisdictions and 90 scopes: the 26 other EU Member States plus
Switzerland, Iceland, Liechtenstein and Norway. The model retains the 12- and
24-month timing alternatives, all three statutory forms of direct capital
connection, beneficial-owner and section 38nb conditions, and anti-abuse
blockers. The 84 non-pilot relief scopes remain outside the active engine until
four-eyes approval.

## Important legal boundary

The completed parser phase demonstrates that the relevant base-treaty articles can be reliably identified and extracted.

A production conclusion must additionally consider protocols, amendments, effective dates, MLI effects, domestic law, EU directives and transaction-specific facts.

Until these layers are completed and validated, unresolved cases must not be presented as definitive results.

## Repository structure

- `data/raw/` — stored source documents
- `data/processed/` — document manifest and SQLite registry
- `data/parsed/` — parsed treaty datasets
- `data/cz_treaty_partners.json` — canonical 100-partner/ISO registry
- `data/audits/` — parser and source-quality audits
- `data/legal_rules/` — structured legal-rule datasets
- `data/legal_sources/` — official legal-source registry
- `data/legal_facts/` — date-sensitive legal facts
- `data/legal_consolidation/` — fail-closed treaty, MLI and protocol candidates
- `data/golden_cases/` — executable end-to-end legal cases
- `knowledge_base/` — country-pair knowledge records
- `taxtreat/parser/` — extraction and article-selection logic
- `taxtreat/engine/` — deterministic rule extraction and evaluation
- `taxtreat/services/` — analysis services
- `reference_cases/` — independently reviewable golden cases
- `app/` — initial API layer

`GET /jurisdictions` exposes the complete 100-country registry and separates
review-ready income types from scopes still awaiting legal consolidation.

## Documentation

- [Project Bible](PROJECT_BIBLE.md)
- [Roadmap](MILESTONES.md)
- [Reference-case standard](reference_cases/README.md)

## Local verification

Install and run:

    python -m pip install -r requirements-dev.txt
    python -m pytest -q
    python -m taxtreat.pipeline.run_pipeline

The production release gate is intentionally red until source artifacts with
full hashes and at least one independently approved legal scope are present:

    python -m taxtreat.pipeline.run_pipeline --production

## Source ingestion

    python -m venv .venv
    . .venv/bin/activate
    pip install -r requirements.txt
    python run.py

Primary outputs:

- `data/raw/**`
- `data/processed/document_manifest.json`
- `data/processed/taxtreat_cz.sqlite`
