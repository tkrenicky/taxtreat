# TaxTreat Project Bible

Status date: **4 August 2026**

This document defines the product scope, architecture, quality standard and current development status of TaxTreat.

## 1. Product vision

TaxTreat should produce a deterministic, reviewable and source-backed withholding-tax analysis for a specified cross-border payment.

Initial product scope:

- payer resident in the Czech Republic,
- recipient resident in a Czech treaty state,
- dividends, interest or royalties,
- analysis for a specified transaction date.

The output should identify:

- Czech domestic-law treatment,
- applicable double tax treaty,
- treaty article and rate,
- relevant protocol or amendment,
- applicable MLI modification,
- relevant EU directive,
- factual conditions,
- required documentation,
- unresolved assumptions or risks,
- final legal basis and withholding-tax result.

## 2. Core principles

### Deterministic

Legal rates and conditions must be selected from structured and validated rules. They must not be invented or inferred without a verified legal basis.

### Source-backed

Every material conclusion must be traceable to a particular legal instrument, provision and source document.

### Date-sensitive

The applicable rule must be determined for the transaction date, including historical treaty versions and effective dates.

### Fail closed

Missing, conflicting or unverified information must result in a conditional or unresolved outcome, not an unsupported definitive answer.

### Reviewable

A tax professional must be able to reproduce the result from stored transaction facts, legal rules and source references.

## 3. Source hierarchy

Preferred source order:

1. official Czech legal publication or authority,
2. official publication of the counterparty state,
3. OECD official MLI materials,
4. EUR-Lex,
5. other verified official treaty or protocol publication,
6. readable legal mirrors used for extraction and cross-checking.

Zákony pro lidi is used as a readable verification mirror for Czech published acts. It is not the sole authority for the current consolidated legal position.

## 4. Processing architecture

    Official legal sources
            ↓
    Document manifest and source registry
            ↓
    Country and legal-act identity validation
            ↓
    Treaty sequence and article selection
            ↓
    Base-treaty Articles 10, 11 and 12 or equivalents
            ↓
    Protocol, amendment and MLI consolidation
            ↓
    Date-sensitive structured legal rules
            ↓
    Hash-bound review packet and four-eyes approval
            ↓
    Deterministic WHT engine
            ↓
    Golden-case and completeness validation
            ↓
    Professional report
            ↓
    Demo application

## 5. Completed baseline

The source-ingestion and base-treaty parser phases were closed on 3 August 2026.

| Metric | Result |
|---|---:|
| Parsed treaty-country datasets | 100 |
| Relevant article comparisons | 300 |
| Missing relevant article blocks | 0 |
| Structural parser issues | 0 |
| Base-act comparisons at least 99.5% | 100/100 |
| Automated tests | 732 passing |
| Raw source artifacts reproducible in a clean clone | 100/100 |
| Recorded SHA-256 hashes for raw treaty artifacts | 100/100 |
| Source auditability | complete (no longer a production blocker) |
| Registered country-income scopes | 300/300 |
| Review-ready AT/CH legal scopes | 6/6 |
| Pending legal consolidation | 294/300 |
| Official MF instrument inventories | 100/100 partners |
| Remaining base-treaty candidate scopes | 294/294; 293 numeric-rate candidates + 1 explicit no-cap conclusion |
| Official MLI WHT effect candidates | 64 partners; 62 outside AT/CH; 7 signed/no-current-effect determinations |
| Remaining instrument-chain candidates | 294 assembled; 0 hard-blocked |
| Candidate legal-review packets | 294/294 queued; 0 approved/promotable |
| Independently approved legal scopes | 0/300 |
| Exact tracked duplicates | 0 |

The parser phase therefore has zero known defects within its defined scope.
Source auditability is complete and is no longer a production blocker. The
remaining production gate is legal approval: no legal scope has yet completed
primary review and independent four-eyes approval, 294 non-pilot review packets
remain awaiting primary review, and no scope may be presented as FINAL before
those approval gates are satisfied.

## 6. Current readiness estimate

These percentages are planning estimates, not legal-quality scores.

| Area | Estimate |
|---|---:|
| Source ingestion and identity | 100% |
| Base-treaty parser and article identification | 100% |
| Base-treaty text QA | 100% |
| Protocol and effective-date mapping | AT/CH pilot complete |
| MLI layer | AT/CH pilot complete |
| All-country instrument inventory | 100/100 official MF rows captured |
| Remaining base-treaty candidates | 294/294 captured; semantic review pending |
| Remaining MLI WHT effect dates | 62 effect candidates plus 7 explicit no-current-effect determinations; approval pending |
| Protocol-effect candidates | 33 scopes / 11 partners / 12 instruments |
| Czech domestic-law candidates | 300/300 scopes; 294 outside pilot |
| Section 19 relief candidates | 90 scopes / 30 partners; 84 outside pilot |
| Remaining instrument-chain candidates | 294/294 assembled; 0 hard-blocked |
| Candidate legal-review queue | 294/294 packets awaiting primary review; 0 approved/promotable |
| Registered legal scope | 300/300 scopes |
| Structured legal rules | 6/300 scopes; AT/CH pilot complete |
| Deterministic rule engine | AT/CH layered path complete |
| Golden cases and legal QA | 8 executable candidate cases |
| Professional reports | 10% |
| Demo API | 10% |
| Demo web interface | 0% |

