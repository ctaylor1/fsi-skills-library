# Source Map — composite-account-membership-checker

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Composite policy / GIPS manual** (versioned rule library) | Inclusion/exclusion criteria, minimum-asset, inclusion-lag, discretion, significant-cash-flow, and completeness rules | Read-only |
| 2 | **Composite register** (system of record for composite definitions and current membership) | The asserted membership each portfolio is checked against | Read-only |
| 3 | **Portfolio/account master + PMS/accounting book of record** | Strategy/mandate, discretion flag, fee-paying flag, under-management and termination dates, market value | Read-only |
| 4 | **Cash-flow / transaction records** | Significant external cash flow magnitude for the SCF policy | Read-only |
| 5 | **Client agreement / IMA metadata** (entity resolution) | Discretion determination inputs and mandate mapping | Read-only |

The **composite policy** governs *what the rule is*; the **composite register** and **book of
record** govern *what the data says*. When the rule and the data disagree, that disagreement is
the exception — cite both sides; never overwrite either.

## Citation format

- Data evidence: `pms:{ref};field={field}@{as_of}` — e.g. `pms:portfolio=P-1002;field=market_value@as_of`.
- Rule citation: every exception carries `rule = {rule_id, rule_version, effective_date}`, e.g.
  `R-INCL-GEQ @ 2026.1 (effective 2026-01-01)`. An exception is never emitted without both a
  data citation and a rule citation.

## Freshness / effective dates

- The **ruleset is a versioned contract**: `ruleset_version` + `ruleset_effective_date` are
  recorded on every queue, and each composite carries its own `rule_version` + `effective_date`.
  A membership check is evaluated against the rule version **in effect for the `as_of` date**;
  applying a newer rule retroactively is a methodology change and is out of scope.
- `as_of` fixes the measurement date. "Last full period" for exclusion timing and the
  inclusion-lag window are both computed relative to `as_of` (see domain-rules.md).
- Re-running with the same inputs and the same `ruleset_version` reproduces the queue exactly.

## Durable identifiers

- `review_id` — durable job id for the whole check: `camc-{firm_id}-{as_of}-0001`.
- `case_ref` — durable per-exception id: `{review_id}-E{NNN}`. Downstream adjudication and any
  authorized correction reference the `case_ref`; the queue is idempotent for a fixed input set.

## Least-privilege operations (deployment)

- `policy.get('composite', ruleset_version)` → versioned inclusion ruleset.
- `composites.definitions()` / `composites.membership(as_of)` → definitions + asserted membership.
- `portfolios.master(as_of)` → strategy, discretion, fee-paying, dates, market value.
- `cashflows.significant(portfolio_id, period)` → SCF magnitude.

All read-only, deterministic, bounded, durable `review_id`, below the fixed timeout; page long
account universes as resumable stages. No write, submission, or membership-mutation operation is
bound — those are prohibited for this skill (see controls.md).
