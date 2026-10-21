---
name: portfolio-characteristics-change-monitor
description: >-
  Compare two APPROVED portfolio characteristic snapshots (current vs prior) across active
  weights, ex-ante tracking error, duration, beta, and factor exposures; compute the
  prior-to-current drift, flag changes beyond configured attention bands, cite evidence for
  every change, and assemble a change-and-exception packet with a suggested review priority.
  Use when a portfolio-risk analyst asks "what changed in this portfolio's risk
  characteristics since last period", "show me the drift in active weights / tracking error /
  duration / beta / factors", or needs a source-linked change-and-exception packet for review.
  HARD BOUNDARY: this skill explains and evidences drift only — it NEVER directs, recommends,
  or executes rebalancing or any trade, and NEVER sets, modifies, or overrides a mandate limit
  or band. It does not adjudicate mandate breaches; any characteristic at or near a supplied
  mandate reference is routed to investment-mandate-reviewer for authoritative testing, and
  remediation stays human.
license: MIT
compatibility: Amazon Quick Desktop; requires approved risk/analytics snapshots, PMS/OMS positions & benchmark, market & reference data, mandate-reference, and drift-config MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Portfolio-risk analyst"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-09-20"
---

# Portfolio Drift Monitor

## Purpose and outcome
Given two **approved** portfolio characteristic snapshots — a current and a prior one — for
the same portfolio and benchmark, compute the prior→current **change** for every comparable
characteristic (active weights, ex-ante tracking error, effective duration, beta, factor
exposures), flag the changes that exceed the configured **attention bands** ("material
drift"), attach cited evidence to each, flag any characteristic at or near a supplied mandate
reference for **routing**, and produce a **change-and-exception packet** with a suggested
review priority. A successful output lets a portfolio-risk analyst see, with evidence, exactly
what moved since last period and which moves warrant attention — so a **human** decides what
to do next. The decision, any remediation, and any limit adjudication remain human.

## Use when
- "What changed in this portfolio's risk characteristics since the last snapshot?"
- "Show me the drift in active weights / tracking error / duration / beta / factor exposures."
- "Compare current vs prior and give me a change-and-exception packet for review."
- An analyst needs a consistent, cited prior→current characteristic comparison to attach to a
  risk review.

## Do not use
- The user wants the drift **fixed** — rebalance, reweight, trim, or construct/size/execute
  trades → out of scope (HARD BOUNDARY). Manager-directed remediation →
  `portfolio-rebalancing-assistant` and the manager's entitled OMS.
- The user wants a **mandate limit set or changed**, or asks whether the portfolio **is in
  breach** → out of scope; this skill does not adjudicate limits. Route the at/near-limit item
  to `investment-mandate-reviewer` (the authoritative limit test).
- **Deeper issuer/sector/factor/look-through** detail behind a drift → `portfolio-exposure-analyzer`.
  **Liquidity / liquidation-horizon** questions from a duration drift → `fund-liquidity-assessor`.
- The user wants **return attribution** (allocation/selection/factor) rather than
  characteristic drift → `portfolio-performance-attributor`.
- A plain **holdings/positioning summary** (not a prior→current comparison) →
  `portfolio-holdings-summarizer`.
- Personalized **investment advice** (what to buy/sell/hold) → out of scope; not licensed advice.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a cited
change-and-exception packet with a durable `packet_id`; downstream analysis, compliance,
escalation, and remediation skills consume it. It must not duplicate their limit adjudication,
disposition, or remediation steps, and it never decides a breach or directs a trade itself.

## Inputs and prerequisites
- `portfolio_id`, `benchmark_id`, `as_of`, `prior_as_of` (`prior_as_of` strictly before
  `as_of`), and `config_version`.
- Two snapshots — `current` and `prior` — each **approved** (`approval.approved: true` with an
  `approval.source_ref`) and carrying the characteristics to compare: `tracking_error`,
  `duration`, `beta`, `active_weights[{key, active_weight}]`, `factors[{key, exposure}]`.
- Optional `config` (attention bands + `route_buffer`) and optional `mandate_reference`
  (limit references used only for proximity routing). Schema and validation:
  [scripts/validate_input.py](scripts/validate_input.py).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **approved risk/analytics
snapshot is the record** for each characteristic; PMS/OMS positions and benchmark provide the
underlying evidence and look-through; reference data resolves classifications; a supplied
mandate reference is used only to flag proximity for routing. Cite every change to **both**
the current and prior snapshot rows and record the `config_version`. Never compute a
characteristic from raw holdings here, and never compare an unapproved snapshot.

## Workflow
1. **Scope & validate** — confirm the portfolio, benchmark, and the two effective dates; load
   both approved snapshots and the config; validate with `validate_input` (fails closed if a
   snapshot is unapproved or the dates are out of order).
2. **Compute changes (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute each
   characteristic's prior→current delta, flag `material` drift (`abs(delta) > band`), and flag
   `route_to_compliance` where a current value is at/near a supplied mandate reference. Each
   change carries its evidence (current + prior citation).
3. **Assemble exceptions** — collect the material-drift and routed changes into the exception
   set, each with its type (`material_drift` / `limit_proximity`), delta, band, and evidence.
4. **Suggest priority** — map the exception set + routing to a band (Informational / Review /
   Elevated) per the deterministic, documented mapping. This is a triage suggestion for a
   human, explicitly **not** a compliance determination.
5. **Route limit proximity** — if any characteristic is at/near a mandate reference, emit a
   handoff to `investment-mandate-reviewer` covering those items (never adjudicate the breach).
6. **Write the packet** — plain-language change-and-exception narrative + the full change set
   + exceptions with evidence + not-evaluable characteristics + the suggested priority + any
   handoff + the standing disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every exception has cited evidence; the suggested priority
maps deterministically from the exception set and routing; **no rebalancing-direction,
limit-modification, breach-determination, or advice language** is present; the standing
disclaimer is present; and any limit-proximity item is routed to `investment-mandate-reviewer`
(never swallowed or self-adjudicated). Fail closed on any miss.

## Human approval
`external-delivery`: human approval is required before the packet is delivered outside the
risk function or written to a case/system of record. No approval is needed for the analyst's
own read. The skill never rebalances, changes a limit, or adjudicates a breach — those are
human/compliance/portfolio-management actions.

## Failure handling
- **Unapproved / draft snapshot** → fail closed; only approved characteristics may be compared.
- **Dates out of order** (`prior_as_of` not before `as_of`) → fail closed; never compare a
  snapshot against a later "prior".
- **Characteristic present in only one snapshot** → report `not_evaluable`; never assume
  unchanged or drift-from-zero.
- **No mandate reference supplied** → limit-proximity routing is disabled; say so and report
  material drift only.
- **Stale / conflicting sources** → cite both; do not resolve silently.
- **Tool timeout** → return the changes computed so far with a clear "incomplete" flag; assume
  no automatic retry.

## Output contract
1. **Summary** — `packet_id`, portfolio, benchmark, window (prior→current + label), counts
   (changes, exceptions, routed), suggested priority band.
2. **Changes** — per characteristic: prior, current, delta, band, `material`, and evidence.
3. **Exceptions** — the material-drift/routed subset, each with type, delta vs band, reason,
   and cited evidence (current + prior `source_ref`).
4. **Routing** — any limit-proximity items and the `investment-mandate-reviewer` handoff.
5. **Not evaluable** — characteristics present in only one snapshot.
6. **Machine-readable** — changes + exceptions + `fired_exceptions` + `route_to_compliance` +
   `packet_id`.
7. **Standing disclaimer** — "Change and exception evidence only; not a rebalancing
   instruction or a compliance determination. No trade, rebalancing, or limit change has been
   made or directed."
See [references/controls.md](references/controls.md).

## Privacy and records
Characteristics and holdings can be **MNPI / client-confidential**. Minimize data in the
packet to what evidences a change or exception. Retain the packet + citations +
`config_version` per records policy; log the read and any external-delivery approval. Route
only to approved risk/compliance queues; never exfiltrate characteristics, holdings, or trade
intentions.

## Gotchas
- **A change is not a decision or an action.** Material drift justifies *review*, never a
  skill-initiated trade, reweight, limit change, or breach finding.
- **Drift is not breach.** Attention bands are drift-review thresholds, not mandate limits.
  Crossing a band means "look at this"; only `investment-mandate-reviewer` tests the limit.
- **Approved snapshots only.** Comparing a draft/unapproved snapshot can manufacture phantom
  drift — the input check fails closed for a reason.
- **Boundary bands.** A delta exactly at the band is a reported change, not an exception; the
  engine flags material drift only when strictly over.
- **Only-in-one-snapshot buckets.** A new sector or factor present now but absent prior is
  `not_evaluable`, not a drift from zero — do not overstate.
- **Bands are versioned config, not judgement.** Never tune a band to a portfolio or infer
  "what's acceptable here"; cite the `config_version`.
- **Sign and direction are factual, intent is not.** Describe the delta and its direction;
  never translate it into a buy/sell/reweight instruction.

## Phase 1 executable boundary

Read [the bounded offline contract](references/phase1-contract.md) before running the scripts or relying on a handoff. It states required input evidence, unavailable cases and source-bound validation. Enterprise connectors and review queues described above are deployment interfaces, not implemented integrations.

## Phase 1 support boundary

Comparable supplied characteristic snapshots; no rebalancing or causal decomposition

This package performs only its documented local supplied-input operations. Live source access, authenticated permissions, production engines and professional acceptance are separate deployment requirements. Generated resources are pinned in `references/package-manifest.json`; maintain the canonical shared source. Legacy identifiers resolve through the repository migration registry.
