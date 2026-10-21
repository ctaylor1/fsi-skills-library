# Controls — portfolio-risk-contribution-analyzer

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `external-delivery` — required before the packet is delivered to a risk
  or investment committee, a client, or a report, or otherwise written to a system of record.

## Prohibited (fail closed)

- No **risk-limit action**: never set, change, calibrate, propose, or approve a risk limit,
  risk-appetite threshold, or utilization cap. Limit-setting is a **human / risk-committee**
  decision — this skill only measures contributions.
- No **mandate or portfolio action**: never mandate, recommend, or execute a trade, rebalance,
  hedge, de-risking, or any position change; no "you should sell/trim/reduce/hedge" directive.
- No **mandate-compliance determination** (breach/no-breach) — that is
  `investment-mandate-reviewer` and a human compliance officer.
- No **investment advice / recommendation** (buy / sell / hold / over- or under-weight), no
  **price target**, and no **guarantee** of risk reduction or return.
- No **assumption without provenance**; no **methodology without a version**; no formula,
  tolerance, rounding, or threshold bent to force a reconciliation tie or a wanted answer.
- No **decomposition when portfolio variance is not positive** (the variance guard); the result
  is mathematically undefined and must fail closed.

## Required output screens (`scripts/validate_output.py`)

- **Tie-outs re-derived independently** from the pack's weights + covariance:
  `portfolio_variance == w' Sigma w`; `total_risk == sqrt(variance)`;
  `MCR_i == (Sigma w)_i / total_risk`; `TRC_i == w_i * MCR_i`; `PCR_i == TRC_i / total_risk`.
- **Euler identity:** `sum(TRC_i) == total_risk`; **percentage:** `sum(PCR_i) == 1`.
- **Group aggregation:** `sum(group TRC) == total_risk`; `sum(group PCR) == 1`.
- **Variance guard:** `var_guard_ok` true (portfolio variance > 0).
- **Reconciliation:** the recorded `reconciled` flag equals `(rel_diff <= tolerance)` where
  `rel_diff = |computed - approved| / |approved|`; a claimed tie must actually hold; and
  `reconciliation.computed_total == pack total_risk`.
- **Methodology/version provenance:** methodology `name` and `version` present.
- **Assumption provenance:** every `assumptions_register` entry has non-empty `provenance`
  **and** `citation`.
- **Reproducibility:** `packet_id` and `inputs_hash` present.
- **Tier boundary (regex screen):** no risk-limit-setting, mandate/trade/rebalance/hedge, or
  investment-advice language in the author narrative (the standing disclaimer is stripped
  first so its negated phrases do not self-trip).
- **Standing disclaimer present:** "Illustrative risk-contribution analysis for analytical
  purposes only; not a risk limit, not a mandate to trade, rebalance, or hedge, and not
  investment advice. Risk contributions are conditional on the stated methodology, weights,
  and covariance inputs, which a qualified human and the approved risk engine must review."

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Weights and the risk decomposition can
  reveal positioning and strategy. Treat the packet, its inputs, and its `packet_id` as
  need-to-know; respect information barriers.
- Minimize holdings detail in output to what evidences a contribution.
- Retain the packet, its assumptions register, and `config_version` per records policy; log the
  read and any external-delivery approval.

## Reproducibility & change control

`inputs_hash` binds the packet to the exact numeric inputs (weights, covariance, methodology
version, config, prior baseline); the `config_version` and methodology `version` bind the
tolerance, materiality thresholds, and method. Re-running the same inputs and config reproduces
the same `packet_id` and the same numbers. Changing an input changes the hash — the audit trail
shows what moved, and the material-change section explains it against the prior baseline.

## Separation of duties

Building the packet (this skill) is separate from independently reviewing it, from any
**limit-setting** decision (risk committee), from any **mandate-compliance determination**
(compliance), and from any **portfolio action** (portfolio manager). The packet is a draft
analytical input to those human judgments, never a substitute for them.
