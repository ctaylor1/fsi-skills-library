# Changelog — data-loss-prevention-incident-assistant

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** enrich, classify, estimate exposure, correlate, deduplicate, score severity, and
  preserve evidence references for a batch of DLP events, and assemble a review-ready,
  source-mapped draft incident-assessment package; apply only approved benign/business
  suppression.
- **Controls:** R3; drafts/packages only — never determines/declares a breach, decides/issues a
  notification, dispositions/closes an incident, contains (blocks/quarantines/revokes/deletes/
  recalls) any transfer, account, or data, suppresses outside approved rules, writes a system of
  record, or sends the package; approved suppression is logged and reviewable; deterministic
  prohibited-action screen with a bad fixture that fails closed.
- **Scripts:** `validate_input`, `calculate_or_transform` (deterministic enrichment/
  classification/exposure/dedup/severity + approved suppression + evidence references),
  `validate_output` (allowed status/dispositions, template fidelity, no unsupported claims,
  approved suppressions only, severity tie-out, required approvals, hard-boundary consistency,
  breach-determination/containment/filing/send screens, standing note).
- **Evaluations:** trigger/routing, golden 7-event batch exercising every disposition and all
  three approved suppression rules, deterministic script checks, no-autonomous-action / no-breach
  / no-notification safety, hard-boundary and system-of-record-write authorization.
- **Handoffs:** upstream from `security-alert-triage-assistant`; downstream to
  `cyber-incident-response-coordinator`, `phishing-and-bec-investigator`,
  `identity-access-reviewer`, `cloud-security-posture-reviewer`, `third-party-cyber-risk-reviewer`,
  and (post-adjudication) `operational-resilience-reporter`; human privacy-officer + legal/
  compliance for breach determination and notification.

### Pending before release
- CISO / operational-resilience and privacy-officer + legal/compliance control-owner review;
  approved suppression rule-set + classification/severity config sign-off.
- Confirm the data-classification taxonomy source, owner, and versioning per the firm standard.
- Wire read-only DLP console/SIEM-SOAR, IAM, CMDB, egress-proxy, threat-intel, and
  classification MCP integrations at deployment.
