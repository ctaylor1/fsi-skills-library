# Source Map — identity-access-reviewer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **IAM / IGA** (identity governance, entitlement catalog) | Accounts, entitlements, grants, privileged flag, approval records, certification history | Read-only |
| 2 | **HR / authoritative identity roster** | Worker status (active/terminated/leave), owner-to-account mapping | Read-only |
| 3 | **SIEM / access logs** | `last_login` / last-use, MFA enforcement signals, service-account activity | Read-only |
| 4 | **CMDB / application registry** | Application and system criticality, service-account ownership | Read-only |
| 5 | **Access-control config** (versioned) | SoD ruleset, inactivity/dormancy thresholds, certification interval, privileged definitions | Read-only |

The **IAM/IGA entitlement record is the position of record** for what access exists. HR is
the position of record for worker status. If IAM shows an active grant but HR shows the
owner terminated, that conflict IS the finding (`orphaned_account`) — cite both, never
resolve it silently or assume one system is stale.

## Citation format

`iam:{source_ref}[@{date}]` — e.g. `iam:iam=erp;grant=G-8@2025-01-01`. Every fired finding
cites the specific account/grant rows and, where relevant, the `last_login` or
`last_certified` date behind it. Staged revocation candidates reference the `grant_id` and
the fired finding that motivates them.

## Freshness / effective dates

- The access-control **config** (SoD rules, thresholds, certification interval) is a
  **versioned contract**; the output records `config_version` so a review is reproducible.
- `last_login` and `last_certified` are effective-dated; a missing `last_login` is treated
  **conservatively as inactive/dormant** and flagged, never silently ignored.
- The review is a point-in-time snapshot at `as_of`; re-running with the same extract and
  config version reproduces the findings and priority.

## Least-privilege operations (deployment)

- `iga.accounts(org_unit)` → accounts with owner, type, last_login, MFA state.
- `iga.entitlements(org_unit)` → grants with privileged flag, approval_ref, last_certified.
- `hr.status(user_id)` → worker status only (no broader HR PII).
- `config.get('iam-review', version)` → SoD rules + thresholds + privileged definitions.

All read-only, deterministic, durable `review_id`, below the fixed timeout; page large org
units as resumable stages. The skill never calls a provisioning/deprovisioning operation —
staging a revocation is producing a **candidate record**, not invoking a write.
