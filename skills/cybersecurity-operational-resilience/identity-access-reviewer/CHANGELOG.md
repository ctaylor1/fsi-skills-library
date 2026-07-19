# Changelog — identity-access-reviewer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** explainable, rule-based access-review findings + cited evidence + staged
  revocation candidates + suggested review priority. Read-only; R3 decision support with
  mandatory human adjudication — no access decision, no revocation/disable/deprovision, no
  certification, no closure or system-of-record write.
- **Findings (deterministic):** segregation-of-duties conflict, dormant privileged access,
  inactive account, orphaned account (terminated / off-roster owner), unapproved privileged,
  stale certification, privileged-without-MFA, over-entitlement — each explainable and
  evidenced (see `scripts/calculate_or_transform.py` and `references/domain-rules.md`).
- **Controls:** R3; hard boundary against access decisions and autonomous action; staged
  revocations are candidates (`status: staged_for_approval`) only; versioned-config
  thresholds and SoD ruleset; review-context prompts required; `required` human approval.
- **Scripts:** `validate_input` (extract schema, evaluability warnings), findings engine,
  `validate_output` (evidence/citation completeness, deterministic priority tie-out,
  decision/execution/closure/certification language screen, staged-candidate check, disclaimer,
  context prompts).
- **Evaluations:** trigger/routing, golden Elevated case (7 findings), no-SoD-rules edge,
  deterministic script checks, no-decision safety fixture (fails closed) + injection,
  approval-required authorization.
- **Handoffs:** downstream to `security-alert-triage-assistant`, `phishing-and-bec-investigator`,
  `cloud-security-posture-reviewer`, `third-party-cyber-risk-reviewer`,
  `cyber-incident-response-coordinator`, `operational-resilience-reporter`; revocation execution
  and certification sign-off are human/IAM-operations actions outside the catalog.

### Pending before release
- Domain SME (IAM control owner) + access-governance blind review; fairness review of finding
  rules (no protected-class proxies).
- Confirm the versioned SoD ruleset / threshold config source and its owner.
- Wire read-only MCP integrations (IAM/IGA, HR roster, SIEM/access logs, CMDB, config) at deployment.
