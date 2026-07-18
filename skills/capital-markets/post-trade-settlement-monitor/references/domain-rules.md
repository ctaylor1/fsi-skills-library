# Domain Rules — post-trade-settlement-monitor

Deterministic settlement-exception **alert rules** and how they map to a **severity band**
and a **suggested route**. Thresholds are configuration (versioned, owned by settlement
operations & compliance), not hard-coded judgments, and never tuned to a desk or
counterparty. Orientation references: CSDR Settlement Discipline Regime (cash penalties,
mandatory buy-in) and the accelerated **T+1** settlement cycle (US since May 2024); the
firm's settlement-operations standard and the deployment market calendar take precedence.

## Alert taxonomy

| Alert | Fires when (default config) | Evidence attached | Fixed severity |
| ----- | --------------------------- | ----------------- | -------------- |
| `unmatched_near_cutoff` | Status `unmatched`/`pending`, ISD ≤ today, and 0 ≤ (cutoff − as_of) ≤ `cutoff_warn_minutes` (default 60) | Instruction + status + cutoff | **High** |
| `cutoff_breach` | Status `unmatched`/`pending`, ISD ≤ today, and as_of is **past** the cutoff | Instruction + status + cutoff | **Critical** |
| `settlement_fail` | Status `failed`, or not settled and ≥ `fail_aging_bands[0]` (default 1) business days past ISD | Instruction + ISD + age | **Warning** |
| `fail_aging_high` | Fail aged ≥ `fail_aging_bands[1]` (default 3) business days | Age vs band | **High** |
| `fail_aging_critical` | Fail aged ≥ `fail_aging_bands[2]` (default 5) business days | Age vs band | **Critical** |
| `buyin_exposure` | Fail aged ≥ `buyin_window_days` (default 4) — CSDR mandatory buy-in exposure | Age vs buy-in window | **Critical** |
| `material_cash_impact` | Fail with \|cash_amount\| ≥ `cash_impact_material` (default 1,000,000) | Cash + materiality | **High** |
| `penalty_accrual` | Accrued CSDR penalty ≥ `penalty_accrual_material` (default 5,000) | Penalty + materiality | **Warning** |

Alerts are **additive and independent**; each instruction reports every alert that fired
with its own cited evidence. There is no opaque composite score. Business-day aging uses the
market calendar (stdlib fallback: Mon–Fri).

## Severity mapping (deterministic, documented)

An item's severity is the **maximum** over its fired alerts' fixed severities, ordered
`Info < Warning < High < Critical`. `validate_output.py` re-derives this from the alert-type
table and fails closed on any mismatch. Severity is a **triage priority for a human queue**;
it is not an at-fault or reportability determination and it never triggers an action.

## Suggested route (deterministic)

| Route (draft only) | Rule |
| ------------------ | ---- |
| settlement-fails & funding desk | any `buyin_exposure` or `material_cash_impact` fired |
| matching & affirmation ops | else any `cutoff_breach` or `unmatched_near_cutoff` fired |
| CSDR penalties analyst | else any `penalty_accrual` fired |
| settlement operations queue | otherwise |

The route is a **drafted escalation target** for the reviewer, not an instruction that is
executed.

## Deduplication & freshness

- `dedup_key = "{instruction_id}:{alert_type}"`. An alert whose key is already in the open
  queue is marked `duplicate` (suppressed from re-paging); a genuinely new escalation (e.g.,
  a fail that ages into a higher band) is a **new** key and is raised.
- A row is `stale` when `as_of − source_as_of > max_source_staleness_minutes` (default 30).
  Stale items are still surfaced and flagged for re-pull; staleness never suppresses an alert.

## Hard boundaries (fail closed)

- Never **act**: match, affirm, cancel, amend, settle, release, initiate/execute a buy-in,
  dispute a penalty, contact a counterparty/custodian/client, or write any book of record.
- Never **decide**: at-fault, reportability, penalty liability, or whether to buy in — those
  are human/authorized-system determinations.
- Never **close or suppress** an exception outside the deterministic dedup logic.
- Never tune thresholds to a desk or counterparty; use only the versioned config.
