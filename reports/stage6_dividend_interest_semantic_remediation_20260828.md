# Stage 6 dividend and interest semantic remediation queue — 2026-08-28

This file records semantic/product compatibility findings discovered while
auditing the 101-country Stage 6 dividend and interest rules against the
browser and guided-intake fact model.

It is not a new legal approval.

## Silent-wrong paths fixed

### Core treaty assumptions

The workspace previously preselected:
- beneficial owner = yes;
- treaty residence = yes;
- Czech PE connection = no.

Those values could reach the engine without an active user decision. The same
defaults also existed in the demo/profile object and recipient edit dialog.

All three facts are now explicit tri-state inputs. Unknown stays unknown through
HTML, profile persistence, and payload construction. Transaction calculations
do not inherit these profile values automatically.

### Cross-calculation stale facts

Treaty-specific follow-up answers and transaction facts could survive into a
new calculation. They are now reset when a new calculation begins, when the
recipient changes, and when the transaction context is reset.

### Voting rights inferred from capital ownership

The browser previously copied capital ownership into voting ownership/control.
This is unsafe for treaties such as Canada where the reduced dividend rate is
based on voting power rather than capital percentage.

Voting rights are now independent explicit facts.

### Coarse recipient entity type

The browser profile exposes generic categories such as company/fund/individual,
while Stage 6 contains narrower treaty statuses such as:
- company other than partnership;
- company with share capital;
- qualifying pension fund;
- bank or financial institution;
- government / central bank / public body;
- wholly government-owned financial institutions.

A generic browser value can no longer disprove a narrower treaty status and
allow a general fallback to become FINAL. The comparison remains unresolved.

### Dividend holding-period buckets

The browser previously converted:
- "at least 12 months" to exactly 12 months;
- "less than 12 months" to 0 months.

This is legally unsafe. Japan, for example, has a 6-month dividend threshold,
while other regimes can require 24 months or two years. An 8-month holding
could therefore be incorrectly represented as zero, and a 30-month holding as
12.

The broad buckets have been removed. Production holding-period facts are now
derived only from a concrete acquisition date. If the date is unknown, the
holding-period fact remains missing and the result fails closed.

## Confirmed country examples protected by regression tests

### Australia — dividends

A generic `company` profile value cannot silently fail the
`company_other_than_partnership` branch and select the 15% fallback.

### Canada — dividends

Voting-power conditions are no longer populated from capital ownership.

### Japan — dividends

The 10% branch requiring at least 25% voting ownership and a 6-month holding
period is evaluated from the actual duration. Unknown duration remains
REVIEW_REQUIRED.

## Interest special-condition policy

Many Stage 6 interest exemptions encode an entire legal classification in one
enum value, for example combinations of:
- government or local authorities;
- central banks;
- public / government-owned financial institutions;
- export-credit institutions;
- government-guaranteed or insured financing;
- credit sales;
- minimum loan terms.

A single encoded value is no longer automatically converted into a client
Yes/No question.

Only explicitly allowlisted objective enums such as `bank` may be reduced to
a client Yes/No input. Composite treaty classifications remain professional
review.

## Safe-review / data-remediation items

### Chile — interest

The 4% branch includes `detailed_eligibility_review_required == true`.
This is not a normal transaction fact and should remain a professional/data
review item rather than being synthesized by the browser.

### Germany — dividends

A historical/special 25% branch uses
`distributed_vs_undistributed_corporate_tax_rate_difference >= 20%`.
The browser does not attempt to infer this condition. It remains review-only
unless the historical rule is separately modeled and source-validated.

### North Korea — interest

The exemption uses compound lender and borrower categories. These categories
are legal classifications and remain professional review rather than client
Yes/No shortcuts.

### Thailand — interest

The 10% Stage 6 branch uses
`company_and_financial_institution_including_insurer`. Source review confirms
that the recipient must be a company and the interest must be received by a
financial institution (including an insurance company). The structured branch
is therefore substantively consistent, although the enum label should be
treated as a legal classification rather than a generic company type.

## Automated compatibility inventory

`scripts/audit_stage6_semantic_compatibility_20260828.py` now classifies each
decision fact as one of:
- explicit browser;
- derived;
- guided client input;
- professional review;
- coarse browser;
- dynamic treaty enum;
- unsupported/unclassified;
- internal control.

For each multi-outcome scope it records semantic-safety findings so that
"verified Stage 6 package" is not treated as equivalent to "browser-ready".

## Release gate

A dividend or interest scope is browser-ready only when:

1. every fact capable of changing the rate is explicitly supplied, safely
   derived, or deliberately routed to professional review;
2. no missing/unknown value is converted to false, zero, 12 months, or another
   synthetic legal fact;
3. generic entity classifications cannot disprove narrower treaty statuses;
4. voting rights are not inferred from capital ownership;
5. holding periods are based on actual dates/durations where the treaty uses a
   duration threshold;
6. composite treaty exemptions are not reduced to client Yes/No questions
   unless their legal meaning is genuinely objective;
7. any fallback can become FINAL only after higher-priority branches have been
   excluded using sufficiently granular facts.
