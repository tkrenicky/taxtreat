# Stage 7A — end-to-end acceptance and professional reporting

Stage 7A validates the released Czech outbound withholding-tax workflow from
request through deterministic evaluation, source-backed API response and a
professional JSON/HTML report.

## Scope

- Source country: Czech Republic.
- Income: dividends, interest and royalties.
- Pilot partners: AT, CH, DE, SG and TW.
- Negative controls: unknown `CZ-ZZ` and reversed `AT-CZ` direction.
- Legal rule release: `stage6-production-rules-2026-08-12.1`.
- Source release: `stage6-source-release-2026-08-12.1`.
- Legal-data cut-off: 2026-08-12.

## Discovery is not approval

The first 15 empty-fact cases are discovery fixtures. Their expected result is
`REVIEW_REQUIRED`; they identify the user facts and determinations needed to
evaluate a released rule path. They do not fabricate transaction facts, legal
conclusions, reviewer actions or approvals.

Final acceptance fixtures may be frozen only after their facts, expected rule
path, rate, citations and supporting documents have been explicitly reviewed.

## Report contract

Every report contains:

- a stable content-derived report ID;
- generation timestamp and legal-data cut-off;
- legal-rule and source-release identifiers;
- transaction scope, supplied facts and user determinations;
- final or candidate result, missing facts and failed conditions;
- deterministic decision path and official source citations;
- required-documentation checklist;
- a clear statement that the output is legal information and workflow support,
  not tax advice.

Unknown Czech treaty pairs remain HTTP 409 fail-closed. Reverse-direction cases
remain outside the current Czech outbound scope.
