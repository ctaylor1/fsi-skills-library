# Domain Rules — cashflow-forecaster

How the forecast is computed and how scenarios behave. All factors and thresholds are
**configuration** (versioned, owned by the banking analytics team), never hard-coded
judgments and never tuned to an individual customer. The computation is deterministic and
reproducible from inputs + `config_version` (see `scripts/calculate_or_transform.py`).

## Historical spread (derived-from-history)

1. Bucket transactions into periods (`month` → `YYYY-MM`; `week` → ISO `YYYY-Www`).
2. Per period: `inflow = Σ credits`, `outflow = Σ debits`, `net = inflow - outflow`.
3. `avg_inflow` / `avg_outflow` = mean of the per-period totals across history.
4. `net_volatility` = population standard deviation of per-period net flow.
5. **Drivers** = signed net per category (fallback: counterparty; else `Uncategorized`),
   ranked by absolute contribution, each with a share of total absolute flow.

## Scenario factors (deterministic, documented)

Each scenario scales the recurring inflow/outflow by config factors, then applies
user-supplied one-off assumptions at their period offset:

| Scenario | inflow_factor | outflow_factor | Meaning |
| -------- | ------------- | -------------- | ------- |
| **base** | 1.00 | 1.00 | Recurring levels continue as observed |
| **upside** | 1.05 | 0.95 | Modestly higher inflow, lower outflow |
| **downside** | 0.90 | 1.10 | Modestly lower inflow, higher outflow |

Per future period: `net = avg_inflow·inflow_factor − avg_outflow·outflow_factor + one_offs`.
Running `balance` accumulates from the opening balance. Because the recurring net is highest
under upside and lowest under downside and the one-offs are identical across scenarios,
ending balances are **monotonic**: `downside ≤ base ≤ upside`. `validate_output` enforces this.

## Assumptions (user-supplied one-offs)

Each carries `id`, `description`, `offset` (1-indexed period into the horizon), `amount`,
`direction`, and `provenance`. One-offs are applied identically to all three scenarios so a
scenario reflects *recurring* uncertainty, not re-litigating the discrete event. Assumptions
outside the horizon are recorded but do not affect the projection (validate_input warns).

## Uncertainty

Reported as a per-period band = `volatility_k · net_volatility` (default `k = 1.0`). This is
a transparency aid derived from historical variability — it is **not** a confidence interval,
a probability, or a promise. State it as an estimate.

## Tie-outs (formula correctness)

- **Scenario tie-out:** `opening_balance + Σ(period net) = ending_balance`, and the ending
  equals the last period's running balance (tolerance 0.01).
- **History tie-out:** the per-period spread reconstructs the raw sum of transaction net flow
  (tolerance 0.01).

## Hard boundaries (fail closed)

- Never give financial, investment, tax, or credit **advice**, and never recommend an action.
- Never make or imply a **credit/eligibility decision** (approved, pre-approved, qualifies,
  denied).
- Never **guarantee** a future balance or outcome; a forecast is a range of estimates.
- Never tune scenario factors to the individual; use only the versioned config.

## Interpretation prompts (include when relevant)

Seasonality not captured in a short history, irregular income, one-off items the user has not
told you about, upcoming rate/fee resets on loans, and the fact that the downside scenario is
a planning aid — not a prediction that it will occur. Invite the user to refine assumptions.
