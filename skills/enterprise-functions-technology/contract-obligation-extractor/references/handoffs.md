# Adjacent-Skill Handoffs — contract-obligation-extractor

Obligation extraction (this skill) is a **separate control activity** from legal
interpretation, ongoing obligation monitoring, and external delivery — each has different
entitlements, accountability, and downstream reliance. This skill emits a durable
`register_id` and a clause-cited draft manifest; it does not advise, monitor, certify, or
deliver.

## Downstream (this skill hands off to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `covenant-compliance-monitor` | The contract carries financial covenants or thresholds that need ongoing monitoring after extraction | `register_id` + the covenant/key-date entries with citations |
| `third-party-risk-assessor` | The counterparty needs a vendor / third-party risk assessment driven by the data terms and dependencies | `register_id` + data-term and dependency entries with citations |
| `meeting-action-tracker` | Extracted obligations and key dates should become tracked action items and deadlines | `register_id` + obligations + key_dates |

## Upstream (feeds this skill)

| Upstream skill | Provides |
| -------------- | -------- |
| `procurement-sourcing-assistant` | The sourced / executed contract to extract obligations from |

The CLM / document-intelligence platform services produce the raw contract and clause
citations. This skill is **interactive** extraction (`aws-fsi-scheduled-agent: no`); a monitor
may populate a queue of contracts but must not extract, interpret, or deliver.

## Non-catalog handoffs (human / licensed)

- **Legal interpretation, enforceability opinions, breach determinations, or negotiation /
  redlining** → licensed legal counsel. No catalog skill provides legal advice, and this
  library's universal prohibitions bar it; the extractor characterizes and cites clauses only.
- **External delivery or execution** of the register or the contract → a human approves and
  delivers/executes via the approval broker; this skill never sends, submits, signs, or
  executes.

## Duplicate-execution prevention

- This skill **does not** interpret enforceability, monitor covenants, assess vendor risk, or
  track tasks — those belong to the named skills or to a human.
- Downstream skills consume this skill's `register_id`/manifest rather than re-extracting.
- A term conflict across clauses is left `conflict` for a human to reconcile, never resolved
  by picking one clause here.
