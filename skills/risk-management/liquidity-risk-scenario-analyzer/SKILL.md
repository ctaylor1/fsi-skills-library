---
name: liquidity-risk-scenario-analyzer
description: >-
  Model institution-specific liquidity stress: project stressed cash inflows/outflows by time
  bucket, apply funding runoff and collateral haircuts, and compute the counterbalancing
  capacity, cumulative funding gap, survival horizon, and coverage ratio, then raise
  source-linked findings against liquidity limits and propose Contingency Funding Plan options.
  Use when a treasury-risk or ALM analyst asks "run our liquidity stress scenarios", "what is our
  survival horizon under an idiosyncratic/market-wide/combined stress", "where does the cumulative
  gap breach the limit", or needs review-ready liquidity evidence for ALCO. This skill produces
  findings, cited evidence, and adjudication-ready contingency proposals ONLY; it NEVER makes a
  regulated liquidity determination, approves or executes a funding/collateral action, clears or
  waives a limit breach, files a regulatory return (e.g. LCR/NSFR/2052a), or writes a system of
  record — those are human (Treasury/ALCO) and authorized-system actions.
license: MIT
compatibility: Amazon Quick Desktop; requires treasury/ALM, core-banking deposit & funding, collateral/HQLA inventory, market-data, and approved-calculation MCP integrations (all read-only), plus a versioned scenario/limit config source.
metadata:
  aws-fsi-category: "Risk Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Enterprise Risk Management"
  aws-fsi-primary-user: "Treasury risk / asset-liability management"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Liquidity Risk Scenario Analyzer

## Purpose and outcome
Given an institution's liquidity position (contractual and behavioral cash flows by time bucket,
funding sources, and counterbalancing assets) and a set of approved stress scenarios, compute a
set of **explainable liquidity metrics** — stressed net cash-flow gap per bucket, counterbalancing
capacity (CBC) after stressed haircuts, **survival horizon**, and a **coverage ratio** — raise
source-linked **findings** against the configured limits, and assemble a review-ready pack with a
deterministic **overall assessment band** plus **proposed Contingency Funding Plan (CFP) options**.
A successful output lets a treasury-risk analyst, and then ALCO, see exactly where liquidity is
constrained and under which scenario — the determination, any funding/collateral action, and any
regulatory filing remain human.

## Use when
- "Run our liquidity stress scenarios and show the survival horizon."
- "Under a combined idiosyncratic + market stress, where does the cumulative gap breach the limit?"
- "What is our stressed coverage ratio and counterbalancing capacity by scenario?"
- An analyst needs consistent, cited liquidity evidence to take to ALCO or the CFP owner.

## Do not use
- The user wants a **regulated liquidity determination**, an **LCR/NSFR/2052a filing**, a **limit
  breach cleared/waived**, or a **funding/collateral trade executed** → out of scope. Provide
  evidence and route to the human (Treasury/ALCO) and authorized systems.
- **Fund / portfolio** redemption-and-asset liquidity (buy-side, redemption gates, swing pricing)
  → `liquidity-stress-analyzer` (asset management). This skill is institution/balance-sheet ALM.
- **Designing** the stress scenarios themselves (narratives, shock calibration, governance) →
  `stress-test-scenario-designer`; this skill consumes the designed scenarios and runs them.
- **Market-risk** or **concentration** limit surveillance → `market-risk-limit-monitor` /
  `concentration-risk-monitor`. Baseline cash-flow projection → `cashflow-forecaster`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a liquidity assessment pack
with a durable `analysis_id`; downstream reporting, enterprise-risk, KRI, exam-response, and
model-validation skills consume it. It must not duplicate their determination, packaging, or
filing steps.

## Inputs and prerequisites
- **Entity / legal entity** and **as-of date**; reporting horizon (default 30 days).
- **Positions**: cash-flow items with `direction` (inflow/outflow), `category` (deposit/funding
  type or inflow type), time `bucket`, `amount` (notional/expected), and a `source_ref`.
- **Counterbalancing assets**: `asset_class` (e.g. `level1_hqla`, `level2a_hqla`), `market_value`,
  `base_haircut`, and a `source_ref`.
