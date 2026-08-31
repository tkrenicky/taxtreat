# Stage 6 semantic audit closure — 2026-08-30

## Status

The semantic audit itself is complete across the 101 CZ outbound Stage 6 country packages and all three product income types: dividends, interest and royalties.

This closure does **not** mean that every existing Stage 6 production rule remains releasable. The audit deliberately identified and quarantined semantic projection defects. A quarantined scope must receive a corrected QA package and a new exact hash-bound legal approval before production materialization can resume for that scope.

## Audit coverage completed

The completed sweep covers:

- royalty-category taxonomy and category-to-rate coverage;
- overlapping / identical-applicability royalty branches with different outcomes;
- catch-all and complement semantics;
- dividend company-status conditions;
- direct vs indirect ownership conditions;
- voting-interest vs capital-ownership conditions;
- dividend holding-period thresholds and broad-bucket approximation risk;
- interest special-condition enums and client-answerable vs professional-review routing;
- composite government / central-bank / public-financing classifications;
- overloaded `beneficial_owner` conditions containing non-boolean legal classifications;
- coarse browser entity types vs narrower treaty-specific statuses;
- voting-rights inference from capital ownership;
- stale transaction facts and cross-calculation state leakage;
- beneficial-owner / PE UX defaults and explicit treaty-residence handling;
- raw EU-relief structured excerpt leakage;
- Section 19 English i18n case sensitivity;
- treaty-locale provenance for authentic, non-authentic, synthesised, machine-translated and suspended text.

## Quarantine / remediation state

`data/legal_consolidation/semantic_remediation_condition_candidates_20260829.json` contains **36 source-backed scope-level remediation candidates**.

The evaluator contains a matching `_PENDING_SEMANTIC_REMEDIATION_SCOPES` registry. The regression contract requires exact equality between the remediation candidate scopes and the engine quarantine set.

For every quarantined scope, the evaluator returns `REVIEW_REQUIRED` with no rate before ordinary rule evaluation. This prevents a known defective Stage 6 projection from producing a client-facing `FINAL` result while the corrected package is awaiting review.

Detected defect classes include, among others:

- corporate reduced-dividend branches where Stage 6 omitted company status;
- missing direct-ownership conditions;
- capital ownership used where the treaty requires voting interest;
- missing one-year holding conditions in reduced-dividend branches;
- Philippines royalty 10% / 15% branches projected with identical conditions;
- Taiwan royalty 10% catch-all projected as literal `other` instead of the complement of equipment;
- Kuwait and Qatar public-body/entity classifications overloaded into the `beneficial_owner` fact.

## Automated semantic closure gates

The added tests require that:

1. every Stage 6 condition fact has an explicit semantic classification;
2. no unregistered identical-applicability / different-outcome Stage 6 conflict exists;
3. every treaty royalty category is parseable into the atomic UI taxonomy;
4. atomic royalty UI categories do not collapse distinct outcomes under the same remaining conditions;
5. every detectable reduced-dividend company/direct/voting/holding projection gap is quarantined;
6. every non-boolean `beneficial_owner` condition is quarantined;
7. the remediation candidate registry and evaluator quarantine registry match exactly;
8. pending semantic remediation candidates remain `needs_review` and explicitly forbid automatic production approval.

## Governance closure

The remediation layer is inserted before country-QA package hashing. Therefore a corrected QA package receives a different `package_sha256` from the previously approved package.

`build_stage6_production_rules.py` requires exact `package_sha256` equality across:

- the country QA package;
- `stage6_production_approval.json`;
- `stage6_production_materialization_readiness.json`; and
- the canonical production source-release gate.

A semantic reprojection therefore cannot silently inherit the old Stage 6 approval. Production materialization remains blocked until a new hash-bound review / approval chain exists.

## Web blockers closed in this branch

- raw structured `eu_relief` excerpts are no longer rendered as client-facing legal text;
- Step 4 English exact translation is case-insensitive and includes explicit Section 19 labels/statuses;
- official-source synthesised and machine-translated English treaty text may be displayed only with explicit provenance badges;
- non-authentic official translation and suspended application have distinct visible status treatment.

## Remaining validation boundary

No GitHub Actions run exists for the current PR head because the repository workflow targets pull requests to `main`, while PR #170 targets the PR #169 feature branch. Earlier branch-specific workflow experimentation produced no usable run and was removed.

Accordingly:

- **semantic audit coverage: complete**;
- **known semantic defects: quarantined and source-backed for reprojection**;
- **full executable regression-suite result: not yet obtained in this environment**;
- **36 corrected scopes: not production-approved until a new human/hash-bound approval is recorded**.

This distinction is intentional and must be preserved in release communication.
