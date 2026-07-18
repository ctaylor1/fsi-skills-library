# Domain Rules — best-execution-reviewer

Explainable best-execution **findings** and how they map to a **suggested review
disposition**. Thresholds are configuration (versioned, owned by the best-execution
committee / compliance), not hard-coded judgments, and are applied per the effective policy
on the trade date. Orientation references: the firm's best-execution policy, MiFID II RTS
27/28, FINRA Rule 5310, and SEC Reg NMS Rules 605/606 take precedence for the applicable
jurisdiction. Best execution is **multi-factor** (price, cost, speed, likelihood of
execution and settlement, size, nature); these findings surface *candidates for review*, not
conclusions.

## Finding taxonomy

| Finding | Fires when (default config) | Evidence attached |
| ------- | --------------------------- | ----------------- |
| `price_outside_benchmark` | Client-adverse deviation vs benchmark > `price_tolerance_bps` (default 5) | Execution price, benchmark, side, adverse bps |
| `price_materially_off` *(escalator)* | Client-adverse deviation vs benchmark > `price_hard_bps` (default 25) | Execution + adverse bps + hard threshold |
| `slow_execution` | Arrival-to-execution latency > `latency_max_seconds` (default 60) | Latency + limit + timestamps |
| `low_fill_rate` | Fill rate < `min_fill_rate` (default 0.90) for an order type in `fill_order_types` (default `["market"]`) | Fill rate + order type |
| `high_cost` | Explicit commission bps + implicit (adverse) bps > `cost_cap_bps` (default 30) | Explicit/implicit/total bps + cap |
| `venue_off_policy` *(escalator)* | Executed on a venue not in the effective `approved_venues` list | Venue/MIC |
| `exception_undocumented` *(escalator)* | `exception_flag` set with no `exception_rationale_ref` on file | Exception flag + missing rationale |

**Client-adverse deviation** is signed so positive = worse for the client: for a **buy**,
`(price − benchmark)`; for a **sell**, `(benchmark − price)`, expressed in bps of the
benchmark. A negative (favourable) deviation never fires a price finding. Findings are
**additive and independent**; the pack reports each that fired with its own evidence. There
is no opaque composite "best-ex score".

## Disposition mapping (deterministic, documented)

| Suggested band | Rule |
| -------------- | ---- |
| **Pass** | 0 findings fired |
| **Review** | 1–2 findings fired, none an escalator |
| **Escalate** | ≥ 3 findings fired, OR any escalator fired (`price_materially_off`, `venue_off_policy`, `exception_undocumented`) |

The disposition is a **triage suggestion for the best-execution committee**. It is not a
best-execution or compliance determination and it never triggers a case action, remediation,
or filing.

## Not-evaluable rules (never guess)

- **No benchmark** on an execution → price and cost checks are `not_evaluable` for that row.
- **Missing arrival/execution timestamps** → `slow_execution` is `not_evaluable` for that row.
- **No effective approved-venue list** → `venue_off_policy` is not enforced (reported as
  not-evaluable), not silently passed.
- **Missing commission or notional** → `high_cost` is `not_evaluable` for that row.
- **Order type outside `fill_order_types`** → `low_fill_rate` is not applied (partial fills on
  limit/worked orders are expected).

## Hard boundaries (fail closed)

- Never state or imply that an execution, desk, or period **was / was not best execution**,
  **is compliant**, or **is / is not in breach** — attribute all conclusions to the human
  committee.
- Never **close, disposition, or clear** an exception or case, and never issue a **remediation
  instruction** or **regulatory filing**.
- Never tune thresholds to a desk or day, or infer a benchmark that was not effective at the
  order's decision time.
- An **undocumented exception** is a records finding, not an allegation of misconduct.

## False-positive checks (always include when any finding fired)

Benchmark source/timestamp alignment to the decision time; order type and client instruction
(limit / directed orders); market conditions (volatility, auctions, halts, thin liquidity);
approved-venue-list version effective on the trade date; the documented exception rationale in
the OMS/EMS annotation or communications archive; and order size / working strategy for large
or illiquid orders. The pack must invite the committee to weigh these before escalating.
