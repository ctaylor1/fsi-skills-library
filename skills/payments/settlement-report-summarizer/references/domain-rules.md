# Domain Rules — settlement-report-summarizer

Descriptive rules used to normalize and summarize a merchant settlement/payout report. These
are **arithmetic and labeling** rules only; none of them is advice or a control decision.

## Signed-amount convention

Credits to the merchant are **positive**; deductions are **negative**.

| Category | Sign | Meaning |
| -------- | ---- | ------- |
| `gross_sales` | + | Card sales presented for settlement (before deductions) |
| `refunds` | − | Amounts returned to cardholders |
| `chargebacks` | − | Disputed amounts debited back |
| `interchange_fees` | − | Fees paid to the issuer via the network |
| `scheme_fees` | − | Card-network / scheme assessments |
| `processor_fees` | − | Acquirer / processor / gateway markup |
| `other_fees` | − | Fees that cannot be classified into the three buckets above |
| `adjustments` | ± | Prior-period corrections, reclassifications, misc. credits/debits |
| `reserve_held` | − | Rolling/holdback reserve withheld this period |
| `reserve_released` | + | Previously held reserve returned this period |
| `cash_advance` | + | Merchant cash-advance disbursement, if bundled in the payout |

Fee lines are commonly reported as a positive `fee_amount` with a negative `net_amount`;
`validate_input.py` warns when the two signs disagree.

## Gross-to-net tie-out (the core deterministic check)

```
net_settlement = sum(signed amount of every valued category)
```

The summary's `net_settlement` must equal this sum and, when a funding advice is present,
must equal `funding.expected_net`. `validate_output.py` enforces both within a 0.50-unit
tolerance. Unvalued/pending lines (no gross/fee/net amount) are **excluded** from the tie-out
and listed under `data_gaps` — never assigned a guessed amount.

## Descriptive metrics (not judgments)

- **Total fees:** `total_fees = sum(|interchange_fees| + |scheme_fees| + |processor_fees| +
  |other_fees|)`.
- **Effective fee rate:** `effective_fee_rate_pct = total_fees / gross_sales * 100`. This is a
  neutral ratio for the period; the skill states it but never calls it high, low, competitive,
  or improvable (that is fee-optimization advice — route to `merchant-fee-optimizer`).
- **Card-brand split:** `by_card_brand` sums to `gross_sales`; report each brand's share as a
  neutral percentage.

## Thresholds

- **Amount tie-out tolerance:** 0.50 currency units (rounding).
- **Fee-rate tolerance:** the larger of 0.05 percentage points or 1% of the computed rate.
- **Reserve** is reported as a neutral held/released line; the skill does not opine on whether
  the reserve level is appropriate.

## Multi-currency

Convert a foreign-currency line into the settlement currency **only** with a cited FX rate and
as-of; otherwise report that line in its own currency and label it. Do not silently sum across
currencies.
