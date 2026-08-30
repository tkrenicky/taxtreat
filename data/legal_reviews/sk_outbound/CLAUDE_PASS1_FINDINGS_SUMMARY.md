# Slovakia adversarial review — pass 1 findings supplied for retest

The first independent review of bundle `taxtreat-sk-claude-review-96997755206f.zip` reported partial coverage and did not approve the branch.

## Coverage limitation reported by reviewer

The reviewer fully traced the runtime/release-gate chain and verified machine-state counts, but explicitly did not complete the domestic A/B legal review, systematic 46-relationship MLI review, detailed compliance review, systematic UI/report review, or broad test-quality pass. Pass 2 must cover those omitted areas.

## FINDING-001 — HIGH

`czech_runtime_fallback_used` in `taxtreat/services/sk_prerelease_decision.py` was a literal `False` on all return paths rather than a computed property. The reviewer concluded tests checking that field could pass even if a Czech dependency leaked into SK.

Requested remediation: make the leakage signal behavior/provenance-backed or remove it, and add adversarial tests that fail when a CZ dependency is actually touched.

## FINDING-002 — LOW

`data/legal_sources/mli_partner_positions/` contained only CZ source files while SK MLI provenance lived under `data/country_sources/sk_mli_inventory_source.json`. The reviewer confirmed this was not actual CZ reuse, but recommended documenting or normalizing the source layout.

## FINDING-003 — MEDIUM

The source-country release gate depended materially on `CountryConfig.runtime_released`. A future non-CZ source country accidentally marked `runtime_released=True` could potentially pass the generic country gate without independently proving scope completion, human review, or country-specific source readiness.

Requested remediation: add a second independently sourced release gate so one config flag alone cannot release a source-country package, plus a regression test that flips the config flag while legal-package readiness remains incomplete.

## Verified invariants from pass 1

The first reviewer reported no finding on these actively checked properties:

- SK does not reach the CZ Stage 6 catalog merely because `data/legal_rules_stage6/sk.json` exists; that file is CZ-source/SK-recipient data.
- Production `/analysis`, `/analysis/intake`, and `/analysis/report` fail closed for unreleased SK.
- SK prerelease evaluation cannot return a final rate.
- Multiple treaty rate candidates are preserved rather than collapsed to the lowest rate.
- The sampled SK MLI relationship used independently sourced Slovak MLI provenance rather than the Czech model.
- Claimed machine-state counts matched the generated runtime manifest summary.

This file is only a faithful remediation/retest summary. Pass 2 must independently inspect code and evidence rather than accepting this summary as proof.
