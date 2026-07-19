# Source Map — cloud-security-posture-reviewer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Cloud posture / CSPM export** (config scanner, resource inventory) | Position of record for resource configuration state | Read-only |
| 2 | **IAM** (users, roles, policies, keys, MFA) | Identity and entitlement attributes | Read-only |
| 3 | **CMDB / asset inventory** | Resource criticality, data classification, ownership | Read-only |
| 4 | **SIEM/SOAR & threat intelligence** | Enrichment (active exploitation context) for prioritization only | Read-only |
| 5 | **Policy config** (versioned) | Thresholds, port sets, allowed regions, required tags, encryptable types | Read-only |

The CSPM/config export is the position of record for configuration state. Where the export
and a claimed compensating control (WAF, SCP/guardrail, private path) disagree, cite both and
raise a finding for the owner — never resolve the conflict as a posture conclusion or clear a
finding on an unverified control.

## Citation format

`{system}:{ref}@{date}` — e.g. `cspm:acct=1111-2222-3333;bucket=s3-customer-exports@2026-07-15`
for a resource, and `config:{version};rule={rule_id}` for the policy rule the finding derives
from (e.g. `config:cspm-policy-2026.07;rule=network.unrestricted_ingress`). Every finding cites
the specific resource record **and** the config rule it fired.

## Freshness / effective dates

- The **policy config** (thresholds, port sets, allowed regions, required tags) is a versioned
  contract; the output records the `config_version` so a review is reproducible.
- A posture export is a **point-in-time snapshot**; state `as_of` and treat the review as valid
  for that snapshot only. A later drift or fix is a new assessment.
- Enrichment from threat intelligence is context for prioritization; it never converts a
  configuration finding into a confirmed compromise (route active-compromise indicators to a
  human incident coordinator).

## Least-privilege operations (deployment)

- `cspm.read(assessment_id)` → bounded resource inventory + configuration attributes.
- `iam.read(account_id)` → identities, roles, policy summaries, key/MFA metadata (no secrets).
- `cmdb.read(resource_id)` → criticality, data classification, owner.
- `config.get('cspm-policy', version)` → thresholds, port sets, allowed regions, required tags.

All read-only, deterministic, durable `review_id`, below the fixed timeout; page long resource
inventories as resumable stages. No write, remediation, finding-closure, exception-grant, or
attestation operation is bound to this skill.
