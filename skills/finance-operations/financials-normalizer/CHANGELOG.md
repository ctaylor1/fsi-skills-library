# Changelog — financials-normalizer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** a multi-step normalization procedure — map source financial-statement line items
  to a standard chart-of-accounts taxonomy, roll them up per account and period, apply
  documented normalization adjustments with provenance, and tie the result out against source
  subtotals and the balance-sheet identity. Read-only; no judgment, no posting.
- **Checks (deterministic):** `missing_provenance`, `unmapped_line_item`,
  `unexplained_adjustment`, `subtotal_tie_out_break` (high), `balance_sheet_identity_break`
  (high) — each explainable and evidenced (see `scripts/calculate_or_transform.py`).
- **Controls:** R2; hard boundary against accounting/audit/investment judgment or
  recommendation, restatement/posting to any system of record, and borrower credit spreading;
  versioned-config tolerances only; source figure never overridden; `external-delivery`
  approval.
- **Scripts:** `validate_input` (schema, mapping/provenance/identity-anchor warnings),
  normalization + tie-out engine, `validate_output` (evidence/citation completeness,
  deterministic readiness tie-out, prohibited decision/advice/posting screen, disclaimer,
  review considerations).
- **Evaluations:** trigger/routing, golden Hold case (two tie-out breaks + provenance/mapping
  findings), income-statement-only edge (identity not evaluable), deterministic script checks,
  prohibited-decision/advice safety fixture that fails closed, and external-delivery
  authorization.
- **Handoffs:** downstream to `three-statement-model-builder`, `dcf-modeler`,
  `lbo-model-builder`, `merger-model-builder`, `comps-analysis-builder`, `valuation-reviewer`,
  `management-reporting-packager`, `audit-evidence-packager`; sideways to
  `financial-spreading-assistant`, `gl-reconciler`, `earnings-results-analyzer`,
  `regulatory-reporting-data-validator`, `financial-statement-audit-assistant`,
  `company-profile-builder`.

### Pending before release
- Domain SME (controllership / model-data governance) + control-owner blind review.
- Confirm the versioned chart-of-accounts mapping pack, normalization-policy library, and
  threshold config source and their owners.
- Wire read-only MCP integrations (document intelligence, entity resolution, mapping/policy
  libraries, config) at deployment.
