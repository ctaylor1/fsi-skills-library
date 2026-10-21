# Domain Rules — portfolio-risk-contribution-analyzer

The deterministic risk-decomposition math, the reconciliation rule, the material-change
definition, and the tie-outs. Formulas, tolerance, materiality thresholds, grouping dimension,
and rounding are **configuration** (versioned, owned by the risk / model-governance function),
not the skill's judgment, and are never bent to force a reconciliation tie or a wanted answer.
Orientation: standard Euler (marginal) risk decomposition of ex-ante volatility as used in
portfolio risk; the firm's approved risk methodology and version take precedence where they
differ, and the packet always records the methodology `version`.

## Ex-ante risk and its Euler decomposition (in `scripts/calculate_or_transform.py`)

Let `w` be the position weight vector and `Sigma` the approved annualized covariance matrix
(aligned to the positions order).

```
portfolio_variance   var_p   = w' * Sigma * w
portfolio_risk       sigma_p = sqrt(var_p)                     # ex-ante volatility
Sigma_w_i                    = (Sigma * w)_i                   # row i of Sigma times w
marginal contribution MCR_i  = Sigma_w_i / sigma_p            # d sigma_p / d w_i
total contribution    TRC_i  = w_i * MCR_i                     # component (total) risk
percent contribution  PCR_i  = TRC_i / sigma_p
```

Because `sigma_p` is homogeneous of degree 1 in `w`, **Euler's theorem gives
`sum(TRC_i) == sigma_p` exactly**, and therefore `sum(PCR_i) == 1`. These are the load-bearing
tie-outs, re-derived independently in `validate_output`.

- **Negative contributions are valid.** A hedge or diversifier can have `Sigma_w_i < 0`, so its
  MCR/TRC/PCR are negative; the contributions still sum to the total. Do not treat a negative
  contribution as an error.
- **Variance guard.** `var_p` must be `> 0`; if it is not (a degenerate or inconsistent
  covariance), the decomposition is undefined — set `var_guard_ok = false`, emit zero
  contributions, and **fail closed** in `validate_output`.

## Grouping

Contributions are aggregated by a configured `grouping_dimension` (default `sector`): the group
TRC is the sum of member TRCs and the group PCR the sum of member PCRs. Group aggregations tie
back to the total (`sum(group TRC) == sigma_p`, `sum(group PCR) == 1`).

## Reconciliation to the approved risk engine total

The packet **reconciles** the computed `sigma_p` to the engine's reported `approved_engine.total_risk`:

```
abs_diff   = computed_total - approved_engine_total
rel_diff   = |abs_diff| / |approved_engine_total|
reconciled = rel_diff <= reconciliation.tolerance_rel        # config, e.g. 0.01
```

- The engine total is the **anchor**; the packet **never overwrites it**. If `rel_diff` exceeds
  the tolerance, the result is **unreconciled** — surface the break for a human; never bend
  rounding, tolerance, or an input to force `reconciled = true`.
- `validate_output` recomputes `rel_diff` and requires the recorded `reconciled` flag to match,
  and requires `reconciliation.computed_total == pack total_risk`.

## Material changes since the prior review

Given a prior approved packet (`prior_review`), changes are measured against documented
materiality thresholds (config):

```
per position:  delta_pcr_i = current_pcr_i - prior_pcr_i
               material_i   = |delta_pcr_i| >= materiality.pcr_abs_threshold      # e.g. 0.03
                              OR the position was added / removed
total:         delta_rel    = (current_total - prior_total) / prior_total
               total_material = |delta_rel| >= materiality.total_risk_rel_threshold  # e.g. 0.05
```

The material-change section lists each position's prior/current PCR, the delta, and the material
flag, plus the total-risk change — an **explanation**, never a recommendation. Positions present
in only one of the two packets are flagged `added` / `removed` and treated as material.

## Tie-outs (every one must hold within tolerance; re-checked in validate_output)

1. `portfolio_variance == w' Sigma w` and `total_risk == sqrt(portfolio_variance)`
2. `MCR_i == (Sigma w)_i / total_risk` for every position
3. `TRC_i == w_i * MCR_i` for every position
4. Euler identity: `sum(TRC_i) == total_risk`
5. `sum(PCR_i) == 1` and `PCR_i == TRC_i / total_risk`
6. Group aggregation: `sum(group TRC) == total_risk`; `sum(group PCR) == 1`
7. Variance guard: `portfolio_variance > 0`
8. Reconciliation consistency: `reconciled == (rel_diff <= tolerance)` and
   `reconciliation.computed_total == total_risk`

## Assumption provenance (mandatory)

Every weight, the covariance, the methodology (with `version`), the approved-engine total, and
the prior-review reference is recorded in the `assumptions_register` with a `provenance` class
and a dated `citation`. An assumption without both, or a missing methodology `version`, is a
control failure — `validate_output` rejects the packet.

## Reproducibility

`packet_id = riskcontrib-{portfolio_id}-{as_of}-{inputs_hash}`, where `inputs_hash` is a hash of
the numeric inputs (weights, covariance, methodology version, grouping, engine total,
tolerance/materiality config, prior packet id). Identical inputs reproduce the identical packet
and numbers; `config_version` and the methodology `version` are recorded so a method change is
never mistaken for a book change.

## Hard boundaries (fail closed)

- Never **set, change, calibrate, propose, or approve a risk limit** or risk-appetite threshold
  — that is a human / risk-committee decision.
- Never **mandate, recommend, or execute** a trade, rebalance, hedge, or de-risking action.
- Never make a **mandate-compliance determination** (breach / no-breach).
- Never present a decomposition when the **variance guard** fails, or claim a **reconciliation
  tie** that does not hold.
- Never fabricate or leave **unsourced** an assumption, or omit the methodology **version**.
- Never give **personalized investment advice**, a price target, or a guarantee.
