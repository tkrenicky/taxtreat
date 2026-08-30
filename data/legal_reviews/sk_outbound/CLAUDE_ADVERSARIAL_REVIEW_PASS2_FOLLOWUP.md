# TaxTreat Slovakia — adversarial review Pass 2 follow-up

## Objective

Continue and complete the independent adversarial review that was cut short by tool limits in Pass 2. Do not repeat only the already-covered runtime trace. Finish the previously incomplete legal/runtime/report/test areas and independently retest every remediation recorded in `CLAUDE_PASS2_PARTIAL_FINDINGS_SUMMARY.md`.

Repository: `tkrenicky/taxtreat`

Compare `main` with `feat/sk-review-ready-20260819` and inspect the full snapshot supplied in this bundle. Do not modify files. Do not approve scopes.

## Mandatory remediation retest

Attempt to break each item below. Do not trust the remediation description.

### R1 — interest/royalty domestic provenance

Inspect `taxtreat/tools/evaluate_sk_domestic_transaction_candidates.py` and the consuming SK prerelease evaluator. Prove whether a corrupted `domestic_transaction_condition_model.json` with `source_country=CZ` or another country is rejected. Confirm that any runtime dependency provenance reported by the SK candidate evaluator is derived from real inputs rather than a literal.

### R2 — released non-CZ gate fallthrough

Inspect the final `app/main.py::require_analysis_source_release`. Simulate the generic source-country release gate returning a valid released SK decision. Confirm the function returns it instead of falling through to a synthetic 409. Also verify that an unreleased or malformed release manifest still fails closed.

### R3 — source-country release evidence

Try to release SK by changing only `CountryConfig.runtime_released=True`. It must still be blocked by independent committed evidence. Independently test incomplete scope count, human review <225, missing cooperating-state evidence, calculation policy not ready, zero-withholding notification scope not ready, report leakage gate not ready, missing/malformed manifest and source-country mismatch.

### R4 — runtime dataset identity

Inspect `taxtreat/services/source_country_runtime_metadata.py` and the final `/analysis` integration. A released non-CZ source country must never use `global_cz_outbound/stage6_source_release.json` as its dataset identity. Attempt to install a spy/throwing CZ Stage 6 loader and prove SK does not invoke it.

### R5 — source-country calculation/compliance routing

Inspect `taxtreat/services/source_country_calculation.py` and final `app/main.py` calls.

For CZ, prove the wrapper preserves existing output exactly.

For SK, verify:
- no CNB/CZK/whole-crown behavior leaks from the Czech calculation helper;
- final calculation remains fail-closed until the source-backed Slovak rounding/FX policy is completed;
- actually withheld tax uses §43 ods. 10–11 / OZN4311v26 and the statutory 15th day of the following calendar month;
- no §38d/§38da or Czech annual notification logic is reachable;
- zero-withholding/non-taxing notification scope remains review-required rather than inheriting a Czech annual regime;
- any operational deadline adjustment beyond the statutory 15th is not overstated if public-holiday handling is incomplete.

### R6 — real rendered report

Do not test `html_localization.py` with isolated hand-written strings only. Construct or reuse a real SK report object and run the complete public `taxtreat.services.reporting.render_report_html()` pipeline.

Search the rendered output systematically for at least:
- Czech WHT titles and hierarchy statements;
- `586/1992`, `§ 38d`, `§ 38da`, `ZDP`;
- Czech payer/recipient role labels;
- `Od českého pravidla`, `české právo zdanit`, `Česká vnitrostátní úprava`;
- CNB-specific copy;
- Czech source-country treaty naming;
- incorrect `lang=cs`;
- any Czech final-copy string introduced by `release_polish.py` after the base renderer.

Confirm the fail-closed post-render leakage assertion would detect a newly introduced Czech legal marker rather than only replacing a known list.

## Complete the legal areas Pass 2 did not finish

### A — domestic dividends

Perform the statutory deep-dive requested in the original brief, including the unresolved concern around §3 ods. 1 písm. e)/g) or any other exception that could affect the modeled §12 ods. 7 písm. c) branch. Use current official Slovak primary sources. Distinguish what is proven from what requires human interpretation.

Verify the decision order and whether any domestic exception is omitted, over-broad or represented with the wrong tax-treatment semantics.

### B — interest and royalties

Complete the Slovak domestic WHT and EU relief review. Check §16 source characterization, relevant §43 branches, registered-PE attribution, beneficial/final recipient requirements, direct 25% ownership relationship, 24-month test, refund mechanics and interaction with treaty/MLI.

Challenge every machine condition against current official primary sources. Flag any condition that is too broad, too narrow or unsupported.

### D — MLI systematic review

Do more than spot-check one relationship. Programmatically inspect all 46 MLI relationships and then manually inspect all exceptional patterns.

Check pair-specific matching/reservations/options/effective dates for WHT-relevant Articles 3, 4, 7, 8, 10 and 12–15 where relevant. Confirm Article 8 365-day treatment only where both positions match. Confirm notice supersession (including Finland) and identify any missing or null effective-date field that downstream code could mistakenly treat as resolved.

Do not infer substantive modification merely from a relationship being listed as MLI-modified.

### E — compliance

Complete Page A/B and row-level review of OZN4311v26. Check rows for ordinary nonresident vs non-cooperating-state cases, individualization, beneficial/final-recipient uncertainty, correction mechanics and whether the package makes any unsupported statement that a separate annual ordinary WHT return never exists.

Review special §43 forms only to ensure the ordinary D/I/R flow does not accidentally absorb them.

### G — UI and report

Complete the systematic residual-Czech-behavior review using the real browser/UI and real report pipeline. Inspect CZ → SK → CZ state restoration, payload source_country, EUR/CZK, CNB calls, payer/recipient labels, PE wording, source metrics, compliance copy, disabled prerelease semantics and report export.

Do not treat the existing `BROWSER_SMOKE_OK` log as sufficient; inspect what it does not cover, especially report generation/export.

## Test-quality pass

Finish the original test-quality criteria across every critical invariant. Specifically identify tests that:
- assert literals emitted by the same implementation rather than an independent property;
- lack a negative/adversarial case;
- would still pass if a Czech fallback were introduced;
- only cover the prerelease state and not a simulated future release state;
- use hand-picked report fixture strings instead of a real render;
- validate counts without validating semantic correctness.

## Required output

Return a complete review, not another partial summary if avoidable.

Group findings by `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` and for each provide:
- finding ID;
- exact file/line or JSON path;
- defect;
- concrete failure scenario;
- evidence;
- why tests catch or miss it;
- recommended fix;
- regression test;
- whether it blocks human review, production release, both or neither.

Then include:
1. `REMEDIATION RETEST` for P2-001 through P2-005 with status `FIXED`, `PARTIAL`, or `NOT FIXED` and evidence;
2. `NO FINDING / VERIFIED INVARIANTS` only for invariants actively attacked;
3. `TOP MANUAL LEGAL REVIEW TARGETS` updated after the completed statutory review;
4. a final machine-readable JSON object with severity counts, finding IDs and remediation statuses.

Never mark the branch approved. Human legal review remains 0/225 unless the repository itself proves otherwise.
