# Controls — aml-alert-triager

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only
  analysis (escalation is a *proposed* state transition via the approval broker).
- **Human approval:** `required` — for every escalation disposition, any closure, and any
  filing. Approved suppression is a bounded, logged, reviewer-sampled action.

## Prohibited (fail closed)

- **Case closure**, **exoneration**, or **SAR drafting/filing**.
- **Suppression** outside `SUP-DUP-01`, `SUP-WL-INTERNAL`, `SUP-SEASONAL-01`.
- **Typology determination** (hints for routing only).
- **Tipping-off**: any customer-facing content revealing monitoring or SAR activity.
- **Auto-merge / auto-close** of alerts or entities.

## Case states (this skill may set only these)

`new` → `needs-data` | `possible-duplicate` (linked) | `approved-suppressed` (rule-bound) |
`escalate-to-investigation`. It may **not** set `closed`, `cleared`, `filed`, or `no-action`.

## Required output screens (`scripts/validate_output.py`)

- Only approved suppression rule IDs appear; each suppression cites its evidence.
- No closure/exoneration/filing language (regex: "close the case", "cleared", "no SAR
  needed", "exonerat", "file the sar", "case closed", "no further action").
- No tipping-off language (customer-facing disclosure of monitoring/SAR).
- Every escalation bundle item is cited; priority equals the deterministic mapping.
- Standing note present: "First-line triage only; no case has been closed, no customer
  exonerated, and no SAR filed."

## Segregation of duties

Triage entitlements are distinct from investigation and from SAR filing. The same person/
skill must not both triage-suppress and adjudicate the substantive case.

## Data classification, privacy, records

- **Restricted (AML/BSA).** SAR-confidentiality and tipping-off controls apply.
- Mask customer/account identifiers to what evidences the alert.
- Retain triage records, suppression logs, and citations with rule/config versions per BSA
  recordkeeping; log analyst identity on every read/suppression/escalation.
