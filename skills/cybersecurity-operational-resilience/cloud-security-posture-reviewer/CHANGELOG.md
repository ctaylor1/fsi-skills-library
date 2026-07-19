# Changelog — cloud-security-posture-reviewer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** cloud security posture review — documented policy checks across identity, network,
  encryption, data exposure, logging, and tagging/region policy + cited evidence + recommended
  remediation + deterministic remediation-priority disposition. Read-only; no attestation, no
  risk acceptance, no finding closure/waiver, no exception, no remediation, no config change.
- **Checks (deterministic):** identity.root_access_key, identity.mfa_disabled,
  identity.stale_access_key, identity.privileged_wildcard, network.unrestricted_ingress,
  data_exposure.public_access, encryption.at_rest_disabled, logging.audit_log_disabled,
  logging.log_validation_disabled, logging.flow_logs_disabled, policy.disallowed_region,
  policy.missing_required_tag — each explainable and evidenced (see
  `scripts/calculate_or_transform.py`); missing attributes reported `not_evaluable`.
- **Controls:** R3; `required` human adjudication; hard boundary against compliance attestation,
  risk acceptance, finding closure/suppression/waiver, exception/waiver grant, remediation
  execution, and system-of-record write; versioned-config thresholds only; reviewer
  considerations required; standing disclaimer.
- **Scripts:** `validate_input` (export schema, evaluability warnings), review engine,
  `validate_output` (evidence/citation completeness, deterministic disposition tie-out,
  attestation/closure/exception/remediation-execution language screen, disclaimer,
  reviewer-considerations).
- **Evaluations:** trigger/routing, golden `remediate_now` case (13 findings across all six
  categories, 4 critical), not-evaluable edge, deterministic script checks, no-attestation
  safety + injection, system-of-record authorization.
- **Handoffs:** upstream `security-alert-triage-assistant`, `cyber-incident-response-coordinator`;
  downstream `identity-access-reviewer`, `vulnerability-prioritization-assistant`,
  `data-loss-prevention-incident-assistant`, `cyber-incident-response-coordinator`,
  `third-party-cyber-risk-reviewer`, `operational-resilience-reporter`. Remediation, risk
  acceptance, exception approval, and compliance attestation route to licensed humans
  (cloud/platform owner / security control owner / CISO / GRC).

### Pending before release
- Domain SME (cloud security) + control-owner blind review; false-positive/negative tuning of
  the check thresholds against real exports.
- Confirm the versioned policy-config source (thresholds, port sets, allowed regions, required
  tags, encryptable types) and its owner.
- Wire read-only MCP integrations (CSPM/config export, IAM, CMDB, SIEM/threat-intel, config) at
  deployment.
