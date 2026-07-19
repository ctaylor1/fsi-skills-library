---
name: investment-policy-statement-builder
description: >-
  Draft or refresh an Investment Policy Statement (IPS) by assembling documented investment
  objectives, risk tolerance, time horizon, liquidity needs, tax considerations, constraints
  and restrictions, strategic asset-allocation ranges, rebalancing policy, benchmarks, and
  governance into an approved firm template with every material figure mapped to a source.
  Use when an advisor, investment counselor, or compliance reviewer needs to build a new IPS,
  refresh an existing one after a profile or allocation change, or package IPS evidence for
  supervisory review. HARD BOUNDARY: draft-only. This skill NEVER approves an allocation as
  suitable, makes a suitability/Reg BI determination, executes or stages trades, guarantees
  returns, files or submits, delivers to the client or custodian, or writes any system of
  record. Every recommendation and approval is left for a licensed human to adjudicate.
license: MIT
compatibility: Amazon Quick Desktop; requires CRM, portfolio-accounting/OMS, planning-engine, product-data, disclosures/restrictions, and approved-tax-assumptions MCP integrations (all read-only) plus the controlled IPS template library.
metadata:
  aws-fsi-category: "Wealth Management"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Wealth Management advisory & compliance"
  aws-fsi-primary-user: "Advisor / investment counselor / compliance reviewer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Investment Policy Statement Builder

## Purpose and outcome
Assemble a complete, source-mapped **draft Investment Policy Statement** from documented
inputs — objectives, risk tolerance, time horizon, liquidity, tax, constraints/restrictions,
strategic asset allocation, rebalancing policy, benchmarks, and governance — laid into the
firm's approved IPS template. The outcome is a review-ready draft in which every required
section is present, every material figure carries a citation, allocation ranges are internally
consistent, and the advisor/compliance/client approval block is recorded as **pending**. The
substantive recommendation, the suitability determination, any trading, and delivery all stay
with licensed humans and downstream skills.

## Use when
- "Draft an Investment Policy Statement for this client from their documented profile."
- "Refresh the IPS — the risk tolerance moved to moderate and the equity band changed."
- "Build the IPS package with the strategic allocation and rebalancing policy for review."
- "Map each IPS assertion to its source and flag anything unsupported before the review meeting."

## Do not use
- **Suitability / Reg BI review** of the resulting recommendation → `suitability-reg-bi-reviewer`
  (this skill drafts; it does not approve suitability).
- **Comparing** competing allocation proposals → `portfolio-proposal-comparator`.
- **Preparing trades** to align a portfolio to IPS targets → `portfolio-rebalancing-assistant`
  (R4, approval-gated).
- **Modeling** retirement income / withdrawal scenarios → `retirement-income-scenario-modeler`.
- **Goal-progress** measurement → `financial-goal-progress-analyzer`.
- Any request to **approve, sign, finalize, file, deliver, or trade** → refuse; keep it a draft
  and route to the human approver.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This is the **drafting** step in a chain of
distinct control activities; it never performs the suitability review or the trading. It emits a
durable `ips_id` + draft package for the advisor, compliance reviewer, and client to adjudicate.

## Inputs and prerequisites
- A documented client profile and approved inputs: governance/parties, objectives, risk tolerance
  (ability, willingness, capacity), time horizon, liquidity needs, **approved** tax assumptions,
  legal/regulatory constraints, client restrictions, the strategic allocation table (per-class
  target/min/max/benchmark), rebalancing method/threshold, and a citation for each. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to CRM, portfolio-accounting/OMS, planning engine, product data, the
  disclosures/restrictions register, and the approved tax-assumptions set.
- The **versioned** approved IPS template and required-section list (a versioned contract).

## Source hierarchy
See [references/source-map.md](references/source-map.md). CRM/planning engine is the system of
record for the client profile and objectives; portfolio-accounting/OMS for holdings and account
structure; product data for permitted instruments; the disclosures/restrictions register for
constraints; the approved tax-assumptions set for tax figures. Cite every material assertion.
Template and tax assumptions are **versioned contracts** recorded on the draft.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm required inputs, per-class allocation
   bands, and that each material field carries a source. Flag anything missing as `needs-data`.
