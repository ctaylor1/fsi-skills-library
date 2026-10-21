# Independent operations forward review

2026-09-20T23:14:04.432255+00:00

Fresh synthetic requests from SKILL/native schema/source map; no fixtures or expected outputs reused. Native source read for API shape. Independent arithmetic uses precision100. Real CLIs use stdin and detached OS pipes; no scratch files.

Professional and deployment acceptance are not established.

## Original findings

- OPS-FWD-F01 (high): Default Decimal precision silently drops a nonzero long-decimal quantity break. Expected 0.00000000000000001; observed 0.000000000000000. Detached validation accepted. Location: skills/asset-management/investment-book-reconciler/scripts/calculate_or_transform.py:70.
- OPS-FWD-F02 (high): Default Decimal subtraction loses an accepted quantity digit while claiming zero residual. Expected 1000000000000.00000000000000001; observed 1000000000000.000000000000000. Detached validation accepted. Location: skills/asset-management/fund-nav-control-reviewer/scripts/calculate_or_transform.py:58.

## Scenario checks

| Case | Results |
| --- | --- |
| OPS-FWD-01 — investment-book-reconciler | fractional_exact: pass, wide_exact: FAIL, two_breaks: FAIL, no_selected_correction: pass |
| OPS-FWD-02 — investment-book-reconciler | basis_withheld: pass, cash_exact: pass, fx_unknown: pass, needs_data: pass |
| OPS-FWD-03 — fund-nav-control-reviewer | stale_rows_excluded: pass, no_stale_control: pass, needs_data: pass, missing_price_routed: pass, no_price_selected: pass, null_not_filled: pass |
| OPS-FWD-04 — fund-nav-control-reviewer | position_exact: FAIL, cash_tolerance_exact: pass, cash_no_break: pass, residuals_zero: pass |
| OPS-FWD-05 — proxy-voting-reviewer | mandate_policy: pass, deviation: pass, precedent_scope: pass, no_action: pass, wrong_mode_rejected: pass |

All five original validators passed; all five added-field tampering attempts were rejected. [Exact inputs, outputs and CLI results](operations-forward-review.json).

## Limits

Book-only price has verifier_total=0 and impact=7.250000 for missing-record bookkeeping. This is not an observed zero verifier price or established NAV impact; retain missing_record classification.

- Five synthetic groups only; no production connectors, authenticated sources or professional acceptance tested.
- Full fresh evidence-mode assembly not run; policy-mode and cross-mode rejection tested.
- Reconstruction repeats native calculations and can validate deterministic errors.
- Long decimal probes exercise documented exactness without a declared precision limit.
- No native package edits made for this original review.

## Repaired replay

The original failing inputs, outputs and validator results above remain unchanged. The two native methods now use a private 256-digit Decimal context and explicit numeric/row bounds; process-global context is preserved. Values beyond the documented bounds fail closed.

- All five original scenario groups replayed successfully. Both long-decimal discrepancies now equal the independent expectations.
- Eight out-of-bound precision/magnitude probes were rejected by both input validation and calculation.
- All 22 operations regression tests passed, including the 60-place exact FX product and global-context isolation checks.
- Both packages passed their native evals. Exact replay outputs, boundary inputs and CLI results are appended in the JSON report.

The missing-verifier price bookkeeping caveat remains; no production or professional acceptance is claimed.
