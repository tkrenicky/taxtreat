# TaxTreat Project Bible

Status date: **4 August 2026**

This document defines the product scope, architecture, quality standard and current development status of TaxTreat.

## 1. Product vision

TaxTreat should produce a deterministic, reviewable and source-backed withholding-tax analysis for a specified cross-border payment.

Initial product scope:

- payer resident in the Czech Republic,
- recipient resident in a Czech treaty state,
- dividends, interest or royalties,
- analysis for a specified transaction date.

The output should identify:

- Czech domestic-law treatment,
- applicable double tax treaty,
- treaty article and rate,
- relevant protocol or amendment,
- applicable MLI modification,
- relevant EU directive,
- factual conditions,
- required documentation,
- unresolved assumptions or risks,
- final legal basis and withholding-tax result.

## 2. Core principles

### Deterministic

Legal rates and conditions must be selected from structured and validated rules. They must not be invented or inferred without a verified legal basis.

### Source-backed

Every material conclusion must be traceable to a particular legal instrument, provision and source document.

### Date-sensitive

The applicable rule must be determined for the transaction date, including historical treaty versions and effective dates.

### Fail closed

Missing, conflicting or unverified information must result in a conditional or unresolved outcome, not an unsupported definitive answer.

### Reviewable

A tax professional must be able to reproduce the result from stored transaction facts, legal rules and source references.

## 3. Source hierarchy

Preferred source order:

1. official Czech legal publication or authority,
2. official publication of the counterparty state,
3. OECD official MLI materials,
4. EUR-Lex,
5. other verified official treaty or protocol publication,
6. readable legal mirrors used for extraction and cross-checking.

Zákony pro lidi is used as a readable verification mirror for Czech published acts. It is not the sole authority for the current consolidated legal position.

## 4. Processing architecture

    Official legal sources
            ↓
    Document manifest and source registry
            ↓
    Country and legal-act identity validation
            ↓
    Treaty sequence and article selection
            ↓
    Base-treaty Articles 10, 11 and 12 or equivalents
            ↓
    Protocol, amendment and MLI consolidation
            ↓
    Date-sensitive structured legal rules
            ↓
    Hash-bound review packet and four-eyes approval
            ↓
    Deterministic WHT engine
            ↓
    Golden-case and completeness validation
            ↓
    Professional report
            ↓
    Demo application

## 5. Completed baseline

The source-ingestion and base-treaty parser phases were closed on 3 August 2026.

| Metric | Result |
|---|---:|
| Parsed treaty-country datasets | 100 |
| Relevant article comparisons | 300 |
| Missing relevant article blocks | 0 |
| Structural parser issues | 0 |
| Base-act comparisons at least 99.5% | 100/100 |
| Automated tests | 732 passing |
| Raw source artifacts reproducible in a clean clone | 100/100 |
| Recorded SHA-256 hashes for raw treaty artifacts | 100/100 |
| Source auditability | complete (no longer a production blocker) |
| Registered country-income scopes | 300/300 |
| Review-ready AT/CH legal scopes | 6/6 |
| Pending legal consolidation | 294/300 |
| Official MF instrument inventories | 100/100 partners |
| Remaining base-treaty candidate scopes | 294/294; 293 numeric-rate candidates + 1 explicit no-cap conclusion |
| Official MLI WHT effect candidates | 64 partners; 62 outside AT/CH; 7 signed/no-current-effect determinations |
| Remaining instrument-chain candidates | 294 assembled; 0 hard-blocked |
| Candidate legal-review packets | 294/294 queued; 0 approved/promotable |
| Independently approved legal scopes | 0/300 |
| Exact tracked duplicates | 0 |

The parser phase therefore has zero known defects within its defined scope.
Source auditability is complete and is no longer a production blocker. The
remaining production gate is legal approval: no legal scope has yet completed
primary review and independent four-eyes approval, 294 non-pilot review packets
remain awaiting primary review, and no scope may be presented as FINAL before
those approval gates are satisfied.

## 6. Current readiness estimate

These percentages are planning estimates, not legal-quality scores.

