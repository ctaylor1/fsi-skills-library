# Domain Rules — knowledge-base-curator

Orientation: enterprise knowledge-management hygiene (currency, non-duplication, single
source of truth, ownership, retention). The firm's knowledge-governance standard, its
**required-topic registry**, and the curation **config** (thresholds, high-risk tags) take
precedence and are versioned contracts. All rules below are deterministic and reproducible
from the recorded `config_version`.

## Finding precedence (per article; first match wins)

Evaluated top-down; the first condition that matches is the article's primary finding.

| # | Finding | Condition | Recommended action |
| - | ------- | --------- | ------------------ |
| 1 | `conflicting` | The article's `asserts{}` disagrees with its cited source-of-truth's `asserts{}`, **or** two active articles on the same `topic_id` assert different values | `reconcile` |
| 2 | `retire` | `expiry_date` is on/before the curation `as_of`, **or** the article is listed in another article's `supersedes[]` | `retire` |
| 3 | `duplicate` | The article shares a `content_hash` or normalized `title` with another active article and is **not** the canonical (canonical = lowest `article_id` in the group) | `merge` |
| 4 | `stale` | `as_of - last_reviewed` exceeds the effective review period, **or** a cited source-of-truth `as_of` is newer than `last_reviewed` | `review-update` |
| 5 | `ownerless` | `owner` is missing/empty | `assign-owner` |
| 6 | `current` | none of the above | `none` |

Articles that are `retire` (expired/superseded) are excluded from the "active" set used for
duplicate and conflict grouping — a superseded article is retired, not merged.

## Coverage gaps (per required topic)

A `required_topics[]` entry with `required: true` and **no active (non-retired) article**
covering its `topic_id` is a `missing` finding with a `create` recommendation and the
registry's `owner_role` as the proposed owner.

## Effective review period

`effective_review_period_days = article.review_period_days` if present, else
`policy.review_period_days`, else the top-level `review_period_days`, else 365.

## Severity mapping (deterministic)

| Finding | Base severity |
| ------- | ------------- |
| `conflicting` | High |
| `missing` (required) | High |
| `retire` | Medium |
| `duplicate` | Medium |
| `stale` | Medium |
| `ownerless` | Medium |
| `current` | Low |

**High-risk bump:** a `stale` finding on an article carrying any `policy.high_risk_tags` tag
(default `compliance`, `regulatory`, `privacy`) is raised to **High** — stale
regulatory/compliance/privacy content is a heightened risk.

## Approver-role mapping

| Recommended action | Approver role |
| ------------------ | ------------- |
| `reconcile` | Content owner (SME) |
| `review-update` | Content owner |
| `merge` | Content owner |
| `assign-owner` | Knowledge governance |
| `retire` | Records / retention owner |
| `create` | Required-topic `owner_role` (else Knowledge governance) |

## Hard boundaries (fail closed)

- No **publish, edit, merge, retire, or delete** — every change is a draft proposal.
- No **system-of-record write** (KB/CMS or controlled-content library).
- No **done-state** on a finding (`published`/`merged`/`retired`/`deleted`/`applied`).
- No **unsupported assertion** — every finding cites the KB record and/or an approved
  source-of-truth; a claim whose `source_id` does not resolve is recorded as unsupported.
- No **auto-merge** of duplicates; dedup links to the canonical for human confirmation.

## Draft proposal contents (per finding)

Durable `pack_id`; the finding and severity; the recommended action; a cited rationale
(`{system}:{ref}@{as_of}`); the draft proposal (proposed review date, canonical target,
proposed owner role, or retirement reason); and an approvals-register entry (`pending` by
default) naming the approver role.
