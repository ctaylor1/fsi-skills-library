# Changelog — beneficial-ownership-verifier

## [0.1.1] — 2026-09-21

Phase 1 repairs the bounded supplied-evidence implementation. Explicit applicable policy profiles replace silent approved defaults; unknown evidence remains unknown. Native output requires detached original-input reconstruction, rejects unvalidated additions and states source truth as unverified.

Supported: a scalar proportional-equity graph with aggregation across chains and a greater-than-or-equal threshold, plus specified direct root-entity control types. Unsupported: trusts/legal arrangements, voting or share-class tests, indirect control/control by other means, exemptions, nominee look-through, CTA filing determinations and independent identity verification. Route unsupported structures to a qualified specialist.

Domain rules, fixtures, handoffs and input/output contracts now match the implementation. Added 24 adversarial regression cases covering policy provenance, source binding and domain failure modes. Source pointers and synthetic fixtures are not independent verification or production acceptance. Human domain/control-owner review and any live integration remain pending. Earlier 0.1.0 claims below are historical and superseded where inconsistent with this entry and current rules.

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** compute effective (indirect) beneficial ownership across an entity's ownership
  graph, identify ownership-prong (≥ threshold) and control-prong UBOs, reconcile against the
  declared list, enumerate evidence-cited gaps, apply the versioned jurisdiction pack, and
  recommend a readiness band. Read-only; no determination, no approval, no closure, no filing.
- **Computation (deterministic):** chain-product-and-sum effective ownership with
  cycle detection; ownership prong + independent control prong; contributing-edge evidence
  per identified UBO (see `scripts/calculate_or_transform.py`).
- **Gap taxonomy:** undeclared_owner, undeclared_control, control_prong_unsatisfied,
  declared_not_supported, circular_ownership (blocking); pct_mismatch, missing_document,
  expired_document, ownership_over_100 (remediable). Deterministic readiness mapping:
  Complete-for-review / Remediation-needed / Escalate (see `references/domain-rules.md`).
- **Controls:** R3 decision-support; hard boundary against beneficial-ownership determination,
  onboarding approval/rejection, identity verification, case closure, and BOI/SAR filing;
  jurisdiction thresholds are versioned config only; tipping-off controls; `required` human
  adjudication.
- **Scripts:** `validate_input` (graph/schema integrity, data-quality warnings), the
  ownership engine, `validate_output` (evidence-citation completeness, deterministic readiness
  tie-out, decision/closure/filing-language screen, standing disclaimer).
- **Evaluations:** trigger/routing, golden Escalate case (undeclared indirect owner surfaced),
  deterministic script checks, no-decision safety + injection, control-prong edge case,
  human-adjudication authorization.
- **Handoffs:** downstream to `kyc-customer-due-diligence-screener`,
  `sanctions-match-adjudicator`, `adverse-media-investigator`,
  `enhanced-due-diligence-packager`, `customer-risk-rating-reviewer`,
  `customer-onboarding-document-checker`, `suspicious-activity-report-drafter`.

### Pending before release
- Domain SME (KYC/financial-crime) + control-owner blind review; fairness/conduct review.
- Confirm the versioned jurisdiction-pack config source (thresholds, control-prong rule,
  effective dates) and its policy owner.
- Wire read-only MCP integrations (registry/document intelligence, entity resolution, KYC/AML,
  sanctions/PEP, config) at deployment.
