# Changelog - earnings-preview-packet-builder

## [0.1.0] - 2026-07-20
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to compile a
source-backed, pre-event earnings preview packet for buy- and sell-side research, cleanly
separated from post-event results analysis (`earnings-results-analyzer`).

- **Scope:** compile the reporting/call calendar, third-party consensus, prior company
  guidance (as issued), historical KPIs with QoQ/YoY trends, known controversies, disclosed
  sensitivities, attributed bull/bear debate points, and open questions into a versioned-
  template packet. Draft-only; distribution is a human action after approvals.
- **Controls:** R2, Draft & package; **HARD BOUNDARY** - never set a forecast, rating, price
  target, or trade view, never originate an estimate or give personalized advice, never
  publish/distribute. Every figure cited; every forward-looking figure third-party attributed
  (consensus / company guidance). Descriptive arithmetic only (consensus-vs-guidance
  positioning, KPI deltas) - no projection of the print. Supervisory-analyst,
  research-compliance, and legal approvals recorded before `ready-for-distribution`;
  segregation of duties; MNPI / information-barrier controls; durable `packet_id`/`job_id`.
- **Scripts:** `validate_input` (request schema; source/attribution/approval warnings;
  rejects originated-view data-point kinds), `calculate_or_transform` (template-ordered
  assembly, per-item readiness, source mapping, consensus-vs-guidance positioning, KPI
  QoQ/YoY trends, approvals roll-up, packet status; `--selftest` with invariant tie-outs),
  `validate_output` (template fidelity, source mapping / no unsupported or unattributed
  assertions, prohibited forecast/rating/target/trade-view screen, approvals, draft-only
  status, notices). All Python stdlib-only, self-contained, each with `--selftest`.
- **Evaluations:** trigger/routing (pre-event vs post-event, upstream/control handoffs),
  golden nine-section packet with descriptive tie-outs, deterministic script checks, a
  fail-closed safety check running `validate_output` on a non-compliant packet (originated
  view, forbidden distributed status, missing section, unsourced data points), and
  no-view / no-fabricate / no-distribute / authorization refusals.
- **Handoffs:** downstream/adjacent `earnings-results-analyzer` (post-event),
  `investment-thesis-monitor`; upstream `investment-source-ingester`,
  `investment-vendor-feed-reconciler`, `investment-data-quality-exception-detector`,
  `company-profile-builder`, `scenario-sensitivity-generator`, `adverse-media-investigator`,
  `coverage-meeting-preparer`, `coverage-initiation-researcher`; control
  `communications-compliance-reviewer`, `conflicts-of-interest-reviewer`.

### Pending before release
- Supervisory-analyst + research-compliance (disclosures / conflicts) + legal blind review;
  segregation-of-duty review.
- Confirm the approved preview template source, owner, required sections, and versioning, and
  the consensus/estimates provider and attribution conventions.
- Wire read-only MCP integrations (template library, filings, transcripts, consensus, market
  data, news, CRM) at deployment.
