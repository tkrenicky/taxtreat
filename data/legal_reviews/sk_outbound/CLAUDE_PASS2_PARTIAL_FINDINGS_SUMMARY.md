# Claude Pass 2 — partial findings summary

This file records the concrete findings returned by the second independent adversarial review before its tool budget was exhausted. It is evidence for the follow-up review, not an approval record.

## Coverage limitation

Pass 2 did not finish the requested full Sections A/B/D/E/G, the full test-quality pass, or the final severity-grouped JSON. The follow-up review must finish those areas rather than treating the absence of findings as evidence of correctness.

## Findings requiring retest after remediation

### P2-001 — domestic interest/royalty provenance remained tautological

`taxtreat/tools/evaluate_sk_domestic_transaction_candidates.py` returned `source_country: SK` as a literal rather than deriving it from `domestic_transaction_condition_model.json`. A corrupted or CZ-contaminated model could therefore be hidden by the result contract.

Remediation intent: load and validate the committed model source-country provenance, derive the output provenance from that model, and fail closed if it is not SK.

### P2-002 — released non-CZ branch fell through to an unconditional 409

`app/main.py::require_analysis_source_release()` called the generic source-country gate for non-CZ countries but, after a successful release decision, fell through to `SOURCE_COUNTRY_RELEASE_GATE_MISSING` instead of returning the successful decision.

Remediation intent: return the successful non-CZ release decision and add a regression test that simulates a validly released SK package.

### P2-003 — real rendered SK HTML contained Czech source-country legal copy

A real SK report generated through the full report rendering pipeline contained Czech copy including `Informace k české srážkové dani`, Czech payer/recipient labels and a Czech-law hierarchy sentence stating that Czech domestic law sets the baseline and may be limited by a treaty.

Remediation intent: localize the full visible SK report contract after the shared frozen Czech presentation layer and fail closed if Czech-source-country legal markers survive post-render. Tests must render a real report rather than apply replacement strings to hand-picked fixtures.

### P2-004 — compliance calculation helper was Czech-law hardcoded

`build_withholding_compliance_schedule()` is a Czech helper (§38d/§38da, end-of-following-month and Czech notification concepts) and was called unconditionally by `/analysis` regardless of source country.

Remediation intent: route compliance by source country. CZ must preserve the legacy output exactly. SK must use OZN4311v26 / §43 ods. 10–11 and the 15th day of the following month for actually withheld tax. Zero-withholding notification scope remains fail-closed until separately reviewed; no Czech annual-notification fallback is permitted.

## Additional gap identified during remediation

### P2-005 — post-release dataset identity was still Czech Stage 6

Even after a future successful SK release gate, `/analysis` still derived `dataset_version` from `load_stage6_source_release()`, which is the Czech source-country Stage 6 release. The follow-up review must verify the new source-country runtime metadata resolver and prove that a non-CZ source country cannot consume the CZ Stage 6 dataset identity.

## Verified clean in Pass 2, subject to follow-up challenge

- 225 treaty scope key structure and candidate/release flags.
- 46 MLI relationship structure, including Finland supersession and Article 8 flags as sampled by the reviewer.
- Core §12 ods. 7 písm. c) dividend outside-subject structure against the primary sources sampled by the reviewer.
- OZN4311v26 / §43 ods. 10–11 monthly / 15th-day mechanics against Slovak Financial Administration guidance.

None of these statements constitutes human legal approval.
