# Changelog — chargeback-dispute-packager

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `existing-updated`). Packages
merchant-side chargeback representments as a controlled, review-ready draft — separated from
dispute submission, fraud determination, and reconciliation (distinct entitlements and
systems of record).

- **Scope:** match the network reason code to its required-evidence groups, compute the
  representment deadline, tie evidence to the disputed transaction, flag compelling-evidence
  eligibility, and draft an exhibit-cited rebuttal from an approved template. Draft-only; no
  system-of-record change.
- **Controls:** R2; never submits/files, never determines fraud/liability, never guarantees
  an outcome, never fabricates evidence; reason codes and windows are a versioned contract
  (`ruleset_version`); PCI/NPI data minimization and PAN masking.
- **Scripts:** `validate_input` (dispute/evidence schema, unknown-reason-code and unsupported
  -claim warnings), packaging engine (deadline + evidence completeness + identity tie-out +
  compelling-evidence + narrative fidelity → status), `validate_output` (approved reason
  code, packageable invariants, guarantee/submission/advice language screen, standing note).
- **Assets:** `assets/output-template.md` representment package template with a reviewer
  sign-off block and standing disclaimer.
- **Evaluations:** trigger/routing, golden 5-dispute queue exercising every status,
  deterministic script checks, a non-compliant-package safety fixture that trips the R2
  guardrail (unknown code, over-claim, submission language, missing disclaimer), and
  no-submission / no-guarantee / no-decision refusals.
- **Handoffs:** upstream `network-rules-change-tracker` (ruleset), acquirer/gateway, OMS;
  adjacent `dispute-operations-assistant`, `payment-fraud-case-investigator`,
  `transaction-reconciliation-helper`, `settlement-break-reconciler`, `merchant-fee-optimizer`.

### Pending before release
- Payments ops/risk control-owner review; confirm reason-code catalog, windows, and
  compelling-evidence rules against the current card-network rulesets and jurisdiction packs.
- Confirm the controlled representment template owner, version, and effective dates.
- Wire read-only MCP integrations (network-rules reference, acquirer/gateway, OMS, templates,
  case portal) at deployment; submission remains a human action outside this skill.
