# Adjacent-Skill Handoffs — research-publication-preparation-assistant

Produces a cited pre-publication packet (`prep_id`) and stops. It does not publish, distribute,
approve, or set the rating/target.

## Downstream (route the human/reviewer to)
| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `filing-disclosure-change-detector` | Filing-disclosure changes must be detected/checked | ticker + filings |
| `communications-compliance-reviewer` | Communications-surveillance review is needed | note id |
| `earnings-preview-packet-builder` | An earnings preview packet is being assembled | ticker |

## Upstream (may call this skill)
Research workflows may request a pre-publication readiness check before supervisory-analyst review.
This skill is interactive (`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill only **checks and flags**; it never publishes, approves, or rates — those belong to
  the supervisory analyst, compliance, and the publishing process.
- Downstream reuses the `prep_id` packet rather than rechecking.
