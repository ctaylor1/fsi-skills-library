---
name: knowledge-base-curator
description: >-
  Curate an enterprise knowledge base: scan an article inventory against its authoritative
  sources and a required-topic registry to identify STALE, DUPLICATE, CONFLICTING, MISSING,
  and OWNERLESS knowledge, then DRAFT the recommended updates, merges, ownership actions,
  metadata fixes, and retirement recommendations as a reviewable curation worklist with
  citations and a human-approval register. Use when a knowledge manager, operations, or
  technology owner asks to audit or clean up a KB, find stale, duplicate, or conflicting
  articles, flag coverage gaps, propose review dates and owners, or prepare a
  retirement/consolidation plan. HARD BOUNDARY: draft-only — it never publishes, edits,
  merges, retires, or deletes an article, never changes a system of record, and never sends
  or submits anything; every recommended change is a proposal a named human content owner
  must approve. Substantive policy/procedure rewrites route to policy-document-assistant;
  answer composition routes to knowledge-answer-composer.
license: MIT
compatibility: Amazon Quick Desktop; requires knowledge-base/content-management, controlled-content-library, document-intelligence, approved-source-retrieval, and permission/approval-broker MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Enterprise Functions & Technology"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Enterprise Functions & Technology"
  aws-fsi-primary-user: "Knowledge manager / operations / technology"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Knowledge Base Curator

## Purpose and outcome
Take a knowledge-base article inventory (with its metadata, authoritative-source links, and a
required-topic registry) and produce a **DRAFT curation worklist**: every article classified
as `stale`, `duplicate`, `conflicting`, `ownerless`, `retire`, or `current`, plus the
`missing`-knowledge gaps for required topics that no article covers. Each finding carries a
recommended action, a cited rationale, a draft-only proposal (updated review date, canonical
merge target, ownership role, retirement reason), and an entry in a **human-approval
register**. The outcome is a reviewable, source-mapped cleanup plan for a knowledge manager —
not a single content change is applied. Publishing, merging, retiring, or deleting stays with
the named content owner.

## Use when
- "Audit / clean up our knowledge base; what's stale or out of date?"
- "Find duplicate or conflicting articles on the same topic."
- "Which required topics have no article (coverage gaps)?"
- "These articles have no owner / a stale review date — propose fixes."
- "Draft a retirement or consolidation plan for expired/superseded content."

## Do not use
- **Rewriting the substantive body of a policy or procedure document** → `policy-document-assistant`.
- **Composing an answer to a customer/agent question from the KB** → `knowledge-answer-composer`.
- **Analyzing a policy/procedure control gap** (not just a knowledge gap) → `policy-procedure-gap-analyzer`.
- **Assessing the impact of a regulatory change** that made content stale → `regulatory-change-impact-analyzer`.
- Any request to **publish, merge, retire, or delete** an article, or to **write the KB /
  CMS system of record** → refuse; this skill drafts only and routes the change to the human owner.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a durable `pack_id`
and per-finding proposals; it never applies a change. Downstream substantive work
(policy rewrites, answer composition, gap/impact analysis) routes to the named catalog
skills. Applying, publishing, merging, retiring, or deleting content is a **human /
operations action** performed by the content owner or records/retention owner in the CMS —
there is no skill that executes it.

## Inputs and prerequisites
- A KB export: `articles[]` with `article_id`, `title`, `status`, `owner`, `last_reviewed`,
  `review_period_days`, optional `expiry_date`, `tags`, `content_hash`, `topic_id`,
  `source_ids[]`, `supersedes[]`, and optional `asserts{}` (key facts). Plus the approved
  `sources[]` register (source-of-truth links with `as_of`), the `required_topics[]` registry,
  the curation `as_of` date, and the `config_version`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the KB/CMS, the controlled-content library (owners, effective/expiry dates),
  and approved-source retrieval. No write access is required or used.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **authoritative source-of-truth**
(policy portal, rate card, regulatory register) outranks the KB article; a KB article that
disagrees with its source-of-truth is `conflicting`. The controlled-content library is the
system of record for owner, effective, and expiry metadata. Cite every finding
`{system}:{ref}@{as_of}`. Config/topic registry and thresholds are **versioned contracts**.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm each `source_id` resolves to the
   approved register; flag articles missing `last_reviewed`/`owner` as data gaps.
