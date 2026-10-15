# Austria reviewer workbook status — 2026-08-25

Status: **human review preparation only / not released**

The generated XLSX is a reviewer handoff artifact and is intentionally not a canonical legal dataset. This repository file records its provenance and review state only.

## Source snapshot

The reviewer workbook is built over the immutable successful Austrian acquisition snapshot from GitHub Actions run **#96** (`at-treaty-acquisition`, artifact SHA-256 `9fe8af155561e3545275362e99431683edc9f2331da91a27efcf3d33c185ec41`).

Snapshot facts: 89 treaty partners, 722 acquired official-source objects, 19 attachment-acquisition failures requiring review/adjudication and 2 curated royalty source overrides.

The workbook applies the current PR #166 review schema and decision architecture over that preserved source snapshot. It must not be represented as a current-head legal approval or as evidence that human review has occurred.

## Review architecture

Review preserves the order: domestic scope → domestic non-rate relief/exemption → special international relief → DTT/MLI substantive entitlement → Austrian relief-at-source procedure → payment-date WHT → refund → assessment/creditability.

A substantive/treaty rate must never be assumed to equal payment-date withholding. For royalties, the reviewer must confirm the withholding base together with the rate; the 20% gross route is separate from the 23% corporate net-expense route.

## Workbook population

- 267 income scopes (89 partners × dividend / interest / royalty)
- snapshot-based prioritisation: 123 HIGH / 113 MEDIUM / 31 STANDARD
- 31 royalty partners in the snapshot/current-schema risk queue
- domestic/procedural review matrix
- source provenance for all 722 acquired source objects
- blank reviewer decision/correction/notes fields

All reviewer decisions start as `Not reviewed`; no machine conclusion is human approval and no row is promotable to canonical solely from the workbook.

## QA / performance

Current code/QA head used for workbook generation: `5dc0a197875004a7234cc904df900fa94d25c090`. Tests, Stage 7 101-country QA, Workspace report export and AT acquisition gate were green at that head. The AT acquisition workflow uses change detection so downstream review/parser changes do not automatically re-run the expensive RIS/BMF acquisition.

## Remaining release blockers

AT remains fail-closed. Attachment failures must be resolved/adjudicated; controlling treaty/instrument text and conditions require human review; domestic/procedural candidate branches require confirmation; MLI/status-instrument effects must be completed where relevant; reviewer corrections must be deterministically materialised; independent approval and release-gate requirements remain mandatory.
