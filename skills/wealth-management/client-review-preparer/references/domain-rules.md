# Domain Rules — client-review-preparer

Orientation references: SEC Regulation Best Interest (Reg BI) and Form CRS, IA fiduciary
standard, FINRA supervision and communications rules, and firm advisory/WSP standards. The
firm's review policy, disclosure config, and freshness thresholds take precedence and are
**versioned contracts**. This skill prepares a review; it makes no recommendation and no
suitability decision.

## Assembly status precedence (first blocking condition wins)

| Order | Status | Condition |
| ----- | ------ | --------- |
| 1 | `needs-data` | Missing `household_name`, `advisor`, `accounts`, or `goals` |
| 2 | `unresolved-entity` | `entity_resolved` is false — identity is never guessed |
| 3 | `account-identity-gap` | A holding/performance/account references an unknown account, or an account lacks `type`/`registration` |
| 4 | `unsupported-content` | A content item (or account) cites a `source_id` not in the inventory |
| 5 | `stale-source` | A cited *critical* source (holdings/performance) is older than `critical_freshness_days` and unacknowledged |
| 6 | `tieout-break` | Holdings do not sum to the reported account value, or accounts do not sum to the household total |
| 7 | `disclosure-gap` | A required disclosure for the review type is missing |
| — | `draft-review` | All invariants hold → packageable |

## Tie-out rules (deterministic)

- **Per-account:** sum of holding `market_value` for an account equals that account's
  `reported_value` (rounded to 2 dp).
- **Household roll-up:** the sum of account `reported_value` equals `total_value`; if
  `household_reported_value` is provided it must equal that sum.
- Values are **reported, never projected**; a mismatch fails closed.

## Disclosure coverage (default config, overridable per deployment)

| Review type | Required disclosures |
| ----------- | -------------------- |
| `annual` | `FORM-CRS`, `REG-BI-DISCLOSURE`, `FEE-SCHEDULE`, `PERFORMANCE-DISCLOSURE` |
| `semiannual` | `FEE-SCHEDULE`, `PERFORMANCE-DISCLOSURE` |
| `ad-hoc` | `PERFORMANCE-DISCLOSURE` |

A packageable pack contains every required disclosure for its review type, each cited. The
set is deployment config (`disclosure_config`), not the agent's judgment.

## Action completeness

Every prior/open action is carried into the pack; an `open` action past its `due_date`
(relative to `as_of_date`) is flagged `overdue`. Actions are surfaced for the advisor; the
skill closes none of them.

## Routing flags (surfaced for a human — never actioned here)

| Trigger | Route (surfaced) |
| ------- | ---------------- |
| `flags.recommendation_contemplated` | `suitability-reg-bi-reviewer` before any recommendation; advisor + supervisory approval |
| `flags.drift_flag` | `portfolio-rebalancing-assistant` — any trade requires advisor and client authorization |
| `flags.senior_investor` | `senior-investor-protection-screener` for trained human review |
| `life_events` present | `financial-goal-progress-analyzer` to re-check goal progress |

## Hard boundaries (fail closed)

- No **investment recommendation**, **suitability determination**, or **trade** — the pack
  surfaces sourced discussion points and options-to-consider, never a recommendation.
- No **case closure**, **filing**, or **system-of-record / CRM write**.
- No **send, submit, or delivery** of the pack — drafting only.
- No **personalized investment, legal, or tax advice**.
- Nothing enters the pack that a **cited source** does not support; identity is never guessed.

## Review pack — required contents

Household/account identity; portfolio summary with per-account and household tie-out;
performance (cited); goals; plan items; prior meeting notes; service history; life events;
open actions (with overdue flags); a discussion agenda; the required disclosures; surfaced
routing flags; a citations index; `reviewer_signoff_required: true`; and a recorded
`approvals` block. Every listed item carries a citation.
