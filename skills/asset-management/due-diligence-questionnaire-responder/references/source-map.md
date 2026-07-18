# Source Map — due-diligence-questionnaire-responder

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Controlled content library** | Approved DDQ/RFP answers with `owner`, `effective_date`, `expires`, and `approval_status`; stale-language blocking | Read-only |
| 2 | **Approved-source retrieval (policies)** | Firm policies and regulatory positions cited by answers (RI policy, infosec, valuation, etc.) | Read-only |
| 3 | **Performance / risk data** | Returns, attribution, exposures, AUM figures cited in answers (each with an `as_of` and owner) | Read-only |
| 4 | **Prior answers** | Previously submitted, still-owned answers reusable when no library entry exists | Read-only |
| 5 | **Permission / approval broker** | Recorded content-owner, product, and compliance approvals; outstanding-approval state | Read-only |
| 6 | **Controlled templates & registers** | The DDQ response template and required-disclosure register (versioned) | Read-only |

The controlled content library is the system of record for what an approved answer *is*;
policies and performance/risk data are the evidencing sources a library answer cites. A
question with no approved, in-date answer is **unsupported** and routed to a content owner —
never answered from unapproved content and never fabricated. This skill reads only; it does
not write answers back, approve content, or deliver the response.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `library:A-PERF-1YR@2026-06-30`,
`perf:D-PERF-1@2026-06-30`, `prior:P-FIRM-HISTORY@2026-01-15`,
`policy:disclosure-standard`, `approvals:AP-C1@2026-07-15`. Every `drafted` or `stale`
answer carries its content-library (or prior-answer) citation plus any data-point citation; a
question with no citable approved source is an open item, never an assumed answer.

## Freshness / effective dates

- Each library/prior answer carries `effective_date` and optional `expires`, and each data
  point carries `as_of` and optional `expires`. Content or data past its `expires` relative to
  `as_of_date` is marked **stale** / **data-gap**, drafted-if-content-exists-but-flagged, and
  listed as an open item for the owner to refresh — it is still cited, never silently used as
  current.
- `approval_status` gates use: only `approved` content is drafted from. `draft` / `in-review`
  / `expired` content becomes an **unapproved-source** open item routed to the owner.
- The content library, the required-disclosure register, and the response template are
  **versioned contracts**; the versions are recorded on the manifest (`config_version`,
  `template_version`) for reproducibility and review.

## Least-privilege operations (deployment)

- `content.search(topic|keywords)` / `content.get(answer_id)` → approved answers + metadata — read-only.
- `policy.get(policy_id, version)` → cited policy text — read-only.
- `perf.get(data_id)` / `risk.get(data_id)` → figures with `as_of` + owner — read-only.
- `prior.get(answer_id)` → reusable prior answers — read-only.
- `approvals.read(questionnaire_id)` → recorded/outstanding approvals — read-only.
No mutation from this skill. The drafted response is a **draft**; content approval, compliance
review, and any external delivery are separate, human-approved steps via the approval broker.