2. **Reconcile risk tolerance** — record ability, willingness, and capacity; the governing
   **overall** tolerance is the most conservative of the three (never override upward silently).
3. **Assemble the draft (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): lay inputs into the
   required template sections, validate allocation consistency (targets sum to 100%; each target
   within its min/max band), build the section→citation source map, and compute a completeness
   score. Anything unsupported or out-of-band is surfaced, not smoothed over.
4. **Record approvals as pending** — write the advisor, compliance, and client approval block with
   status `pending`; the draft is never self-approved.
5. **Validate the draft** — run [scripts/validate_output.py](scripts/validate_output.py); fix
   every finding or fail closed.
6. **Package, do not deliver** — emit the draft IPS keyed to
   [assets/output-template.md](assets/output-template.md) with the `ips_id`, source map, gaps
   list, and standing note. Delivery, signature, and any trade stay with humans.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check enforces: all required template sections present; every allocation line and
material figure cited (no unsupported assertions); allocation targets sum to 100% and sit within
their bands; approvals recorded and still `pending`; `draft_status` = `draft` and never delivered;
no suitability-approval / trade-execution / filing / delivery / guaranteed-return language; and the
standing note present. Fail closed on any miss.

## Human approval
`required`. This skill produces a **draft only**. The advisor owns the recommendation, a supervisor
/ compliance reviewer owns the suitability and supervision sign-off, and the client owns acceptance
by signature. No allocation is "approved as suitable," nothing is finalized, filed, delivered, or
traded by this skill. Approvals are captured as a pending block for humans to complete out-of-band.

## Failure handling
- **Missing / uncited input** → set `needs-data`, list exactly what is missing; never invent a
  figure, allocation, or citation to complete a section.
- **Allocation out of band / targets ≠ 100%** → surface the inconsistency as an error; do not
  silently re-weight.
- **Risk-tolerance conflict** (willingness ≠ ability) → record both and govern to the most
  conservative; flag for advisor discussion.
- **Stale template / tax-assumption version** → stop and flag; the template and tax set are
  versioned contracts.
- **Stale / conflicting sources** → cite both and flag; do not pick a winner.
- **Tool timeout** → return the partial draft with an explicit incomplete flag; assume no retry.

## Output contract
1. **Draft IPS** — the required sections (see [references/domain-rules.md](references/domain-rules.md))
   laid into the approved template, each with its citations.
2. **Strategic allocation table** — per class: target/min/max/benchmark + citation, with the
   consistency check (sum, within-band) shown.
3. **Source map** — section → citations; **gaps list** — any `needs-data` items.
4. **Approval block** — advisor / compliance / client, each `pending`.
5. **Machine-readable** — the draft object keyed by `ips_id`, with `draft_status: draft` and
   `delivery_status: not-delivered`.
6. **Standing note** — "Draft IPS for human review only; no allocation approved as suitable, no
   suitability determination made, and nothing finalized, filed, delivered, or traded."
See [references/controls.md](references/controls.md).

## Privacy and records
**Highly Confidential — customer NPI/PII.** Mask client and account identifiers in output to what
the draft requires. Retain the draft, its source map, gaps, and the template/tax-assumption
versions per firm books-and-records (SEC/FINRA recordkeeping) requirements. Log every read and each
draft generation with the author identity. Do not place NPI in identifiers or logs.

## Gotchas
- **Draft ≠ recommendation approved.** Laying an allocation into the IPS is not a suitability
  determination; that is the reviewer's job downstream.
- **Every figure needs a source.** An allocation band or tax rate with no citation is an
  unsupported assertion and fails the output screen — inputs must be documented, not inferred.
- **Governing risk tolerance is the floor.** Overall tolerance is the most conservative of ability,
  willingness, and capacity; never round it up to fit a target allocation.
- **Bands must be internally consistent.** Targets sum to 100% and each sits within its min/max, or
  the draft fails closed — the builder does not re-weight to "make it work."
- **Versioned template & tax set.** Record the template and tax-assumption versions on every draft
  so the artifact is reproducible and reviewable.
- **No delivery from here.** Signature, custodian delivery, and trading are separate, human- and
  approval-gated steps — this skill stops at a reviewed-ready draft.
