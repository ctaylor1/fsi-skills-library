# Adjacent-Skill Handoffs — prospectus-plain-language-breakdown

This skill produces a **plain-language, page-cited breakdown** of one offering document and
stops. It does not advise, judge suitability, benchmark fees, draft marketing, or act.
Downstream skills consume the breakdown via its durable `breakdown_id`.

## Downstream (this skill hands off to)

| Downstream skill | When to route | Handoff artifact |
| ---------------- | ------------- | ---------------- |
| `suitability-reg-bi-reviewer` | User asks whether the offering is suitable / in their best interest, or wants a Reg BI judgment on a recommendation | `breakdown_id` + client/account context |
| `portfolio-risk-diversification-check` | User wants a personalized risk/diversification view given their portfolio (educational, non-advice) | `breakdown_id` + `snapshot_id` |
| `fee-and-charge-reviewer` | User wants a fee **reasonableness / benchmarking** conclusion, not just what the fees are | `breakdown_id` + fee lines with page cites |
| `fund-fact-sheet-builder` / `fund-commentary-drafter` | User wants a marketing fact sheet or commentary drafted from the document (approval-gated) | `breakdown_id` |
| `senior-investor-protection-screener` | The reader is a senior/vulnerable investor and protection screening applies | `breakdown_id` + client context |

## Upstream (may call this skill)

`suitability-reg-bi-reviewer`, `client-review-preparer`, and `relationship-manager-client-briefer`
may request a plain-language breakdown of the offering document from this skill rather than
re-reading the prospectus themselves.

## Sibling explainers (route by document type, do not overlap)

- `trade-confirmation-explainer` — explains a trade confirmation, not a prospectus.
- `corporate-action-interpreter` — explains a corporate-action notice, not a prospectus.

## Duplicate-execution prevention

- This skill **only explains** the document; it must not perform suitability, fee
  benchmarking, marketing drafting, or advice — those belong to the skills above.
- Downstream skills must **not** re-read and re-summarize the prospectus when a valid
  `breakdown_id` for the same document + effective date already exists; they reuse it.