| Area | Estimate |
|---|---:|
| Source ingestion and identity | 100% |
| Base-treaty parser and article identification | 100% |
| Base-treaty text QA | 100% |
| Protocol and effective-date mapping | AT/CH pilot complete |
| MLI layer | AT/CH pilot complete |
| All-country instrument inventory | 100/100 official MF rows captured |
| Remaining base-treaty candidates | 294/294 captured; semantic review pending |
| Remaining MLI WHT effect dates | 62 effect candidates plus 7 explicit no-current-effect determinations; approval pending |
| Protocol-effect candidates | 33 scopes / 11 partners / 12 instruments |
| Czech domestic-law candidates | 300/300 scopes; 294 outside pilot |
| Section 19 relief candidates | 90 scopes / 30 partners; 84 outside pilot |
| Remaining instrument-chain candidates | 294/294 assembled; 0 hard-blocked |
| Candidate legal-review queue | 294/294 packets awaiting primary review; 0 approved/promotable |
| Registered legal scope | 300/300 scopes |
| Structured legal rules | 6/300 scopes; AT/CH pilot complete |
| Deterministic rule engine | AT/CH layered path complete |
| Golden cases and legal QA | 8 executable candidate cases |
| Professional reports | 10% |
| Demo API | 10% |
| Demo web interface | 0% |

The AT/CH calculation pilot is review-ready but not legally releasable. Overall
production readiness remains blocked by the absence of a legal scope that has
completed primary review and independent four-eyes approval. No scope may be
presented as FINAL before those gates are satisfied.

For the remaining 98 treaty partners, the official Czech instrument inventory
and all 294 relevant base-treaty articles are now stored as hashed review
candidates. These records are deliberately separate from active legal rules:
protocol amendments, special-rate conditions, EU/domestic relief and four-eyes
approval must still be consolidated before a candidate can enter the canonical
calculation path.

For the 11 non-pilot partners with protocols, the protocol layer is now stored
as 33 structured review candidates based on 12 official instruments. These
records distinguish rate replacements, conditional exemptions, definition or
scope changes and protocols with no Article 10-12 effect. Belarus and Russia
now also have article-specific, date-sensitive status-instrument candidates.
All records remain outside the active engine.

The Czech domestic-law candidate layer now covers all 300 scopes and keeps the
standard 15% rate separate from the protective 35% path. Section 19 relief is
represented for 30 eligible partner jurisdictions and 90 scopes, including 84
outside the pilot. These records preserve statutory ownership, duration,
beneficial-owner, section 38nb and anti-abuse conditions and remain outside the
active engine pending four-eyes approval.

The review-only candidate layers are now joined in one deterministic
instrument-chain registry for the remaining 294 scopes. All 294 are
mechanically assembled. The former 34 gaps are represented explicitly: two
additional MLI WHT effect candidates, seven signed-but-unratified no-effect
determinations, two status-instrument overlays and one Greek dividend no-cap
conclusion. Assembly does not promote a scope to `review_ready`; every
non-pilot chain still requires semantic and independent legal review.

Every non-pilot chain now has a deterministic legal-review packet bound to its
candidate SHA-256. The packet identifies the complete evidence-source set and
all scope-specific review tasks. A primary reviewer may return the candidate or
accept it for independent approval, but the approval gate remains closed until
all evidence artifacts are bound by SHA-256 and a canonical rule snapshot is
recorded. The reviewer and approver must be different identities. At the
current baseline all 294 packets await primary review and none can be promoted
into active legal rules until the existing approval gates are satisfied.

## 7. Definition of core completion

The legal and calculation core is complete only when:

- every supported treaty has a complete legal-instrument chain,
- protocols and amendments are assigned to the correct treaty,
- every rule has valid-from and, where relevant, valid-to dates,
- treaty replacements and terminations are represented,
- bilateral MLI effects are determined,
- Czech domestic law is represented,
- relevant EU directives are represented,
- all supported countries contain structured dividend, interest and royalty rules,
- all material factual conditions are structured,
- unresolved facts produce a fail-closed result,
- every conclusion contains legal provenance,
- positive and negative golden cases cover material outcomes,
- the full-country completeness audit reports no known gap,
- all automated tests pass.

“100%” means complete coverage of the defined scope with zero known defects and controlled handling of uncertainty. It does not mean that future legal changes cannot occur.

## 8. Structured rule requirements

Each rule should contain, where relevant:

- payer and recipient jurisdiction,
- transaction type,
- legal instrument,
- article and paragraph,
- standard and reduced rates,
- ownership threshold,
- holding period,
- beneficial-owner condition,
- entity-type condition,
- government or public-body exemption,
- related-party limitation,
- permanent-establishment interaction,
- valid-from and valid-to dates,
- protocol or MLI override,
- source reference,
- verification status.

