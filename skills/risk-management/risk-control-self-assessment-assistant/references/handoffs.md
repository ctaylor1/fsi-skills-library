# Adjacent-Skill Handoffs — risk-control-self-assessment-assistant

RCSA is a **first-line** self-assessment activity. It drafts an evidence-mapped package for
human adjudication; it does not perform second-line challenge, event investigation, or the
final GRC sign-off. Handoffs below use catalog skills where one fits; everything else is an
explicit **human / operations** handoff.

## Upstream / feeder (evidence into this skill)

| Feeder skill | Provides |
| ------------ | -------- |
| `operational-risk-event-analyzer` | Loss / near-miss event analysis that corroborates or contradicts control effectiveness |
| `key-risk-indicator-monitor` | KRI levels and breaches used as quantitative effectiveness evidence |
| `third-party-risk-assessor` | Control coverage for outsourced / vendor-run processes in scope |

## Downstream (this skill routes to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `enterprise-risk-assessment-builder` | RCSA results aggregate into the top-down / enterprise risk assessment | Draft RCSA package + residual summary |
| `operational-risk-event-analyzer` | A live loss event or near-miss surfaces during the RCSA and needs root-cause analysis | risk_id + event reference |
| `policy-procedure-gap-analyzer` | A control gap traces to a missing or deficient policy/procedure | risk_id + control gap description |
| `audit-evidence-packager` | RCSA evidence must be packaged for internal audit or an examiner | evidence map + citations |
| `board-committee-pack-builder` | RCSA outcomes roll up into a risk-committee / board pack | residual summary + above-appetite items |

## Human / operations handoffs (no catalog skill — do not invent one)

- **Independent challenge & validation** → the **second-line operational-risk function**. The
  assistant cannot substitute for this control.
- **Assessment sign-off & control-owner attestation** → **first-line management** and the
  **control/process owner**, via the GRC platform.
- **Remediation ownership, tracking to closure, waiver, or risk acceptance** → the **GRC
  issue-management / remediation owners** and, above appetite, the **accountable risk owner
  or risk committee**. The assistant drafts and ages remediation items; humans own and close
  them.
- **Writing the RCSA to the system of record** → a **human** action in the GRC platform.

## Duplicate-execution prevention

- This skill **does not** investigate events, run the independent second-line challenge, or
  sign off/finalize the RCSA — those belong to the skills and humans above.
- Downstream consumers take the draft package (with its methodology/appetite versions and
  evidence citations) rather than re-deriving the ratings.
- Remediation items are **flagged** for human owners; the assistant never closes or waives them.
