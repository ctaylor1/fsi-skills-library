# Transaction comparison contract

## Required input

Top level: as_of (ISO date), config_version, records (nonempty array), optional config.
Each record: legal_entity_id, account_id, currency (uppercase three-letter identifier),
settlement_cycle, record_id, txn_ref, source, date, source_ref, and amount (decimal string
or null). Omitted amount has the same unknown semantics as null. The source account IDs
must already map to one explicitly resolved reconciliation account; adapters cannot
silently use a shared default account. No entity/account resolver ships in this package.

Sources: gateway, processor, acquirer, bank, ledger, merchant, settlement, reserve, fee_batch.
level is transaction (default) or settlement. A settlement-level row routes independently.
Each row's amount must represent the documented comparison basis; capture gross, settlement
net and fees must not be silently relabeled as the same measure.

config.expected_sources defaults to gateway/processor/bank/ledger and must contain at least
two distinct supported sources. config.amount_tolerance defaults to decimal 0.01 and must
be finite and nonnegative. config.cash_rank is rejected: only bank establishes cash.

## Matching and arithmetic

Group by legal_entity_id/account_id/currency/settlement_cycle/level/txn_ref.
A duplicated source or record identity quarantines the entire ambiguous group; no first-row
selection, automatic aggregation or duplicate reversal. All source evidence is retained.

Index source identities before matching. A source record ID is unique within its legal
entity/account/source namespace across transaction references, levels, currencies and cycles.
A source_ref must identify an immutable source row; reusing that row reference within the
same source conflicts across all partitions, even if the caller changes the local record ID.
Quarantine every affected group and carry the conflict into settlement handoffs. Independent
rows in different namespaces may share local IDs, but must have distinct source row locators.
There is no implicit many-to-many allocation or automatic duplicate removal.

Compare every unambiguous, valued source pair using Decimal. Difference = right minus left;
absolute difference <= tolerance is within tolerance. Explicit zero remains evaluable.
Missing counterpart or value remains null and is not evaluable. A bank/ledger match does
not suppress differences involving gateway, merchant, acquirer or processor.

Raw source statuses are not comparable. Only caller-provided normalized_state labels are
compared. Adapters must document their common lifecycle mapping; the package does not
interpret unrelated processor statuses as equivalent.

Partition totals show a known_subtotal and known/missing group counts. The full total is null
unless every group in that partition supplies an unambiguous amount for the source. No total
crosses a partition boundary, includes routed settlements, or assumes absent evidence is zero.
Amounts serialize as strings; this avoids float rounding at the output boundary.

## Result interpretation

Issue types: AMBIGUOUS_DUPLICATE, MISSING_SOURCE, UNVALUED_RECORD, AMOUNT_MISMATCH,
STATE_MISMATCH. Preserve every issue with its scoped stable ID and evidence. Do not sum
pairwise differences as independent economic losses.

fully_evaluated_and_matched requires no unresolved issues or settlement routes and an
evaluable bank/ledger comparison for every transaction group. Matching supplied evidence
does not establish its completeness outside the declared input scope or authorize closure.

The deterministic result includes an input snapshot and hash. Validate with --input to bind
the original source supplied to the calculation; validation without it checks only internal
consistency. Source authentication and access controls remain runtime responsibilities.
