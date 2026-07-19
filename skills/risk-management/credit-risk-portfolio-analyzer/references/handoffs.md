# Adjacent-Skill Handoffs — credit-risk-portfolio-analyzer

This skill produces a cited **portfolio analysis pack** (`analysis_id`) with metrics,
exceptions, evidence, and a suggested review disposition, then stops. It does not decide,
set an allowance, dispose of a limit breach, close a case, file, or write a system of
record — those are human/authorized actions performed after adjudication.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `stress-test-scenario-designer` | The analyst needs macro scenarios / shock parameters designed before running scenario impact | portfolio segments + horizons |
| `concentration-risk-monitor` | A flagged concentration should be tracked/alerted on an ongoing basis | `analysis_id` + concentration exceptions |
| `key-risk-indicator-monitor` | Portfolio metrics should feed standing KRIs and thresholds | `analysis_id` + metrics |
| `credit-memo-drafter` | Findings must be written up as a committee credit review memo (draft-only, human-filed) | `analysis_id` + exceptions/evidence |
| `enterprise-risk-assessment-builder` | Portfolio credit risk rolls up into the enterprise risk assessment | `analysis_id` + disposition |
| `covenant-compliance-monitor` | A specific loan/facility needs covenant-level tracking, not portfolio analysis | obligor + facility |

## Upstream (may call this skill)

`key-risk-indicator-monitor` and `concentration-risk-monitor` (read-only monitors) may flag a
metric and request a deep-dive portfolio analysis; a human analyst then invokes this skill.
This skill is interactive (`aws-fsi-scheduled-agent: no`) and is not itself a monitor.

## Model governance boundary

PD/LGD are governed model outputs. Questions about model soundness, calibration, or
documentation belong to Data, AI & Model Governance skills such as `model-validation-assistant`
and `model-risk-documenter`, not to this analyzer. This skill consumes model outputs and
records their version; it never re-estimates or validates the models.

## Human / specialist handoffs (no catalog skill)

Adjudication of every exception — the actual credit decision, allowance/reserve
determination, limit disposition or waiver, workout referral, and any regulatory filing — is
performed by the accountable **human credit-risk officer, workout/servicing team, and the
credit risk committee**, and where required by licensed/authorized specialists. This skill
never substitutes for that adjudication.

## Duplicate-execution prevention

- This skill computes **metrics, exceptions, and evidence only**; it must not reach a
  disposition-as-decision, set an allowance, or act on a limit — those belong to the human
  and the downstream skills.
- Downstream skills reuse the `analysis_id` evidence rather than recomputing the analytics.
