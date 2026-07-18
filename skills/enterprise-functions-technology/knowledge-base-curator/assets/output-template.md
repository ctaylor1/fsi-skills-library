# Knowledge Base Curation Worklist — DRAFT

> DRAFT knowledge-base curation worklist for human review; nothing has been published,
> updated, merged, retired, or deleted, and no change has been approved by this skill.

**Pack ID:** `{pack_id}` · **Scope:** {scope} · **As of:** {as_of}
**Config:** `{config_version}` · **Classification:** {classification} · **Curator:** {curator}

The worklist MUST contain every section below (the output validator enforces presence).
Each finding MUST carry a citation `{system}:{ref}@{as_of}` to the KB record and/or an
approved source-of-truth. Every recommended change (action ≠ `none`) MUST appear in the
Approvals register (§7) as `pending` until a named human owner approves it.

---

## 1. Cover
Scope, curation `as_of`, `config_version`, classification, and the curator/knowledge-manager
owner. No content claims here.

## 2. Summary
Counts by finding type (`conflicting`, `retire`, `duplicate`, `stale`, `ownerless`,
`current`, `missing`) and by severity (High / Medium / Low).

## 3. Findings
One row per article:

| Article | Finding | Severity | Recommended action | Rationale (cited) | Proposal |
| ------- | ------- | -------- | ------------------ | ----------------- | -------- |

- Finding is one of `conflicting` / `retire` / `duplicate` / `stale` / `ownerless` /
  `current`. The skill never sets `published` / `merged` / `retired` / `deleted` / `applied`.
- Every non-`current` finding has a proposal (proposed review date, canonical merge target,
  proposed owner role, or retirement reason) — a **draft**, not an applied change.

## 4. Retirement recommendations
The `retire` subset (expired or superseded articles): article, reason, and the
records/retention owner who must action it. Recommendation only.

## 5. Coverage gaps
Required topics with no active article: `topic_id`, title, proposed owner role, `create`
recommendation.

## 6. Sources (approved-source register)
Every source used: `source_id`, system, ref, `as_of`, owner. This is the citation backbone; a
finding whose supporting `source_id` is not here is an **unsupported assertion** and blocks
the pack.

## 7. Approvals register
Every recommended change, with approver role, approver identity, status
(`pending` / `obtained`), and date. Required approvals must be **recorded** here; the skill
sets `pending` — a human sets `obtained` with their identity.

---

## Completeness and sourcing footer (machine-checked)
- **Completeness:** required sections present vs. missing.
- **Unsupported claims:** MUST be empty.
- **Standing note:** the DRAFT banner above MUST be present verbatim.
