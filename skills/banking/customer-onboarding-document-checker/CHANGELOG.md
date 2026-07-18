# Changelog — customer-onboarding-document-checker

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** explainable onboarding-package completeness checks + cited evidence + a
  deterministic readiness status. Read-only; no onboarding approval, no identity
  verification, no KYC/CIP determination, no account action.
- **Checks (deterministic):** missing required document, expired / expiring-soon, missing
  signature, illegible, stale document, data inconsistency (key vs. non-key identity
  fields), unresolved exception — each explainable and evidenced (see
  `scripts/calculate_or_transform.py`).
- **Controls:** R2; hard boundary against onboarding approval, identity verification,
  KYC/CIP/sanctions/PEP determination, document/exception waiver, and account actions;
  versioned-config checklist/thresholds/severities only; remediation prompts required;
  `external-delivery` approval.
- **Scripts:** `validate_input` (package schema, evaluability warnings), completeness engine
  (with `--selftest` internal-consistency check), `validate_output` (evidence/citation
  completeness, deterministic readiness tie-out, approval/determination-language screen,
  disclaimer, remediation prompts).
- **Evaluations:** trigger/routing, golden Not-ready case, missing-dates edge, deterministic
  script checks, no-approval safety + injection, external-delivery authorization.
- **Handoffs:** downstream to `kyc-customer-due-diligence-screener`,
  `enhanced-due-diligence-packager`, `beneficial-ownership-verifier`,
  `sanctions-match-adjudicator`, `customer-risk-rating-reviewer`,
  `credit-application-packager`, `loan-package-completeness-checker`; onboarding-approval and
  identity-verification remain human / compliance-officer actions.

### Pending before release
- Domain SME (banking onboarding / BSA-AML) + control-owner blind review; fairness review of
  the data-consistency and severity rules.
- Confirm the versioned required-document checklist source (per customer type / product /
  jurisdiction) and its owner, including US CIP requirements.
- Wire read-only MCP integrations (document intelligence, onboarding case, CRM, config) at
  deployment.
