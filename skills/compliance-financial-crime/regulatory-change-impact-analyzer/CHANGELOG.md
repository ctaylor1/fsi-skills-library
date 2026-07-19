# Changelog — regulatory-change-impact-analyzer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** extract obligations from a regulatory change, test applicability to the firm,
  map applicable obligations to policies/controls/systems/data/training/owners, surface
  findings with cited evidence, and recommend a disposition band. Read-only; no determination,
  no closure, no filing.
- **Findings (deterministic):** applicable_in_scope, mapping_gap, owner_gap,
  overdue_or_retroactive, short_lead_time, authority_conflict — each explainable and evidenced
  (see `scripts/calculate_or_transform.py`).
- **Controls:** R3; human adjudication `required`; hard boundary against compliance
  determination, applicability closure, change closure, conflict resolution, filing, and
  attestation; versioned-config thresholds only; adjudication prompts required; standing
  disclaimer and `mandatory_adjudication` enforced.
- **Scripts:** `validate_input` (instrument/obligation/firm-profile schema, evaluability
  warnings), mapping engine, `validate_output` (evidence/citation completeness, deterministic
  disposition tie-out, R3 prohibited-decision/closure/filing screen, disclaimer + adjudication
  controls).
- **Evaluations:** trigger/routing, golden Priority case, out-of-scope edge, deterministic
  script checks, no-determination safety + injection, adjudication authorization.
- **Handoffs:** downstream to `policy-procedure-gap-analyzer`,
  `risk-control-self-assessment-assistant`, `regulatory-reporting-data-validator`,
  `privacy-impact-assessment-assistant`, `regulatory-exam-response-packager`; out-of-scope
  routing to `contract-obligation-extractor`, `model-change-impact-analyzer`,
  `enterprise-risk-assessment-builder`.

### Pending before release
- Domain SME (compliance change-management) + control-owner blind review; legal review of the
  conflict-handling and applicability boundaries.
- Confirm the versioned lead-time/mapping-completeness config source and its owner.
- Wire read-only MCP integrations (regulatory corpus, firm profile, control inventory, config)
  at deployment.
