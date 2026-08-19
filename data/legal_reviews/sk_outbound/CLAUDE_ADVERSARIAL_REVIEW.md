# TaxTreat Slovakia — independent adversarial review brief

## Review target

Repository: `tkrenicky/taxtreat`

Compare:

- base: `main`
- head: `feat/sk-review-ready-20260819`

Review the complete Slovakia source-country implementation introduced by that diff. Do not assume any prior AI conclusion, test expectation, extracted rate, legal interpretation, risk classification, or implementation choice is correct.

## Role

Act as an independent adversarial reviewer of a deterministic withholding-tax engine. Your task is to find defects, unsupported assumptions, source/logic mismatches, incomplete release gates, Czech-to-Slovak leakage, and tests that merely restate implementation rather than prove the legal/product requirement.

Do **not** modify files. Do **not** approve scopes. Do **not** convert machine candidates into legal conclusions.

## Review bundle / generated evidence

The Git branch intentionally does **not** commit generated machine-review JSON outputs. When this review is supplied as a ZIP, use the bundle created by:

`PYTHONPATH="$PWD" python scripts/build_sk_claude_review_bundle.py`

The bundle builder must fail closed unless the expected local generated SK evidence exists and the pre-release runtime invariants still hold. The ZIP includes the full tracked repository snapshot, `main...HEAD` binary patch, git metadata/status, and the generated SK evidence enumerated in `claude_review_scope.json`.

If you are reviewing a clean Git checkout rather than the prepared ZIP, do **not** treat missing generated JSON files as evidence that the implementation never produced them. Instead, report that the review input is incomplete unless the machine evidence has been regenerated from official sources. Do not fabricate or reconstruct missing generated evidence.

## Hard product invariants

1. Slovakia is a legally distinct source-country package. Czech domestic law, Czech ZDP references, Czech exemptions, Czech deadlines, Czech CNB/CZK behavior, Czech source catalogs, or Czech runtime fallbacks must never be used for an SK transaction.
2. Production SK runtime must remain closed until all explicit release gates are satisfied.
3. Machine extraction/candidate evidence is not a legal conclusion.
4. Human legal review is intentionally `0/225` before the full package is ready.
5. A user representation must not substitute for a source-backed annual cooperating/non-cooperating-state legal fact.
6. Multiple treaty percentages extracted from text must never be collapsed to the lowest percentage merely because it is numerically favorable.
7. Pair-specific MLI matching and withholding-effective dates must be respected. Slovakia must not reuse the Czech MLI model.
8. Taiwan's primary-source-summary fallback must remain explicit, non-byte-exact, candidate-only, non-approved, and non-released.
9. The normal production `/analysis` path must fail closed for unreleased SK. Any SK pre-release endpoint must be visibly non-production and incapable of returning a final rate.
10. CZ behavior must remain unchanged by the SK work.

## Current machine state to challenge, not assume

Expected current preparation state:

- 75 treaty relationships
- 225 treaty scopes: dividend / interest / royalty
- 46 MLI relationships / 138 MLI scopes
- 87 non-MLI scopes
- 225 semantic candidate scopes
- 152 scopes with one or more machine rate candidates
- 13 exclusive-residence-taxation candidates
- 3 Taiwan primary-summary-fallback scopes
- 225/225 pre-release candidate evaluations
- 225/225 `REVIEW_REQUIRED`
- 0 final-rate scopes
- 0 Czech-runtime-fallback scopes
- 0 human-reviewed scopes
- 0 production-released scopes

Treat every count above as something to independently verify from repository data and code.

## Known unresolved blocker

The official Slovak Ministry of Finance 2026 cooperating-state list is identified as MF document `49561`, valid 1 January 2026 through 31 December 2026, but the official attachment body has not yet been ingested into the repository. The engine must therefore fail closed on any legal branch requiring this annual list.

Do not reconstruct that list from treaty partners, secondary sources, memory, or inference.

## Legal-engine areas requiring separate review

### A. Slovak domestic dividends

Challenge the implementation of the corporate dividend logic under Slovak Act No. 595/2003 Z. z., especially the model around § 12 ods. 7 písm. c).

Check at least:

- corporate-recipient scope;
- distribution deductibility at payer;
- non-cooperating-state exception;
- § 3 ods. 1 písm. f) exception;
- whether the treatment is correctly represented as an outside-subject rule rather than a Czech-style participation/Parent-Subsidiary exemption;
- whether treaty/MLI analysis is reached only when a domestically taxable branch remains;
- whether any transaction fact is improperly allowed to replace the annual MF legal fact.

### B. Slovak interest and royalties

Challenge:

