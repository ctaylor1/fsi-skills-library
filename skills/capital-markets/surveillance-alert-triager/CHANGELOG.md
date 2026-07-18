# Changelog — surveillance-alert-triager

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to separate
first-line surveillance triage from substantive investigation (distinct entitlements,
evidence depth, throughput metrics, and case states).

- **Scope:** prioritize trade- and e-comms-surveillance alerts, dedup (link, never delete),
  apply ONLY approved suppression rules, and package escalations with a durable `case_id` and
  an evidence bundle (chronology, parties, amounts, citations). Read-only; escalation is a
  *proposed* state transition via the approval broker.
- **Controls:** R3; no case closure / market-abuse determination / exoneration / filing;
  suppression limited to `SUP-DUP-01`, `SUP-WL-KNOWN`, `SUP-CALIB-01`; restricted-list /
  watch-list proximity overrides suppression; versioned rule/priority config.
- **Scripts:** `validate_input` (alert-queue schema, needs-data warnings), triage engine
  (dedup + documented priority + approved suppression + deterministic cited chronology and
  evidence bundle), `validate_output` (durable case_id, allowed dispositions, approved
  suppressions only, escalation/chronology citation completeness, priority tie-out,
  closure/determination/filing screen, standing note).
- **Evaluations:** trigger/routing, golden 7-alert queue exercising every disposition,
  deterministic script checks, no-closure/unapproved-suppression safety fixture,
  determination refusal, prompt injection, closure-authorization refusal.
- **Handoffs:** downstream to `market-surveillance-alert-investigator`,
  `communications-compliance-reviewer`, `best-execution-reviewer`,
  `conflicts-of-interest-reviewer`; substantive closure/determination/filing are
  human-adjudicated.

### Pending before release
- Surveillance control-owner + legal (MNPI-handling) blind review; segregation-of-duty review.
- Confirm the approved suppression rule set + priority config source, owner, and versioning.
- Wire read-only MCP integrations (surveillance/case-mgmt, OMS/EMS, comms archive,
  market/reference data, account context, restricted-list flags) at deployment.
