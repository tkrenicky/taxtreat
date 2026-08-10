# CZ-core scalable legal QA and release workflow

Status: proposed machine-enforced workflow, awaiting human QA. This document
does not record a legal review, approval, verification, effective-date
conclusion, or production release.

## Product-scope MLI path

For Czech outbound dividends, interest, and royalties the country package uses
only this path:

1. establish whether the bilateral agreement is a Covered Tax Agreement and
   whether the relevant MLI positions match;
2. include only a modification capable of affecting these WHT outputs;
3. present Article 7 PPT as an anti-abuse condition, never an automated legal
   conclusion; and
4. bind the pair-specific Czech MF WHT effective-date notice.

The official Czech OECD position expressly reserves the entirety of Article 8.
MLI Article 8 therefore adds no 365-day dividend holding period to a Czech CTA.
For the current product, Article 7(1) PPT is the only provision carried as a
direct WHT-output condition. Article 6 is retained once as interpretive preamble
context. Capital gains, PE provisions, MAP, corresponding adjustments,
arbitration, and administrative provisions are outside this product output and
do not influence the WHT result.

The evidence and exact hashes are in
`data/legal_reviews/global_cz_outbound/cz_wht_mli_product_scope.json`. Every
pair-specific MLI result remains candidate evidence with `needs_review` status.

## PPT product condition

Where the country package has a WHT-relevant MLI PPT effect or official treaty
evidence of a bilateral PPT/equivalent anti-abuse provision, TaxTreat asks one
representation:

> I confirm, for the purpose of this treaty research, that obtaining the treaty
> benefit was not one of the principal purposes of the transaction or
> arrangement in circumstances where granting that benefit would be contrary
> to the object and purpose of the relevant treaty provisions.

Confirmed means the treaty research may be presented on that stated user basis,
subject to every other treaty and domestic condition. Not confirmed or unknown
retains the research but prevents any unconditional statement that treaty
relief is available and flags a separate PPT/anti-abuse assessment. Neither path
means TaxTreat has determined that the PPT is satisfied.

## Country-package QA

All three income scopes are reviewed together. The machine assigns exactly one
risk category:

- `STANDARD`: no enumerated exception or elevated feature;
- `ELEVATED`: unusual numbering, material protocol overlay, multiple bilateral
  instruments, unusual language/prevailing
  text, or a preserved historical/current official-byte difference; or
- `EXCEPTION`: conflicting primary evidence, unresolved legal effect, treaty
  status uncertainty, or effective-date conflict.

The classifier is deterministic. Machine classification is not legal review.
Article 7 PPT applicability plus its pair-specific WHT effective date is a
standard cross-cutting product condition. It does not by itself elevate a
mechanically clean package; elevation requires another country-specific feature.
The concise reviewer view is split into ten Markdown batches of ten countries;
the JSON queue retains full candidate excerpts, conditions, references, and
hashes for audit.

## Approval and release

Every country requires one hash-bound high-level QA event. All `EXCEPTION`
packages require a separate independent reviewer. A deterministic 5% sample of
`STANDARD` and 10% sample of `ELEVATED` packages also requires independent
review; the sample is bound to the methodology version and treaty-pair ID.
The category quota is exact (rounded up) and selection uses deterministic
SHA-256 ranking. This is a methodology-control sample, not a second full treaty
review.

Country QA alone never verifies a scope or promotes a rule. Release still
requires correction closure, green automated invariants, a separate explicit
hash-bound rule-promotion action, and an explicit production source-release
action. Reviewer and independent reviewer identities must differ where the
second review is required.

The legacy 294-scope four-eyes path remains fail-closed in this change. The new
country-level gate is additive because replacing the existing promotion path
before any real country QA records or an approved migration policy would weaken
the only live promotion control. Its hard-coded locations and the safe migration
boundary are listed in `cz_scalable_release_governance.json`.

## Expected effort

The operating target is 3–5 minutes for a `STANDARD` country and 8–15 minutes
for an `ELEVATED` country. `EXCEPTION` work is issue-driven and has no artificial
minimum. Independent work is limited to all exceptions and the deterministic
sample. For the current 80/20/0 queue, primary QA is estimated at 400–700
minutes and the six-package independent sample at another 28–50 minutes: about
7–13 hours in total. These are planning estimates, not completed time or review
records.
