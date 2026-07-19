# Domain Rules — retirement-income-scenario-modeler

The deterministic decumulation math, the driver definitions, the withdrawal logic, the
scenario construction, and the tie-outs. Formulas and defaults are **configuration**
(versioned, owned by the planning / model-governance function), not the skill's judgment, and
are never bent to reach a desired answer. Orientation: a standard cash-flow decumulation
model as used in retirement planning; the firm's planning standard takes precedence where it
differs. All figures are **nominal dollars**; `annual_need` and guaranteed-income amounts are
stated in **first-retirement-year dollars** and inflate from the retirement year.

## Time frame

The projection covers the **decumulation phase only**: year index `j = 0 .. (horizon_age -
retirement_age)`, with `age_j = retirement_age + j`. Balances are stated as of the retirement
date. Pre-retirement accumulation is out of scope (see `financial-goal-progress-analyzer`).

## Per-year build (in `scripts/calculate_or_transform.py`)

```
spending_j          = annual_need * (1 + inflation)^j
guaranteed_gross_j  = sum over streams of  amount_s * (1 + cola_s)^j   if age_j >= start_age_s
guaranteed_net_j    = guaranteed_gross_j * (1 - guaranteed_income_tax_rate)
```

### Withdrawal (funding the after-tax spending gap)

`spending_gap` (default): the portfolio funds the remaining after-tax need. Draw accounts in
the documented `order`; for a source with effective tax rate `r_s`, delivering `net` requires
gross `net / (1 - r_s)`, bounded by the account balance:

```
remaining_net = max(0, spending_j - guaranteed_net_j)
for each account a in order (while remaining_net > 0):
    gross_a       = min(begin_a, remaining_net / (1 - r_a))
    remaining_net = remaining_net - gross_a * (1 - r_a)
net_withdrawal_j  = sum_a gross_a * (1 - r_a)      # == gross_total - tax_portfolio
tax_portfolio_j   = sum_a gross_a * r_a
```

`fixed_pct` (alternative): draw a fixed `fixed_pct * begin_portfolio` gross each year in
`order`, bounded by balances; net proceeds are then compared to spending (may leave a surplus
or a shortfall). Surplus is **not** reinvested (a documented, conservative simplification).

### Funding outcome and roll-forward

```
funded_j     = guaranteed_net_j + net_withdrawal_j
shortfall_j  = max(0, spending_j - funded_j)        # unfunded need; depletion signal
surplus_j    = max(0, funded_j - spending_j)
for each account a:
    return_a_j = return_sequence[a][j]  if provided else (expected_return_a + return_delta)
    end_a      = max(0, begin_a - gross_a) * (1 + return_a_j)
    begin_a (next year) = end_a
```

Withdrawals are **bounded by the balance**, so an account cannot go negative; when the
portfolio cannot fund the gap, `shortfall_j > 0` and the plan is under-funded that year.

## Scenarios (deterministic, documented)

Three cases are always produced. `base` uses the input assumptions as given. `favorable` and
`adverse` apply the documented `scenario_adjustments`:

- `return_delta` — added to every account's expected return.
- `inflation_delta` — added to the inflation rate.
- optional `return_sequence` — an explicit per-account list of early-year returns that
  **overrides** the flat return for those years. This models **sequence-of-returns risk**:
  poor returns early in retirement, while withdrawals are being taken, damage the plan more
  than the same average return in a smoother order.

Deltas are signed so that **favorable improves and adverse worsens** the outcome. The engine
and `scripts/validate_output.py` both require the scenario summary to be **monotonic**:
terminal portfolio value `adverse <= base <= favorable`, and total shortfall
`favorable <= base <= adverse`.

## Tie-outs (every one must hold within tolerance; re-checked in validate_output)

1. Balance roll-forward: `end_a == (begin_a - gross_a) * (1 + return_a_j)` for every account, year.
2. Continuity: `begin_a` of year `j+1` equals `end_a` of year `j`.
3. Funding identity: `guaranteed_net_j + net_withdrawal_j + shortfall_j - surplus_j == spending_j`.
4. Tax identity: `net_withdrawal_j == gross_total_j - tax_portfolio_j`;
   `tax_total_j == tax_portfolio_j + tax_guaranteed_j`.
5. Portfolio totals: `begin_portfolio_j / end_portfolio_j` equal the sums of account begins/ends.
6. Non-negativity: no balance `< 0`; no `gross_a > begin_a`.
7. Scenario monotonicity across adverse / base / favorable (terminal value and shortfall).

The engine checks tie-outs 1–6 by **independently re-deriving them from the emitted rows**
(the same computation `validate_output` performs), not by comparing a value to the expression
that produced it, and reports the result per scenario in `tieouts` and in
`model_checks.all_tieouts_ok`. `validate_output` re-derives them again and, on top of that,
**fails closed if the pack self-reports a tie-out failure** — a model that flags its own
tie-outs as broken is never presented.

## Assumption provenance (mandatory)

Every spending figure, expected return, tax rate, guaranteed-income amount/COLA, and
withdrawal parameter is recorded in the `assumptions_register` with a `provenance` class and a
dated `citation`. An assumption without both is a control failure — `validate_output` rejects
the pack.

## Reproducibility

`model_id = retire-{household}-{valuation_date}-{inputs_hash}`, where `inputs_hash` is a hash
of the numeric assumptions. Identical inputs reproduce the identical model and numbers.

## Hard boundaries (fail closed)

- Never output a **recommendation** (retire / claim / delay / annuitize / convert / buy a
  product / adopt a withdrawal rate), a **guarantee** of income or that assets will last, or a
  **probability of success presented as a promise** — those are licensed-advisor + client
  judgments. The projection is a **range conditional on stated assumptions**.
- Never make a **regulated decision**, sign off **suitability**, close a **case**, **file**,
  **trade**, **post**, or write a **system of record**.
- Never **hide a depletion / shortfall**, and never tune a return, inflation rate, tax rate,
  tolerance, or scenario delta to erase one or to reach a wanted answer.
- Never fabricate or leave **unsourced** an assumption; every number carries provenance.
- Never give **personalized investment, tax, insurance, or legal advice**.
