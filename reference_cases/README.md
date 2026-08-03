# TaxTreat Reference Cases

Reference cases are independently reviewable golden cases used to validate the deterministic withholding-tax engine.

## Required content

Each case must include:

- payer and recipient jurisdictions,
- transaction type,
- transaction date,
- all material transaction facts,
- expected withholding-tax result,
- Czech domestic-law analysis,
- applicable treaty article and paragraph,
- applicable protocol or amendment,
- MLI effect where relevant,
- EU directive where relevant,
- conditions and unresolved facts,
- legal source references,
- expected explanation,
- verification status.

## Validation standard

Each case should test both the expected result and the principal alternative outcomes.

Examples include:

- ownership threshold fulfilled versus not fulfilled,
- holding period fulfilled versus not fulfilled,
- beneficial owner confirmed versus unresolved,
- ordinary recipient versus government or central bank,
- treaty rate versus domestic-law fallback,
- current transaction date versus historical transaction date,
- EU directive conditions fulfilled versus not fulfilled.

A case may be marked `verified` only after independent legal review of:

- transaction facts,
- applicable legal instruments,
- calculation,
- effective dates,
- source evidence,
- expected result.

## Purpose

Golden cases serve as:

- regression controls,
- legal-quality checks,
- examples of fail-closed behaviour,
- evidence that structured rules produce the expected result.

They are not merely illustrative marketing examples.

## Current status

The reference-case framework exists, but comprehensive country coverage is not yet complete.

Building the full golden-case suite forms part of the legal-consolidation and deterministic-engine phases.

Reference cases must not be generated solely from base-treaty parser output without validating:

- protocols and amendments,
- effective dates,
- MLI effects,
- Czech domestic law,
- relevant EU legislation,
- transaction-specific conditions.
