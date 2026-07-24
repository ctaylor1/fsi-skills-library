# Adjacent-Skill Handoffs — liability-evidence-matrix-builder

Produces a cited fact→evidence matrix (`matrix_id`) and stops. It does not determine liability,
fault, or apportionment.

## Downstream (route the human/adjuster to)
| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `claim-damage-evaluation-comparator` | Damage documents/line items need comparison | claim id + document refs |
| `claim-settlement-authority-packet` | A settlement-authority request must be assembled | claim id + evaluated inputs |
| `fnol-normalizer` | Intake needs normalization first | fnol id |

## Upstream (may call this skill)
Claims investigation workflows may request an evidence matrix. This skill is interactive
(`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill only **maps evidence and flags gaps**; it never determines liability or decides the
  claim — those belong to the adjuster.
- Downstream reuses the `matrix_id` bundle rather than rebuilding.
