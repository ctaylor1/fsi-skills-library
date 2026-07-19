---
name: stress-test-scenario-designer
description: >-
  Design severe-but-plausible stress-test scenarios — severity ladders (baseline / adverse /
  severely-adverse), risk-factor shocks, transmission channels, assumptions, management
  actions, and reverse-stress thresholds — with transparent, reproducible severity, coverage,
  plausibility, and distance-to-breach evidence for a human reviewer. Use when an enterprise,
  capital, or liquidity risk analyst asks to build or calibrate stress / ICAAP / ILAAP /
  CCAR-style scenarios, define transmission channels from macro/market factors to binding
  constraints (CET1, LCR), or find the reverse-stress point that reaches a limit. HARD
  BOUNDARY: this skill designs and recommends candidate scenarios only; it NEVER adopts or
  approves a scenario, makes a capital/liquidity adequacy or pass/fail determination, sets a
  binding limit or trigger, certifies the transmission model, or files a regulatory
  submission — adoption requires human adjudication by the risk committee / model risk / board.
license: MIT
compatibility: Amazon Quick Desktop; requires read-only stress-config, risk-register/limits, finance and operational data, loss-event/scenario-library, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Risk Management"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Domain workflow"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Enterprise Risk Management"
  aws-fsi-primary-user: "Enterprise, capital, or liquidity risk analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Stress-Test Scenario Designer

## Purpose and outcome
Given a firm's binding constraints, material risk drivers, and versioned scenario config,
assemble a **candidate stress-scenario set**: a severity ladder with risk-factor shocks,
explicit transmission channels to each binding constraint, documented assumptions and
management actions, and a reverse-stress threshold. The engine computes **explainable**
severity, coverage, plausibility, distance-to-breach, and a reverse-stress multiple, then maps
the deterministic flags to a **readiness band**. A successful output lets a risk committee /
model-risk reviewer challenge and adjudicate a complete, reproducible, source-linked design —
the adoption, adequacy call, and any filing remain human.

## Use when
- "Design a severely-adverse scenario for our capital stress test with transmission channels."
- "Calibrate a severe-but-plausible adverse/severely-adverse ladder for these drivers."
- "What reverse-stress scenario takes CET1 (or LCR) to its minimum?"
- A reviewer needs a consistent, cited scenario-design pack to attach to an ICAAP/ILAAP or
  CCAR/DFAST-style exercise for challenge.

## Do not use
- The user wants to **adopt/approve** a scenario, make a **capital/liquidity adequacy or
  pass/fail** call, set a **binding limit**, or **file** a submission → out of scope. Provide
  the design + evidence and route to the human risk committee / model risk / board (see
  [references/controls.md](references/controls.md)).
- **Running** the downstream analytics on a scenario → `liquidity-risk-scenario-analyzer`
  (funding/survival horizon), `market-risk-limit-monitor` (stress loss vs limits), or
  `credit-risk-portfolio-analyzer` (portfolio loss/migration).
- **Independent validation** of the transmission model/betas → `model-validation-assistant`.
- A **service-disruption / operational-resilience** severe-but-plausible test (not a
  financial-capital/liquidity scenario) → `operational-resilience-scenario-tester`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a design pack with a
durable `design_id`; downstream analytics, validation, and documentation skills consume it. It
must not duplicate their execution or reach an adoption/adequacy conclusion.

## Inputs and prerequisites
- **Binding constraints** (metric, direction `min`/`max`, limit, starting value, unit) — e.g.
  CET1 ratio, LCR.
- **Risk factors** with a baseline value and severe-but-plausible bands
  (`plausible_max_shock`, `severe_min_shock`).
- **Scenarios** (baseline + at least one stress), each with variables, transmission channels,
  assumptions, and (for stress scenarios) management actions.
- **Impact model** — versioned linear transmission betas per constraint; optional
  `reverse_stress` target. Read access to the sources in
  [references/source-map.md](references/source-map.md). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The stress-testing standard and
