# Adjacent-Skill Handoffs — fnol-normalizer

Produces a normalized intake record + cited exceptions (`normalization_id`) and stops. It does
not open, route, or adjudicate a claim.

## Downstream (route the human/reviewer to)
| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `claim-damage-evaluation-comparator` | Damage documents/line items need comparison | claim id + document refs |
| `liability-evidence-matrix-builder` | Fault/liability evidence mapping is needed | claim id + facts |

## Upstream (may call this skill)
Claims-intake workflows may request FNOL normalization before downstream handling. This skill is
interactive (`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill only **normalizes and flags**; it never opens, routes, or adjudicates a claim —
  those belong to the claims system and the human.
- Downstream reuses the normalized record + `normalization_id` rather than re-normalizing.
