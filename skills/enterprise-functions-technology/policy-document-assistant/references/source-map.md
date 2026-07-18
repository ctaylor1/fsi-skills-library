# Source Map — policy-document-assistant

## Source hierarchy (highest first)

| Rank | Source (platform service / MCP integration) | Used for | Access |
| ---- | ------------------------------------------- | -------- | ------ |
| 1 | **Approved requirements register** (controlled templates & registers) | The only citable basis for normative "shall/must" statements | Read-only |
| 2 | **Controlled content library** | Owners, effective dates, expiry, prior-version-of-record, stale-language blocking | Read-only |
| 3 | **Approved-source retrieval** (regulatory / standards) | Regulation, supervisory guidance, and standard text behind each requirement | Read-only |
| 4 | **Document intelligence** | Clause/section/version extraction from the prior policy and supplied drafts | Read-only |
| 5 | **Entity resolution** | Owner roles, business units, related policy/procedure IDs | Read-only |
| 6 | **Policy standard + version/review config** (versioned) | Version-bump rules, tier review cadence, required-approval matrix, template sections | Read-only |

A normative statement may be sourced **only** from an `approved` requirements-register
entry (rank 1) that itself carries an authoritative source (rank 3). No requirement, no
clause. The register and the policy standard config are **versioned contracts**.

## Citation format

`{system}:{ref}@{version/date}` — e.g. `reg:31CFR1020.220(a)(2)(i)@2026-01`,
`policy:ERM-STD-04@v3.1`, `cms:POL-AML-001@v2.3`, `config:policy-std@2026.07`.
Every normative clause carries at least one such citation in its `sources`; every cited
reference is echoed in **Related Documents and Source Mapping**.

## Freshness / effective dates

- Read the **current version of record** and its effective/expiry dates fresh before drafting;
  do not base a change on a stale copy.
- Requirements must be `approved` and current; a superseded or draft requirement is **not**
  citable. A requirement past its expiry is flagged, not silently used.
- The version-bump rule, tier review cadence, and approval matrix are read from the
  **versioned** policy standard config; the config version is recorded on the draft so the
  computed version and next-review date are reproducible.

## Least-privilege operations (deployment)

- `requirements.read(req_id | register_version)` — read-only.
- `content.get(policy_id, version)` / `content.current(policy_id)` — read-only prior version.
- `sources.get(citation)` — read-only regulation/standard text.
- `config.get('policy-std', version)` — read-only version/review/approval rules.

No mutation from this skill. Recording approvals, publishing, activating, or making a policy
effective are performed by humans through the controlled content library and the approval
broker — **never** by this skill.
