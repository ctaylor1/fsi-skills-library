# Source Map — credit-risk-portfolio-analyzer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Loan/exposure tape** (system of record for balances/EAD) | Exposures, EAD, days-past-due, obligor, segment/sector/geography | Read-only |
| 2 | **Risk-rating & model store** | Current + prior internal grade, PD, LGD (model outputs) | Read-only |
| 3 | **Collateral register** | Collateral values, lien position, LTV inputs | Read-only |
| 4 | **Risk limits / appetite config** (versioned) | Concentration, delinquency, LTV, EL-budget, migration thresholds | Read-only |
| 5 | **Scenario library** (versioned) | Stress PD/LGD multipliers and scenario definitions | Read-only |
| 6 | **Loss-event / charge-off history** | Realized loss context and vintage calibration | Read-only |

The loan/exposure tape is the position of record for balances and delinquency. PD/LGD are
**model outputs** governed by model risk management — this skill consumes them, it does not
re-estimate or re-calibrate them. If the tape and a rating/model snapshot conflict on an
exposure, cite both and flag for the analyst; never silently reconcile.

## Citation format

`{system}:{ref}@{as_of}` — e.g. `loan_tape:port=CRP-DEMO-01;exp=L-0001@2026-06-30`. Every
exception cites the specific exposure rows behind it (and, for aggregate metrics such as EL,
the top contributing exposures) so a reviewer can trace each finding to the tape.

## Freshness / effective dates

- Limits/appetite config and the scenario library are **versioned contracts**; the output
  records `config_version` and the scenario name so an analysis is reproducible.
- All metrics are stated `as_of` a single portfolio date; mixing as-of dates across exposures
  is a data-quality error the analyst must resolve upstream.
- PD/LGD carry a model version/vintage in the rating store; low-confidence or stale model
  outputs must be surfaced, not smoothed over.

## Least-privilege operations (deployment)

- `loan_tape.read(portfolio_id, as_of)` → bounded, paged exposure rows.
- `rating_store.read(portfolio_id, as_of)` → current/prior grade, PD, LGD, model version.
- `collateral.read(portfolio_id)` → collateral values and lien position.
- `limits.get('credit', version)` → concentration/delinquency/LTV/EL/migration thresholds.
- `scenarios.get(name, version)` → PD/LGD multipliers.

All read-only, deterministic, durable `analysis_id`, below the fixed timeout; page large
loan tapes as resumable stages. No write, submission, or system-of-record change is ever
performed by this skill.
