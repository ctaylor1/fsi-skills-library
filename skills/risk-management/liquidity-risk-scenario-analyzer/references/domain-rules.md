# Domain Rules — liquidity-risk-scenario-analyzer

Explainable liquidity **metrics**, the **findings** they raise against limits, and the
deterministic **assessment band**. Behavioral assumptions (runoff, rollover, inflow realization),
haircut add-ons, and limits are **configuration** (versioned, owned by ALM/ERM), not hard-coded
judgments, and are never tuned to make a position pass. Orientation references: Basel III LCR/NSFR,
the firm's ILAAP/liquidity-risk standard, and supervisory liquidity-stress guidance take
precedence over anything here.

## Position model

Each cash-flow item has `direction` (inflow/outflow), a `category`, a time `bucket`, and an
`amount` (notional/expected). Counterbalancing assets have an `asset_class`, `market_value`, and
`base_haircut`. Buckets carry an `end_day` and are evaluated in ascending order.

## Scenario stress (applied per category / class)

| Input | Meaning | Effect |
| ----- | ------- | ------ |
| `outflow_rates[category]` (default `default_outflow_rate`) | Fraction of an outflow notional that runs off / must be paid under stress | `stressed_outflow = amount × rate` |
| `inflow_rates[category]` (default `default_inflow_rate`) | Fraction of a contractual inflow realized under stress (inflow haircut) | `stressed_inflow = amount × rate` |
| `cb_haircut_addon[asset_class]` | Stress add-on to the base haircut on a counterbalancing asset | `available = market_value × (1 − min(1, base + addon))` |

Typical categories: `retail_stable`, `retail_less_stable`, `operational_deposits`,
`wholesale_unsecured`, `wholesale_secured`, `committed_facility_drawdown` (outflows);
`loan_repayment`, `maturing_reverse_repo`, `marketable_securities_coupon` (inflows).

## Metrics (deterministic)

- **Counterbalancing capacity (CBC)** = Σ over assets of `market_value × (1 − effective_haircut)`.
- **Net flow / cumulative gap** per bucket = `stressed_inflow − stressed_outflow`, accumulated.
- **Liquidity position** per bucket = `CBC + cumulative_net` (buffer remaining after covering the
  cumulative net outflow to that bucket).
- **Survival horizon** = the last bucket `end_day` at which the liquidity position stayed ≥ 0
  (0 if it is negative in the first bucket; the full horizon if it never goes negative).
- **Coverage ratio** = `CBC / net_cumulative_outflow_at_horizon` (where net cumulative outflow is
  `max(0, −cumulative_net)` at the reporting horizon); `null` when there is net cumulative inflow.
- **Peak cumulative gap** = the most negative cumulative net across buckets.

## Findings (each cited to evidence)

| Finding | Severity | Fires when |
| ------- | -------- | ---------- |
| `survival_horizon_breach` | CRITICAL | `survival_horizon_days < limits.min_survival_days` |
| `coverage_ratio_breach` | HIGH | coverage is not null and `< limits.min_coverage_ratio` |
| `funding_concentration` | MEDIUM | a single funding category exceeds `limits.concentration_limit_pct` of maturing/contractual outflow notional (structural, scenario-independent) |

Findings are **additive and evidenced**; there is no opaque composite "liquidity score". Survival
and coverage are reported per scenario because the survival minimum can be shorter than the
coverage (LCR-style) horizon — a scenario can pass one and breach the other.

## Assessment band (deterministic mapping)

The overall band is the highest severity present across all findings (per-scenario + structural):

| Band | Rule |
| ---- | ---- |
| **Breach** | any CRITICAL finding (survival horizon below minimum in any scenario) |
| **Elevated** | any HIGH finding (coverage below minimum) and no CRITICAL |
| **Watch** | any MEDIUM finding (e.g. funding concentration) and no CRITICAL/HIGH |
| **Within appetite** | no findings fired |

The band is a **triage read for a human reviewer**. It is not a regulated liquidity determination
and it never triggers a funding, collateral, limit, or filing action.

## Hard boundaries (fail closed)

- Never state or imply that the institution **is** (non-)compliant, in breach as a matter of record,
  or adequately funded — describe metrics factually and attribute conclusions to Treasury/ALCO.
- Never recommend or take a **funding/collateral/limit/filing action** (draw, repo, pledge, sell,
  raise/lower/waive a limit, clear a breach, file a return).
- Never tune runoff/rollover/haircut assumptions or limits to make a position pass.
- `funding_concentration` describes a **structural share**, not a judgment about a counterparty.

## Proposed contingency options (always include when band ≠ Within appetite)

Monetize Level 1 HQLA via repo; pre-position additional eligible collateral at the central-bank
standing facility; term out maturing wholesale unsecured funding; slow discretionary asset growth /
new lending during the stress window. Each is a **proposal requiring Treasury/ALCO adjudication**;
the pack lists them as options for the Contingency Funding Plan owner to evaluate, never as
executed or approved actions.
