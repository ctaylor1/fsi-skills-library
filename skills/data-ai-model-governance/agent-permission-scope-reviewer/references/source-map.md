# Source Map — agent-permission-scope-reviewer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **IAM / entitlement system** (position of record) | What is actually granted / provisioned today | Read-only |
| 2 | Agent/skill **permission manifest** (the request under review) | Declared tools, operations, modes, gates, revocation | Read-only |
| 3 | **Data catalog** | Authoritative data classification of each source the operation touches | Read-only |
| 4 | **Agent/tool logs** | Whether audit logging is actually emitted for the operation | Read-only |
| 5 | Least-privilege **control policy** (versioned) | Approved rule set, thresholds, and severity mapping | Read-only |

The manifest is a **request**, not proof. Never treat a manifest's `logged: true` or a
declared `data_classification` as fact when the data catalog or agent/tool logs say
otherwise — cite both and raise the conflict as a finding.

## Citation format

`{system}:{ref}@{date}` — e.g. `manifest:op=OP-003;field=approval_gate@2026-07-15`,
`policy:iam-lp-2026.07#LP-WRITE-NOGATE`, or `catalog:src=core-banking-txns;class=Highly Confidential@2026-07-15`.
Every finding cites the specific manifest field(s) and the policy rule it violates.

## Freshness / effective dates

- The control policy (rule set, thresholds, severity mapping) is a **versioned contract**;
  the output records the `policy_version` used so a review is reproducible.
- Bind findings to the `policy_version` in force at `as_of`; do not back-date a newer rule
  onto an older request without stating so.
- Data classification is taken from the data catalog as of the review date.

## Least-privilege operations (deployment)

- `iam.entitlements.get(agent_id)` → currently granted operations (read-only).
- `manifest.get(agent_id, version)` → the requested scope under review.
- `catalog.classify(source)` → authoritative data classification.
- `logs.coverage(agent_id, operation)` → whether audit logging is emitted.
- `policy.get('least-privilege', version)` → rule set + thresholds + severity mapping.
All read-only, deterministic, durable `review_id`, below the fixed timeout; page long
manifests as resumable stages. This skill has **no write, grant, provision, or revoke
operation** of its own.
