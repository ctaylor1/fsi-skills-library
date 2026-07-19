---
name: financial-goal-progress-analyzer
description: >-
  Measure a client's progress toward stated financial goals (retirement, education,
  home purchase, legacy) by projecting each goal's value at its target date under approved,
  versioned assumptions, computing a funded ratio and status band, quantifying the
  shortfall or surplus, and surfacing illustrative planning levers with cited evidence. Use
  when an advisor or planner asks "are we on track for retirement", "how funded is the
  college goal", "what's the gap to the down-payment target", or needs a review-ready,
  source-linked goal-progress read. HARD BOUNDARY: this skill produces findings, evidence,
  and illustrative what-if levers ONLY for a human advisor; it NEVER makes a recommendation
  or suitability determination, gives personalized investment/tax advice, guarantees
  results, or places a trade, files, posts, closes, or writes any system of record.
license: MIT
compatibility: Amazon Quick Desktop; requires CRM, portfolio-accounting/OMS, planning-engine, product-data, disclosures/restrictions, and approved-assumptions MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Wealth Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Wealth Management advisory & compliance"
  aws-fsi-primary-user: "Financial advisor / planner"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Financial Goal Progress Analyzer

## Purpose and outcome
Given a client's stated goals, dedicated balances, contribution cash flows, and the firm's
**approved, versioned assumptions**, project each goal's value at its target date, compute a
**funded ratio** and a documented **status band** (On track / At risk / Off track),
quantify the shortfall or surplus, and derive **illustrative planning levers** (arithmetic
what-ifs). A successful output is a source-linked progress read an advisor can take into a
client conversation. The analysis surfaces evidence and levers; every judgement,
recommendation, and action stays with the licensed human.

## Use when
- "Are we on track for retirement / the college goal / the down payment?"
- "How funded is each goal, and where is the biggest gap?"
- "Show the shortfall to target and what would move the needle."
- An advisor needs a consistent, cited goal-progress read to attach to a client review.

## Do not use
- The user wants a **recommendation, product/allocation selection, or suitability sign-off**
  → out of scope. Provide the progress evidence and route to the advisor; for a Reg BI /
  suitability evidence review route to `suitability-reg-bi-reviewer` (which also does not
  approve the recommendation).
- The user wants a **retirement decumulation / sequence-of-returns / withdrawal-strategy
  model** with ranges → `retirement-income-scenario-modeler`.
- The user wants **drift analysis and a proposed trade list** → `portfolio-rebalancing-assistant`
  (R4, approval-gated).
- The user wants to **compare two portfolio proposals** → `portfolio-proposal-comparator`.
- The user wants the **client-review brief/deck assembled** → `client-review-preparer`.
- Signs of **exploitation, diminished capacity, or unusual disbursement** → stop the
  progress read and route to `senior-investor-protection-screener` and a trained human.
- **Personalized investment, tax, or legal advice** → out of scope for any skill; refer to
  the licensed advisor / tax professional.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a cited progress
analysis with a durable `analysis_id`; downstream review/modeling/suitability skills consume
it. It must not duplicate their modeling, recommendation, or trade-staging steps.

## Inputs and prerequisites
- Client identifier and the **goals** to evaluate, each with target amount, target date,
  dedicated balance, and (optionally) a monthly contribution and `target_terms`
  (`nominal` or `real`).
- **Approved assumptions** (expected return, inflation, status thresholds) as a *versioned
  contract*; the analysis records the `assumptions_version`. Never invent a return.
- Read access to CRM, portfolio accounting/OMS, and the planning engine. Schema and field
  detail: [scripts/validate_input.py](scripts/validate_input.py) and
  [references/source-map.md](references/source-map.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The goal record (planning
engine/CRM) defines the objective; portfolio accounting is the position of record for the
dedicated balance; the cash-flow schedule sources contributions; approved assumptions are a
versioned contract. Cite every figure to its source; never substitute a client assertion for
the account record.

## Workflow
1. **Scope & validate** — confirm the client and the goals in scope; load balances,
   contributions, and the approved assumptions; run
   [scripts/validate_input.py](scripts/validate_input.py).
2. **Project & band (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to project each
   goal (present balance grown at the approved return plus the contribution annuity, with
   inflation handling for `real`-terms goals), compute the funded ratio, and map it to a
   status band per the documented thresholds. Rules:
   [references/domain-rules.md](references/domain-rules.md).
3. **Attach evidence** — for each goal, cite the goal record, the balance, the contribution
   schedule, and the assumptions version.
4. **Derive levers** — for any goal not On track, compute the illustrative levers (additional
   monthly contribution, additional months, target reduction to match the projection). These
   are what-ifs for advisor-client discussion, explicitly **not** recommendations.
5. **Write the analysis** — plain-language status per goal + evidence + levers + explicit
   uncertainty (estimates, not guarantees) + data gaps / not-evaluable goals.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every evaluated goal has a status band and cited evidence;
each status equals the deterministic band mapping from its funded ratio; summary counts tie
to the per-goal bands; off-track goals carry levers; **no recommendation / suitability /
advice / guarantee / trade / filing / closure language is present**; and the standing
disclaimer is included. Fail closed on any miss.

## Human approval
`required` (R3). This is read-only decision support. A licensed human advisor must adjudicate
before any recommendation, suitability conclusion, client commitment, trade, filing, or
system-of-record change. The skill stages none of these; it never acts.

## Failure handling
- **Missing/zero target or unparseable/past target date** → report the goal as
  `not_evaluable` with the reason; do not fabricate a projection.
- **Ambiguous client/goal identity** → stop and confirm; never analyze the wrong client.
- **Missing contribution** → treat as 0 and label the assumption; do not guess a schedule.
- **Missing/omitted assumptions** → use approved defaults, record the `assumptions_version`,
  and flag that defaults were used; never substitute a personal return estimate.
- **Stale/conflicting balances** → cite both and flag; do not silently reconcile.
- **Tool timeout** → return the goals computed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — client (masked), as-of date, assumptions version, goals evaluated, counts by
   status band, count not evaluable.
2. **Per goal** — name, target (+ terms), target date, months to target, projected value
   (nominal and real), funded ratio, status band, shortfall/surplus, cited evidence, and (for
   off-track goals) illustrative levers.
3. **Not evaluable** — goals excluded and why.
4. **Caveats** — projections are estimates under approved assumptions, not guarantees; bands
   are a triage aid, not a suitability determination.
5. **Machine-readable** — goals + evidence + `analysis_id` for downstream skills.
6. **Standing disclaimer** — "Decision-support analysis only under approved assumptions; not a
   recommendation, suitability determination, guarantee of results, or investment/tax advice.
   No decision, trade, filing, or system-of-record change has been made."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask account/client numbers (last 4). Minimize customer data in the output
to what evidences a goal's status. Retain the analysis + citations + assumptions version per
records policy; log the read and any approval. Never exfiltrate customer data.

## Gotchas
- **A funded ratio is not a decision.** A low ratio justifies advisor discussion, never a
  recommendation, a suitability conclusion, or a trade.
- **Terms matter.** A `real`-terms target must be compared in today's dollars; mixing nominal
  projection against a real target overstates progress. The engine handles this per goal.
- **Assumptions are a contract, not a dial.** Use only the approved, versioned assumptions;
  never tune a return to make a goal "look" on track.
- **Estimates, not guarantees.** Present projections as ranges/estimates; the disclaimer and
  caveats exist for this reason. Avoid "will reach / guaranteed to" language entirely.
- **Levers are illustrative arithmetic**, not advice — describe what would close the modeled
  gap, and hand the choice to the advisor and client.
