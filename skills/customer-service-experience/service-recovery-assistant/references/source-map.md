# Source Map — service-recovery-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Case / complaint management** | Service-failure record, case state, prior remediation, durable `case_id` | Read-only |
| 2 | **CRM** | Customer profile, tenure, segment, vulnerability flag, relationship history | Read-only |
| 3 | **Contact-center transcripts** | What was said/promised, commitments, sentiment, missed callbacks | Read-only |
| 4 | **Approved knowledge / product terms** | Applicable service standard, product terms, disclosures, approved apology language | Read-only |
| 5 | **Approved goodwill / redress matrix** + **approval thresholds** (versioned) | Deterministic remediation and required approval tier | Read-only |
| 6 | **Precedent set** (prior recovery cases) | Consistency / fair-value context | Read-only |

The **case-management** system is the system of record for the failure and any remediation
state. This skill never writes it; a proposed remediation is delivered as a draft for a
human to approve and (separately) action.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `crm:case=SR-3002@2026-07-06`,
`call=CT-88120@2026-07-09`, `policy:svc-standard-3.2`, `config:svc-recovery@2026.06`.
Every failure-assessment finding, quoted figure, and drafted claim carries a citation.

## Freshness / effective dates

- Read the case and CRM record fresh so a recovery is not drafted for an already-resolved or
  already-escalated case.
- The goodwill/redress matrix, approval thresholds, and approved apology language are
  **versioned contracts**; the version is recorded on every proposed remediation
  (`matrix_version`) for reproducibility and review.

## Least-privilege operations (deployment)

- `cases.read(case_id)`, `crm.customer(customer_id)`, `transcripts.read(interaction_id)` —
  read-only, bounded to the case.
- `knowledge.get(policy_ref)`, `terms.get(product_ref)` — approved-source retrieval only.
- `config.get('svc-recovery-matrix'|'svc-recovery-thresholds', version)` — read-only,
  versioned.
- `precedent.find(failure_type)` — read-only, de-identified aggregates.

No mutation from this skill. Delivery of the communication and any goodwill/redress payment
are separate, approval-gated actions performed downstream (see `references/handoffs.md`),
never by this skill.
