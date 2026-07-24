# Domain Rules — composite-account-membership-checker

How the firm's approved, versioned composite-inclusion rules are applied to account data to
produce **membership exceptions**. Rules are configuration owned by the performance/GIPS policy
team — a **versioned contract**, never hard-coded judgment and never tuned to a single account.
Orientation reference: the GIPS (Global Investment Performance Standards) composite-construction
principles; the **firm's approved composite policy and its `rule_version` take precedence** and
are the authoritative source for every threshold below.

## Versioning & effective dates

- Every queue records `ruleset_version` + `ruleset_effective_date`; every composite carries its
  own `rule_id`, `rule_version`, `effective_date`.
- A portfolio is evaluated against the rule version **in effect for the `as_of` date**. Applying a
  newer rule to an earlier period is a methodology change and is **out of scope** (see controls.md).
- `review_id` (`camc-{firm_id}-{as_of}-0001`) and per-exception `case_ref` (`{review_id}-E{NNN}`)
  are durable; re-running with identical inputs and ruleset reproduces the queue byte-for-byte.

## Inclusion / exclusion criteria (per composite, from config)

A portfolio is **expected in** a composite when **all** hold as of `as_of`:

| Criterion | Config field | Rule |
| --------- | ------------ | ---- |
| Strategy match | `strategy` | portfolio strategy equals the composite strategy |
| Discretion | `requires_discretionary` | if true, the portfolio must be discretionary |
| Minimum asset | `min_asset_value` | market value >= the composite minimum |
| Inclusion timing | `inclusion_lag_months` | whole months from `under_mgmt_date` to `as_of` >= the lag |
| Still active | `termination_date` | not terminated beyond its last full measurement period |

**Inclusion timing** — a portfolio joins after the documented lag (e.g. the first full month after
coming under management). Whole months are day-of-month aware: under management 2026-01-10 with a
1-month lag is a member from 2026-02 onward.

**Exclusion timing** — a terminated portfolio remains a member **through the last full measurement
period** it was under management, then is expected out. "Beyond last full period" is exact by month
key: `as_of` month strictly greater than the termination month.

**Significant cash flow (SCF)** — where `significant_cash_flow_pct` is set, a member whose external
cash flow meets/exceeds the threshold is flagged for the analyst to apply the documented
temporary-removal policy. This skill flags; it does not remove.

**Completeness** — every discretionary, fee-paying portfolio must belong to at least one composite.
One that matches no defined composite and is held in none is a composite-coverage gap.

## Exception taxonomy

| Exception type | Fires when | Severity |
| -------------- | ---------- | -------- |
| `improper_inclusion` | Assigned to a composite it fails (strategy / discretion / below minimum), or assigned to an undefined composite | high |
| `stale_inclusion` | Terminated portfolio still assigned beyond its last full measurement period | high |
| `unassigned_discretionary` | Discretionary fee-paying portfolio matching no composite and assigned to none | high |
| `missing_inclusion` | Meets all inclusion criteria (past lag, active) but is not assigned | medium |
| `early_inclusion` | Assigned before the inclusion lag has elapsed | medium |
| `significant_cash_flow_review` | Member breaches the SCF threshold; temporary-removal policy review | low |

Non-exception informational states: `compliant` (assigned exactly as expected) and
`pending_inclusion` (eligible but within the inclusion lag — not yet a member, not an error).

Each exception is **explainable and evidenced**: it names the criterion, the rule (`rule_id` +
`rule_version` + `effective_date`), the expected vs. asserted membership, and the specific data
rows (`pms:...@as_of`). There is no opaque score.

## Queue-priority mapping (deterministic, documented)

Escalators = `{improper_inclusion, stale_inclusion, unassigned_discretionary}`.

| Priority | Rule |
| -------- | ---- |
| **Elevated** | any escalator fired, OR >= 3 exceptions total |
| **Review** | 1–2 exceptions, none an escalator |
| **None** | no exceptions (queue empty) |

`queue_priority` is a **triage order for a human analyst**. It is not an adjudication and never
triggers a membership, methodology, or performance change. `validate_output.py` recomputes it from
the exception set and fails closed on any mismatch.

## Hard boundaries (fail closed)

- Never change a composite, its membership, the methodology, or reported performance; never close,
  resolve, file, or write a system of record. Emit evidence with `status: for_review` only.
- Never recompute returns/attribution — route to `performance-attribution-builder`.
- Never apply a rule version that was not in effect for the `as_of` date.
- Never infer thresholds; use only the versioned config. When strategy, discretion, dates, or the
  rule version are missing or ambiguous, stop and surface the gap rather than guessing.
