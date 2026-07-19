# Domain Rules — credit-risk-portfolio-analyzer

Transparent credit-portfolio calculations and how limit/threshold **exceptions** map to a
**review disposition band**. Thresholds are configuration (versioned, owned by the risk
appetite / limits framework), not hard-coded judgments. PD and LGD are governed model
outputs consumed as-is; this skill never re-estimates them. Orientation references: the
firm's credit risk appetite statement and limits framework, and supervisory guidance on
credit risk review and allowance governance (e.g., interagency credit-risk-review and
CECL/ACL governance principles) take precedence over anything here.

## Metrics (deterministic — see `scripts/calculate_or_transform.py`)

| Metric | Definition |
| ------ | ---------- |
| Expected loss (EL) | `EL = PD × LGD × EAD` per exposure, summed; `el_pct_ead = EL / total_EAD` |
| Quality distribution | EAD share by internal grade; EAD-weighted average PD and LGD |
| Delinquency | EAD by DPD bucket (current, 1–29, 30–59, 60–89, 90+); `dpd_90plus_pct` |
| Concentration | EAD share by obligor / sector / geography; HHI per dimension; top-name share |
| Collateral | Secured/unsecured EAD share; EAD-weighted LTV over secured (`Σ EAD / Σ collateral`) |
| Migration | Grade transitions vs `prior_rating`; downgrade rate; net notch per rated pair |
| Vintage | EAD, 90+ rate, and EL rate grouped by origination cohort |
| Scenario impact | Stressed `EL` with `PD×pd_mult`, `LGD×lgd_mult` (each capped at 1.0); delta vs base |

Grade ordinal scale for migration: `AAA, AA, A, BBB, BB, B, CCC, CC, C, D` (worsening). A
downgrade is a move to a higher index. Pairs whose grades are off-scale are not counted
(reported as not-evaluable rather than guessed).

## Exception thresholds (default config)

| Exception code | Fires when | Severity |
| -------------- | ---------- | -------- |
| `single_name_concentration` | any obligor EAD share > `single_name_max_pct` (0.10) | critical |
| `sector_concentration` | any sector EAD share > `sector_max_pct` (0.25) | critical |
| `delinquency_90plus` | `dpd_90plus_pct` > `delinquency_90plus_max_pct` (0.03) | critical |
| `geography_concentration` | any geography EAD share > `geography_max_pct` (0.35) | high |
| `collateral_ltv` | any secured exposure LTV > `max_ltv` (0.80) | high |
| `el_budget` | `el_pct_ead` > `el_budget_pct` (0.015) | high |
| `scenario_el` | stressed EL % of EAD > `scenario_el_max_pct` (0.025) | high |
| `migration_downgrade` | `downgrade_rate` > `downgrade_rate_max` (0.15) | medium |

Each fired exception attaches the specific exposure rows behind it (and, for aggregate
metrics, the top EL contributors), each with a source citation.

## Disposition mapping (deterministic, documented)

| Suggested band | Rule |
| -------------- | ---- |
| **Elevated** | any `critical` exception present |
| **Watch** | at least one exception, none critical |
| **Stable** | no exceptions |

The disposition is a **triage suggestion for a human credit-risk officer / credit risk
committee**. It is not a credit decision, an allowance/reserve determination, a limit
disposition, or a case closure, and it triggers no system-of-record change.

## Hard boundaries (fail closed)

- Never **make or communicate a credit decision** (approval, adverse action, denial), **set
  or book an allowance/reserve/provision**, **dispose of or waive a limit breach**, **close
  a case/exception**, **file** a regulatory report, or **post/write** to any system of record.
- Never re-estimate or re-calibrate **PD/LGD**; they are governed model outputs. If a model
  output is missing, stale, or off-scale, mark the dependent metric not-evaluable.
- Never **tune thresholds to a name** to make a breach disappear; use only the versioned
  limits config, and record its version.
- Describe migration and delinquency **factually**; do not assert a forward default outcome
  for a named obligor.

## Adjudication prompts (always include when exceptions fired)

Invite the human adjudicator to weigh mitigating context before any decision: recent
paydowns or amortization, updated collateral appraisals, guarantees or credit enhancements,
scheduled restructurings/modifications, seasonal or timing effects in delinquency, model
overrides on file, and whether a concentration is within an approved, documented exception.
