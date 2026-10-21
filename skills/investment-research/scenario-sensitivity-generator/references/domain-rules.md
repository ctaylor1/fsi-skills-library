# Domain Rules — scenario-sensitivity-generator

## Version 0.2.0 contract

This engine evaluates a supplied arithmetic graph only. It has no native three-statement, DCF or credit-runner adapter and cannot establish economic coherence, financing feasibility, calibrated scenario probabilities or full instrument repricing. Model formulas must be mapped and independently checked before reuse; a model_id alone does not prove integration. Invalid/non-finite formulas and unsupported argument shapes fail explicitly.


Deterministic analytical mechanics. The upstream model and the firm's approved assumption
set govern; nothing here originates a valuation or a view.

## Formula grammar (whitelisted, deterministic)

Output formulas may reference drivers and earlier outputs using only:
`+ - * / ** %`, parentheses, and `min` / `max` / `abs`. No code, no lookups, no learned
functions, no external calls. An undefined or unsupported formula, or a reference to an
unknown driver/output, **fails closed** — the model definition must be corrected.

## Analyses

| Analysis | Definition |
| -------- | ---------- |
| **Scenario** | Apply named driver overrides (e.g. base/bull/bear); recompute all outputs; report each output and its delta / % vs. base. |
| **One-way sensitivity** | Vary a single driver over N points; report output and % change at each. |
| **Two-way table** | Vary a row driver × a column driver; report the output at each cell (grid = rows × cols × formula cost — cap and stage). |
| **Breakeven** | Solve for the driver value at which an output equals a target, by **bisection within a stated bracket** (requires a sign change in range). |
| **Decision threshold** | The driver level at which an output crosses a reference level; report the bracket searched, convergence, and which side the base case sits on. |

## Rules

- **Recompute everything** from drivers + formulas; never estimate, interpolate a formula,
  or free-type an output.
- **Bracketing:** same-sign endpoints mean no sign-change bracket was found; they do not establish that no interior root exists. Return `search_status: not-bracketed`, no solution and an explicit unknown-existence note. Never extrapolate beyond the supplied bracket or assert absence of crossings.
- **Two-way axes:** row and column drivers must be distinct; the same driver cannot represent two independent axes.
- **Monotonicity:** a reported root is one crossing; if the output is non-monotonic, state
  that other crossings may exist and widen/relayer the bracket — do not assert uniqueness.
- **Provenance:** every driver requires a `source_ref`; a plausible table on an unsourced
  guess is flagged, not delivered.
- **Reproducibility:** pin `config_version`; identical inputs must reproduce identical
  numbers.

## No-advice boundary

Describe behaviour factually ("equity value rises with EBITDA margin; breakeven margin is
14.2%"). Never prescribe an action, imply a fair value, or present a standalone price
target. The output validator screens for advice phrasing ("implies upside", "attractive
entry", "buy/sell/hold", "price target", "should").
