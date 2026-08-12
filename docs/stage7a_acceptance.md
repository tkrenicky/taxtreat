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

## Acceptance matrix

The versioned fixture at `data/acceptance/stage7a_pilot.json` contains exactly
17 cases:

- 15 released empty-fact discovery cases covering five pilot partners and three
  income types;
- one unknown Czech pair that must return HTTP 409 and the canonical
  `SOURCE_NOT_RELEASED` blocker;
- one reverse-direction request that must remain `OUT_OF_SCOPE`.

Run the deterministic matrix and write both machine-readable and reviewable
artifacts with:

```bash
python scripts/run_stage7a_acceptance.py \
  --output-dir artifacts/stage7a
```

The command exits non-zero when any case fails. Its SHA-256 is derived from the
canonicalized case results, so unchanged runtime behavior produces unchanged
acceptance evidence.

## Optional transaction amount

A CZK request may include:

```json
{
  "transaction_amount": {
    "amount": "100000.55",
    "currency": "CZK"
  }
}
```

For a foreign-currency payment, the request must additionally carry frozen CNB
rate evidence:

```json
{
  "transaction_amount": {
    "amount": "1000.00",
    "currency": "EUR",
    "payment_date": "2026-08-12",
    "accounting_date": "2026-08-10",
    "exchange_rate": {
      "source": "CNB",
      "currency": "EUR",
      "czk_per_unit": "24.85",
      "effective_date": "2026-08-10",
      "source_url": "https://www.cnb.cz/..."
    }
  }
}
```

The applicable rate date is the earlier of payment and accounting, following
the confirmed Section 38 ZDP workflow. The currency amount is converted without
intermediate rounding. The resulting withholding tax is denominated in CZK and
rounded down to whole crowns under Section 36(3) ZDP.

The report preserves the original amount, both event dates, the selected rate
date, normalized CZK-per-unit rate and source URL. Missing dates, non-CNB
evidence, a currency mismatch or a rate for the wrong date produces
`NOT_CALCULATED`.

TaxTreat calculates tax only when the released legal engine returns a `FINAL`
rate. A candidate rate or `REVIEW_REQUIRED` result never produces a tax amount.
This separation prevents an unresolved legal conclusion from appearing as a
precise payable amount.

## Extensible client facts

The request already accepts structured transaction facts and user
determinations. Useful future guided inputs include:

- recipient tax residence and entity type;
- beneficial-owner status and supporting evidence;
- direct or indirect ownership percentage and holding period;
- relationship between payer and recipient;
- permanent-establishment connection;
- arm's-length limitations;
- eligibility for an EU directive exemption;
- payment, record and entitlement dates;
- available residence, ownership and exemption documents.

These inputs must remain factual or explicitly user-supplied determinations.
TaxTreat must identify missing evidence and must not invent legal approval.

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
