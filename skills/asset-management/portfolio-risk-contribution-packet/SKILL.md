---
name: portfolio-risk-contribution-packet
description: >-
  Build a source-linked risk-contribution packet: from approved weights and an approved
  covariance matrix, compute ex-ante portfolio risk and its Euler decomposition into marginal
  (MCR), total (TRC), and percentage (PCR) risk contributions per position and group,
  reconcile the computed total to the approved risk engine's reported total, and explain
  material changes since the prior review — every figure tied out, every assumption sourced,
  and the methodology/version shown. Use when a portfolio-risk analyst asks to "compute
  marginal and total risk contributions", "show what is driving portfolio risk / risk
  concentration", "reconcile risk contributions to the risk engine", or "explain what changed
  in the risk decomposition since last review". This skill models and explains only; it NEVER
  sets or changes a risk limit, NEVER mandates or recommends a trade, rebalance, or hedge, and
  NEVER gives investment advice — limit-setting and portfolio actions are human /
  risk-committee decisions.
license: MIT
compatibility: Amazon Quick Desktop; requires PMS/OMS-holdings, approved-risk-model (covariance/methodology), approved-risk-engine (official totals), prior-packet-store, and versioned-riskcontrib-config MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Model & calculate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Portfolio-risk analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Portfolio Risk-Contribution Packet

## Purpose and outcome
Given a portfolio's **approved weights** and an **approved covariance matrix**, build a
**deterministic, source-linked risk-contribution packet**: compute ex-ante portfolio risk
and decompose it (Euler / marginal decomposition) into **marginal (MCR)**, **total (TRC)**,
and **percentage (PCR)** risk contributions per position and per group; **reconcile** the
computed total to the **approved risk engine's** reported total; and **explain material
changes** in the decomposition since the prior review — every figure tied out, every
assumption sourced, and the **methodology and version** shown. A successful output lets a
portfolio-risk analyst see *what is driving portfolio risk* and *what moved since last time*,
and hands a reproducible packet (`packet_id`) to review and downstream skills. **Risk-limit
decisions and any portfolio action remain with humans** (risk committee, mandate compliance,
portfolio manager).

## Use when
- "Compute the marginal and total risk contributions for this portfolio."
- "What is driving our ex-ante risk / where is risk concentrated by position or sector?"
- "Reconcile the risk contributions to the approved risk engine's total."
- "Explain what changed in the risk decomposition since the last review."
- A risk analyst needs a defensible, reproducible contribution packet to attach to a review.

## Do not use
- The user wants to **set, change, calibrate, or approve a risk limit**, or a risk-appetite
  threshold → **out of scope for every skill in this library**; route to the **risk committee
  / limits-governance owner** (a human). No skill here sets limits (see
  [references/handoffs.md](references/handoffs.md)).
- The user wants a **trade, rebalance, hedge, or de-risking action** recommended or executed
  → out of scope; route to the **portfolio manager** (human authorization required).
- The question is **is this a mandate/guideline breach** or a limit-utilization test of a
  proposed trade → `mandate-compliance-monitor` (and a human compliance officer).
- The question is **absolute exposures** (issuer/sector/country/currency/duration/liquidity,
  look-through), not *risk contributions* → `portfolio-exposure-analyzer` (the named adjacent
  skill — exposures vs risk contributions).
- Ongoing **limit / VaR / breach monitoring and escalation** → `market-risk-limit-monitor`.
- **Stress or scenario** loss attribution → `portfolio-stress-test-runner` (definitions from
  `stress-test-scenario-designer`); **liquidation-horizon / redemption** risk →
  `liquidity-stress-analyzer`; **return attribution** (allocation/selection/factor) →
  `performance-attribution-builder`.
- **Personalized investment advice** → licensed-human matter.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a risk-contribution
packet with a durable `packet_id`, `inputs_hash`, and `config_version`; downstream review,
memo, and monitoring skills consume it without recomputing it. It is **adjacent to**
`portfolio-exposure-analyzer` — that skill answers *how much am I exposed to X* (absolute
exposures); this skill answers *how much of my risk comes from X* (risk contributions). It
must not duplicate that exposure work, the mandate-compliance determination, or any
limit-setting or portfolio action.

## Inputs and prerequisites
- **Portfolio identifier** and an **`as_of` date** (anchors weights and the covariance).
- **Positions** — per position: `position_id`, `instrument_id`, grouping labels (`issuer`,
  `sector`, `asset_class`), and `weight` as `{value, provenance, citation}` (fraction of NAV;
  from PMS/OMS holdings).
- **Covariance** — an approved, square annualized covariance `matrix` with an `order` matching
  the positions, plus `provenance`/`citation` (from the approved risk model).
- **Methodology** — `{name, version, provenance, citation}` (the approved risk-model
  methodology and its version).
- **Approved-engine total** — `approved_engine.total_risk` `{value, provenance, citation}`:
  the risk engine's official ex-ante total to **reconcile** to.
- **Config** — `reconciliation.tolerance_rel`, `materiality` thresholds, `grouping_dimension`.
- **Prior review** (optional but expected) — prior `packet_id`, `as_of`, `total_risk`, and
  per-position `pcr`/`trc` for the **material-change** comparison.