## 9. Golden-case standard

Each golden case must contain:

- complete transaction facts,
- transaction date,
- expected result,
- applicable legal instruments,
- expected rate,
- conditions and assumptions,
- negative alternatives,
- source evidence,
- independent-review status.

Golden cases are regression controls, not merely illustrative examples.

## 10. Current phase

The current phase is:

**Legal consolidation and effective dates**

Required sequence:

    legal-instrument inventory
    → protocol assignment
    → effective dates
    → MLI matching
    → consolidated rules
    → complete country coverage
    → golden cases
    → professional reports
    → demo application

The report generator and demo must not become the principal focus before the legal core can reliably identify the rule applicable on a specified transaction date.

## 11. Initial demo boundary

The first demo should support:

- Czech payer,
- one foreign recipient,
- dividends, interest or royalties,
- specified transaction date,
- ownership and beneficial-owner facts,
- source-backed result,
- explicit unresolved-state handling.

The first demo does not need:

- payments originating from every country,
- VAT, customs or transfer-pricing analysis,
- accounting treatment,
- billing or subscription functionality.

## 12. Phase governance

A phase may be closed only after:

1. its defined scope is complete,
2. the relevant quality audit reports no known gap,
3. regression tests pass,
4. project documentation is updated,
5. obsolete implementation paths are removed,
6. changes are merged into `main`.

The source-ingestion and parser phases satisfy these conditions subject to the final pull-request merge.

## 11. Current State

**Last updated:** 9 August 2026  
**Project status:** Stage 4/7 complete; Stage 5/7 ready to start.  
**Estimated overall project completion:** approximately 82%.

### Repository baseline

- Repository: `tkrenicky/taxtreat`
- Canonical branch: `main`
- Stage 4 merge commit: `8df90db`
- Stage 4 PR: `#110 – Complete Stage 4 fail-closed runtime integration`
- Full automated suite at Stage 4 closure: **1,329 passed**
- Post-merge critical verification: **75 passed**
- Working tree after Stage 4 closure: clean and synchronized with `origin/main`.

### Current Czech outbound treaty universe

The current first-market scope is Czech outbound withholding-tax research for:

- dividends;
- interest; and
- royalties.

The repository covers approximately **100 Czech treaty partners**.

The original AT/CH pilot covers:

- 2 treaty partners;
- 6 income scopes.

The legacy `remaining_294` consolidation dataset represents:

- 98 non-pilot treaty partners;
- 3 income types per partner;
- 294 scopes.

The `remaining_294` dataset is a historical legal-review-linked snapshot. It must not be silently regenerated or rehashed where this would invalidate existing review provenance.

### Final23 Stage 4 runtime cohort

Stage 4 migrated the following 18 countries into the dedicated runtime-candidate workflow:

`AD, BA, BB, BH, BW, CL, CM, CO, CY, GB, GH, HK, JP, KR, LU, PA, PL, QA`

Coverage:

- 18 recipient countries;
- 54 income scopes;
- 78 runtime candidate rules;
- semantic mapping: **54/54**;
- repository-backed provenance: **78/78**.

All Final23 runtime rules remain:

`verification_status = needs_review`

They are intentionally stored in:

`data/legal_rule_candidates/final23/`

and not in:

`data/legal_rules/`

Therefore Final23 candidates are **not production-authoritative legal rules**.

### Production boundary

The following distinction is mandatory:

- `data/legal_rules/` = production legal-rule catalogue;
- `data/legal_rule_candidates/` = non-production candidate catalogue;
- candidate data must never become production-authoritative merely because parsing, mapping, provenance or tests succeed.

Stage 4 introduced and tested an explicit migration boundary:

`data/legal_consolidation/final23_migration_boundary.json`

The boundary preserves the existing legal-review provenance of the legacy `remaining_294` snapshot while allowing Final23 scopes to proceed through their own candidate workflow.

Existing legal-review hashes must not be rewritten merely because underlying parsed text has subsequently been corrected.

### Runtime fail-closed status

The `/analysis` runtime path now enforces the production source-release gate before invoking the decision engine for Czech-source transactions.

For an unreleased, unknown, blocked or partially verified Czech treaty pair:

