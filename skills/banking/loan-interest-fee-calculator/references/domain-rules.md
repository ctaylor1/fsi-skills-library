# Domain Rules — loan-interest-fee-calculator

The deterministic recalculation math, the day-count conventions, the amortization and
participation logic, the tie-outs, and the version/effective-date rules. Formulas, day-count
conventions, tolerances, and materiality thresholds are **configuration** (versioned, owned
by loan-servicing operations and the approved-calculation function), not the skill's
judgment, and are never bent to reach a wanted figure. Orientation: standard US
loan-servicing interest, fee, amortization, and participation mechanics; the executed
agreement and the firm's servicing standard take precedence where they differ.

## Interest accrual (per period, in `scripts/calculate_or_transform.py`)

```
interest = principal * annual_rate * year_fraction(start, end, day_count)
```

`year_fraction` implements four supported day-count conventions:

| Convention | Year fraction |
| ---------- | ------------- |
| `30/360` (US/NASD) | `(360*(y2-y1) + 30*(m2-m1) + (d2'-d1')) / 360`, with `d1'=30 if d1=31`; `d2'=30 if d2=31 and d1'=30` |
| `30E/360` (European) | as above but `d1'=30 if d1=31`, `d2'=30 if d2=31` (unconditional) |
| `actual/360` | `actual_days / 360` |
| `actual/365` (fixed) | `actual_days / 365` |

The **day-count convention comes from the executed note / cited rate table**, never a
default guess; the engine defaults an unrecognized convention to `30/360` and input
validation warns.

## Fees

| Basis | Formula |
| ----- | ------- |
| `flat` | `amount` (a fixed, cited fee) |
| `pct_balance` | `base * rate` (e.g. servicing fee = balance x fee rate) |
| `pct_payment` | `base * rate` (e.g. fee = scheduled payment x fee rate) |

Every fee amount, base, and rate is a cited input from the agreement or the approved rate
table.

## Amortization

Level-payment (`level_payment`) or interest-only (`interest_only`). Periodic rate
`r = annual_rate / periods_per_year`.

```
level payment:  payment = principal * r / (1 - (1+r)^-n)      # r>0; else principal/n
per period t:   interest_t   = balance_start_t * r
                principal_t  = payment - interest_t           # final period pays remaining balance
                balance_end_t = balance_start_t - principal_t
```

The **final period absorbs rounding drift** (its principal repays the exact remaining
balance) so the schedule ends at a zero balance and the principal repaid ties to the note
amount.

## Settlement / payoff

```
payoff = principal_outstanding
       + accrued_interest
       + per_diem * per_diem_days        # interest accruing to the payoff date
       + fees_due
       - unapplied_funds                 # suspense / unapplied balances credited back
```

Each line is emitted as a signed component so the walk is inspectable.

## Participation allocations

Given a shared `total_amount` and participant `share_pct` values that sum to 1:

```
allocation_i = round(total_amount * share_pct_i, 2)   for every participant except the last
allocation_last = total_amount - sum(all earlier allocations)   # residual, so the sum is EXACT
```

The **last participant receives the rounding residual** so allocations sum exactly to the
shared amount — no cent is created or lost across the syndicate.

## Variance report vs. reconciliation (two distinct layers)

- **Variance report** compares each recomputed figure to the **servicing-ledger booked
  amount** (`book_amount`). `variance = computed - book`; `status = match` within tolerance,
  else `variance`; `material = |variance| > materiality_threshold`. This surfaces ledger
  discrepancies for human review.
- **Reconciliation** compares the recomputed **grand totals** to any stated
  **approved-calculation-engine totals** (`approved_engine_totals`). Each stated total must
  be reconciled: `variance = recomputed - approved`; `status = reconciled` within tolerance,
  else `out-of-balance`. This confirms the recomputation ties to the sanctioned engine.

Tolerance (`TOL = 0.01`) and `materiality_threshold` (default 25.00) are versioned config.

## Tie-outs (each must hold within tolerance; independently re-derived in `validate_output`)

1. interest `== principal * annual_rate * year_fraction(day_count)`
2. fee `== amount` (flat) or `base * rate` (percent)
3. amortization: `interest_t == balance_start_t * periodic_rate`; `principal_t + interest_t
   == payment` (non-final periods); `sum(principal_t) == principal`; `ending_balance == 0`
4. settlement `== sum(signed components)`
5. participation `sum(allocations) == total_amount` (exact)
6. variance-report and reconciliation math internally consistent

## Version & effective-date rules

- `calc_date` anchors the accrual windows, the payoff date, and which rate-table version
  applies; state it in the workbook.
- `rate_table_version` binds every rate to an **approved, versioned rate table**; a rate
  cannot be used without a version.
- `config_version` binds the tolerances, materiality threshold, day-count defaults, and
  formulas — the workbook records it so a recomputation is reproducible.
- `inputs_hash` binds the workbook to the exact numeric inputs; re-running the same inputs
  reproduces the same `calc_id` and the same numbers.
- Do **not** mix rate-table versions or config versions within one workbook.

## Durable identifiers

- `case_id` — the durable loan-servicing case id, carried through unchanged.
- `calc_id = licalc-{loan_id}-{calc_date}-{inputs_hash}` — the durable recomputation id.

## Assumption provenance (mandatory)

Every principal, rate, fee, base, settlement component, participation total, and share is
recorded in the `assumptions_register` with a `provenance` class and a dated `citation`. An
assumption without both is a control failure — `validate_output` rejects the workbook.

## Hard boundaries (fail closed)

- **Never post, book, apply, waive, reverse, credit, refund, or approve an adjustment** to
  any account or system of record. `action_taken` is always `none`; the workbook is a draft
  for human review. Any account change is a separate, human-authorized step.
- Never give **personalized financial, legal, or tax advice**.
- Never use a **rate without an approved rate-table version** or an **assumption without
  provenance**.
- Never adjust a formula, tolerance, materiality threshold, or day-count convention to reach
  a wanted figure.
- Never present a participation allocation set whose parts do not sum exactly to the shared
  total, or an amortization schedule that does not end at a zero balance.
