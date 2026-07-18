# Changelog — relationship-manager-client-briefer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). A "Draft & package"
(R2) copilot that assembles a source-cited commercial relationship-manager client brief for
human review — draft-only, never delivered or written to a system of record.

- **Scope:** resolve the client entity and contacts, then draft a brief covering exposures
  (with committed/outstanding tie-out), covenant status, profitability, product holdings,
  service issues, recent news/adverse-media flags, pipeline, cross-sell context, source dates,
  and open actions, from an approved template. Read-only inputs; no CRM/system-of-record write.
- **Controls:** R2 / `external-delivery`; no delivery/send/submit/file and no CRM write; no
  credit/covenant/pricing/risk-rating decision (breaches and at-risk covenants are surfaced and
  routed, never waived or adjudicated); no investment/legal/tax advice; every item cited or
  stripped; tighter `critical_freshness_days` for exposures/covenants/profitability.
- **Assets:** approved `output-template.md` with exposure tie-out, surfaced covenant/news
  flags, cross-sell-as-context framing, recorded approvals, and reviewer sign-off block.
- **Scripts:** `validate_input` (client-intake schema, needs-data/unresolved/unsupported/stale
  warnings), `calculate_or_transform` (entity/source-integrity + freshness + exposure tie-out +
  overdue-action and covenant/adverse-news flags + template assembly), `validate_output`
  (template fidelity, no unsupported claims, exposure tie-out, recorded approvals, delivery/
  CRM-write, credit/covenant/pricing/rating decision, advice, standing-note screens).
- **Evaluations:** trigger/routing, golden 6-client queue exercising every status
  (draft-brief ×2 incl. breach-surfaced and acknowledged-stale, needs-data, unresolved-entity,
  unsupported-content, stale-source), deterministic script checks, a non-compliant fixture that
  must fail closed, and delivery/decision/advice/fabrication + authorization refusals.
- **Handoffs:** `credit-memo-drafter`, `covenant-compliance-monitor`,
  `commercial-cash-management-advisor`, `customer-onboarding-document-checker`,
  `collections-treatment-planner`, `loan-servicing-exception-resolver`,
  `adverse-media-investigator`, `kyc-customer-due-diligence-screener`,
  `customer-risk-rating-reviewer`, `complaint-resolution-assistant`, `meeting-action-tracker`;
  delivery and CRM writes to an authorized human.

### Pending before release
- Banking product/credit-operations control-owner + privacy (customer NPI/PII minimization)
  blind review; segregation-of-duty review (drafting vs. credit/covenant adjudication).
- Confirm the approved brief template source, owner, and version, and the freshness thresholds
  (`freshness_days`, `critical_freshness_days`) per deployment.
- Wire read-only MCP integrations (CRM, core banking/servicing, covenant tracking,
  profitability, service, news) at deployment.
