# Adjacent-Skill Handoffs — portfolio-holdings-summarizer

This skill produces a **normalized holdings snapshot** and stops. It does not analyze,
advise, or act. Downstream skills consume the snapshot via its durable `snapshot_id`.

## Downstream (this skill hands off to)

| Downstream skill | When to route | Handoff artifact |
| ---------------- | ------------- | ---------------- |
| `portfolio-risk-diversification-check` | User asks whether/how the portfolio is concentrated, diversified, or exposed (educational, non-advice) | `snapshot_id` + normalized holdings table |
| `suitability-reg-bi-reviewer` | Any suitability / Reg BI question about a recommendation | `snapshot_id` + account context |
| `performance-attribution-builder` | User asks about return/attribution over time | `snapshot_id` + period |
| `client-review-preparer` | Associate assembling a client-review packet | `snapshot_id` |
| `portfolio-proposal-comparator` | Comparing this portfolio to a proposed one | `snapshot_id` |

## Upstream (may call this skill)

`client-review-preparer`, `portfolio-risk-diversification-check`, and
`portfolio-proposal-comparator` may request a fresh snapshot from this skill rather than
re-normalizing holdings themselves.

## Duplicate-execution prevention

- This skill **only summarizes**; it must not perform diversification, suitability,
  performance, or advice work — those belong to the skills above.
- Downstream skills must **not** re-normalize holdings when a valid `snapshot_id` for the
  same account+as-of already exists; they reuse it.
