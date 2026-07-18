# Changelog — premium-quote-comparator

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `existing-updated` relative to
the AWS baseline — stronger evidence, comparability-flag, and no-advice/no-determination
guardrails).

- **Scope:** normalize ≥2 quotes to a 12-month annualized basis, build a coverage/limit/
  deductible grid, enumerate material differences, and surface comparability flags. Read-only;
  no recommendation, no advice, no coverage/eligibility determination.
- **Normalization (deterministic):** premium annualized by payments-per-year; fees by
  12/term_months; `annualized_total_cost` and `cost_spread`; factual lowest-cost argmin (see
  `scripts/calculate_or_transform.py`).
- **Differences & flags:** coverage / deductible / limit / exclusion / endorsement / term
  differences, each cited; `coverage_/deductible_/limit_/exclusion_/endorsement_/term_/
  currency_mismatch` flags so cost is never read in isolation.
- **Controls:** R2; hard boundary against recommending/selecting a policy, insurance/
  suitability advice, and coverage/eligibility determination; versioned-config normalization
  only; `external-delivery` approval.
- **Scripts:** `validate_input` (quote schema, comparability warnings), normalization/
  comparison engine, `validate_output` (citation completeness, deterministic lowest-cost
  tie-out, no-advice + no-determination screen, disclaimer, flags-present-when-differences).
- **Evaluations:** trigger/routing, golden normalized comparison, single-quote and
  mixed-currency edges, deterministic script checks, no-advice safety + injection,
  external-delivery authorization.
- **Handoffs:** downstream to `coverage-gap-analyzer`, `policy-wording-comparator`,
  `policy-document-explainer`, `policy-renewal-reviewer`, `submission-intake-triager`.

### Pending before release
- Domain SME (product/pricing) + control-owner blind review; conduct review of neutral,
  non-advisory framing.
- Confirm the versioned normalization/crosswalk config source and its owner.
- Wire read-only MCP integrations (producer/rating, document intelligence, reference data,
  config) at deployment.
