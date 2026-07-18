# Changelog — coverage-meeting-preparer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to give coverage
bankers and senior relationship managers a controlled, source-cited way to draft client and
prospect meeting briefs without crossing into recommendation, delivery, or information-barrier
territory.

- **Scope:** assemble a DRAFT coverage-meeting brief — relationship history, deduped/date-sorted
  developments, strategic issues, the counterparty's likely objectives (framed as hypotheses),
  discussion questions, and follow-ups — from approved, in-inventory, cited sources. Draft-only;
  external delivery is a human action.
- **Controls:** R2 "Draft & package"; `external-delivery` approval. No send/distribute/file/
  execute; no investment recommendation, price target, valuation opinion, rating, or investment/
  legal/tax advice; every claim cites an approved source; MNPI kept private-side / internal-only
  with recorded control-room clearance; freshness screening against `freshness_days`.
- **Statuses:** `needs-data`, `unsupported-claims`, `stale-source`, `barrier-hold`, and the
  packageable `draft-brief` (precedence in that order).
- **Scripts:** `validate_input` (intake schema; needs-data / unsupported / stale / barrier
  warnings), brief assembler `calculate_or_transform` (dedup + source-integrity + freshness +
  MNPI tagging + template-shaped DRAFT with recorded approvals), `validate_output` (template
  fidelity, unsupported/unapproved-claim screen, blocking-stale screen, MNPI-internal-only and
  control-room screen, approvals recorded, delivery/advice language screen, standing note).
- **Assets:** `assets/output-template.md` — the approved coverage-brief template with the
  standing note, handling label, MNPI internal-only markers, and reviewer sign-off block.
- **Evaluations:** trigger/routing, a golden 5-meeting queue exercising every status
  (draft-brief, needs-data, unsupported-claims, stale-source, barrier-hold), deterministic
  script checks, a non-compliant `brief_bad.json` safety fixture (overreach: unsupported claim,
  MNPI in a shareable field, unrecorded approvals, delivery + recommendation language) that must
  fail closed, plus injection/recommendation/MNPI/fabrication refusals and a delivery
  authorization refusal.
- **Handoffs:** upstream from `company-profile-builder`, `earnings-results-analyzer`,
  `market-landscape-researcher`, `comps-analysis-builder`; downstream to
  `investment-banking-pitch-builder`, `due-diligence-packager`, `transaction-process-tracker`,
  `buyer-investor-list-builder`; recommendation/rating, external delivery, and MNPI wall-crossing
  reserved for licensed research, an authorized human, and the control room.

### Pending before release
- Coverage/Research supervisory + compliance/control-room blind review; information-barrier
  (MNPI) segregation-of-duty review.
- Confirm the approved coverage-brief template, approved-source list, and `freshness_days` source,
  owner, and versioning (`config_version`).
- Wire read-only MCP integrations (CRM, filings, transcripts, market data, research, data room)
  at deployment.