versioned scenario config are the position of record for severity bands, plausibility floors,
transmission betas, and constraint limits; risk register and finance data supply drivers and
starting values. Cite every projected impact to a config version and a dated starting value.

## Workflow
1. **Scope & load** — confirm the binding constraints, drivers, and `config_version`; load
   factors, bands, betas, and starting values; validate with `validate_input`.
2. **Build the ladder** — for each scenario, set risk-factor values and document transmission
   channels, assumptions, and management actions.
3. **Compute (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute shock
   vectors, impact-weighted severity, per-constraint projection and distance-to-breach, the
   reverse-stress multiple, coverage/plausibility/monotonicity flags, and the readiness band.
   Calculations are **explainable**, not a black box (see
   [references/domain-rules.md](references/domain-rules.md)).
4. **Assess readiness** — surface coverage gaps, implausible/insufficient shocks, and
   non-monotonic severity as **Not-ready**; a clean set is **Ready-for-review** (a
   completeness gate, not an approval).
5. **Write the pack** — plain-language design + per-scenario evidence + reverse-stress result
   + explicit uncertainties and calibration caveats, ending with the standing disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: structural completeness (channels/assumptions/actions),
numeric distance-to-breach, no coverage gaps, a reverse-stress result, the readiness band ties
to the deterministic mapping, no decision/adoption/filing/advice language, and the disclaimer
is present. Fail closed on any miss.

## Human approval
`required`: mandatory human adjudication (risk committee / model risk / board) before any
scenario is **adopted**, any **limit/trigger** is set, any **capital/liquidity decision** is
made, or anything is **filed**. No approval is needed for the reviewer's own read of a
candidate pack. The skill never writes a system of record.

## Failure handling
- **Missing config/betas** → state which constraints cannot be projected; do not invent
  sensitivities.
- **Thin/absent plausibility bands** → compute severity but flag that severe-but-plausible
  calibration is unscreened; do not assert a shock is plausible.
- **Non-monotonic ladder** → readiness `Not-ready`; surface the mis-ordered scenarios.
- **Ambiguous constraint/starting value** → stop and confirm; never project against a guessed
  starting point.
- **Conflicting standard vs config vs data** → cite all; do not resolve silently.
- **Tool timeout** → return scenarios computed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — `design_id`, config version, scenario count, readiness band.
2. **Scenarios** — per scenario: severity score, shock vector, per-constraint stressed value +
   distance-to-breach, transmission channels, assumptions, management actions, and any
   coverage/plausibility flags.
3. **Reverse stress** — target constraint, scaling multiple (or "not reachable"), and the
   plain-language interpretation.
4. **Uncertainties / caveats** — calibration limits, model dependency, data as-of gaps.
5. **Machine-readable** — full pack + `design_id` for downstream skills.
6. **Standing disclaimer** — the `DISCLAIMER` text in
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py).
See [references/controls.md](references/controls.md).

## Privacy and records
**Confidential** firm risk/finance data; typically no customer PII — keep exposures and
starting values at the aggregate level the design needs. Retain the pack + `design_id` +
`config_version` + starting-value as-of dates per records policy; log the read and the human
adjudication decision. Never exfiltrate firm risk data.

## Gotchas
- **A candidate is not an adopted scenario.** A `Ready-for-review` band means *complete enough
  to challenge*, never that capital/liquidity is adequate or that the firm passes.
- **Reverse stress cuts both ways**: `λ < 1` means the scenario already reaches the limit
  below full severity — do not report that as a breach *determination*, only as a projection.
- **Severe-but-plausible is a band, not a max**: an implausibly severe shock is as much a
  calibration failure as an insufficiently severe one; both flag `Not-ready`.
- **Betas are a model**: they are versioned config and require independent validation — never
  certify them here.
- **Do not calibrate to a desired outcome**: bands, floors, and betas come from the approved
  config, not from tuning a scenario until a constraint (does not) breach.
