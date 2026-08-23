# TaxTreat Slovakia — independent adversarial review, pass 2

## Purpose

This is the second independent adversarial review of the Slovakia source-country package. The first pass was intentionally partial. Do not repeat that limited coverage. This pass must focus on the areas that the first reviewer explicitly did not complete, and must independently re-test the two substantive technical findings from pass 1 after their remediation.

Repository: `tkrenicky/taxtreat`

Compare:

- base: `main`
- head: `feat/sk-review-ready-20260819`

Do not modify files. Do not approve scopes. Do not treat machine candidates or green tests as legal conclusions.

## First-pass findings to re-test

### FINDING-001 — runtime CZ leakage signal

The first pass found that `czech_runtime_fallback_used=False` was previously a literal constant. The remediation adds runtime dependency source-country provenance and derives the CZ-leakage signal from actual dependency provenance.

Independently verify that:

- the signal is no longer a tautological constant;
- a deliberately injected CZ domestic dependency is detected;
- the normal SK path reports only SK dependencies;
- the 225-scope validator cannot silently pass if a CZ dependency appears;
- no other shared runtime dependency can bypass the provenance check.

If the remediation is insufficient, issue a new finding.

### FINDING-003 — release by one flag

The first pass found that a future non-CZ source country could potentially be released by flipping `CountryConfig.runtime_released=True` without independent legal-package evidence. The remediation adds an independent committed source-country release manifest/evidence gate.

Independently verify that:

- `runtime_released=True` alone cannot release SK;
- human review completion, country-specific source readiness and explicit release eligibility are independently required;
- missing or malformed release manifests fail closed;
- CZ production behavior remains unchanged;
- `/analysis`, `/analysis/intake` and `/analysis/report` cannot bypass the second gate.

## Mandatory coverage — do not skip

The first review explicitly did not complete these areas. This pass must cover them.

### A. Slovak domestic dividends

Review the full model and code path around Slovak Act No. 595/2003 Z. z., especially § 12 ods. 7 písm. c).

Check:

- corporate-recipient scope;
- treatment as outside subject of corporate income tax rather than a Czech/EU-style Parent-Subsidiary exemption;
- payer deductibility condition and partial/deductible extent semantics;
- § 3 ods. 1 písm. f) exception;
- non-cooperating-state exception under § 2 písm. x) and relevant § 43 branch;
- decision precedence: domestic outside-subject rule before treaty/MLI only where legally appropriate;
- whether unresolved cooperating-state status correctly prevents a final domestic conclusion;
- whether any user fact can improperly substitute for the source-backed annual MF legal fact;
- whether the model is safe when the annual list is eventually ingested.

Use official primary sources for any legal challenge or verification.

### B. Slovak interest and royalties

Review the full domestic and EU-relief candidate logic, including:

- § 43 domestic WHT branches;
- registered Slovak PE attribution/exclusion;
- EU interest/royalty relief legal-person/PE scope;
- beneficial/final recipient requirement;
- direct 25% ownership link and allowed relationship directions;
- 24-month holding condition;
- post-payment completion/refund mechanics;
- interaction with treaty and MLI limitations;
- any hidden Czech threshold, CZK, CNB, § 38d or § 38da assumption.

Use official primary sources for legal conclusions.

### D. MLI — systematic review

Do not merely spot-check one relationship. Programmatically inspect all 46 MLI relationships / 138 scopes, then manually inspect the highest-risk exceptions.

Review:

- Slovak MLI source provenance;
- covered-tax-agreement matching;
- Slovakia and partner reservations/options;
- Article 3 transparent entities where relevant;
- Article 4 dual-resident entities;
- Article 7 PPT;
- Article 8 dividend transfer transactions / 365-day condition;
- Article 10 third-jurisdiction PE;
- Articles 12–15 PE-related provisions where they can affect WHT analysis;
- pair-specific withholding effective dates;
- superseding notices/instruments, including Finland;
- whether `mli_listed_modified` or a general effective date is ever used as a substitute for pair-specific matching.

List every relationship whose machine evidence is structurally insufficient for deterministic release without human interpretation.

### E. Compliance

Review the Slovak ordinary corporate outbound dividend/interest/royalty compliance model in detail against official Financial Administration / Slov-Lex sources.

Verify or challenge:

- `OZN4311v26`;
- § 43 ods. 11;
- monthly period;
- notification and remittance by the 15th day of the following calendar month;
- withholding moment under § 43 ods. 10;
- row 02 / row 03 treatment where modeled;
- Page B individualization logic where modeled;
- correction mechanics;
- whether the statement that no separate ordinary annual WHT return is configured is appropriately narrow;
- separation from special § 43(13)/(15) forms/regimes.

Flag any UI/report wording broader than the evidence.

### G. UI/report — rendered-behavior review

Perform a systematic residual-Czech-behavior audit of the actual SK UI/report path. Do not stop at source-code string searches.

Review at least:

- source-country switch CZ → SK → CZ;
- EUR vs CZK;
- CNB calls/fields;
- payer labels and registry assumptions;
- PE labels;
- domestic-law references;
- Czech ZDP / Act 586/1992 references;
- § 38d / § 38da leakage;
- compliance form/deadline wording;
- source counts 75/225 vs 101/303;
- report title, facts, conclusion, citations, documentation and compliance sections;
- Taiwan fallback rendering;
- whether any SK pre-release surface sounds like a final/released legal conclusion;
- whether string-replacement localization leaves Czech semantics underneath.

Use the bundled successful browser smoke log as evidence of what was tested, but independently inspect what it did not test.

## Treaty/data systematic checks

Programmatically inspect all 225 scopes, not a spot sample, for:

- missing/duplicate scope keys;
- article-resolution statuses weaker than clean expected-number/title matches;
- multiple rate candidates;
- ownership-linked rates;
- holding-period candidates;
- exclusive-residence candidates;
- BO wording;
- PE/fixed-base wording;
- primary-summary fallback;
- source URL/hash presence and consistency;
- accidental approval/release fields.

Do not decide which treaty rate is legally final unless human-reviewed source context supports it.

## Test-quality pass

Inspect the tests around every material invariant above. Specifically identify tests that only reassert implementation constants instead of testing external behavior. Require adversarial negative cases for:

- CZ dependency leakage;
- accidental release-flag flip;
- malformed/missing release manifest;
- missing annual cooperating-state evidence;
- multiple treaty rate candidates;
- MLI effective-date mismatch;
- CZ → SK → CZ UI contamination;
- report Czech-law leakage.

## Required output

Return findings grouped as `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`.

For each finding provide:

- finding ID, continuing numbering from the prior review if practical;
- severity;
- exact file/line or JSON path/record;
- defect/concern;
- concrete failure scenario;
- why tests do/do not catch it;
- recommended fix;
- recommended regression test;
- whether it blocks human review, production release, both, or neither;
- primary-source citation for legal findings.

Then provide:

1. `PASS-1 FINDINGS RETEST` — explicit verdict on FINDING-001, FINDING-002, FINDING-003;
2. `SYSTEMATIC COVERAGE COUNTS` — number of treaty scopes, MLI relationships/scopes, compliance models and rendered UI/report surfaces actually inspected;
3. `NO FINDING / VERIFIED INVARIANTS`;
4. `TOP MANUAL LEGAL REVIEW TARGETS` updated after this deeper pass;
5. final machine-readable JSON with severity counts, finding IDs, and pass/fail status for each prior finding.

Do not mark the branch approved. Human legal review remains 0/225 until separately performed.
