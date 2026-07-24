# Adjacent-Skill Handoffs — financing-alternatives-calculator

Produces a factual cost-comparison worksheet (`calc_id`) and stops. It does not recommend, rank,
or advise which alternative to choose.

## Downstream (route the human/analyst to)
| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `capital-structure-maturity-mapper` | The existing debt-stack/maturity context is needed | request id + company |
| `pricing-hedging-scenario-calculator` | Derivative/hedge pricing scenarios are needed | terms refs |
| `market-window-readiness-pack` | Launch-readiness for the chosen route is assembled | request id |

## Upstream (may call this skill)
DCM/ECM and coverage workflows may request a financing-cost comparison. This skill is interactive
(`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill only **computes and presents** per-alternative metrics; it never recommends or
  ranks — that belongs to the banker.
- Downstream reuses the `calc_id` worksheet rather than recomputing.
