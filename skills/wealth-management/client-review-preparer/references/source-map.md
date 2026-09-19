# Client-review sources

Authority is field-specific: wealth CRM for household/advisor/notes/actions; custody/accounting
for accounts and positions; performance system for reported returns; planning for goals; controlled
libraries for disclosures, template and review policy. Citation format is system:ref@date.

Every material item must reference an owned, dated source in the review inventory. Missing,
future-dated or expired evidence rejects input. Source-age thresholds are explicit deployment
configuration; a named reviewer/reason is required for an age exception, and expired validity
cannot be extended by the agent. Approved template/policy versions and validity are mandatory.

Proposed read-only operations: crm.read, portfolio.read/custody.read, performance.read,
planning.read, disclosures.read and config.get. These connectors are not implemented here.
The scripts validate supplied records and metadata; they do not independently retrieve sources
or prove a supplied citation supports its assertion. Human source readback is required.

Retain request/review IDs, source inventory, versions, input snapshot/hash and prior_artifact_id
when supplied. Identical inputs yield the same artifact ID; changes produce a new artifact ID.
No live CRM, delivery, trade, calendar or book-of-record writes occur.
