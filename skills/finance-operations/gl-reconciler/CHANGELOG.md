# Changelog — gl-reconciler

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** deterministic GL-to-subledger reconciliation — match records, classify breaks,
  trace lineage, tie out, and draft PROPOSED correction entries. Draft-only; no posting, no
  adjudication, no forced tie.
- **Break taxonomy (deterministic):** `timing_difference`, `amount_mismatch`,
  `unrecorded_in_gl`, `unsupported_in_gl`, `duplicate` — each with a signed `gl_impact`,
  materiality flag, and GL/subledger lineage citations (see
  `scripts/calculate_or_transform.py`).
- **Tie-out invariants:** classified breaks must fully explain the GL-vs-subledger difference
  (`residual == 0`); each correction offsets its break; corrected GL agrees to subledger after
  proposed corrections, leaving only documented timing items.
- **Controls:** R2; hard boundary against posting/booking (corrections are `status: "PROPOSED"`
  only), forcing a tie, adjudicating which side is correct, and per-reconciliation threshold
  tuning; versioned-config tolerances/materiality; `external-delivery` approval; segregation of
  duties between preparer and poster.
- **Idempotency:** `reconciliation_id` derived from `entity/account/as_of + input_fingerprint`
  (SHA-256 of normalized inputs) with no timestamp/random component; identical inputs reproduce
  identical output.
- **Scripts:** `validate_input` (job schema, matching-feasibility warnings), the reconciliation
  engine, `validate_output` (tie-outs, break taxonomy, lineage, idempotency, proposed-only +
  no-posting-language screen, disclaimer). All stdlib-only with `--selftest`.
- **Evaluations:** trigger/routing, golden reconciliation tie-out, clean-tie edge, deterministic
  script checks, no-posting/no-plug safety on a non-compliant fixture + injection, and
  external-delivery authorization.
- **Handoffs:** downstream to `accounts-payable-exception-resolver`, `fpa-variance-analyzer`,
  `regulatory-reporting-data-validator`, `audit-evidence-packager`,
  `financial-statement-audit-assistant`; upstream `month-end-close-orchestrator`; payment/
  settlement reconciliation routed to `settlement-break-reconciler` /
  `transaction-reconciliation-helper`. Posting is a human/authorized-system action.

### Pending before release
- Domain SME (controllership) + control-owner blind review; SoD confirmation for preparer vs
  poster.
- Confirm the versioned tolerance/materiality/suspense-account config source and its owner.
- Wire read-only MCP integrations (ERP/GL, subledgers, consolidation/FP&A, config) at deployment.
