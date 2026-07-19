# Changelog — advisor-follow-up-assistant

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to assemble a
source-mapped **draft** post-meeting follow-up package from a documented client meeting, separating
drafting from the downstream suitability review, IPS build, trading, and the human/operations send
and CRM write (distinct entitlements, evidence, and approvals).

- **Scope:** lay the meeting summary, action items (owner + due date), client communication draft,
  required disclosures, proposed CRM update, and next-meeting reminder into the approved 7-section
  follow-up template; map every material assertion to a source; check disclosure completeness for
  every recommendation discussed; record advisor / supervisory-principal approvals as `pending`.
  Draft-only; no send, no system-of-record change.
- **Controls:** R3; no sending/delivery, no CRM or system-of-record write, no trading/staging, no
  suitability/Reg BI determination, no scheduling, no guarantees; every recommendation flagged for
  disclosure must be covered and every one flagged for suitability review is routed to
  `suitability-reg-bi-reviewer`; `draft_status` stays `draft`, `delivery_status` `not-delivered`,
  `crm_write_status` `not-written`; versioned template and disclosures contracts recorded on the draft.
- **Scripts:** `validate_input` (request schema, action-item and citation checks, disclosure-gap and
  needs-data warnings), `calculate_or_transform` (section assembly, disclosure completeness,
  suitability/senior routing, source map, completeness), `validate_output` (template fidelity,
  uncited/unsupported assertions, disclosure and routing completeness, action-item completeness,
  approval-pending, draft-only status flags, prohibited-language screen, standing note).
- **Evaluations:** trigger/routing tests, golden draft exercising all 7 sections and the
  disclosure/routing/citation checks, deterministic script checks, a non-compliant-draft safety
  fixture that fails closed (21 findings across every guardrail family), plus injection / guarantee /
  suitability-shortcut refusals and a finalize-send-and-write authorization refusal.
- **Handoffs:** upstream `client-review-preparer`, `financial-goal-progress-analyzer`,
  `retirement-income-scenario-modeler`; downstream `suitability-reg-bi-reviewer`,
  `investment-policy-statement-builder`, `portfolio-rebalancing-assistant`,
  `portfolio-proposal-comparator`, `senior-investor-protection-screener`.

### Pending before release
- Wealth-management advisory + compliance/supervision blind review; legal review of standard
  disclosure and client-communication language; accessibility review of the output template.
- Confirm the approved follow-up template, required-section list, and disclosures library — their
  owners, versions, and effective-date/stale-content controls; confirm FINRA Rule 2210 principal
  pre-approval vs. correspondence-supervision thresholds for the deployment.
- Wire read-only MCP integrations (CRM/meeting record, planning engine, portfolio-accounting/OMS,
  product data, disclosures/restrictions register, approved tax assumptions) at deployment.
