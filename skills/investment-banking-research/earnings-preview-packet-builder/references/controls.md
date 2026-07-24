# Controls - earnings-preview-packet-builder

- **Risk tier:** R2 - analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change. The skill assembles a draft deliverable; it stages nothing for
  execution and performs no publication or distribution.
- **Human approval:** `external-delivery` - a supervisory analyst, research-compliance /
  control room, and legal/disclaimer sign-off must be **recorded** before the packet may be
  marked `ready-for-distribution`, and the actual distribution to any desk or external party
  is performed by a person, never by this skill.

## Prohibited (fail closed)

- **Setting a forecast, rating, price target, or trade view**, carrying an originated
  estimate, or giving personalized investment advice - the R2 prohibited-decision/advice
  screen in `validate_output` fails closed on any such content (see domain-rules for the
  patterns and prohibited data-point kinds).
- **Publishing, sending, distributing, or filing** the packet, or marking it
  `published`/`distributed`/`sent`/`filed`/`posted`/`released`.
- **Fabricating** any figure, KPI, controversy, or source; keeping a data point without an
  approved `source_ref`; keeping a forward-looking figure without a third-party attribution.
- Marking `ready-for-distribution` without all required approvals recorded and approved.

## Packet states (this skill may set only these)

`draft` -> `hold-for-approval` -> `ready-for-distribution`. It may **not** set `published`,
`distributed`, `sent`, `filed`, `posted`, `released`, or `emailed`, or any state implying the
packet left the desk. `ready-for-distribution` means humans cleared the draft for a person to
distribute.

## Required output screens (`scripts/validate_output.py`)

- Every required template section is present (template fidelity / completeness).
- Every item has a takeaway and at least one cited source; every data point has an approved
  `source_ref`; every forward-looking data point is third-party attributed (no origination).
- No forecast / rating / price-target / trade-view / advice language anywhere in titles,
  takeaways, or data points; no originated-view data-point kind.
- Each required approval role is recorded; `ready-for-distribution` only when all approved.
- Draft-only notice and standing note present; `packet_status` is never a distributed state.

## Segregation of duties

The **preparer** (research associate assembling the packet) is distinct from the **approvers**
(supervisory analyst, research compliance / control room, legal). The same person must not
both assemble and self-approve the required control approvals.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Pre-event research routinely sits
  behind information barriers; **control-room clearance and wall-cross checks** apply. No
  selective disclosure; distribution only to cleared recipients by a person.
- Retain the packet, its source map, the template `id@version`, the `packet_id`/`job_id`, and
  the approval records per the research records-retention policy; log preparer identity and
  every approval. Recertify per `aws-fsi-recertification-date`.
