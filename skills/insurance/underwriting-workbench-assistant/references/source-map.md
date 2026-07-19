# Source Map — underwriting-workbench-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Policy administration / submission** | Submission of record, insured entity, occupancy class, requested limit, TIV | Read-only |
| 2 | **Loss & claims history** | 3-year loss ratio, large losses, development | Read-only |
| 3 | **Property / exposure data (COPE)** | Construction, occupancy, protection, exposure, values | Read-only |
| 4 | **Catastrophe model** | Peril zone, modeled PML, accumulation percentage | Read-only |
| 5 | **Financial / credit data** | Insured financial strength / credit score | Read-only |
| 6 | **Third-party risk screening** | Sanctions / adverse-media / distress flags (route to specialist; do not adjudicate) | Read-only |
| 7 | Approved **underwriting rules, appetite & authority config** (versioned) | Rule application, thresholds, binding-authority limits | Read-only |

Policy administration is the **system of record** for the submission; this skill never
writes back to it. Underwriting rules, appetite, and authority are **versioned contracts**.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `policyadmin:sub=SUB-88102;exposure@2026-07-01`,
`lossdb:insured=B****;3yr@2026-06-30`, `catmodel:sub=SUB-88102;v2026.1`,
`config:uw-appetite@uw-2026.07`. Every profile line item carries a citation; every rule
finding cites the source that triggered it.

## Freshness / effective dates

- Each risk section carries an `as_of` date. Age is measured against the review
  `as_of_date` on the batch — **never** the system clock — so results are reproducible.
- Per-section freshness SLAs and the rule thresholds live in versioned config; the
  `config_version` is recorded on every compiled profile. See
  [domain-rules.md](domain-rules.md).
- A **stale critical section** (property, catastrophe, exposure) forces `needs-data`; a
  stale non-critical section raises a `UW-FRESHNESS` exception that routes to the
  underwriter.

## Least-privilege operations (deployment)

- `submission.read(submission_id)`, `exposure.read(submission_id)` — read-only.
- `loss.read(insured_id, window)`, `catmodel.read(submission_id, version)` — read-only.
- `financial.read(insured_id)`, `tprisk.read(insured_id)` — read-only (flag only, no
  adjudication).
- `config.get('uw-appetite'|'uw-authority'|'uw-rules', version)` — read-only.

No mutation from this skill. The compiled workbench profile is a **draft proposal**; any
bind, quote, decline, issuance, or policy-administration write happens only through the
human underwriter and the approval broker, outside this skill.
