# Adjacent-Skill Handoffs — market-window-readiness-pack

Produces a cited launch-readiness packet (`packet_id`) and stops. It does not decide launch,
clear pricing, or advise on market timing.

## Downstream (route the human/reviewer to)
| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `financing-alternatives-calculator` | Financing-cost comparison for the structure is needed | deal id + terms |
| `research-publication-preparation-assistant` | Connected research must clear pre-publication | deal id |
| `issuer-capital-structure-mapper` | The issuer's debt-stack context is needed | issuer id |

## Upstream (may call this skill)
DCM/ECM and syndicate workflows may request a launch-readiness packet ahead of a go/no-go gate.
This skill is interactive (`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill only **checks readiness and evidences gaps**; it never decides launch or advises on
  timing — those belong to the banker and the launch process.
- Downstream reuses the `packet_id` evidence rather than recomputing.
