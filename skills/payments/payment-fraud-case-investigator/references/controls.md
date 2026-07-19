# Controls — payment-fraud-case-investigator

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only
  analysis. The output is an **evidence bundle + disposition recommendation**; any case-state
  change is a *proposal* recorded via the approval broker.
- **Human approval:** `required` — before any fraud determination, case closure, account/
  beneficiary block, customer commitment, recovery, payment return, or SAR filing. This skill
  proposes and evidences; a human adjudicator decides.

## Prohibited (fail closed)

- **Fraud determination** or exoneration (the skill recommends; it never concludes fraud or
  clears a customer).
- **Case closure** or any `closed` / `no-action` state.
- **Blocking** an account or beneficiary, freezing funds, reversing, or returning a payment.
- **SAR drafting/filing** or reporting to authorities.
- **Sanctions-match adjudication** and **APP/BEC** social-engineering investigation — routed
  to specialists.
- Emitting a bundle **without a durable `case_id`** or with an **uncited** evidence item.

## Disposition values (this skill may set only these — all recommendations)

`recommend-fraud` | `recommend-legitimate` | `recommend-elevated-monitoring` |
`needs-evidence` | `route-specialist`.

It may **not** set `closed`, `fraud-confirmed`, `cleared`, `blocked`, `filed`, or `no-action`.

## Required output screens (`scripts/validate_output.py`)

- Every record carries a durable `case_id` (format `PFC-*`).
- Disposition is one of the five recommendation values above (no decision/closure/filing
  state).
- The bundle's `recommended_disposition` matches the record; `route-specialist` names a
  target.
- Every `evidence_items[]` entry is cited and the bundle carries `citations`.
- `risk_band` agrees with `risk_score` (documented thresholds: High ≥ 8, Low ≤ 3, else
  Elevated).
- No autonomous closure / fraud-determination / block / SAR-filing language (regex screen).
- Standing note present: "Investigation evidence and a disposition recommendation only; no
  case has been closed, no fraud determination has been made, and no filing has been
  performed. Human adjudication is required before any block, closure, filing, or customer
  commitment."

## Segregation of duties

Investigation entitlements are distinct from adjudication, from sanctions/BEC specialist
adjudication, and from SAR filing and payment repair. The investigator (this skill) must not
also approve, close, block, or file. Upstream triage/monitoring (raising the alert) is a
separate control activity again (see `handoffs.md`).

## Data classification, privacy, records

- **Highly Confidential — customer NPI/PII and cardholder data (PCI).** Never emit full PAN;
  mask account/customer/beneficiary identifiers to what evidences the case.
- Retain the case bundle, chronology, citations, and `config_version`/`rules_version` per
  records policy; log analyst identity on every read and every recommendation.
- Fail closed when identity, completeness, source, version, or authorization is uncertain —
  set `needs-evidence` rather than guessing.