- **Scenarios**: per-category outflow/inflow stress rates and per-class CBC haircut add-ons, from
  the **versioned scenario/limit config** (owner: ALM/ERM), plus `limits` (min survival days, min
  coverage ratio, concentration limit). Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to treasury/ALM, deposits & funding, and the collateral/HQLA inventory (see
  [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The treasury/ALM position of record and
collateral inventory are authoritative; behavioral assumptions (runoff/rollover), stress rates,
and limits come from the **versioned config**, never from ad-hoc tuning. Cite every finding's
evidence to a source row and record the config version.

## Workflow
1. **Scope & validate** — confirm entity, as-of, currency, horizon, and the scenario set; run
   [scripts/validate_input.py](scripts/validate_input.py). Fail closed on structural errors; note
   data-quality warnings that limit reliability.
2. **Compute (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py). For each scenario it
   projects stressed inflows/outflows per bucket, running cumulative gap, CBC after stressed
   haircuts, survival horizon, and coverage ratio. Metrics are **explainable**, not a black-box
   score.
3. **Raise findings** — compare metrics to limits: `survival_horizon_breach` (CRITICAL),
   `coverage_ratio_breach` (HIGH), and structural `funding_concentration` (MEDIUM). Each finding
   carries its own evidence rows and citations.
4. **Assess (deterministic band)** — map the finding severities to an overall band
   (Within appetite / Watch / Elevated / Breach) per the documented mapping. This is a triage
   read for a human, explicitly **not** a regulated determination.
5. **Propose, do not act** — list CFP options (monetize HQLA, pre-position collateral, term out
   funding, slow asset growth), each **labeled a proposal requiring Treasury/ALCO adjudication**.
6. **Write the pack** — plain-language explanation per scenario + findings + evidence + the
   assessment band + proposed options + explicit uncertainties and assumptions.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check confirms: every finding has cited evidence; the band equals the deterministic
mapping; findings tie out to the numbers (survival/coverage breaches match the limits); no
regulated-decision / closure / filing / commitment language is present; the standing disclaimer is
included; and proposed options are supplied whenever the band is not "Within appetite". Fail closed
on any miss.

## Human approval
`required` (R3). Human review and adjudication are required before any regulated liquidity
decision, limit-breach disposition, funding/collateral action, or regulatory filing, and before the
pack is written to a case/system of record or delivered externally. No approval is needed for the
analyst's own read. The skill never takes a funding, collateral, limit, or filing action.

## Failure handling
- **Insufficient/thin data** (few positions, missing categories) → state metrics are
  low-confidence; do not overstate the assessment; list what is missing.
- **Ambiguous entity / as-of** → stop and confirm; never analyze the wrong entity or period.
- **Missing scenario rates** → categories fall back to documented defaults; surface which ones did.
- **Stale/conflicting sources** → cite both the position of record and the conflicting value; do
  not resolve silently.
- **Tool timeout / large book** → page the position by portfolio/desk into resumable stages; return
  the scenarios computed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — entity, as-of, currency, horizon, scenario set, worst scenario, overall band.
2. **Per scenario** — CBC (with per-asset haircut detail), bucketed stressed flows and cumulative
   gap, survival horizon, coverage ratio, and fired findings with cited evidence.
3. **Structural findings** — e.g. funding concentration, with evidence.
4. **Proposed contingency options** — CFP measures, each labeled adjudication-required.
5. **Assumptions / data gaps** — behavioral assumptions used, config version, and not-evaluable items.
6. **Machine-readable** — the analysis core + `analysis_id` for downstream skills.
7. **Standing disclaimer** — "Liquidity stress analysis and evidence only; not a regulatory
   determination, funding decision, or limit action. All contingency measures are proposals
   requiring Treasury/ALCO adjudication. No funding action has been taken and no system of record
   has been updated."
See [references/controls.md](references/controls.md).

## Privacy and records
**Confidential** treasury/risk data (no customer NPI required; keep it out of the analysis). Mask
any counterparty identifiers not needed for a finding. Retain the analysis + citations + config
version per records policy so a run is reproducible; log the read and any adjudication/delivery
approval. Never exfiltrate position or collateral data.

## Gotchas
- **A finding is not a decision.** Breaches justify *escalation and adjudication*, never an
  autonomous determination, a cleared breach, or a funding/collateral action.
- **Survival horizon vs. coverage horizon differ.** The survival minimum can be shorter than the
  coverage (LCR-style) horizon; a scenario can pass survival yet breach coverage — report both.
- **Baseline vs. stressed inflows.** Contractual inflows are haircut under stress (and inflow caps
  may apply); never assume 100% inflow realization in an idiosyncratic scenario.
- **Secured funding still rolls off.** Model repo/secured rollover explicitly; widening haircuts
  reduce both inflows and CBC at the same time (double hit) — the config captures this.
- **Do not tune assumptions to pass.** Runoff/rollover rates, haircuts, and limits come from the
  versioned config, not from guessing what "should" clear the limit.
- **Concentration is factual.** Report a funding concentration as a share with evidence; it is a
  structural observation, not a judgment about the counterparty.
