# Austria reviewer workbook status — 2026-08-25

Status: **human review preparation only / not released**

The generated XLSX is a reviewer handoff artifact and is intentionally not a canonical legal dataset. This repository file records its provenance and review state only.

## Source snapshot

The reviewer workbook is built over the immutable successful Austrian acquisition snapshot from GitHub Actions run **#96** (`at-treaty-acquisition`, artifact SHA-256 `9fe8af155561e3545275362e99431683edc9f2331da91a27efcf3d33c185ec41`).

Snapshot facts:

- 89 treaty partners;
- 722 acquired official-source objects;
- 19 attachment-acquisition failures requiring review/adjudication;
- 2 curated royalty source overrides.

The workbook applies the **current PR #166 review schema and decision architecture** over that preserved source snapshot. It must not be represented as a current-head legal approval or as evidence that human review has occurred.

## Current decision architecture

Review must preserve the following ordering and distinctions:

1. domestic scope;
2. domestic non-rate relief / exemption;
3. special international relief where applicable (including EU–Switzerland Article 9);
4. DTT / MLI substantive entitlement;
5. Austrian relief-at-source procedure;
6. withholding actually due at the payment date;
7. refund route where applicable;
8. assessment / creditability consequences where relevant.

A substantive or treaty rate must never be assumed to equal the payment-date withholding rate.

For royalties, the reviewer must confirm the withholding **base** together with the rate. In particular, the current candidate model keeps the 20% gross route separate from the 23% corporate net-expense route.

## Workbook population

The generated reviewer workbook contains:

- 267 income scopes (89 partners × dividend / interest / royalty);
- review-priority queue: 123 HIGH / 113 MEDIUM / 31 STANDARD under the snapshot-based prioritisation;
- 31 royalty partners in the snapshot/current-schema risk queue;
- a domestic/procedural review matrix;
- complete source provenance rows for the 722 acquired source objects;
- blank reviewer decision/correction/notes fields.

All reviewer decisions start as `Not reviewed`; no machine conclusion is human approval and no row is promotable to canonical solely from the workbook.

## QA / performance

Current code/QA head used for workbook generation: `5dc0a197875004a7234cc904df900fa94d25c090`.

Required CI was green at that head:

- Tests;
- Stage 7 101-country end-to-end QA;
- Workspace report export acceptance;
- AT evidence acquisition gate.

The AT acquisition workflow uses change detection so downstream review/parser changes do not automatically re-run the expensive full RIS/BMF acquisition.

## Remaining release blockers

AT remains fail-closed. Before production materialisation/release, at minimum:

- attachment-acquisition failures must be resolved or adjudicated;
- controlling treaty/instrument text and conditions must be human-reviewed;
- domestic/procedural candidate branches must be confirmed;
- MLI/status-instrument effects must be completed where relevant;
- reviewer corrections must be deterministically materialised;
- independent approval and release-gate requirements must be satisfied.
