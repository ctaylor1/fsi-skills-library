# Settlement reconciliation contract

## Scope and input

mode is reconcile-settlement (default for migrated callers) or explain-payout. For report-only
mode see payout-explanation.md. Reconciliation requires as_of, period.start/end,
config_version and at least one populated list in sources; omitted source lists are gaps.
Each source record requires legal_entity_id, account_id, currency, settlement_cycle,
record_id, match_key and source_ref. Never substitute a default entity, account or cycle.

| Source | Date | Amount fields |
| --- | --- | --- |
| network | settlement_date | gross |
| processor | settlement_date | gross, fees, reserve, refunds, chargebacks, adjustments, net |
| bank_cash | value_date | amount |
| ledger | post_date | net |

Amounts are finite decimals, preferably JSON strings. Missing/null fields remain unknown.
Fees, reserve, refunds and chargebacks are positive deductions; adjustments are signed.
The net calculation is gross - fees - reserve - refunds - chargebacks + adjustments and
runs only when every component is explicit, including zero. Normalization is a caller
responsibility; adapters must not insert zeros for unobserved components.

## Matching and checks

Group by legal_entity_id/account_id/currency/settlement_cycle/match_key. Duplicate records
within one source or duplicated record identities quarantine the entire group. Retain all
citations; no first-row winner, blind summation or proposed reversal.

Detect reused source identities before grouping. A record ID is unique within the legal
entity/account/source namespace across batches, currencies and cycles. A source_ref is an
immutable source-row locator, unique within the source across all declared partitions.
Reusing that row under a new match key, amount, currency, cycle or local ID quarantines
every affected group. Independent namespaces can share local IDs with distinct row locators.
Many-to-many allocation requires an explicit separate contract and is not inferred here.

Evaluate network gross vs processor gross; calculated processor net vs reported net;
processor net vs bank cash; processor net vs ledger; bank cash vs ledger; actual fees and
reserve vs their independently scoped schedule. Every check has expected, observed,
observed-minus-expected, tolerance and status. Missing support yields not_evaluable.
Each upstream difference remains visible when downstream amounts happen to agree.

Tolerance config keys: amount_tolerance_abs, fee_tolerance_abs, reserve_tolerance_abs,
cash_tolerance_abs, net_calc_tolerance_abs. Each defaults to 0.01 and must be nonnegative.
Use the approved precision/tolerance for the source contract and currency; defaults are
examples, not a universal materiality rule.

## Effective fee and reserve schedule

Every schedule row requires legal_entity_id/account_id/currency/scheme/version/source_ref,
effective_from and optional effective_to. Select exactly one covering the processor
settlement_date and full scope. Missing or overlapping rows are not evaluable.

Expected fee = gross * rate_bps / 10000; expected reserve = gross * reserve_bps / 10000.
Neither missing rate means zero. Round HALF_UP to config.currency_minor_units[currency],
which must explicitly supply a precision integer 0..8. Missing precision prevents the
schedule check. This simple bps formula is appropriate only when the contract actually uses
it; tiered, fixed, capped or transaction-specific pricing needs a separately normalized
expected-fee calculation and a future explicit extension.

## Cash timing

Missing cash is pending only with a cited expected_funding_date strictly after as_of.
Each such date needs funding_due_source_ref. Conflicting dates never imply pending cash.
When the date has arrived, or no valid date is supplied, surface MISSING_IN_BANK and retain
unknown cash. No built-in period-end lag, holiday calendar or universal rail timetable.
The prior cash_settlement_lag_days option is rejected.

## Output interpretation

Issue types include GROSS_MISMATCH, NET_CALC_MISMATCH, NET_CASH_MISMATCH,
LEDGER_SETTLEMENT_MISMATCH, LEDGER_CASH_MISMATCH, FEE_VARIANCE, RESERVE_VARIANCE,
MISSING_IN_BANK, MISSING_IN_LEDGER, MISSING_IN_SETTLEMENT, MISSING_NETWORK,
MISSING_PROCESSOR, UNVALUED_FIELD and AMBIGUOUS_DUPLICATE. PENDING_FUNDING is a separate item.

Partition totals distinguish known_subtotal from complete total and disclose missing or
quarantined group counts. No cross-partition monetary total is emitted. Do not add overlapping
gross, fee, cash and ledger differences into a purported loss. A group matches only when
every required check is evaluable and within tolerance, with no issue or pending item.

No corrections or debit/credit accounts are generated. Output validation recomputes the
complete contract, including source lineage, checks, coverage and handoffs. Pass --input
to bind the original supplied file; internal consistency alone does not authenticate evidence.
