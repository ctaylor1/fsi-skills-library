# Source Map — knowledge-base-curator

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Authoritative source-of-truth** (policy portal, rate card, regulatory register) | Ground truth for facts an article asserts; drives `conflicting` and source-driven `stale` | Read-only |
| 2 | **Controlled-content library** | System of record for owner, effective/expiry dates, status | Read-only |
| 3 | **Knowledge base / CMS** | Article inventory, `content_hash`, `topic_id`, `supersedes`, last-reviewed | Read-only |
| 4 | **Required-topic registry** (versioned) | Expected coverage; drives `missing` gaps | Read-only |
| 5 | **Curation config** (thresholds, high-risk tags) (versioned) | Staleness period, severity bumps | Read-only |

A KB article never outranks its cited source-of-truth. When the article and the
source-of-truth disagree, the finding is `conflicting` and both are cited — the skill does
not pick a winner.

## Citation format

`{system}:{ref}@{as_of}` — e.g. `kb:KB-100@2024-01-10`, `policy-portal:POL-KYC-v9@2026-06-01`,
`content-lib:KB-103;expiry@2026-06-30`, `config:kb-curation@v2026.07`.

## Freshness / effective dates

- `last_reviewed` is compared to the curation `as_of` against the effective review period.
- A cited source-of-truth whose `as_of` is **newer** than the article's `last_reviewed`
  forces `stale` (the source changed since the article was last reviewed).
- Thresholds, the required-topic registry, and the high-risk-tag list are **versioned**; the
  `config_version` is recorded on every pack for reproducibility.

## Least-privilege operations (deployment)

- `kb.export(scope)`, `kb.article.read(article_id)` — read-only.
- `content_lib.metadata(article_id)` → owner, effective, expiry, status — read-only.
- `sources.resolve(source_id)` → source-of-truth ref + `as_of` — read-only.
- `topics.registry(version)`, `config.get('kb-curation', version)` — read-only.

No mutation from this skill. Applying an update, merging a duplicate, assigning an owner, or
retiring/deleting an article is performed by the human content owner (or records/retention
owner) in the CMS — this skill only drafts and records the proposal via the approval broker.
