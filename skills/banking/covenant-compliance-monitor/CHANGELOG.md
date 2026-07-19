# Changelog — covenant-compliance-monitor

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). A scheduled, read-only,
alert-only covenant-compliance monitor for commercial banking (risk tier R3, decision support).

- **Scope:** evaluate credit facilities against the financial, negative, and reporting
  covenants parsed from their credit agreements; compute each test from approved financial
  spreads; reconcile the borrower compliance certificate against the bank's independent
  calculation; classify PASS/WARN/BREACH with cited evidence, headroom, and trend; deduplicate
  against open exceptions; check spread freshness; queue severity-ranked exceptions. Read-only;
  **no autonomous default, waiver, amendment, risk-rating change, closure, or filing.**
- **Covenant engine (deterministic):** financial ratio/level covenants (max caps and min
  floors) computed from a `formula` over approved-spread line items; negative-covenant basket
  caps; reporting-deliverable deadlines (overdue BREACH / late WARN); certificate reconciliation
  (bank-computed vs borrower-reported beyond tolerance); period-over-period trend — each
  explainable, evidenced, and reproducible (see `scripts/calculate_or_transform.py`). The
  `breach_type` (financial_test / negative_covenant / reconciliation / reporting / freshness)
  distinguishes a computed covenant breach from a certificate discrepancy or an overdue filing.
- **Controls:** R3; scheduled `read-only-monitoring`, alert-only posture; hard boundary against
  declaring default, accelerating/restructuring, granting/drafting waivers or amendments,
  issuing reservations of rights, changing risk ratings, notifying the borrower, and
  closing/suppressing alerts; versioned covenant-library thresholds only; `required` human
  adjudication before any covenant decision or system-of-record change.
- **Scripts:** `validate_input` (run/facility/covenant schema, evaluability + freshness/dedup/
  reconciliation warnings), the covenant engine, and `validate_output` (alert well-formedness,
  deterministic severity/queue tie-out, deduplication integrity, freshness-handling,
  no-autonomous-action screen, disclaimer, escalation tie-out).
- **Evaluations:** trigger/routing, a golden multi-facility exception run (leverage/coverage/
  basket/reporting breach mix, a certificate reconciliation break, deduplication, trend, and a
  fully-compliant facility), deterministic script checks, a no-autonomous-action safety fixture
  (`expect_exit 1`) plus an injection case, a no-open-baseline edge, and required-adjudication
  authorization.
- **Handoffs:** downstream to `loan-servicing-exception-resolver`, `credit-memo-drafter`,
  `credit-risk-portfolio-analyzer`, `financial-spreading-assistant`, `cashflow-forecaster`, and
  `relationship-manager-client-briefer`; ambiguous covenant definitions and every disposition
  remain human (loan-documentation/legal counsel, credit officer, and credit committee).

### Pending before release
- Domain SME (credit / portfolio management) + control-owner blind review; legal review of the
  covenant-parse-to-library mapping and defined-term fidelity.
- Confirm the versioned covenant-library source, its owner, and the `config_version` contract,
  including how amendments re-baseline it.
- Wire read-only MCP integrations (credit-agreement/covenant library, approved spreads,
  compliance certificates, loan servicing, prior-alert store) at deployment.
- Calibrate `cushion`, `recon_tolerance`, and `max_staleness_days` per portfolio with credit.
