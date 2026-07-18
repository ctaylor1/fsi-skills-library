# Source Map — policy-document-explainer

Every statement in the explanation must cite one of the sources below, ranked. See the
shared platform services in [`docs/SHARED-SERVICES.md`](../../../../docs/SHARED-SERVICES.md).

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Policy-administration **system of record** | In-force form + endorsements, declarations, effective/expiration dates, limits | Read-only |
| 2 | Executed **policy document / declarations page** for the period | Section/clause text, page-level citations, actual dollar amounts | Read-only (document-intelligence) |
| 3 | **Filed/approved form & endorsement library** | Standard wording of forms the document references (e.g. HO-3, endorsements) | Read-only (approved-source retrieval) |
| 4 | User-provided document/file | Only when 1–3 unavailable; must be labeled as unverified | Read-only |

Never let a user assertion override the policy of record. If sources conflict, present both
with citations and stop for human review. Explain the **document as written** — do not
resolve ambiguous wording by inferring intent.

## Citation format

Each element carries a citation of the form `{system}:{ref}@{as_of}` — e.g.
`polad:policy=****7788;form=HO-3(07/2021)@2026-01-01`, `dec:page1;CovA@2026-01-01`, or
`form:HO-3;SectionI.Exclusions.para3@2026-01-01`. The machine-readable output stores the
citation per element; the narrative references them inline where a statement is made.

- Cite the **declarations page** for dollar amounts (limits, deductibles, premium).
- Cite the **form / endorsement** for wording (coverage grants, exclusions, conditions,
  definitions).

## Freshness / effective dates

- Every explanation states a single **form edition** and **effective/expiration window**;
  reject an expiration date earlier than the effective date.
- A policy can be reissued or amended mid-term; explain the version in force for the stated
  period and flag any mid-term endorsement that changes it.
- A referenced endorsement or form that is not present is a **data gap** — do not describe its
  contents from memory.

## Least-privilege operations (deployment)

- `policy.read(policy_id, as_of)` → in-force form, endorsements, declarations (bounded).
- `docintel.extract(document_id)` → sections with page/clause references.
- `forms.retrieve(form_edition | endorsement_id)` → filed/approved wording.
All read-only, deterministic schemas, durable `explanation_id`, below the fixed timeout.