2. **Classify (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): computes each
   article's finding by documented precedence (`conflicting` > `retire` > `duplicate` >
   `stale` > `ownerless` > `current`), assigns a severity, and attaches a draft proposal.
   See [references/domain-rules.md](references/domain-rules.md).
3. **Detect coverage gaps** — required topics with no active (non-retired) article become
   `missing` findings with a `create` recommendation and proposed owner role.
4. **Build the approvals register** — every finding whose action is not `none` is recorded as
   `pending`, with the approver role; no change is presented as applied or approved.
5. **Assemble the draft pack** — populate the template sections
   ([assets/output-template.md](assets/output-template.md)), attach citations, list any
   unsupported claims, and add the standing DRAFT note.
6. **Never apply** — no publish, merge, retire, delete, or system-of-record write.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check enforces: `status` is `draft`; required template sections present
(cover/summary/findings non-empty; retirements/gaps present); every finding cites its
evidence; **no unsupported claims**; every recommended change appears in the approvals
register with an approver role and status; no finding is presented in a done-state
(`published`/`merged`/`retired`/`deleted`/`applied`); no send/submit/publish/delete
language; standing note present. Fail closed on any miss.

## Human approval
`external-delivery`. This skill produces an internal draft worklist that may be reviewer-
sampled for internal use, but **any change to the KB — publishing an update, merging a
duplicate, assigning an owner, retiring or deleting an article — and any external delivery of
the pack requires a named human content owner (or records/retention owner) to approve**. The
skill proposes and records; the human decides and acts.

## Failure handling
- **Unresolvable source_id** → record the finding as an **unsupported claim**; do not cite a
  source that is not in the approved register.
- **Missing `last_reviewed`/`owner`** → do not guess; flag `stale`/`ownerless` with a
  data-gap note so a human supplies the value.
- **Ambiguous duplicate** (partial overlap, different `content_hash`) → link as a candidate to
  the canonical for human confirmation; never auto-merge or drop.
- **Conflicting sources** → cite both the article and the source-of-truth; recommend
  `reconcile`; do not pick a winner.
- **Tool timeout / partial export** → return the partial worklist with an explicit incomplete
  flag; assume no retry.

## Output contract
1. **Cover** — KB scope, `as_of`, `config_version`, classification, curator/owner.
2. **Summary** — counts by finding type and severity.
3. **Findings** — per article: `article_id`, finding, severity, recommended action, cited
   rationale, draft proposal.
4. **Retirement recommendations** — the `retire` subset (expired/superseded); recommendation
   only, routed to the records/retention owner.
5. **Coverage gaps** — required topics with no active article (`missing` → `create`).
6. **Sources** — approved-source register (the citation backbone).
7. **Approvals register** — every recommended change with approver role and `pending`/`obtained` status.
8. **Machine-readable** — the pack JSON keyed by `pack_id`.
9. **Standing note** — "DRAFT knowledge-base curation worklist for human review; nothing has
   been published, updated, merged, retired, or deleted, and no change has been approved by
   this skill." See [references/controls.md](references/controls.md).

## Privacy and records
**Confidential.** Minimize content copied into the pack — cite the KB record and quote only
what evidences a finding. Do not surface restricted article bodies; reference them by
`article_id` and location. Retain the curation pack, citations, and config/registry versions
per records policy; log the curator identity and every read. Deletion/retirement of source
content is a records action for the retention owner, never performed here.

## Gotchas
- **Curation is not editing.** A `review-update` proposal is a draft; the article body is not
  changed and nothing is published until the owner approves.
- **Dedup links, never deletes.** A `duplicate` points to its canonical article; the canonical
  is kept and the duplicate is proposed for merge, not silently removed.
- **Conflict ≠ staleness.** An article can be recently reviewed yet still `conflicting` with
  its source-of-truth; the source-of-truth outranks the article.
- **Retire is a recommendation.** Expired/superseded articles are flagged for retirement with
  a reason; the records/retention owner performs the retirement.
- **Thresholds and the topic registry are versioned.** Record the `config_version` on every
  pack so a finding is reproducible and reviewable.
