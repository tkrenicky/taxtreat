# Stage 7C: authenticated workspace architecture

## Product decision

TaxTreat should become a workspace rather than a single anonymous calculation
form. The reusable business object is the foreign recipient; a payment is a
separate event and every calculation is a versioned output tied to the facts,
documents and legal dataset used at that time.

The public website may explain the product and its coverage. Detailed client
data, saved recipients, payments, documents and professional review belong
behind authentication.

## Domain hierarchy

```text
organisation
  ├── members and roles
  └── Czech payers
       ├── foreign recipients
       │    ├── profile facts
       │    ├── documents and validity periods
       │    └── change history
       └── payments
            ├── transaction facts
            ├── calculation versions
            ├── open action items
            └── professional review
```

An advisory firm can be an organisation that manages several payer clients.
A standalone company can have a single payer. This avoids conflating the
logged-in customer, the Czech withholding agent and the foreign recipient.

## Roles

| Role | Client-facing access | Professional detail |
| --- | --- | --- |
| Organisation owner | members, billing, all payer clients | no legal override by default |
| Client administrator | payer, recipients, payments, documents | status and requested evidence |
| Client contributor | assigned recipients and payments | client-answerable facts only |
| Tax adviser | assigned payer clients and reviews | legal layers, citations, conditions and review decision |
| Platform administrator | operational support | access only through audited support elevation |

Legal determinations must never be writable through the same endpoint as
client-supplied facts. A client can correct a fact or upload evidence; only an
authorised professional reviewer can close a legal-review item.

## Information architecture

1. **Přehled** — work queue, expiring documents, payments requiring action and
   recent completed outputs.
2. **Plátci** — Czech payer clients. This section is visible to advisers and
   multi-company organisations; a single-company client lands directly in its
   payer workspace.
3. **Příjemci** — reusable foreign-recipient profiles, completeness, tax
   residence evidence and payment history.
4. **Kontroly plateb** — individual transactions with status, responsible
   person, result version and action items.
5. **Výstupy** — downloadable calculation records and professional reports.
6. **Zdroje** — treaty text and documented legal sources supporting outputs.

The guided flow has three primary stages:

1. select or create the recipient;
2. enter payment facts and answer only transaction-specific questions;
3. review the rate, CZK tax, net payment, rationale, evidence and action items.

Users can save and leave between stages only after secure persistence exists.

## Relevant patterns adopted from TaxCrossing

- reusable recipient profiles rather than repeated entry;
- a short recipient → payment → result flow;
- profile completeness tied to concrete missing evidence;
- a result led by amount, rate and status, followed by rationale;
- payment history, documents and outputs grouped under the recipient;
- explicit action items instead of exposing internal engine conditions;
- separate dashboards for work management and individual calculations;
- persistent navigation and restrained, professional visual hierarchy.

## Patterns deliberately not copied

- US forms, TIN, backup withholding and reporting concepts;
- treating a user confirmation as professional approval;
- presenting an AI chat answer as a legal conclusion;
- a generic compliance badge when only a tax calculation was performed;
- billing and content-marketing sections before the core workflow is mature;
- storing uploaded contracts before authentication, tenant isolation,
  retention controls and encryption are operational.

## Czech equivalents

| US-oriented pattern | TaxTreat equivalent |
| --- | --- |
| Payee profile | zahraniční příjemce příjmu |
| W-8 status | potvrzení o daňovém rezidentství and supporting declarations |
| Payment review | kontrola konkrétní platby českého plátce |
| Treaty-rate worksheet | výpočet srážkové daně with source citations |
| Action needed | údaj k doplnění / podmínka k ověření poradcem |
| Confirm assessment | uzavřít výpočet only after permitted review state |

## Persistence and security gate

The current Stage 7B application is stateless. The workspace demo must not use
localStorage, cookies or a fake login to imply secure persistence.

Before saved client cases are enabled, the following are release blockers:

- real authentication with organisation membership and server-side session
  verification;
- tenant-scoped authorisation on every read and write;
- PostgreSQL row ownership and immutable calculation-version identifiers;
- authenticated encryption for sensitive fields with managed key rotation;
- private document storage with short-lived authorised downloads;
- audit events for reads, edits, exports, reviews and support access;
- retention, deletion and backup-recovery procedures;
- EU data-processing and vendor terms reviewed before production use.

The recommended implementation boundary is a dedicated web frontend with the
existing Python calculation engine retained as a protected backend service.
The authentication and storage providers remain an explicit architecture
decision; they must not be simulated in the public demo.