- § 43 domestic WHT branch;
- Slovak registered-PE attribution/exclusion branch;
- EU interest/royalty relief conditions under the Slovak model;
- beneficial/final recipient condition;
- direct 25% ownership link;
- 24-month condition and post-payment completion/refund handling;
- interactions with treaty/protocol/MLI limitations;
- any hidden Czech threshold, § 38da, CZK, or CNB assumption.

### C. Treaty evidence

For all 225 scopes, inspect whether the machine layer preserves rather than prematurely resolves:

- article-number variance;
- rate candidates;
- ownership-linked rates;
- beneficial-owner wording;
- PE/fixed-base carve-outs;
- holding-period language;
- exclusive-residence taxation wording;
- source URL/hash provenance;
- non-standard source handling;
- Taiwan fallback handling.

Identify scopes where candidate extraction is structurally insufficient to support a future deterministic rule without human interpretation.

### D. MLI

Independently inspect the Slovak MLI model and pair-specific evidence. Slovakia may have WHT-relevant effects beyond PPT, including where matched:

- Article 3 transparent entities;
- Article 4 dual-resident entities;
- Article 7 PPT;
- Article 8 dividend transfer transactions / 365-day test;
- Article 10 third-jurisdiction PE;
- Articles 12–15 PE-related provisions.

Check matching, reservations/options, notice supersession, and WHT effective dates. Do not assume `mli_listed_modified` proves a specific substantive modification.

### E. Compliance

Challenge the ordinary corporate outbound dividend/interest/royalty compliance model, including:

- form `OZN4311v26`;
- § 43 ods. 11;
- monthly periodicity;
- notification/remittance deadline modeled as the 15th day of the following calendar month;
- Page B / nonresident individual-specific logic if present in broader code;
- correction mechanics if modeled;
- absence of a configured separate ordinary annual WHT return for the standard D/I/R flow;
- separation from special regimes/forms under other § 43 provisions.

Flag any statement that is broader than the supporting primary-source evidence.

### F. Runtime/API/release gates

Inspect:

- `taxtreat/countries/registry.py`
- `taxtreat/services/decision.py`
- `taxtreat/services/source_country_release_gate.py`
- `taxtreat/services/sk_prerelease_decision.py`
- `app/sk_prerelease.py`
- `app/main.py`
- SK runtime manifest and matrix tools/tests.

Try to find any path by which:

- SK reaches the Czech Stage 6 rule catalog;
- SK reaches Czech calculation/compliance helpers after its release gate should have stopped processing;
- an unsupported source country is accepted;
- a pre-release result can claim a final rate or production status;
- a generated artifact can be missing while tests still create a false sense of readiness;
- release can be flipped by one flag without all 225 scopes and source gates being independently satisfied.

### G. Report/UI

Inspect the actual `/ui` workspace implementation and report path for residual Czech behavior in SK context, including:

- `source_country` payload;
- EUR vs CZK;
- CNB requests;
- PE labels;
- payer labels;
- domestic-law references;
- § 38d / § 38da leakage;
- source metrics;
- compliance wording and deadlines;
- report HTML localization;
- CZ → SK → CZ state restoration;
- any UI statement that sounds like a released legal conclusion while SK remains pre-release.

Do not treat string-replacement localization as sufficient if the underlying legal semantics or calculation remain Czech-specific.

## Test-quality review

For each important invariant, ask whether the test:

1. tests an external requirement or merely repeats a constant from implementation;
2. includes an adversarial negative case;
3. would fail if a Czech fallback leaked into SK;
4. would fail if release state was accidentally enabled;
5. would fail if the cooperating-state list was missing or stale;
6. would detect incorrect treaty-rate selection among multiple candidates;
7. would detect incorrect MLI effective dates;
8. would detect cross-country UI/report state contamination.

Identify missing tests explicitly.

## Required output format

Return findings only. Group them as:

- `CRITICAL`
- `HIGH`
- `MEDIUM`
- `LOW`

For every finding provide:

- finding ID;
- severity;
- exact file and line(s), or exact JSON path/data record;
- defect/concern;
- concrete failure scenario;
- why current tests do or do not catch it;
- recommended fix;
- recommended regression test;
- whether the issue blocks human review, production release, both, or neither.

Then provide:

1. a short `NO FINDING / VERIFIED INVARIANTS` section for invariants you actively attempted to break but could not;
2. a `TOP 10 MANUAL LEGAL REVIEW TARGETS` section listing the highest-value country/income scopes or cross-cutting legal issues for a human Slovak tax-law review;
3. a final machine-readable JSON object with counts by severity and an array of finding IDs.

Do not mark the branch approved. Do not infer that green tests establish legal correctness.
