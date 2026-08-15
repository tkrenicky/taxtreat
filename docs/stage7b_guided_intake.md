# Stage 7B — guided client intake

Stage 7B turns deterministic missing-fact output into a transaction-specific
questionnaire. It does not add legal conclusions or infer unanswered facts.

## Endpoint

`POST /analysis/intake` accepts the same payload as `POST /analysis` and
returns both the current analysis and an intake plan.

Each question includes:

- a stable question identifier;
- the exact request path where an answer belongs;
- a client-fact, legal-determination, legal-evidence or FX-evidence category;
- expected response type;
- a plain-language prompt and reason;
- a supporting-document checklist;
- whether the client may answer it directly.

## Safety boundary

Client facts remain client assertions. They are not evidence of legal approval.

Items prefixed with `determination:` require explicit reviewed
determinations. Items prefixed with `legal_fact:` cannot be answered by the
client and must be resolved from released legal evidence or professional
review.

The intake plan never changes a `REVIEW_REQUIRED` result. A subsequent
analysis can become final only after the canonical engine receives sufficient
facts, determinations and released legal evidence.

## Amount and CNB evidence

If a foreign-currency amount cannot be calculated because its CNB evidence is
missing or inconsistent, the plan requests:

- payment date;
- accounting date;
- CNB rate for the earlier date;
- currency and CZK-per-unit value;
- official source URL;
- payment or accounting record.

Candidate rates remain excluded from all tax calculations.
