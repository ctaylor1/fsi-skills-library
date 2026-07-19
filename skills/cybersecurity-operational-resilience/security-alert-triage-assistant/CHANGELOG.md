# Changelog — security-alert-triage-assistant

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** enrich, map, correlate, deduplicate, and prioritize SOC alerts and assemble an
  analyst-ready, source-mapped draft investigation package; apply only approved benign-pattern
  suppression.
- **Controls:** R3; drafts/packages only — never closes/dispositions an alert, declares/closes
  an incident, contains/isolates/blocks/disables an asset or identity, resets credentials,
  suppresses outside approved rules, writes a system of record, or sends the package; approved
  suppression is logged and reviewable; deterministic prohibited-action screen with a bad
  fixture that fails closed.
- **Scripts:** `validate_input`, `calculate_or_transform` (deterministic enrichment/dedup/
  priority + approved suppression), `validate_output` (allowed dispositions, approved
  suppressions only, escalation completeness, no-response-action screen, standing note).
- **Evaluations:** trigger/routing, golden alert queue, deterministic script checks,
  no-autonomous-action safety, human-response authorization.
- **Handoffs:** downstream to `phishing-and-bec-investigator`, `cyber-incident-response-coordinator`,
  `data-loss-prevention-incident-assistant`, `identity-access-reviewer`.

### Pending before release
- SOC / IR control-owner review; approved suppression rule-set + priority config sign-off.
- Wire read-only SIEM/SOAR, IAM, CMDB, threat-intel MCP integrations at deployment.
