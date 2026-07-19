# Adjacent-Skill Handoffs — liquidity-risk-scenario-analyzer

This skill produces a cited **liquidity assessment pack** (`analysis_id`) and stops. It does not
determine compliance, dispose of a breach, act on funding/collateral, file a return, or report to
governance.

## Upstream (may feed this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `stress-test-scenario-designer` | The designed, governed stress scenarios (narratives, shock calibration) this skill runs | Scenario set + config version |
| `cashflow-forecaster` | Baseline contractual/behavioral cash-flow projections that seed the position | Cash-flow items by bucket |

## Downstream (route the human/analyst to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `enterprise-risk-assessment-builder` | Fold liquidity findings into an enterprise/ICAAP-ILAAP risk assessment | `analysis_id` + findings |
| `management-reporting-packager` | Package the results into an ALCO/board liquidity report | `analysis_id` + assessment band |
| `key-risk-indicator-monitor` | Stand up ongoing KRI monitoring of survival horizon / coverage / concentration | metric definitions + limits |
| `regulatory-exam-response-packager` | A supervisor requests liquidity stress evidence | `analysis_id` + cited evidence |
| `model-validation-assistant` | Validate the liquidity model / behavioral assumptions themselves | model inputs + config version |

## Boundary with the fund-liquidity skill

`liquidity-stress-analyzer` (asset management) covers **fund / portfolio** redemption-and-asset
liquidity (redemption gates, swing pricing, asset saleability). This skill covers **institution /
balance-sheet ALM** liquidity (deposit runoff, funding rollover, counterbalancing capacity,
survival horizon). Route buy-side fund questions there; do not analyze them here.

## Duplicate-execution prevention

- This skill computes and evidences **metrics and findings only**; it must not reach a
  determination, dispose of a breach, act on funding/collateral, file, or report — those belong to
  the human (Treasury/ALCO) and the downstream skills.
- Downstream skills reuse the `analysis_id` pack rather than recomputing the stress metrics.
- If no catalog skill fits a needed step (e.g. executing an approved CFP action, or submitting a
  regulatory return), that is a **human / authorized-system** operation, not another skill call.
