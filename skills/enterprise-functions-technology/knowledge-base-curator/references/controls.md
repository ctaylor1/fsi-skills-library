# Controls — knowledge-base-curator

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `external-delivery` — a named human content owner (or records/retention
  owner) must approve before any KB change (publish/update/merge/assign-owner/retire/delete)
  and before external delivery of the pack. Internal draft use may be reviewer-sampled.

## Prohibited (fail closed)

- **Publishing, editing, merging, retiring, or deleting** any article.
- **Writing the KB / CMS or controlled-content library** system of record.
- **Sending or submitting** the pack anywhere (draft-only).
- Presenting a finding in a **done-state** (`published`, `merged`, `retired`, `deleted`,
  `applied`) — the skill only proposes.
- **Unsupported assertions** — any finding whose rationale is not backed by a resolvable
  citation to the KB record and/or an approved source-of-truth.

## Finding states (this skill may set only these)

Per article: `conflicting` | `retire` | `duplicate` | `stale` | `ownerless` | `current`.
Per required topic: `missing`. Recommended actions: `reconcile` | `retire` | `merge` |
`review-update` | `assign-owner` | `create` | `none`. It may **not** set an article to
`published`, `merged`, `retired`, `deleted`, or `approved`.

## Required output screens (`scripts/validate_output.py`)

- `status` is `draft`.
- Template fidelity: `cover`, `summary`, `findings` present and non-empty; `retirements` and
  `gaps` present (may be empty).
- Every finding carries at least one citation; `unsupported_claims` is empty.
- Every recommended change (action ≠ `none`) appears in the approvals register with an
  `approver_role` and a `status`; an `obtained` approval names a human approver.
- No done-state on any finding; no send/submit/publish/delete language.
- Standing note present: "DRAFT knowledge-base curation worklist for human review; nothing
  has been published, updated, merged, retired, or deleted, and no change has been approved by
  this skill."

## Segregation of duties

Curation (this skill, drafting) is distinct from content ownership and from records
retirement. The same person/skill must not both draft the curation recommendation and approve
or apply the change in the CMS.

## Data classification, privacy, records

- **Confidential.** Minimize copied content; reference articles by `article_id` and location.
- Retain the curation pack, citations, and config/registry versions per records policy; log
  the curator identity and every read.
- Retirement/deletion of content is a records action for the retention owner, never performed
  here.
