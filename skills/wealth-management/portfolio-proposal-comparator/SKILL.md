---
name: portfolio-proposal-comparator
description: >-
  Compare two or more portfolio proposals side by side across objectives, risk, costs, taxes,
  liquidity, concentration, product features, and conflicts of interest, with every assumption
  stated and every difference cited to source. Use when an advisor or portfolio specialist asks
  to "compare these proposals", "which proposal costs more / is more concentrated", "show the
  trade-offs between option A and option B", or needs an even-handed, review-ready comparison for
  a client discussion or a supervisory file. This skill surfaces differences, threshold breaches,
  and conflicts as evidence for a licensed human to adjudicate; it NEVER selects or recommends a
  proposal, makes a suitability/Reg BI determination, gives personalized investment or tax advice,
  or executes trades — those are human / authorized-system actions.
license: MIT
compatibility: Amazon Quick Desktop; requires CRM, portfolio-accounting/OMS, planning-engine, product-data, disclosures/restrictions, and approved-tax-assumption MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Wealth Management"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Domain workflow"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Wealth Management advisory & compliance"
  aws-fsi-primary-user: "Advisor / portfolio specialist"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Portfolio Proposal Comparator

## Purpose and outcome
Given two or more portfolio proposals for the same client, compute a **deterministic, even-handed
comparison** across the eight dimensions — objectives, risk/allocation, costs, taxes, liquidity,
concentration, product features, and conflicts of interest — attach cited evidence to every
material difference, flag every threshold breach or conflict, and state every assumption used. A
successful output is a **review-ready comparison pack** that lets a licensed advisor (and, where
required, a supervisor) adjudicate the trade-offs against the full client profile. The choice of
proposal, the suitability determination, and any trade remain **human**.

## Use when
- "Compare these two (or three) proposals across cost, risk, liquidity, and concentration."
- "Which proposal is more concentrated / more expensive / more tax-efficient?" (as a factual
  comparison, not a recommendation).
- "Show the trade-offs between option A and option B for a client discussion."
- A supervisor wants a consistent, cited, assumptions-transparent comparison for the file.

## Do not use
- The user wants the skill to **pick, rank, or recommend** a proposal, or to state that a proposal
  **is suitable** / Reg BI compliant → out of scope. Produce the comparison and route the
  suitability/Reg BI documentation to `suitability-reg-bi-reviewer` (which itself does not approve
  the recommendation) and the decision to the licensed advisor.
