# Changelog

## 0.2.0 — 2026-09-20

- Adopt Phase 1 ownership and canonical naming; preserve alias metadata.
- Require source-bound native validation and document bounded support.
 — fund-nav-control-reviewer

## 2026-09-20 — Phase 1 development corrections (unreleased)

- Repaired bounded native methods and disclosed their supported scope; see domain-rules and schema.
- Added detached original-input reconstruction, finite-JSON hashing and rejection of unvalidated output fields.
- Revised synthetic fixtures and independent operation regressions; no production, professional or institutional acceptance claimed.


## [0.1.0] — 2026-07-20
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** deterministic NAV-component tie-out — match the fund book of record to the
  independent custodian, administrator/transfer agent, and approved pricing source across
  positions, prices, accruals, income, expenses, shares, and cash; classify breaks, trace
  lineage, tie out, and draft PROPOSED-only resolutions. Draft-only; no NAV strike, no price
  selection, no posting, no adjudication, no forced tie.
- **Break taxonomy (deterministic):** `quantity_break`, `price_break`, `cash_break`,
  `accrual_break`, `income_break`, `expense_break`, `shares_break`, `missing_record`,
  `timing_difference` — each with a signed `impact`, materiality flag, and
  book/custodian/administrator/pricing lineage citations (see
  `scripts/calculate_or_transform.py`).
- **Tie-out invariants:** each `(component, currency)` control total ties
  (`difference == breaks_impact_sum`, recomputed from the break list); overall `residual == 0`;
  `out_of_tolerance_count == captured_break_count`. `position` and `price` are line-level;
  additive components are tied out per currency.
- **Controls:** R3; hard boundary against striking/finalizing/certifying NAV, choosing or
  overriding a price, and posting an accounting entry (resolutions are `status: "PROPOSED"`
  with `chooses_value`/`strikes_nav`/`posts_entry` all false); forcing a tie; adjudicating
  which source is correct; per-tie-out threshold tuning. Versioned-config
  tolerances/materiality/cutoff/component-source map; `required` human approval; segregation of
  duties between preparer and the NAV strike / poster.
- **Idempotency:** `tie_out_id` derived from `fund/share_class/as_of + input_fingerprint`
  (SHA-256 of normalized inputs) with no timestamp/random component; identical inputs reproduce
  identical output.
- **Scripts:** `validate_input` (job schema, matching-feasibility warnings), the tie-out
  engine, `validate_output` (tie-outs, break taxonomy, lineage, idempotency, proposed-only +
  no-strike/no-price/no-post language and forbidden-field screen, disclaimer). All stdlib-only
  with `--selftest`.
- **Evaluations:** trigger/routing, golden tie-out (nine break types, control-total tie-outs),
  clean-tie edge, deterministic script checks, fail-closed safety on a non-compliant fixture +
  injection, and R3 authorization.
- **Handoffs:** downstream to `fund-valuation-oversight-reviewer` (price breaks),
  `investment-book-reconciler`, `investment-data-quality-reviewer`,
  `investment-data-quality-reviewer`, `trade-break-resolver`; upstream
  `investment-record-normalizer` and `month-end-close-orchestrator`. NAV strike, price
  selection, and posting are human/authorized-system actions.

### Pending before release
- Domain SME (fund controllership / valuation) + control-owner blind review; SoD confirmation
  for preparer vs NAV strike / poster.
- Confirm the versioned tolerance/materiality/cutoff/component-source config source and its owner.
- Wire read-only MCP integrations (ABOR, custodian, administrator/TA, approved pricing) at
  deployment.

## 2026-09-20 — Forward precision repair (unreleased)

- Independent fresh inputs exposed silent default-Decimal rounding beyond 28 significant digits. Added private 256-digit arithmetic contexts, bounded 38-digit inputs/exponents and 100,000-record limits, with explicit rejection instead of silent precision loss.
- Added 30-digit reconciliation/NAV, long FX-product, unsupported-bound and process-context isolation regressions. Original failures and repaired replay are recorded in the Phase 1 forward review.
