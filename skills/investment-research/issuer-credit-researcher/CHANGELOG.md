# Changelog

## 0.2.1 — 2026-10-20

Treat omitted and explicitly null financial amounts consistently as unknown while
preserving their exact original representation. Add field-specific missingness
issues and retain independently supported metrics. Missing cash-flow evidence or
an unavailable positive FFO/debt denominator now produces a partial result.
Omitted or null debt reconciliation and instrument inclusion evidence also yield
partial results without calculation errors. Excluded structural instruments may
retain unknown principal without affecting an explicitly reconciled debt scope.
Add omission/null, real-zero, supported-value and original-bound public-command
regressions. Earlier phase and repair checkpoint evidence is unchanged.

## 0.2.0 — 2026-10-20

Require source-bound issuer, economic event and additive-component evidence before
adjusted EBITDA. Repeated event totals under different row IDs, aliases across
documents, incompatible contexts, conflicting versions and total/component overlap
withhold adjusted metrics. Reconcile a cited supplied debt inventory, explicit
inclusions/exclusions and principal-to-carrying-value bridge to reported gross
debt using exact decimal-value rational arithmetic. Missing or contradictory debt
evidence withholds leverage and FFO/debt while retaining independently supported
EBITDA, interest coverage and free cash flow. Retain the reconciliations, reasons,
citations and calculation lineage in the original-bound output. Earlier phase and
control-repair evidence is unchanged.

## 0.1.1 — 2026-10-20

Reject future reported financial periods at the as-of and knowledge-cutoff
boundaries. Reject duplicate EBITDA adjustment IDs before summation, including
conflicting amounts or citations. Add adverse CLI fixtures and arithmetic
regressions; retain source-eligibility withholding and the original Phase 2
valid fixture.

## 0.1.0 — 2026-10-20

Phase 2 bounded supplied-evidence analytical method; institution acceptance remains unestablished.
