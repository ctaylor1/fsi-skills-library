# Controls — portfolio-hedge-reviewer

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `external-delivery` — required before the packet is delivered to a
  portfolio manager, investment committee, trade ticket, OMS, or risk system of record.

## Prohibited (fail closed)

- No **hedge selection, recommendation, ranking, or endorsement**, and no implication that a
  candidate is best / optimal / preferred / the one to use.
- No **decision to hedge**, hedge sizing, or hedge-ratio target.
- No **trade authorization, staging, routing, or execution** of any hedge or overlay.
- No **personalized investment, legal, or tax advice**; no **guarantee** of hedge efficacy,
  protection, or return.
- No **invented** hedge, scenario, sensitivity, or cost; no **assumption without provenance**;
  no formula, tolerance, factor unit, or shock bent to reach a wanted coverage or P&L.
- No **unreconciled** packet presented as tied out when approved-engine totals disagree.

## Required output screens (`scripts/validate_output.py`)

- Every hedge ties out: `residual[f] == portfolio[f] + hedge[f]`; `residual_gross ==
  sum|residual|`; `coverage_overall` matches its formula.
- Scenario P&L ties out: `portfolio == sum(P*shock)`, `hedge == sum(H*shock)`, and
  `hedged == portfolio + hedge == sum(residual*shock)` (linearity).
- Reconciliation: portfolio gross sensitivity and each scenario P&L reconcile to supplied
  approved-engine totals within tolerance.
- Provenance: every `assumptions_register` entry has a non-empty `provenance` **and**
  `citation`; `model.id`, `model.version`, and `model.effective_date` are recorded.
- Reproducibility: `packet_id` and `inputs_hash` present.
- Completeness: every candidate hedge appears with residual, coverage, and scenario P&L.
- Tier boundary: no hedge-selection / recommendation / execution / advice / guaranteed-
  efficacy language in the author narrative or limitations (regex screen).
- Standing disclaimer present (see [domain-rules.md](domain-rules.md) and the SKILL.md
  output contract).

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Portfolio sensitivities, candidate
  hedges, and their sizes can reveal positioning and forward intent; treat the packet, its
  inputs, `case_id`, and `packet_id` as need-to-know.
- Respect information barriers; do not move position or hedge-intent data across a wall.
- Retain the packet, its assumptions register, `config_version`, and `model.version` per
  records policy; log the read and any external-delivery approval.

## Reproducibility & change control

`inputs_hash` binds the packet to the exact numeric assumptions; `config_version` binds the
factor units and tolerances; `model.version` binds the sensitivity methodology. Re-running
the same inputs, config, and model reproduces the same `packet_id` and numbers. Changing an
assumption changes the hash — the audit trail shows what moved.

## Separation of duties

Computing the comparison (this skill) is separate from **deciding which hedge to use** (the
portfolio manager / investment committee), from **independently reviewing** the numbers, from
**testing residual exposure against limits** (`market-risk-limit-monitor`,
`investment-mandate-reviewer`), and from **executing** any trade (the trading desk / OMS). The
packet is a neutral input to a human's judgment, never a substitute for it.


## Phase 4 supplied full-repricing extension

For explicitly selected `advanced-derivatives`, use [the separate advanced contract](advanced-derivatives.md). Preserve full-book engine/benchmark binding and the no-fallback boundary; the first-order method above is not a complex derivative pricer.
