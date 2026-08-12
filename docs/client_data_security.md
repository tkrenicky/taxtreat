# Client data security

## Current Stage 7B behavior

The client form sends a request to the analysis endpoint and receives the result
without creating a client account, case record, or transaction record. TaxTreat
does not persist the submitted client payload in the current Stage 7B version.
The browser keeps the current payload only in page memory so that the user can
refine the calculation or download the result.

The client UI may therefore state that submitted data is not stored. It must not
claim that stored client data is encrypted while no persistent client-data store
exists.

## Mandatory controls before persistence is enabled

Any future feature that stores client cases or transaction data must implement
all of the following before its client-facing release:

- authenticated application-layer encryption for sensitive fields using
  AES-256-GCM or an equivalent reviewed construction;
- envelope encryption with a separate data-encryption key and a managed key
  management service; encryption keys must not be stored in the database;
- strict tenant isolation and least-privilege authorization;
- redaction of request bodies and sensitive fields from application, platform,
  analytics, and error logs;
- encrypted backups, documented key rotation, and tested recovery;
- explicit retention periods, deletion workflows, and an audit trail for access;
- automated tests proving that plaintext sensitive values are absent from the
  database, logs, analytics, and backups.

A client-facing claim that stored data is encrypted may be added only after
these controls are implemented and verified in the deployed environment.
