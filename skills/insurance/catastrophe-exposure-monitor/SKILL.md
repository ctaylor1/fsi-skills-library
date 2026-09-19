---
name: catastrophe-exposure-monitor
description: "Calculate read-only catastrophe exposure and event-scenario threshold alerts from supplied portfolio, footprint and model snapshots. Use to monitor accumulation, location limits, compatible named event scenarios and source freshness while preserving unknown prior alerts. Does not generate PML, sum marginal quantiles, run a catastrophe model, schedule itself or change underwriting/reinsurance decisions."
license: MIT
compatibility: Python 3.10+; offline structured inputs and supplied source evidence. Expected source systems are not bundled production connectors.
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "System-interaction or operational skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Monitor & alert"
  aws-fsi-agent-pattern: "Scheduled monitor + human queue"
  aws-fsi-delivery-wave: "Insurance Phase 1"
  aws-fsi-action-mode: "Scheduled read-only; alert only"
  aws-fsi-scheduled-agent: "read-only-monitoring"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "Reviewed target-specific jurisdiction/product profiles required; fixture coverage is not global applicability"
  aws-fsi-owner: "Insurance catastrophe exposure management"
  aws-fsi-primary-user: "Catastrophe risk / portfolio manager"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Catastrophe Exposure Monitor

## Purpose and outcome
Compute read-only exposure observations and threshold alerts from supplied event, portfolio and model snapshots. Report incomplete evidence explicitly and preserve prior alerts whose metrics cannot be reevaluated. The helper neither schedules itself nor runs a catastrophe model.

## Use when
Refresh zone/single-location exposure or supplied aligned event-scenario alerts; compare current and prior keys; flag stale, future, missing or incompatible data for a catastrophe-risk reviewer.

## Do not use
For underwriting decisions, route to `insurance-underwriting-risk-reviewer`; treaty implications to `reinsurance-contract-reviewer`; reserving to `pc-reserving-analysis-assistant`; incoming claim triage to `claims-triage-assistant`. Marginal PML/quantile aggregation and model generation are not implemented.

## Adjacent-skill handoffs
Read [references/handoffs.md](references/handoffs.md). A modeled loss is neither a booked reserve nor an authorized reinsurance transaction. Preserve model/context versions and unresolved issues in native receiver input.

## Inputs and prerequisites
Read [references/domain-rules.md](references/domain-rules.md) for explicit currency/financial/limit grain, coverage declarations, timezone-aware timestamps, allocated limit identities and event/footprint/exposure/model/scenario bindings. The three required source roles are policy_admin, event_feed and cat_model.

## Source hierarchy
Read [references/source-map.md](references/source-map.md). Supplied policy limits, TIV and model losses remain distinct. A model result cannot replace missing exposure evidence or an outdated footprint.

## Workflow
1. Run `scripts/validate_input.py`. Stop on malformed/nonfinite monetary input; preserve feed and coverage gaps as partial evidence.
2. Run `scripts/calculate_or_transform.py`. It validates input itself, checks freshness and bindings, and produces measured exposure metrics with source evidence.
3. Review new/ongoing breaches and retained unknown prior alerts. Clearing requires the same metric observed below threshold with complete current evidence.
4. Run `scripts/validate_output.py`. Callable `validate(output, input_doc)` also recomputes the expected snapshot when original input is supplied.

## Validation loop
`scripts/test_regressions.py` tests absent/stale/future feeds, false clears, mixed currency/grain, reused event models, mismatched scenario IDs and nonfinite values. Structural passing does not validate the underlying model's scientific quality.

## Human approval
The script returns an alert package locally. External distribution, queue writes and underwriting/reinsurance/reserving actions require their separately authorized workflow. No approval or execution claim is produced here.

## Failure handling
Retain unknown prior alerts on absent events, stale/missing feeds, incomplete exposure, unavailable model bindings or incompatible basis. Never clear because a row disappeared. Report exposed-location gaps; withhold full-event model totals unless every identified exposed location has compatible aligned scenarios. Do not sum marginal percentiles.

## Output contract
The package includes all evaluated metrics, cited alerts, new/ongoing/cleared/unknown counts, source freshness, financial/model bindings, gaps, current snapshot evidence state, overall completeness/evaluability and a content-bound artifact. Read [references/insurance-contract.md](references/insurance-contract.md). Missing exposure never produces a measured zero. Retained unknown prior alerts make the overall run partial even when another metric has complete evidence to clear; runs without observed breaches then report Unknown.

## Privacy and records
Carry authorized location/policy identifiers rather than unnecessary customer data. Retain snapshots, configuration and evidence references according to the deployment's records policy. The helper cannot authenticate external source assertions.

## Gotchas
Cleared means a measured threshold observation; it is not closure. Unique allocated limit IDs prevent repeated shared policy limits being added. Aligned low/mid/high scenario identifiers are not quantiles or return periods. Configured thresholds are illustrative until a risk owner supplies an appropriate versioned policy.
