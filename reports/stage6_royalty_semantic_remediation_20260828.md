# Stage 6 royalty semantic remediation queue — 2026-08-28

This file records semantic/product compatibility findings discovered while
auditing the 101-country Stage 6 royalty rules against the browser taxonomy.

It is not a new legal approval. It is a remediation queue for rules whose
structured projection or UI mapping can otherwise produce ambiguous,
incomplete, or unsafe outcomes.

## Systemic fixes already implemented

- Browser and guided intake use seven atomic royalty categories:
  copyright (non-film/non-software), film/broadcast, software, industrial IP,
  financial lease equipment, operating lease/other equipment use, and other.
- Legacy broad royalty inputs fail closed when they match treaty branches with
  different outcomes.
- An atomic royalty category that is not covered by any structured treaty
  category branch cannot fall through to a domestic FINAL result; it returns
  REVIEW_REQUIRED.
- Every Stage 6 treaty royalty category is audited for parser coverage.
- Atomic UI categories are audited for collisions where the same non-category
  conditions would otherwise lead to different rates.
- Treaty-specific answers are reset between calculations to prevent
  cross-transaction contamination.

## Confirmed semantic defect fixed

### Spain (ES)

Stage 6 contains:
- copyright excluding cinematographic/broadcast recordings: 0%;
- all other Article 12 royalties: 5%.

The parser previously mapped `all_other_article_12_royalties` back to ordinary
copyright as well, so the same copyright input could touch both 0% and 5%
branches. The parser now treats this catch-all as the complement of the
ordinary copyright carve-out.

## Confirmed data-remediation items

### Taiwan (TW)

Stage 6 contains:
- industrial/commercial/scientific equipment: 5%;
- `other`: 10%.

The source text says 10% applies "in all other cases". The structured value
`other` is therefore too narrow and collides conceptually with the browser's
literal "other" category.

Do not globally reinterpret `other` as a catch-all. Taiwan needs an explicit
structured value meaning "all royalties except equipment" (or an equivalent
country-specific complement representation) followed by source-backed
re-approval of the Stage 6 projection.

Until remediated, software/copyright/industrial-IP categories not matching the
equipment branch fail closed as REVIEW_REQUIRED rather than silently using a
wrong rate.

### Philippines (PH)

Two treaty royalty rules currently have identical applicability conditions
(`beneficial_owner == true`) but different rates (10% and 15%).

This is a Stage 6 projection defect: the missing legal distinction must be
reconstructed from the treaty text and encoded as an explicit category or
other material condition. Engine conflict detection keeps this REVIEW_REQUIRED.

### United Kingdom (GB)

The Stage 6 projection separates:
- copyright literary/artistic/scientific works including films/broadcast
  recordings: 0%;
- patent/trademark/design/process/equipment/know-how: 10%.

Computer software is not explicitly classified in the structured category
values. The engine must not infer whether software belongs to the copyright
branch or another branch. Software therefore remains REVIEW_REQUIRED pending
source-backed legal classification.

### Greece (GR)

The Stage 6 projection separates copyright (including films) at 0% from
industrial IP/equipment/know-how at 10%, without an explicit software category.
Software remains REVIEW_REQUIRED pending legal classification.

### Italy (IT)

The Stage 6 projection separates copyright (including films) at 0% from
industrial IP/equipment/know-how at 5%, without an explicit software category.
Software remains REVIEW_REQUIRED pending legal classification.

## Additional coverage-gap candidates

The semantic inventory script
`scripts/audit_stage6_semantic_compatibility_20260828.py` enumerates every
atomic royalty category that is not covered by a jurisdiction's structured
category branches. These gaps are intentionally fail-closed and should be
reviewed country-by-country before declaring the royalty web flow complete.

## Release gate

A royalty scope should not be treated as browser-ready merely because its
Stage 6 package is verified. For a multi-category treaty, browser-ready means:

1. each material treaty category is represented by an unambiguous structured
   category;
2. each of the seven atomic browser categories maps to zero or one legal
   outcome after the other transaction conditions are applied;
3. any zero-coverage category has been legally confirmed to be outside the
   treaty royalty definition, otherwise it remains REVIEW_REQUIRED;
4. catch-all branches are represented as explicit complements, not overloaded
   generic labels such as `other`;
5. a real-rule regression test exists for every previously discovered
   ambiguity that could produce a wrong FINAL result.
