# Controls — service-recovery-assistant

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `external-delivery` — a recorded human approval at the computed
  authority tier is required before the communication is delivered or any goodwill/redress
  is paid or posted. Internal drafting is reviewer-sampled. This skill only ever produces a
  draft package.

## Prohibited (fail closed)

- **Sending, delivering, paying, crediting, or posting** anything — the skill never
  executes; `delivery.sent` is always false.
- **Goodwill above the approved matrix cap**, or **redress of an undocumented detriment**
  (undocumented detriment → `needs-data`).
- **Liability / negligence admissions**, **guarantees** ("this will never happen again",
  "we guarantee"), or **entitlement assertions** ("you are legally entitled to").
- **Unsupported monetary figures** — every amount quoted to the customer must equal a
  computed value (`direct_redress`, `goodwill_gesture`, or `total`).
- **Investment, legal, or tax advice** in a recovery communication.
- **Formal regulated complaint handling / final-response decisions** — refer out.

## Case states (this skill may set only these)

`draft-for-approval` | `needs-data` | `refer-specialist`. It may **not** set `sent`,
`delivered`, `paid`, `resolved`, or `closed`.

## Required output screens (`scripts/validate_output.py`)

- Only the three allowed dispositions appear; no `delivery.sent: true`.
- Each `draft-for-approval` entry carries all required template sections, non-empty
  (`case_summary`, `failure_assessment`, `customer_impact`, `precedent_and_policy`,
  `proposed_remediation`, `communication_draft`, `required_approvals`, `sources`).
- Remediation ties out (`redress + goodwill == total`), goodwill ≤ matrix cap,
  `matrix_version` recorded, cited.
- Every monetary figure in the drafted communication is a computed value.
- Required approval is **recorded**: tier + approver role present; a `recorded` status
  needs a named approver and decision.
- No liability/guarantee/entitlement/advice/"already actioned" language.
- Standing note present: "Draft for human review only; no communication has been sent and
  no goodwill or redress has been paid."

## Approval authority tiers (versioned config)

| Tier | Role | Default authority |
| ---- | ---- | ----------------- |
| Tier 1 | Service agent | total ≤ $50 |
| Tier 2 | Team lead | total ≤ $150 |
| Tier 3 | Operations manager | total > $150, any vulnerability, or above standard authority |

Approval level is a proposal for the business; the human approver of record authorizes the
spend and the external delivery.

## Segregation of duties

Drafting a recovery is separate from approving it and from executing it. The same person
must not draft and self-approve; execution (send/pay/post) is a distinct, approval-gated
downstream activity.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask customer identifiers in output to what is
  needed to evidence the case (`customer_ref` is masked to the last 4).
- Retain the draft package, the computed remediation with `matrix_version`, citations, and
  the approval record per complaint/records-retention policy; log the drafter identity and
  every read.
