# Adjacent-Skill Handoffs — claim-damage-evaluation-comparator

Produces a cited line-item comparison packet (`comparison_id`) and stops. It does not value the
claim, determine coverage/liability, or approve payment.

## Downstream (route the human/reviewer to)
| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `liability-evidence-matrix-builder` | Fault/liability mapping to evidence is needed | claim id + evidence refs |
| `claim-settlement-authority-packet` | A settlement-authority request must be assembled | claim id + evaluated inputs |

## Upstream (may call this skill)
Claims-handling workflows may request a document comparison. This skill is interactive
(`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill only **compares documents and evidences findings**; it never values, settles, or
  approves — those belong to the licensed adjuster.
- Downstream reuses the `comparison_id` evidence rather than recomputing.
