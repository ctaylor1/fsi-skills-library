# Domain Rules — merchant-fee-optimizer

How merchant card-processing fees are decomposed and how savings **opportunities** are
estimated. Benchmarks are configuration (versioned, owned by payments operations), not
hard-coded judgments, and never tuned to an individual merchant. Card-network interchange
schedules and rules take precedence over any benchmark; validate estimates against the
schedule in effect for the statement period.

## Fee decomposition

For a statement period:

- **Volume** = sum of settled card-sale amounts.
- **Interchange** = sum of interchange fees (paid to the issuer; largely non-negotiable
  pass-through, set by card-network schedules).
- **Assessments** = sum of network assessment/brand fees (paid to Visa/Mastercard/etc.;
  non-negotiable pass-through).
- **Processor markup** = sum of processor/acquirer fees (the negotiable component).
- **Fixed monthly fees** = statement, PCI, gateway, and similar recurring fees.
- **Total fees** = interchange + assessments + markup + fixed monthly fees.
- **Effective rate (bps)** = total fees ÷ volume × 10,000 (informational; sensitive to card
  mix, ticket size, and channel — a high effective rate is not by itself a pricing problem).
- **Implied markup (bps)** = processor markup ÷ volume × 10,000.

## Opportunity taxonomy

| Opportunity | Fires when (default config) | Estimate | Evidence attached |
| ----------- | --------------------------- | -------- | ----------------- |
| `pricing_model_switch` | Pricing model is `tiered`/`blended`/`flat` AND implied markup > `interchange_plus_markup_bps` (default 25) | `(implied_markup_bps − benchmark) ÷ 10,000 × volume` per month | Statement markup line + implied vs benchmark bps |
| `downgrade_recovery` | ≥ 1 transaction `downgraded` with a `qualified_interchange_fee` | `downgrade_recoverable_share` (default 0.7) × Σ(interchange − qualified) | The downgraded txns + category + incremental cost |
| `level_2_3_enablement` | Commercial/corporate-card txns submitted at Level 1 only | `level23_savings_bps` (default 80) ÷ 10,000 × eligible volume | Those txns + card type + level |

Opportunities are **independent and additive**; each is reported separately with its own
evidence and assumptions. Downgrade recovery (fixing existing categories) and Level 2/3
enablement (unlocking commercial-card programs) are kept distinct so they do not double count.

## Estimate ranges (no single guaranteed number)

Each opportunity produces a **point estimate**, then a range:

- `est_savings_high` = point estimate × `savings_high_band` (default 1.0 — the ceiling; do
  not overpromise beyond the point estimate).
- `est_savings_low` = point estimate × `savings_low_band` (default 0.6 — a conservative
  floor).

`total_estimated_savings.monthly_low/high` = the sum of fired opportunities; `annual` =
12 × monthly. Estimates are always presented as a **range with assumptions**, never a firm
promise.

## Hard boundaries (fail closed)

- Never **guarantee** savings or state a firm/"risk-free" promise.
- Never **recommend or direct** signing, terminating, cancelling, or switching a processor or
  contract — present options and route the decision to the human.
- Never give **legal, tax, or accounting advice**, including opinions on contract
  enforceability; surface contract terms factually.
- Never assert a downgrade or a Level 2/3 saving without tying it to the current published
  interchange schedule; treat those tables as versioned contracts.
- Never tune benchmarks to the individual merchant.

## Assumptions & caveats to always surface

Interchange/assessments are pass-through and largely non-negotiable; card mix and channel
drive much of the effective rate; Level 2/3 requires the merchant to capture and transmit
line-item data and to qualify; downgrade recovery requires process/integration changes;
early-termination fees and notice windows affect the economics of any change; all rates
change and must be validated against current schedules.
