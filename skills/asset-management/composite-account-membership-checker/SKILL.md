---
name: composite-account-membership-checker
description: >-
  Apply the firm's approved, versioned composite-inclusion rules (GIPS composite construction:
  strategy, discretion, minimum asset, inclusion/exclusion timing, significant cash flow, and
  completeness) to portfolio/account data, identify membership exceptions, and produce a
  review-ready evidence queue that cites the rule id and version behind each finding. Use when a
  performance analyst asks "which accounts belong in this composite", "flag composite membership
  exceptions", "check GIPS composite inclusion", or needs an adjudication queue of misclassified
  portfolios. HARD BOUNDARY: this skill evidences and routes only — it NEVER changes a composite,
  its membership, the methodology, or reported performance, never closes/files/writes a system of
  record, and every exception is staged for mandatory human adjudication. Route return or
  attribution recalculation to performance-attribution-builder.
license: MIT
compatibility: Amazon Quick Desktop; requires composite-policy/GIPS-rule-library, composite-register, portfolio/PMS book-of-record, cash-flow, and entity-resolution MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Performance analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Composite Account Membership Checker

## Purpose and outcome
Given a portfolio/account universe, the composite definitions, and the firm's approved,
**versioned** composite-inclusion ruleset, deterministically compute each portfolio's
**rule-derived expected membership**, compare it to the **asserted membership** on the composite
register, and emit an **exception evidence queue** — each item citing the rule id/version and the
data rows behind it, ranked by a documented queue priority. A successful output lets a performance
analyst adjudicate exactly which accounts look misclassified and why. The adjudication, and any
composite/performance change, remains human.

## Use when
- "Which accounts belong in the Global Equity composite? Flag anything that doesn't fit."
- "Run the composite inclusion rules over this book and give me an exception queue with citations."
- "Check GIPS composite membership for misclassified, missing, or stale portfolios."
- A performance analyst needs a consistent, cited membership write-up to adjudicate before a
  composite is reported or a GIPS report is produced.

## Do not use
- The user wants to **apply a change** — add/remove/reassign a portfolio, edit a composite
  definition, or restate/recalculate performance → out of scope (the HARD BOUNDARY). Produce the
  cited exception and route to the human analyst and the authorized system.
- **Return or performance attribution** (re)building → `performance-attribution-builder`.
- The underlying **account data is wrong at the source** (bad strategy/discretion flags, dates) →
  `investment-data-quality-exception-detector`.
- **Mandate/guideline compliance** monitoring or discretion determination → `mandate-compliance-monitor`.
- GIPS **disclosure/report** authoring after adjudication → `fund-fact-sheet-builder` or
  `fund-commentary-drafter`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits an exception queue with a
durable `review_id` and per-exception `case_ref`; downstream adjudication, correction, and
reporting consume those ids. It must not duplicate their change or recalculation steps.

## Inputs and prerequisites
- **Composite definitions**: `composite_id`, strategy, `min_asset_value`, `inclusion_lag_months`,
  `requires_discretionary`, optional `significant_cash_flow_pct`, and `rule_id` + `rule_version` +
  `effective_date`.
- **Portfolio rows**: `portfolio_id`, strategy, `discretionary`, `fee_paying`, `under_mgmt_date`,
  `termination_date` (nullable), `market_value`, `assigned_composite_ids[]`,
  `significant_cash_flow_pct`, `source_ref`.
- **Run context**: `firm_id`, `as_of`, `ruleset_version`, `ruleset_effective_date`.
- Read access to the composite policy library, composite register, and PMS book of record.
  Schema and validation: [scripts/validate_input.py](scripts/validate_input.py).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **composite policy** governs the
rule; the **composite register** and **book of record** govern the data. When rule and data
disagree, that disagreement *is* the exception — cite both, resolve neither. Every exception
carries a data citation (`pms:...@as_of`) and a rule citation (`rule_id @ rule_version`).

## Workflow
1. **Scope & validate** — confirm the firm, `as_of`, and `ruleset_version`; load composites and
   portfolios; run `validate_input`. Fail closed on structural problems; note evaluability warnings.