- analysis stops before the decision engine;
- the API returns HTTP 409;
- the response uses `SOURCE_NOT_RELEASED`;
- unresolved legal coverage cannot silently reach a tax result.

Non-Czech source jurisdictions remain outside the current Czech source-release gate.

### Stage 4 completion definition

Stage 4 is technically complete because:

- the runtime candidate architecture is implemented;
- Final23 semantic mapping is complete;
- Final23 provenance is complete;
- candidates are isolated from production autoload;
- source-release gating is fail-closed;
- legacy legal-review hashes remain frozen;
- migration boundaries are explicitly documented and tested;
- the complete test suite passes.

Stage 4 completion **does not mean that Final23 is legally released for production**.

The Stage 4 gate expressly distinguishes:

- `stage4_complete = true`
- `production_legal_release_complete = false`

Relevant artifact:

`data/legal_reviews/global_cz_outbound/stage4_final_runtime_release_gate.json`

### Current legal readiness

The project now has a proven technical path from official-source evidence through candidate generation, provenance, review gating and runtime integration.

The primary remaining bottleneck is no longer runtime architecture.

It is **full legal consolidation and legal verification across the Czech treaty universe**.

That is the purpose of Stage 5.

## 12. Roadmap

TaxTreat development follows seven stages.

### Stage 1/7 – Foundations and data model

**Status: Complete**

Established the repository structure, core legal-data model, treaty-pair concepts, directional analysis model and basic application architecture.

### Stage 2/7 – Legal evidence and consolidation infrastructure

**Status: Complete**

Established official-source inventory, evidence handling, hashing, parsing, consolidation artifacts, review records and fail-closed legal-data concepts.

### Stage 3/7 – Pilot legal validation

**Status: Complete**

Validated the legal workflow through the AT/CH pilot and the first larger Czech outbound candidate cohorts.

Established the principle that a numeric extraction is not itself a legal conclusion.

### Stage 4/7 – Runtime decision integration

**Status: Complete – 9 August 2026**

Final23 runtime integration completed.

Key outcome:

- 18 countries;
- 54 scopes;
- 78 candidate rules;
- 54/54 semantic mapping;
- 78/78 provenance;
- strict candidate/production separation;
- source-release fail-closed API gate;
- frozen legacy review provenance;
- 1,329 passing tests.

Stage 4 is a technical runtime milestone, not a production legal-release milestone.

### Stage 5/7 – Full legal consolidation

**Status: Current stage**

Objective:

Extend legally verified Czech outbound coverage from the pilot/Final23 work to the full Czech treaty universe.

Stage 5 must consolidate, for every supported country and each of dividends, interest and royalties:

1. official treaty identity;
2. official treaty text;
3. Articles 10, 11 and 12;
4. protocols and amendments;
5. MLI position and effective dates;
6. authentic-language status and prevailing-language rules;
7. official English-version availability where relevant;
8. withholding-tax effective dates;
9. domestic-law interaction;
10. relevant EU-directive interaction;
11. structured legal-rule mapping;
12. conditions and unresolved factual requirements;
13. exact source provenance;
14. legal-review status;
15. end-to-end fail-closed behaviour.

A scope may become production-authoritative only after all mandatory legal gates are satisfied and the required human review/approval metadata is present.

**No fabricated reviewer, approver, effective date, source or verification status is permitted.**

Candidate or partially consolidated scopes remain `needs_review` / `REVIEW_REQUIRED`.

#### Stage 5 operating principles

- Official sources only for production legal content.
- Work in repeatable batches rather than one-off country-specific hacks.
- Prefer automation for collection, comparison, evidence assembly and deterministic checks.
- Do not use an LLM to invent production legal content.
- Fail closed whenever a mandatory legal layer is unresolved.
- Preserve historical source versions and legal-review provenance.
- Do not silently rehash or overwrite reviewed snapshots.
- Keep candidate and production catalogues physically and logically separated.
- Every batch must have automated integrity tests.
- Full-suite regressions must be run before merge.
- Merge only when the relevant tests are green.

#### Stage 5 completion target

Stage 5 is complete only when the intended Czech outbound treaty universe has an explicit, auditable status for all three supported income types.

Every scope must be one of:

- legally verified and eligible for production release; or
- explicitly blocked with a documented legal reason.

There must be no silent or ambiguous gaps.

### Stage 6/7 – Product, reports, UI and commercial layer

