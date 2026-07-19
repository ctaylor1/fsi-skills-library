# Changelog — claims-triage-assistant

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to separate
first-line claims triage (classify, prioritize, surface coverage questions, route) from
substantive adjudication, adjusting, coverage analysis, and payment — distinct entitlements,
accountability, and case states.

- **Scope:** classify each newly reported claim's severity/complexity and urgency/service-level
  bands from explainable drivers, surface (never answer) coverage questions, recommend
  specialist routing, and assemble a draft triage summary. Draft-only; no system-of-record
  change. Every output is a recommendation for human adjudication.
- **Controls:** R3; human approval `required` (`triage_lead_review` +
  `claims_supervisor_approval`). No coverage determination, reserve, approval/denial,
  payment/settlement, assignment, closure, fraud/liability conclusion, or filing. Dispositions
  limited to `draft-ready`, `refer-specialist`, `needs-data`, `needs-review`. Versioned
  severity-map / triage-config.
- **Scripts:** `validate_input` (claims-queue schema, needs-data / needs-review warnings);
  triage engine (documented severity + urgency bands, coverage-question surfacing, routing,
  draft-summary assembly, fail-closed on unmapped claim_type / undetermined liability);
  `validate_output` (allowed dispositions, band tie-out, required template sections + DRAFT
  marker + citations, recorded approvals, no-unsupported-claim + no-executed-action screens,
  standing note).
- **Evaluations:** trigger/routing (fraud, coverage, subrogation, complex-file), golden
  8-claim queue exercising every disposition, deterministic script checks, no-decision /
  no-closure safety on a non-compliant fixture (fails closed), coverage-decision refusal,
  prompt injection, assignment/reserve authorization refusal.
- **Handoffs:** routes to `coverage-gap-analyzer`, `claims-fraud-referral-assistant`,
  `subrogation-opportunity-screener`, `claims-file-reviewer`, `policy-document-explainer`,
  `reserving-analysis-assistant`; upstream `claim-readiness-checker`,
  `catastrophe-exposure-monitor`; human owners for adjudication, CAT/major-loss, litigation,
  vulnerable-claimant support, and regulatory reporting.

### Pending before release
- Claims control-owner + legal/compliance (unfair-claims-practices, prompt-pay) blind review;
  segregation-of-duty review (triage vs. adjudication vs. payment).
- Confirm the approved severity map + triage config (thresholds, SLA targets, statutory
  windows) source, owner, and versioning per jurisdiction pack.
- Wire read-only MCP integrations (claims/case-mgmt, policy admin, product terms, document
  intelligence, catastrophe data) at deployment.
