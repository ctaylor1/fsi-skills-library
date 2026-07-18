# Risk Tiers, Action Modes, and Human Approval

Every skill declares a risk tier (`aws-fsi-risk-tier`), a default action mode
(`aws-fsi-action-mode`), and a human-approval posture (`aws-fsi-human-approval`). These
three fields must be mutually consistent per the table below.

## Tiers

| Tier | Definition | Typical action mode | Human approval |
| ---- | ---------- | ------------------- | -------------- |
| **R1** | Informational: source-grounded explanations and summaries. | Read-only analysis | External delivery or system-of-record change (otherwise reviewer sampling) |
| **R2** | Analytical / drafting: models, analyses, reconciliations, deliverables. No binding decision. | Read-only analysis **or** draft-only | External delivery or system-of-record change (otherwise reviewer sampling) |
| **R3** | Regulated / control decision support: evidence + recommendations with mandatory human adjudication. | Read-only analysis, draft-only, or scheduled read-only | **Required before** any regulated decision, filing, customer commitment, trade, payment, posting, case closure, control attestation, or system-of-record change |
| **R4** | Approval-gated action: plan → validate → approve → execute → verify → audit. | Approval-gated write or submission | **Required before** execution of any write, submission, or state change |

## Action modes

- **Read-only analysis** — the skill reads sources and produces analysis/evidence; it
  makes no writes and stages nothing for execution.
- **Draft-only; no system-of-record change** — the skill produces a draft deliverable
  (memo, package, response, entry proposal) that a human must review and act on.
- **Scheduled read-only; alert only** — a scheduled agent monitors sources read-only and
  raises alerts / queue items. It never acts. Only the 12 approved monitors use this mode
  (`aws-fsi-scheduled-agent: read-only-monitoring`).
- **Approval-gated write or submission** — the skill may execute a write **only** after an
  explicit human approval, and must provide idempotency, verification, and rollback
  guidance (R4 only).

## Human-approval encoding

`aws-fsi-human-approval` takes one of:

| Value | Meaning |
| ----- | ------- |
| `none` | No approval gate (reserved; not used by any current skill). |
| `external-delivery` | Human approval required before external delivery or any system-of-record change; internal analytical use may be reviewer-sampled. Used by R1/R2. |
| `required` | Human approval required before any regulated decision, filing, commitment, trade, payment, posting, closure, attestation, or system write. Used by R3/R4. |

## Universal prohibitions

Regardless of tier, no skill in this library may, without an explicit human approval gate:

- make or communicate a **binding regulated decision** (credit approval/adverse action,
  coverage/reserve determination, suitability approval, fraud/AML finding, sanctions hit
  disposition, etc.);
- **close a case** or suppress an alert outside approved deterministic logic;
- **file, submit, trade, pay, post a journal, or write a system of record**;
- provide **personalized investment, legal, or tax advice**;
- **bypass authorization** or assume step-up authentication / automatic retries.

When completeness, identity, source, version, or authorization is uncertain, the skill
**fails closed** — it stops and surfaces the gap rather than guessing.