- **Personalized investment or tax advice** ("what should this client buy", "should they realize
  this gain") → out of scope; provide the factual comparison only and route to the advisor / a
  licensed tax specialist.
- Building the **proposed trade list / drift analysis** to reach a chosen target →
  `portfolio-rebalancing-assistant`.
- Establishing the **objectives, constraints, and benchmarks** the proposals should be measured
  against → `investment-policy-statement-builder`; measuring **goal funding** →
  `financial-goal-progress-analyzer`; **retirement income** paths →
  `retirement-income-scenario-modeler`.
- Signs of exploitation, diminished capacity, or an unusual disbursement in the request →
  `senior-investor-protection-screener`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a comparison pack with a
durable `comparison_id`; it does not select, approve, rebalance, or file. Downstream skills consume
the `comparison_id` and evidence rather than recomputing the comparison. Upstream,
`client-review-preparer` may embed a comparison in a review brief and `advisor-follow-up-assistant`
may reference it in approved follow-ups.

## Inputs and prerequisites
- **Two or more proposals** for the same client, each with its holdings (weight, expense ratio,
  asset class, sector, issuer, liquidity, share class, proprietary flag) and proposal-level fields
  (advisory fee, assumed turnover, revenue-sharing, surrender period, stated objective).
- Optional **stated client objective** to check each proposal against.
- **Approved configuration** (versioned): concentration limits, illiquidity limit, cost-dispersion
  threshold, and the approved tax-drag assumptions. Schema and defaults:
  [scripts/validate_input.py](scripts/validate_input.py) and
  [references/domain-rules.md](references/domain-rules.md).
- Read access to CRM, portfolio-accounting/OMS, planning engine, product data, and
  disclosures/restrictions. Never substitute a marketing sheet for the OMS/product record.

## Source hierarchy
See [references/source-map.md](references/source-map.md). Portfolio-accounting/OMS holdings are the
position of record; product data resolves expense ratios, share classes, liquidity, and proprietary
status; the planning engine supplies objectives/constraints; approved config supplies thresholds and
tax assumptions. Cite every difference and flag to a source row.

## Workflow
1. **Scope & confirm** — confirm the client and the exact set of proposals being compared; load each
   proposal's holdings and product attributes; validate with `validate_input`. If fewer than two
   proposals are supplied, stop — there is nothing to compare (never fabricate a second option).
2. **Compute metrics (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute, per proposal:
   weighted expense, total cost, tax-drag estimate (approved assumptions), allocation, single-issuer
   and single-sector concentration, illiquid weight, proprietary weight, and product features.
3. **Flag differences (deterministic)** — raise a flag with cited evidence for each threshold breach
   (concentration, liquidity), each conflict (proprietary product, revenue-sharing, costlier share
   class), each objective mismatch, and material cost dispersion between proposals.
4. **Build the side-by-side matrix** — one row per dimension, one column per proposal; values only,
   **no ranking or winner column**.
5. **Write the pack** — plain-language comparison + the matrix + the flags + the transparent
   assumptions block + the explicit items requiring advisor adjudication. Do **not** conclude which
   proposal to use.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after. The
output check confirms: each proposal's total cost ties out to weighted-expense + advisory fee; every
flag has cited evidence; the assumptions block is present; `adjudication_required` is true; **no
proposal-selection field carries a value**; no decision / recommendation / advice / trade-execution /
filing language is present; and the standing disclaimer is present. **Fail closed** on any miss.

## Human approval
`required` (R3). A licensed human must adjudicate before the comparison is used as the basis for any
client-facing recommendation, any suitability/Reg BI determination, any trade, or any system-of-record
write. The comparator never performs those steps; it produces evidence and stops. No approval is
needed for the advisor's own read of the comparison.

## Failure handling
- **Only one proposal supplied** → stop; a comparison needs at least two. Do not invent a benchmark
  or a second proposal that was not provided.
- **Missing product attributes** (expense ratio, share class, liquidity, proprietary flag) → compute
  only the dimensions the data supports; label the rest **not-evaluable**; do not guess.
- **Weights that do not sum to ~1.0** → surface the data-quality warning; do not silently normalize
  in a way that hides concentration.
- **Ambiguous client/proposal identity** → stop and confirm; never compare the wrong client's
  proposals.
- **Stale/conflicting sources** (OMS vs product sheet) → cite both and flag; do not resolve silently.
- **Tool timeout** → return the proposals compared so far with a clear "incomplete" flag; never
  extrapolate the missing proposal.

## Output contract
1. **Summary** — client (masked), as-of, config version, proposals compared, count of flags,
   `adjudication_required: true`.
2. **Side-by-side matrix** — per dimension, per proposal; values only.
3. **Flags** — per flag: name, dimension, affected proposal, plain-language reason with the named
   threshold, and cited evidence rows.
4. **Assumptions** — the config thresholds and the explicit assumption notes (tax-drag basis, cost
   gross-of-waivers, risk = allocation not forecast, diversified look-through, even-handedness).
5. **Items for advisor adjudication** — the flags and material differences a licensed human must
   weigh; **no recommended proposal**.
6. **Not-evaluable** — dimensions the data did not support.
7. **Machine-readable** — proposals + matrix + flags + `comparison_id` for downstream skills.
8. **Standing disclaimer** — "Comparison and evidence only; not investment, tax, or suitability
   advice and not a recommendation to select any proposal. A licensed human must review before any
   client discussion or action; no trade has been placed and no system of record has been updated."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask client/account numbers to last 4. Minimize customer data in the output to what
evidences a difference or flag. Retain the comparison + citations + config version per records policy;
log the read and any human adjudication/delivery approval. Never exfiltrate customer or proposal data.

## Gotchas
- **A comparison is not a decision.** More flags on one proposal justify *adjudication*, never a
  conclusion that the other proposal is the right or suitable choice — that is the advisor's call.
- **Concentration look-through**: a 50% weight in one broad index fund is not single-issuer
  concentration. Diversified funds are excluded from single-issuer/single-sector limits; only
  single-name holdings and true sector bets count. Confirm the `diversified` flag from product data.
- **Cost is not just the expense ratio**: total cost adds the advisory fee, and revenue-sharing or a
  costlier share class is a **conflict** to disclose, not a number to net out.
- **Tax-drag is an estimate**, computed from approved assumptions — it is not personalized tax advice
  and it is not the client's actual tax outcome.
- **Even-handedness**: do not lead with the "cheaper" or "simpler" proposal. Present both symmetrically
  with their own flags; the reviewer weighs the trade-offs.
- **Thresholds are config, not judgment**: never tune a limit to make a proposal pass or fail; use the
  versioned config and record its version.
