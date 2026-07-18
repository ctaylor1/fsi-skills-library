# Changelog — aml-alert-triager

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to separate
first-line AML triage from substantive investigation (distinct entitlements, evidence
depth, throughput metrics, and case states).

- **Scope:** prioritize alerts, dedup (link, never delete), apply ONLY approved
  suppression rules, and package escalations. Read-only; escalation is a *proposed*
  state transition via the approval broker.
- **Controls:** R3; no case closure/exoneration/SAR; suppression limited to `SUP-DUP-01`,
  `SUP-WL-INTERNAL`, `SUP-SEASONAL-01`; sanctions/adverse-media flag overrides suppression;
  tipping-off / SAR-confidentiality screen; versioned rule/priority config.
- **Scripts:** `validate_input` (alert-queue schema, needs-data warnings), triage engine
  (dedup + documented priority + approved suppression + escalation bundle),
  `validate_output` (allowed dispositions, approved suppressions only, escalation
  completeness, priority tie-out, closure/tipping-off screen, standing note).
- **Evaluations:** trigger/routing, golden 7-alert queue exercising every disposition,
  deterministic script checks, no-closure/unapproved-suppression safety, tipping-off
  refusal, prompt injection, closure-authorization refusal.
- **Handoffs:** downstream to `transaction-monitoring-alert-investigator`,
  `sanctions-match-adjudicator`, `suspicious-activity-report-drafter` (post-investigation),
  `customer-risk-rating-reviewer`.

### Pending before release
- FIU/AML control-owner + legal (SAR-confidentiality) blind review; segregation-of-duty review.
- Confirm the approved suppression rule set + priority config source, owner, and versioning.
- Wire read-only MCP integrations (monitoring/case-mgmt, KYC, transactions, flags) at deployment.
