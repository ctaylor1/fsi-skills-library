# Changelog — data-quality-issue-investigator

## [Unreleased]
Pre-commit adversarial-review fixes.

- **Severity tie-out honors the versioned config.** `validate_output._expected_band` no longer
  hardcodes the 9/5/2 band thresholds; it reads the same `severity_config` the engine used, and
  the engine now emits that `severity_config` on its output so a non-default threshold ties out
  against itself instead of failing its own tie-out. New deterministic fixture/eval
  `det-output-altconfig` (`evals/files/investigation_altconfig.json`) validates under a
  non-default config (would have failed exit 1 under the old hardcoded thresholds).
- **Input validation fails closed on a malformed period.** `validate_input` guards the
  `period` type before dereferencing, so a scalar period yields a clean validation error
  instead of an uncaught `AttributeError`. New safety fixture/eval `safety-malformed-period`
  (`evals/files/dq_issues_bad_period.json`) proves the fail-closed behavior.

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to work a
data-quality issue as a durable, audit-ready case — separating investigation (evidence +
recommendation) from detection/monitoring upstream and from remediation/closure downstream
(distinct entitlements, evidence depth, and case states).

- **Scope:** profile the defect, quantify impact and blast radius, build a cited chronology,
  resolve parties, and assemble an evidence bundle with a durable `case_id` and a recommended
  severity + remediation path. Read-only; every disposition is a *recommendation*.
- **Controls:** R3; no case closure/resolution, root-cause confirmation, remediation marking,
  waiver, or filing; material/regulated impact forces incident escalation; dedup links (never
  merges/closes); versioned severity config recorded on every case.
- **Scripts:** `validate_input` (issue-queue schema, needs-data warnings, failing>total
  guard), investigation engine (dedup + documented severity + chronology + evidence bundle +
  recommendation), `validate_output` (durable case_id, recommendation-only dispositions,
  evidence/chronology citation completeness, severity tie-out, duplicate linkage,
  closure/determination language screen, standing note).
- **Evaluations:** trigger/routing, golden 7-issue queue exercising every disposition,
  deterministic script checks, no-closure/determination safety fixture (fails closed),
  prompt-injection and root-cause-confirmation refusals, closure-authorization refusal.
- **Handoffs:** `data-lineage-documenter` (upstream trace), `ai-incident-investigator`
  (material/regulated impact), `model-change-impact-analyzer`, `model-inventory-maintainer`;
  remediation and closure are human/operations hand-offs.

### Pending before release
- Data-governance control-owner + model-risk blind review; segregation-of-duty review
  (investigation vs. remediation vs. closure).
- Confirm the severity-config source, owner, thresholds, and versioning.
- Wire read-only MCP integrations (issue/case system, data catalog, DQ/profiling, model
  registry, agent/tool logs) at deployment.
