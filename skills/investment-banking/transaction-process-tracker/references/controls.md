# Controls — transaction-process-tracker

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change. The tracker records status and computes reminders; it stages
  nothing for execution.
- **Human approval:** `external-delivery` — a named human owner must review and approve
  before the tracker is delivered externally or any system of record is changed. Internal
  analytical use is reviewer-sampled.

## Prohibited (fail closed)

- **Bid selection / counterparty recommendation** — never name a winning bid, recommend a
  buyer, or award/grant exclusivity. That is a human deal-team decision.
- **Personalized investment advice** — no buy/sell/valuation opinion; the tracker organizes
  process facts only.
- **Execution of any process action** — never send outreach, execute or sign an NDA, grant
  data-room access, submit a bid/LOI/IOI, or deliver the tracker.
- **Fabricating or advancing status** — never mark an NDA executed, access granted, or a
  milestone complete without a cited source; never silently repair a control exception.
- **Recording an approval that was not given** — required approvals are captured only from
  the governance system; missing ones surface as outstanding open items.

## Deterministic control gates (surfaced, never auto-resolved)

The engine ([scripts/calculate_or_transform.py](../scripts/calculate_or_transform.py))
applies process-sequence gates and emits a **control-exception** open item for each breach:

- **NDA before access/diligence** — an active party at or beyond `access` (or with access
  `granted`) without an **executed NDA** → `nda-not-executed`.
- **Access before diligence** — an active party at or beyond `diligence` without **granted**
  data-room access → `access-not-granted`.

Exceptions are escalated to the deal team; the party is **not** advanced until resolved.

## Required output screens (`scripts/validate_output.py`)

- All required template sections present (`process_summary`, `party_tracker`, `approvals`,
  `reminders`, `change_log`, `open_items`, `source_index`).
- **No unsupported claims** — every party entry and every recorded bid carries a citation.
- **Control-gate consistency** — an active access-granted / NDA-not-executed party must
  carry the matching exception; an unflagged breach fails closed.
- **Required approvals recorded** — recorded approvals are well-formed (type + role + date +
  citation); missing required approvals appear as outstanding; delivery approval is required.
- **No decision / recommendation language** and **no send/grant/deliver (execution)
  language** (regex screens).
- `tracker_status` is `draft-tracker`; the standing note is present.

## Segregation of duties

Tracking is distinct from deciding and from executing. The analyst/skill that maintains the
tracker does not select bids, grant access, or approve delivery — those sit with the deal
team lead, the data-room administrator, legal counsel, and the governance/approvals owner.

## Data classification, privacy, records

- **Highly Confidential — MNPI / client-confidential.** Treat the counterparty list, bids,
  and deal status as material non-public information; enforce need-to-know and any ethical
  wall / wall-cross list.
- Mask counterparty and personal identifiers to what the tracker requires; store bid amounts
  and party identities only where the deal team is entitled.
- Retain each tracker snapshot, its change log, citations, and `config_version` so any state
  is reproducible; log the analyst identity and the approver on delivery.
