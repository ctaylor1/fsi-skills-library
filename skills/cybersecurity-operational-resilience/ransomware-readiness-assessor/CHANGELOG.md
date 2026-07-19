# Changelog — ransomware-readiness-assessor

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** explainable, rule-based ransomware-readiness gap findings + cited evidence + staged
  remediation candidates + suggested remediation-review priority across identity, segmentation,
  backups, recovery, detection, third parties, exercises, communications, and critical-service
  dependencies. Read-only; R3 decision support with mandatory human adjudication — no readiness
  decision or attestation, no risk acceptance, no remediation execution, no filing, no closure or
  system-of-record write.
- **Findings (deterministic):** privileged-MFA gap, admin-tiering gap, segmentation gap,
  backup-coverage gap, backup-immutability gap, stale restore test, detection-coverage gap,
  dependency-mapping gap, critical-third-party resilience gap, overdue exercise, crisis-comms gap —
  each explainable and evidenced, with absence of positive control evidence treated conservatively
  as a gap (see `scripts/calculate_or_transform.py` and `references/domain-rules.md`).
- **Controls:** R3; hard boundary against readiness decisions/attestation and autonomous action;
  staged remediations are candidates (`status: staged_for_approval`) only; versioned-config
  thresholds and intervals; review-context prompts required; `required` human approval.
- **Scripts:** `validate_input` (extract schema, evaluability warnings), findings engine,
  `validate_output` (evidence/citation completeness, deterministic priority tie-out,
  decision/attestation/risk-acceptance/execution/filing/closure language screen, staged-candidate
  check, disclaimer, context prompts).
- **Evaluations:** trigger/routing, golden Elevated case (10 gaps fired, comms clean),
  no-optional-domains edge, deterministic script checks, no-decision safety fixture (fails closed)
  + injection, approval-required authorization.
- **Handoffs:** downstream to `cyber-incident-response-coordinator` (live incident),
  `identity-access-reviewer`, `cloud-security-posture-reviewer`, `vulnerability-prioritization-assistant`,
  `third-party-cyber-risk-reviewer`, `operational-resilience-scenario-tester`,
  `operational-resilience-reporter`, `data-loss-prevention-incident-assistant`,
  `security-alert-triage-assistant`; remediation execution, readiness attestation, risk acceptance,
  and regulatory filing are human/operations/governance actions outside the catalog.

### Pending before release
- Domain SME (CISO office / operational resilience) + control-owner blind review; confirm the
  readiness control library maps to the firm's standard and to NIST CSF 2.0 / CISA #StopRansomware.
- Confirm the versioned threshold/interval config source and its owner.
- Wire read-only MCP integrations (CMDB, backup/recovery, IAM/PAM, SIEM/EDR, vulnerability/cloud
  posture, threat-intel, vendor-risk, GRC/exercise, BCP/crisis-comms) at deployment.