- Schema: [scripts/validate_input.py](scripts/validate_input.py). Sources and least-privilege
  operations: [references/source-map.md](references/source-map.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **approved risk engine total**
is the reconciliation anchor; the **approved risk model** supplies the covariance and
versioned methodology; **PMS/OMS holdings** are the position of record for weights; the
**prior approved packet** is the baseline for change; **versioned config** supplies tolerance,
materiality, rounding, and grouping. **Cite every assumption with a date**; never override the
engine's total — reconcile to it, and surface any break for a human.

## Workflow
1. **Scope** — confirm portfolio, `as_of`, currency/units, risk measure, grouping dimension,
   and reconciliation tolerance; load weights, covariance, methodology, engine total, prior.
2. **Validate input** — run [scripts/validate_input.py](scripts/validate_input.py); resolve
   errors (missing/degenerate covariance, mismatched order, missing engine total/version),
   note warnings (missing provenance, weights ≠ 1, negative weights, no prior baseline).
3. **Compute (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): portfolio variance
   and risk, MCR/TRC/PCR per position, group aggregation, reconciliation to the engine total,
   and material changes vs the prior review — each with its tie-outs.
4. **Read the checks** — confirm the Euler identity (`sum(TRC) == total risk`), PCR sums to 1,
   group aggregations tie, the variance guard holds, and reconciliation is consistent; confirm
   every assumption carries provenance + citation and the methodology/version is present.
5. **Write the packet** — a plain-language explanation of the decomposition, the reconciliation
   result, and the material changes since prior review, with explicit assumptions and sources,
   the methodology/version, and the standing disclaimer. **No limit, no action, no advice.**

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check **independently re-derives** the decomposition from the pack's weights
and covariance (portfolio variance, MCR, TRC, PCR), re-checks the Euler identity, PCR sum, and
group aggregations, verifies the reconciliation flag against the recomputed relative
difference, requires methodology/version and provenance + citation on every assumption and
`packet_id` + `inputs_hash`, screens the narrative for **limit-setting / mandate / advice**
language, and requires the disclaimer. **Fail closed on any miss.**

## Human approval
`external-delivery`: human review and approval are required before the packet is delivered to
an investment/risk committee, a client, or a report, or written to any system of record. No
approval is needed for the analyst's own read. The skill takes **no action**, sets **no
limit**, and makes **no portfolio decision**.

## Failure handling
- **Missing/non-square covariance, or order ≠ positions** → `validate_input` errors; do not
  guess or pad the matrix.
- **Non-positive portfolio variance** (degenerate/inconsistent covariance) → the decomposition
  is undefined; the variance guard fails and the packet **fails closed**.
- **Unsourced assumption or missing methodology version** → warned on input, **rejected** on
  output; every number needs a source and the methodology needs a version.
- **Reconciliation break** (computed total not within tolerance of the engine total) → present
  it explicitly as an unreconciled result for a human; **never** silently overwrite either
  figure or claim a tie that does not hold.
- **No prior review** → produce the packet with a "no prior baseline" note; do not fabricate a
  prior decomposition.
- **Tool timeout** → return the contributions computed so far with an explicit "incomplete"
  flag; do not assume a retry.

## Output contract
1. **Summary** — portfolio (masked as needed), `as_of`, currency/units, risk measure,
   methodology + version, computed total risk, and the reconciliation result.
2. **Contributions** — per position: `weight`, `mcr`, `trc`, `pcr`, and group label; ranked so
   the largest risk contributors are visible.
3. **Group contributions** — TRC and PCR aggregated by the configured dimension (e.g. sector).
4. **Reconciliation** — approved-engine total, computed total, absolute/relative difference,
   tolerance, and the `reconciled` flag.
5. **Material changes** — vs the prior review: total-risk change and per-position PCR changes,
   each flagged against the documented materiality thresholds.
6. **Assumptions register** — every weight, the covariance, methodology, engine total, and
   prior-review reference with `provenance` + `citation`.
7. **Model checks** — the Euler identity, PCR sum, group ties, variance guard, reconciliation.
8. **Machine-readable** — the full packet JSON with `packet_id`, `inputs_hash`, and
   `config_version` for downstream skills.
9. **Standing disclaimer** — "Illustrative risk-contribution analysis for analytical purposes
   only; not a risk limit, not a mandate to trade, rebalance, or hedge, and not investment
   advice. Risk contributions are conditional on the stated methodology, weights, and
   covariance inputs, which a qualified human and the approved risk engine must review."
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
MNPI / client-confidential. Portfolio weights and the risk decomposition can reveal positioning
and strategy — treat the packet, its inputs, and its `packet_id` as need-to-know and respect
information barriers. Minimize holdings detail in output to what evidences a contribution.
Retain the packet, its assumptions register, and `config_version` per records policy; log the
read and any external-delivery approval. Never exfiltrate holdings or covariance.

## Gotchas
- **A risk contribution is not a limit and not an instruction.** TRC/PCR describe *where risk
  comes from* conditional on the inputs; setting a limit or deciding to trade, rebalance, or
  hedge belongs to the risk committee, mandate compliance, and the portfolio manager.
- **Contributions can be negative.** A hedge or diversifier can carry a negative TRC; the
  contributions still sum to the total. Do not treat a negative contribution as an error.
- **Reconcile, do not overwrite.** If the computed total disagrees with the engine, surface
  the break — never bend rounding, tolerance, or an input to force a tie.
- **Covariance drives the answer.** MCR uses `Sigma * w`; a stale or inconsistent covariance
  silently distorts every contribution. Cite the covariance source and `as_of`.
- **Exposure ≠ risk contribution.** A large *weight* is not the same as a large *risk*
  contribution; correlation and volatility reweight it. Route absolute-exposure questions to
  `portfolio-exposure-analyzer`.
- **Methodology is versioned.** Marginal-contribution results depend on the methodology
  version; always show it so a change in method is never mistaken for a change in the book.
