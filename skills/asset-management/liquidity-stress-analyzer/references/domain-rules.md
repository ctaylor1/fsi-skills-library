# Domain Rules — liquidity-stress-analyzer

Explainable liquidity **metrics** and how they map to a **liquidity-risk band**. Thresholds
and model parameters are configuration (versioned, owned by the liquidity-risk function), not
hard-coded judgments, and never tuned to a desired answer. Scenario assumptions are supplied
explicitly and recorded with every result. Orientation references: SEC 22e-4 / open-end fund
liquidity-risk-management principles and the firm's liquidity-risk standard take precedence at
deployment.

## Liquidation model (participation-of-ADV)

For each position, tradable value per day = `adv_value × participation_rate × adv_haircut`.
- **Liquidatable within D days** = Σ min(market_value, daily_capacity × D) across positions.
- **Days to liquidate a position** = market_value ÷ daily_capacity (∞ if capacity ≤ 0).
- **Full-liquidation horizon** = max days-to-liquidate across positions.
The model is deterministic and assumes orderly trading; it ignores second-order price impact.

## Cost model

Per position: `cost_bps = spread_bps × spread_cost_weight × spread_multiple + impact_coeff_bps
× participation_rate`. Portfolio cost = MV-weighted cost_bps (also reported in base currency).

## Metric taxonomy

| Metric | Breaches when (default config) | Class | Evidence attached |
| ------ | ------------------------------ | ----- | ----------------- |
| `redemption_coverage_shortfall` | Liquidatable-at-notice ÷ redemption demand < 1.0 | Stress | Top liquidation sources + basis |
| `redemption_coverage_thin` | Coverage in [1.0, `coverage_watch_multiple`) (default 1.25) | Watch | Top liquidation sources + basis |
| `full_liquidation_horizon_exceeded` | Any position's days-to-liquidate > `max_horizon_days` (default 30) | Stress | The long-horizon positions |
| `collateral_buffer_shortfall` | Liquidity buffer ÷ additional margin (`Σ notional × price_shock`) < 1.0 | Stress | Margin positions + basis |
| `liquidation_cost_elevated` | Portfolio cost > `cost_watch_bps` (default 75 bps) | Watch | Highest-cost positions |
| `illiquid_concentration` | NAV fraction not liquidatable within `illiquid_bucket_days` > `illiquid_nav_watch_frac` (default 0.20) | Watch | The illiquid positions |

Metrics are **additive and independent**; the output reports each that breached with its own
evidence. There is no opaque composite "liquidity score".

## Band mapping (deterministic, documented)

| Suggested band | Rule |
| -------------- | ---- |
| **Stressed** | Any **Stress-class** metric breached (coverage shortfall, horizon exceeded, or collateral shortfall) |
| **Watch** | No Stress-class breach, but any **Watch-class** metric breached (thin coverage, elevated cost, or illiquid concentration) |
| **Adequate** | No metric breached |

The band is a **triage suggestion for a human liquidity risk committee**. It is not a decision
to gate, suspend, trade, or a mandate-breach finding, and it never triggers an action.

## Hard boundaries (fail closed)

- Never recommend or take a **trade, cash-raise, or liquidation** ("sell", "execute the
  liquidation", "place the order").
- Never recommend or take a **fund-liquidity action** (gate/suspend redemptions, side pocket,
  swing pricing, fund suspension).
- Never assert the fund **is** "in breach", "illiquid", or "insolvent" — describe metrics
  factually and attribute breach findings to compliance and the committee.
- Never tune thresholds or the participation rate to a desired liquidity answer.
- Always disclose the **scenario assumptions**; a stress metric without its assumptions is
  meaningless.

## Modeling caveats (always include when a metric breached)

ADV/spread are point-in-time estimates; the participation model assumes orderly trading and
ignores second-order impact; redemptions and market stress may be correlated across positions
and investors; scenario parameters are assumptions, not forecasts (vary them); credit lines
and lines of last resort outside the modeled buffer are not counted. The pack must invite the
committee to weigh these.
