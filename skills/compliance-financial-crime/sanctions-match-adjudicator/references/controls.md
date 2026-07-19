# Controls — sanctions-match-adjudicator

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only analysis
  (a disposition is a *proposed* case-state transition via the approval broker).
- **Human approval:** `required` — for every true/false-match determination, payment
  block/reject/release, account block/unblock, sanctions-list case closure, and blocking/OFAC
  (or connected SAR) filing. Adjudication only recommends and evidences.

## Prohibited (fail closed)

- **Confirming or discounting a match**, **blocking/rejecting/releasing** a payment,
  **blocking/unblocking** an account, **closing** a case, or **filing** a blocking/OFAC report.
- **Adjudicating a hit with no documented screening provenance** (`screening_engine` +
  `screening_run_id`).
- **Clearing a hit on name alone** (name-only subject → `needs-data`).
- **Auto-discounting conflicting strong signals** (name/DOB match with an identifier mismatch →
  L2 review, never a self-clear).
- **Auto-merging / re-adjudicating** a duplicate; dedup **links** for human confirmation.
- **Tipping-off**: any customer-facing content revealing screening, blocking intent, or
  connected SAR activity.

## Disposition set (this skill may recommend only these)

`recommend-true-match-escalate` | `recommend-potential-match-l2-review` |
`recommend-false-positive-discount` | `needs-data` | `possible-duplicate`.

It may **not** emit `confirmed`, `cleared`, `blocked`, `released`, `unblocked`, `filed`, or
`closed`. Each recommendation records a `disposition_basis`
(`score-band` | `ownership-override` | `strong-id-override` | `conflict-guard` | `needs-data` |
`possible-duplicate`) so the reason is auditable.

## Required output screens (`scripts/validate_output.py`)

- Durable `case_id` of the form `SANC-<alert_id>`; screening provenance present.
- Disposition ∈ the allowed recommendation set; `disposition_basis` ∈ the allowed set.
- Every chronology event, match factor, and party is cited; the bundle citation list and
  chronology are non-empty.
- `disposition_basis` ties out: `score-band` matches the score bands; `ownership-override` and
  `strong-id-override` require their corroborating factor and recommend true-match; the
  `conflict-guard` requires a discriminator and recommends L2 review.
- No confirmation/discount/block/release/filing language (regex screen for affirmative,
  completed actions such as "case closed", "confirmed the true match", "blocked the payment",
  "released the payment", "filed the blocking report", "no further action taken", "exonerat…").
- Standing note present (see SKILL.md Output contract).

## Segregation of duties

Screening (list matching), adjudication (this skill's evidence + recommendation), and the
blocking/reporting decision are distinct entitlements. The same person/skill must not both
adjudicate and decide the block/report.

## Data classification, privacy, records

- **Restricted.** Mask internal customer/account identifiers to what evidences the match; the
  matched *name* is evidence and is retained.
- Where an adjudication connects to suspicious-activity reporting, **SAR-confidentiality /
  tipping-off** controls apply — no customer-facing disclosure of screening/blocking/SAR.
- Retain the evidence bundle, match-factor values, and citations with the weights/bands config
  version per sanctions recordkeeping; log analyst identity on every read and on the recommendation.
