# Domain Rules — cloud-security-posture-reviewer

The policy checks and how they map to a **remediation-priority disposition**. Thresholds, port
sets, allowed regions, required tags, and encryptable types are configuration (versioned, owned
by the cloud-security / control team), not hard-coded judgments, and never tuned to a specific
environment to reach a desired disposition. The firm's cloud-security baseline and, where
applicable, framework mappings (CIS, PCI DSS, SOC 2, FFIEC, NIST 800-53) take precedence.

## Policy checks (findings)

| Check (rule) | Category | Severity | Fires when |
| ------------ | -------- | -------- | ---------- |
| `identity.root_access_key` | identity | **critical** | An account has an active root access key |
| `identity.mfa_disabled` | identity | high | An IAM user with console access has no MFA |
| `identity.stale_access_key` | identity | medium | Access key age > `max_access_key_age_days` (default 90) |
| `identity.privileged_wildcard` | identity | high | An attached identity grants wildcard admin (Action:\* on Resource:\*) |
| `network.unrestricted_ingress` | network | **critical** / high | Ingress from `0.0.0.0/0` (or `::/0`) to a `critical_ports` member (22, 3389 → critical) or a `sensitive_ports` member (DB/cache ports → high) |
| `data_exposure.public_access` | data_exposure | **critical** / high | `public_access` true or public-read/-write ACL — critical if the resource holds sensitive data, else high |
| `encryption.at_rest_disabled` | encryption | **critical** / high | An encryptable resource has `encrypted=false` — critical if it holds sensitive data, else high |
| `logging.audit_log_disabled` | logging | high | Account audit logging (e.g. CloudTrail) is disabled |
| `logging.log_validation_disabled` | logging | medium | Audit logging is on but log-file integrity validation is off |
| `logging.flow_logs_disabled` | logging | medium | A VPC has flow logs disabled |
| `policy.disallowed_region` | policy | medium | A regional resource is deployed outside `allowed_regions` |
| `policy.missing_required_tag` | policy | low | A tagged resource is missing a `required_tags` member |

Findings are **independent and additive**; each fired check reports its own evidence (resource
record + config rule) and a recommended remediation. There is no opaque composite "security
score" and no automated attestation, risk acceptance, or remediation.

A check whose attributes are absent (e.g. a security group with no `ingress` on record, or an
encryptable resource with no `encrypted` attribute) is reported under **`not_evaluable`** — never
inferred as a pass.

## Remediation-priority disposition (deterministic, documented)

| Disposition | Rule |
| ----------- | ---- |
| **remediate_now** | One or more **critical** findings |
| **remediation_required** | One or more **high** findings, no critical |
| **review_recommended** | One or more **medium/low** findings, no critical/high |
| **posture_acceptable** | No findings fired |

The disposition is a **triage suggestion for a human owner** — it describes the state of the
export, not a compliance position. It is not an attestation and never triggers a remediation,
a finding closure, an exception, or a risk acceptance.

## Hard boundaries (fail closed)

- Never state or imply that an account/environment/resource is secure or compliant, or attest
  to any framework — describe findings factually and attribute attestation to the human.
- Never accept risk, close/suppress/waive a finding, grant an exception, or file a POA&M.
- Never apply/deploy a remediation or change any cloud configuration (security group, IAM/bucket
  policy, keys, encryption, logging) — recommend the remediation; a human applies it.
- Never tune thresholds, port sets, allowed regions, or required tags to force a disposition for
  a specific environment.

## Reviewer considerations (always include when any finding fired)

Remediation, risk acceptance, and exception approval are the owner's decisions; a compensating
control outside the export may mitigate a finding; criticality and data-classification labels
drive severity and may be wrong; framework mappings change how a finding is weighted. The pack
must invite the reviewer to weigh these before acting.
