# Source Map — claims-triage-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Claims / case management** | Claim record + state (system of record), `claim_id`, FNOL details | Read-only |
| 2 | **Policy administration** | Policy period, status, insured/coverages, party data | Read-only |
| 3 | **Underwriting rules / product terms** | Exclusion keywords, coverage grants, effective-dated terms | Read-only |
| 4 | **Document intelligence** | FNOL/loss-notice fields, adjuster notes, supporting documents | Read-only |
| 5 | **Actuarial / catastrophe data** | Catastrophe event codes, exposure context | Read-only |
| 6 | **Producer / agency systems** | Producer of record, submission channel | Read-only |
| 7 | Versioned **severity map** + **triage config** (thresholds, SLA targets) | Classification | Read-only |

## Citation format

`{system}:{ref}@{date/version}` — e.g. `claims:claim=CLM-4001@2026-07-04`,
`policy:pol=POL-****8801@2026-07-01`, `terms:commercial_property@v2026.05`,
`config:clm-triage@clm-triage-2026.07`.

## Freshness / effective dates

- Claim state must be read fresh (avoid triaging an already-assigned or already-worked claim).
- Coverage questions are assessed against the policy terms and period **in force at the date
  of loss**, not today's terms. The skill only surfaces the question; it never answers it.
- Severity map and triage config are **versioned**; the version is recorded on every triage
  record for reproducibility and review.

## Least-privilege operations (deployment)

- `claims.read(claim_id)`, `claims.find(queue|policy_id)` — read-only.
- `policy.read(policy_id, as_of=loss_date)`, `terms.get(product, effective_date)` — read-only, bounded.
- `docintel.read(document_id)` — read-only extraction of FNOL/loss-notice fields.
- `catdata.read(catastrophe_code)` — read-only catastrophe context (no exposure decision).
- `config.get('clm-triage-severity'|'clm-triage-config', version)` — read-only.

No mutation from this skill. Assigning the claim, setting a reserve, deciding coverage,
issuing payment, or closing/filing is performed elsewhere (adjuster of record / claims
supervisor, or a named specialist skill) **only** via the approval broker, and is out of
scope here.
