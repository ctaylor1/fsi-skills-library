# Changelog — phishing-and-bec-investigator

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to separate
substantive phishing/BEC **investigation** from first-line triage, from containment
execution, and from fund recovery (distinct entitlements, evidence depth, and case states).

- **Scope:** analyze a reported message (headers, SPF/DKIM/DMARC, sender identity, links,
  attachments, BEC payment / vendor-bank-change, behavior, related alerts); build a durable
  case with a cited evidence bundle (chronology, parties, indicators, amounts); emit a
  disposition RECOMMENDATION plus recommended containment / fraud-coordination steps.
  Read-only; every action is *proposed* via the approval broker / downstream skills.
- **Controls:** R3; no final determination, case closure, executed containment (block,
  quarantine, credential reset, isolation), payment recall, or filing; dedup links (never
  merges/closes); missing authentication evidence → `needs-data`; versioned scoring /
  watchlist / vendor-bank registries.
- **Scripts:** `validate_input` (report-bundle schema, needs-data warnings), investigation
  engine (indicator extraction + documented scoring + disposition recommendation + evidence
  bundle), `validate_output` (durable case_id, allowed recommendation dispositions, evidence
  completeness + citations, band tie-out, determination/closure/action language screen,
  standing note).
- **Evaluations:** trigger/routing, golden 7-report queue exercising every disposition
  (BEC, credential, malware, suspicious, benign, needs-data, possible-duplicate),
  deterministic script checks, fail-closed safety on a non-compliant fixture, no-autonomous-
  action refusal, prompt-injection refusal, closure-authorization refusal.
- **Handoffs:** upstream from `security-alert-triage-assistant`; downstream/routing to
  `payment-fraud-case-investigator`, `cyber-incident-response-coordinator`,
  `identity-access-reviewer`, `data-loss-prevention-incident-assistant`.

### Pending before release
- CISO / operational-resilience control-owner + fraud-ops + legal blind review;
  segregation-of-duty review (investigate vs. contain vs. recover).
- Confirm the scoring config, impersonation watchlist, known-domain list, and vendor bank
  registry source, owner, and versioning.
- Wire read-only MCP integrations (SIEM/SOAR, email gateway, IAM, threat intel, vendor
  reference data, CMDB) at deployment.