The AT/CH calculation pilot is review-ready but not legally releasable. Overall
production readiness remains blocked by the absence of a legal scope that has
completed primary review and independent four-eyes approval. No scope may be
presented as FINAL before those gates are satisfied.

For the remaining 98 treaty partners, the official Czech instrument inventory
and all 294 relevant base-treaty articles are now stored as hashed review
candidates. These records are deliberately separate from active legal rules:
protocol amendments, special-rate conditions, EU/domestic relief and four-eyes
approval must still be consolidated before a candidate can enter the canonical
calculation path.

For the 11 non-pilot partners with protocols, the protocol layer is now stored
as 33 structured review candidates based on 12 official instruments. These
records distinguish rate replacements, conditional exemptions, definition or
scope changes and protocols with no Article 10-12 effect. Belarus and Russia
now also have article-specific, date-sensitive status-instrument candidates.
All records remain outside the active engine.

The Czech domestic-law candidate layer now covers all 300 scopes and keeps the
standard 15% rate separate from the protective 35% path. Section 19 relief is
represented for 30 eligible partner jurisdictions and 90 scopes, including 84
outside the pilot. These records preserve statutory ownership, duration,
beneficial-owner, section 38nb and anti-abuse conditions and remain outside the
active engine pending four-eyes approval.

The review-only candidate layers are now joined in one deterministic
instrument-chain registry for the remaining 294 scopes. All 294 are
mechanically assembled. The former 34 gaps are represented explicitly: two
additional MLI WHT effect candidates, seven signed-but-unratified no-effect
determinations, two status-instrument overlays and one Greek dividend no-cap
conclusion. Assembly does not promote a scope to `review_ready`; every
non-pilot chain still requires semantic and independent legal review.

Every non-pilot chain now has a deterministic legal-review packet bound to its
candidate SHA-256. The packet identifies the complete evidence-source set and
all scope-specific review tasks. A primary reviewer may return the candidate or
accept it for independent approval, but the approval gate remains closed until
all evidence artifacts are bound by SHA-256 and a canonical rule snapshot is
recorded. The reviewer and approver must be different identities. At the
current baseline all 294 packets await primary review and none can be promoted
into active legal rules until the existing approval gates are satisfied.

## 7. Definition of core completion

The legal and calculation core is complete only when:

- every supported treaty has a complete legal-instrument chain,
- protocols and amendments are assigned to the correct treaty,
- every rule has valid-from and, where relevant, valid-to dates,
- treaty replacements and terminations are represented,
- bilateral MLI effects are determined,
- Czech domestic law is represented,
- relevant EU directives are represented,
- all supported countries contain structured dividend, interest and royalty rules,
- all material factual conditions are structured,
- unresolved facts produce a fail-closed result,
- every conclusion contains legal provenance,
- positive and negative golden cases cover material outcomes,
- the full-country completeness audit reports no known gap,
- all automated tests pass.

“100%” means complete coverage of the defined scope with zero known defects and controlled handling of uncertainty. It does not mean that future legal changes cannot occur.

## 8. Structured rule requirements

Each rule should contain, where relevant:

- payer and recipient jurisdiction,
- transaction type,
- legal instrument,
- article and paragraph,
- standard and reduced rates,
- ownership threshold,
- holding period,
- beneficial-owner condition,
- entity-type condition,
- government or public-body exemption,
- related-party limitation,
- permanent-establishment interaction,
- valid-from and valid-to dates,
- protocol or MLI override,
- source reference,
- verification status.

## 9. Golden-case standard

Each golden case must contain:

- complete transaction facts,
- transaction date,
- expected result,
- applicable legal instruments,
- expected rate,
- conditions and assumptions,
- negative alternatives,
- source evidence,
- independent-review status.

Golden cases are regression controls, not merely illustrative examples.

## 10. Current phase

The current phase is:

**Legal consolidation and effective dates**

Required sequence:

    legal-instrument inventory
    → protocol assignment
    → effective dates
    → MLI matching
    → consolidated rules
    → complete country coverage
    → golden cases
    → professional reports
    → demo application

The report generator and demo must not become the principal focus before the legal core can reliably identify the rule applicable on a specified transaction date.

## 11. Initial demo boundary

The first demo should support:

- Czech payer,
- one foreign recipient,
- dividends, interest or royalties,
- specified transaction date,
- ownership and beneficial-owner facts,
- source-backed result,
- explicit unresolved-state handling.

The first demo does not need:

- payments originating from every country,
- VAT, customs or transfer-pricing analysis,
- accounting treatment,
- billing or subscription functionality.

## 12. Phase governance

A phase may be closed only after:

1. its defined scope is complete,
2. the relevant quality audit reports no known gap,
3. regression tests pass,
4. project documentation is updated,
5. obsolete implementation paths are removed,
6. changes are merged into `main`.

The source-ingestion and parser phases satisfy these conditions subject to the final pull-request merge.
