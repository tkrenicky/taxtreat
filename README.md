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
| Structured legal scopes | 4/300 |
| Fully approved legal scopes | 0/300 |
| Executable golden cases | 1 (currently `REVIEW_REQUIRED`) |
| Production readiness | blocked by source and legal approval gates |

Zákony pro lidi is used as a readable verification mirror for the relevant published Czech act. It is not treated as the sole authoritative source for the current legal position.

## Canonical decision path

All new decisions run through `taxtreat.services.decision`. The API and golden
cases use that same public service. Legacy extraction engines remain only for
parser compatibility and must not be used to issue a final report.

The canonical path requires a transaction date, separates transaction facts
from date-sensitive legal facts, returns `OUT_OF_SCOPE` for unsupported cases,
and fails closed whenever legal provenance or approval is incomplete.

## Current development phase

Development now moves from reliable base-treaty extraction to legal consolidation and date-sensitive calculation.

The next phase covers:

- protocols and amending instruments,
- entry-into-force and effective dates,
- treaty replacement and termination,
- bilateral MLI matching,
- Czech domestic-law rules,
- relevant EU directives,
- structured dividend, interest and royalty rules,
- deterministic selection of the applicable rule,
- golden cases and fail-closed validation.

The repository already contains the initial deterministic legal-rule framework and pilot structured rules. This is groundwork, not complete legal coverage.

## Important legal boundary

The completed parser phase demonstrates that the relevant base-treaty articles can be reliably identified and extracted.

A production conclusion must additionally consider protocols, amendments, effective dates, MLI effects, domestic law, EU directives and transaction-specific facts.

Until these layers are completed and validated, unresolved cases must not be presented as definitive results.

## Repository structure

- `data/raw/` — stored source documents
- `data/processed/` — document manifest and SQLite registry
- `data/parsed/` — parsed treaty datasets
- `data/audits/` — parser and source-quality audits
- `data/legal_rules/` — structured legal-rule datasets
- `knowledge_base/` — country-pair knowledge records
- `taxtreat/parser/` — extraction and article-selection logic
- `taxtreat/engine/` — deterministic rule extraction and evaluation
- `taxtreat/services/` — analysis services
- `reference_cases/` — independently reviewable golden cases
- `app/` — initial API layer

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
