# Changelog — claims-file-reviewer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** claim-file review — chronology + documented review checks + cited evidence +
  deterministic review-readiness band. Read-only; no coverage/reserve determination, no
  claim action.
- **Checks (deterministic):** coverage-citation-missing, loss-outside-policy-period,
  report-before-loss, late-report, chronology-gap, missing-document (by claim type),
  reserve-unsupported, reserve/severity-mismatch, payment-authority-missing,
  payment-evidence-missing, decision-untraceable, stale-open-issue — each explainable and
  evidenced (see `scripts/calculate_or_transform.py`).
- **Controls:** R3; `required` human adjudication; hard boundary against coverage/reserve
  determination, approve/deny, reserve change, payment/settlement, case closure, and filing;
  versioned-config thresholds only; reviewer considerations required; standing disclaimer.
- **Scripts:** `validate_input` (claim-file schema, evaluability warnings), review engine,
  `validate_output` (evidence/citation completeness, deterministic readiness tie-out,
  determination/action-language screen, disclaimer, reviewer-considerations).
- **Evaluations:** trigger/routing, golden `escalate` case, thin-file edge, deterministic
  script checks, no-determination safety + injection, system-of-record authorization.
- **Handoffs:** upstream `claims-triage-assistant`; downstream
  `claims-fraud-referral-assistant`, `reserving-analysis-assistant`,
  `subrogation-opportunity-screener`, `coverage-gap-analyzer`, `policy-wording-comparator`,
  `policy-document-explainer`. Coverage/reserve decisions and confirmed fraud dispositions
  route to licensed humans (adjuster / claims manager / coverage counsel / SIU).

### Pending before release
- Domain SME (claims) + control-owner blind review; fairness review of findings language.
- Confirm the versioned review-config source (required-doc sets, thresholds) and its owner.
- Wire read-only MCP integrations (claims, policy, evidence, payments/reserves, config) at
  deployment.
