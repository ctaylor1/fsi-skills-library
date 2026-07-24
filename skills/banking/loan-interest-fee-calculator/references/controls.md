# Controls — loan-interest-fee-calculator

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `external-delivery` — required before the workbook or payoff quote is
  delivered to a borrower, participant, counterparty, or another system, or otherwise written
  to a system of record. Posting or approving any adjustment is out of scope entirely.

## Prohibited (fail closed)

- **No posting, booking, applying, waiving, reversal, crediting, refunding, or approval** of
  an adjustment to any account, ledger, or system of record — this is the **HARD BOUNDARY**.
  The workbook always carries `action_taken: "none"`.
- No **binding servicing decision** (fee waiver, interest correction, payoff acceptance,
  charge-off) — those are human/authorized-workflow outcomes.
- No **personalized financial, legal, or tax advice**.
- No **rate without an approved rate-table version**; no **assumption without provenance**.
- No formula, tolerance, materiality threshold, or day-count convention **bent to reach a
  wanted figure**.
- No **participation allocation** whose parts do not sum exactly to the shared total; no
  **amortization schedule** that does not end at a zero balance.

## Required output screens (`scripts/validate_output.py`)

- Every section ties out, **re-derived independently** (not trusted from the workbook):
  interest from `principal * rate * year_fraction(day_count)`; fees from the basis;
  amortization interest/principal/payment and a zero ending balance; settlement from its
  signed components; participation allocations summing exactly to the shared total.
- **Variance report** math is consistent (`variance = computed - book`; `status`/`material`
  flags correct).
- **Reconciliation** to every stated approved-engine total (`variance = recomputed -
  approved`; `status` correct); reconciliation present.
- Every `assumptions_register` entry has a non-empty `provenance` **and** `citation`.
- `calc_id`, `inputs_hash`, and `config_version` present (reproducibility).
- **Tier boundary:** `action_taken == "none"`, no truthy posting/approval flag, and no
  posting/approval or personalized-advice language in the author narrative (regex screen).
- Standing disclaimer present.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Loan data embeds borrower identity, balances,
  and account numbers. Treat the workbook, its inputs, `case_id`, and `calc_id` as
  need-to-know; de-identify borrower data in fixtures and examples.
- Retain the workbook, its assumptions register, `config_version`, and `rate_table_version`
  per records policy; log the read and any external-delivery approval.

## Reproducibility & change control

`inputs_hash` binds the workbook to the exact numeric inputs; `config_version` and
`rate_table_version` bind the formulas, tolerances, and rates. Re-running the same inputs and
versions reproduces the same `calc_id` and the same numbers. Changing an input changes the
hash — the audit trail shows what moved.

## Separation of duties

Recalculating and reporting (this skill) is separate from investigating a servicing
exception, from approving a correction, and from posting it to the system of record. The
workbook is a draft input to a human's judgment and to authorized-execution workflows, never
a substitute for either. Incomplete closing conditions and substantive servicing exceptions
route out (see [handoffs.md](handoffs.md)); this skill never closes a case or executes a
change.
