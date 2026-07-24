# Adjacent-Skill Handoffs — capital-structure-maturity-mapper

Produces a descriptive capital-structure map (`map_id`) and stops. It does not advise, recommend,
or suggest a transaction.

## Downstream (route the human/analyst to)
| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `financing-alternatives-calculator` | Illustrative cost/impact of financing options is needed | company id + maturity wall |
| `credit-terms-covenant-extractor` | Covenant/terms extraction from the debt docs | instrument refs |
| `covenant-compliance-monitor` | Covenant-headroom monitoring against the debt stack | map id + instrument refs |

## Upstream (may call this skill)
DCM and coverage workflows may request a capital-structure map. This skill is interactive
(`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill only **describes and maps**; it never advises or recommends — that belongs to the
  banker.
- Downstream reuses the `map_id` map rather than recomputing.