**Status: Planned**

Includes customer analysis workflow, professional research reports, source viewer, credits, account management, admin/review interfaces and commercial product presentation.

### Stage 7/7 – Production QA, security and launch

**Status: Planned**

Includes final regression testing, security review, operational controls, monitoring, release management, legal/commercial launch checks and production deployment.

## 15. AI Handover

You are joining the TaxTreat project after completion of Stage 4/7.

### Mandatory starting state

As of 9 August 2026:

- Stage 4/7 is **100% complete**.
- Overall project estimate is approximately **82%**.
- Stage 5/7 – Full legal consolidation is the current stage.
- Canonical repository branch is `main`.
- Stage 4 was merged through PR #110.
- Stage 4 merge commit is `8df90db`.
- Full test suite at closure: **1,329 passed**.
- Post-merge critical verification: **75 passed**.

Do not reopen or redesign Stage 4 unless a new regression proves that it is necessary.

### Final23

Final23 consists of:

`AD, BA, BB, BH, BW, CL, CM, CO, CY, GB, GH, HK, JP, KR, LU, PA, PL, QA`

It contains:

- 18 countries;
- 54 income scopes;
- 78 runtime candidate rules.

All 78 rules remain `needs_review`.

They are stored under:

`data/legal_rule_candidates/final23/`

They must not be moved back into the production `data/legal_rules/` directory unless they satisfy the production legal-release requirements.

### Critical architecture

Preserve all of the following:

1. Official sources are authoritative.
2. Extraction is not legal verification.
3. Provenance is not legal approval.
4. A candidate rule is not a production rule.
5. `needs_review` rules cannot produce a final production legal conclusion.
6. Unknown or incomplete law must fail closed.
7. Source-release gating must occur before the decision engine for Czech-source analyses.
8. Existing legal-review provenance and hashes must not be silently rewritten.
9. Historical legal evidence must remain auditable.
10. Never fabricate reviewer or approver metadata.

### Legacy remaining_294 boundary

`data/legal_consolidation/remaining_294_base_candidates.json`

and its downstream legal-review-linked artifacts represent a historical snapshot.

Some underlying `data/parsed/*.json` texts were later corrected.

Therefore a regenerated `remaining_294` dataset may legitimately differ from the frozen snapshot.

Do not solve this by automatically replacing legal-review hashes.

Final23 scopes have an explicit migration boundary in:

`data/legal_consolidation/final23_migration_boundary.json`

### Stage 5 mission

The next task is not to build another runtime engine.

The next task is to **scale the legal-consolidation workflow across the complete Czech outbound treaty universe**.

Before making changes:

1. inspect `PROJECT_BIBLE.md`;
2. inspect the Stage 4 release gate;
3. inspect the Final23 migration boundary;
4. inspect current legal-consolidation inventories and review artifacts;
5. inspect `git status` and recent commits;
6. identify the exact remaining country/scopes and their blockers.

Then produce an evidence-based Stage 5 execution plan.

### Working style

The project owner is not a developer.

During active implementation:

- provide large executable Bash batches;
- keep explanations short and operational;
- commands must be directly copyable;
- do not use `set -e`, `set -euo pipefail` or `exit`;
- avoid repeated small diagnostic prompts;
- prefer one comprehensive batch where safe;
- never merge if tests fail;
- report Stage 5 and whole-project progress percentages at the top of every substantive response.

Do not claim legal or production readiness merely because technical tests pass.

Accuracy and legal auditability take priority over speed.


## 14. Change Log

### 9 August 2026 – Stage 4 complete

- Completed Stage 4/7 runtime decision integration.
- Merged PR #110 into `main` at `8df90db`.
- Full repository suite: 1,329 tests passed.
- Final23 runtime cohort: 18 countries, 54 scopes and 78 candidate rules.
- Completed 54/54 semantic mappings and 78/78 repository-backed provenance.
- Moved Final23 `needs_review` rules out of production `data/legal_rules/` into `data/legal_rule_candidates/final23/`.
- Enforced strict fail-closed source-release gating before the decision engine.
- Added explicit Final23 migration boundary.
- Preserved legacy `remaining_294` legal-review hashes and historical snapshot.
- Confirmed `stage4_complete = true`.
- Confirmed `production_legal_release_complete = false`.
- Opened Stage 5/7: Full legal consolidation across the Czech treaty universe.