2. **Derive expected membership (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to apply, per composite,
   the strategy / discretion / minimum-asset / inclusion-lag / exclusion-timing / SCF / completeness
   rules and build each portfolio's expected membership set for the rule version in effect.
3. **Diff against asserted membership** — classify every difference into the exception taxonomy
   (`improper_inclusion`, `stale_inclusion`, `missing_inclusion`, `early_inclusion`,
   `unassigned_discretionary`, `significant_cash_flow_review`) with evidence and rule citations;
   record `compliant` / `pending_inclusion` states as informational, not exceptions.
4. **Rank the queue** — map the fired exception set to a queue priority (Elevated / Review / None)
   per the documented, deterministic mapping. This is triage order for a human, not an adjudication.
5. **Write the pack** — a plain-language summary + the per-exception evidence + priority + the
   standing disclaimer, each exception `status: for_review` for the analyst to adjudicate.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output screen confirms: every exception has cited evidence **and** a `rule_id`/`rule_version`;
`queue_priority` equals the deterministic mapping; **no** membership/methodology/performance change
or closure/filing language is present; every `status == for_review` with
`human_adjudication_required == true`; and the standing disclaimer is present. Fail closed on any
miss (a non-compliant pack exits non-zero).

## Human approval
`required`: mandatory human adjudication. The skill never changes composite membership, methodology,
or reported performance, never closes/files an exception, and never writes a system of record. The
performance analyst adjudicates; the composite management committee / performance operations (a
human/authorized system) applies any change under its own controls.

## Failure handling
- **Missing rule version / effective date** → stop; do not evaluate against an unknown or newer
  rule. Surface the gap.
- **Missing strategy / discretion / dates** on a portfolio → mark the affected rule
  "not evaluable" for that portfolio; do not guess membership.
- **Portfolio assigned to an undefined composite** → flag as `improper_inclusion` citing the
  completeness rule; never silently drop the assignment.
- **Rule vs. data conflict** → cite both sides as the exception; never overwrite either source.
- **Tool timeout / large universe** → return the exceptions computed so far with an explicit
  "incomplete" flag and the paged range covered.

## Output contract
1. **Summary** — firm, `as_of`, `ruleset_version`, portfolios evaluated, exception count, queue
   priority, `review_id`.
2. **Exceptions** — per item: `case_ref`, portfolio, composite, `exception_type`, severity, the
   plain-language reason, expected vs. asserted membership, `status: for_review`, the rule citation
   (`rule_id` + `rule_version` + `effective_date`), and cited evidence rows.
3. **Informational** — `compliant` and `pending_inclusion` portfolios (not exceptions).
4. **Machine-readable** — the queue JSON (`review_id`, `exceptions[]`, `queue_priority`) for
   downstream adjudication/reporting.
5. **Standing disclaimer** — "Composite-membership exceptions are evidence for analyst adjudication
   only; this skill does not modify composites, methodology, or reported performance."
See [references/controls.md](references/controls.md).

## Privacy and records
MNPI / client-confidential. Reference portfolios by identifier, not client name; minimize account
data to what evidences an exception. Retain the queue + citations + `ruleset_version` per records
policy; log the read and the adjudication hand-off. Never exfiltrate holdings or client data.

## Gotchas
- **A membership exception is not a correction.** Even an obvious below-minimum inclusion is
  flagged for adjudication — the skill never moves the portfolio or restates the composite.
- **Rule version follows the period.** Evaluate against the `rule_version` in effect for `as_of`;
  applying a newer rule retroactively is a methodology change and is prohibited.
- **Exclusion timing is "last full period", not the termination date.** A portfolio stays a member
  through its last full measurement period, then is expected out — off-by-one here creates false
  `stale_inclusion` or misses real ones.
- **Discretion is an input, not a determination.** Consume the discretion flag; do not decide
  whether an account is discretionary — that is `mandate-compliance-monitor` / a human.
- **Completeness gaps point at missing composites.** An `unassigned_discretionary` finding often
  means a composite definition is missing, not that a portfolio is wrong — say so for the analyst.
- **Don't recompute returns.** SCF and timing findings never imply a performance number here;
  recalculation routes to `performance-attribution-builder`.
