# Domain Rules — transaction-reconciliation-helper

Deterministic matching, a documented **break taxonomy**, the **tie-out identity**, and the
**proposed-entry** rules. Tolerances and expected sources are configuration (versioned,
owned by payments operations), not hard-coded judgments. Orientation only — the firm's
reconciliation and journal-entry standards take precedence.

## Matching

Records are grouped by shared **`txn_ref`**. Within a group:

1. Records are indexed by `source`; a repeated record within one source is a `duplicate`.
2. `expected_sources` (config, default `gateway, processor, bank, ledger`) defines which
   systems each transaction should appear in.
3. The **cash position of record** for the group is the highest-ranked present source in
   `config.cash_rank` (default `bank > processor > gateway`). The ledger is the side tied
   out, never the cash position of record.
4. Amounts are compared with `amount_tolerance` (default 0.01). A difference within
   tolerance is a match; beyond tolerance it is a break.

## Break taxonomy

| `break_type` | Fires when | Proposed resolution (draft) |
| ------------ | ---------- | --------------------------- |
| `missing_record` | Present in ≥2 sources but absent from an expected source | If **ledger** is missing → propose a ledger entry at the cash-position amount. If a **cash** source is missing → propose *investigate* (possible in-transit within `intransit_days`). |
| `unmatched` | Present in exactly one source (orphan) | Ledger-only orphan → propose reversing the unsupported entry pending investigation. Cash-only orphan → propose recording it in the ledger. |
| `amount_mismatch` | Present across sources but ledger ≠ cash position beyond tolerance | Propose a ledger adjustment = `cash_position − ledger`. |
| `duplicate` | Same record repeated within one source | Propose *investigate* / de-duplicate before any entry. |
| `currency_mismatch` | Records in a group span currencies | Propose *investigate*; resolve FX basis first. |
| `status_mismatch` | Lifecycle status conflicts across sources (e.g. refunded vs captured) | Propose *investigate*; confirm the true status. |
| `timing_difference` | Matched but posted on different dates within `intransit_days` | Reconciling item — flag, no adjustment. |
| `fee_variance` | Net difference explained by a documented processor fee | Reconciling item — attribute to fees, no adjustment unless mis-fee'd. |

Breaks are **independent and evidenced**; each carries its own source rows and citation.

## Tie-out identity (deterministic, documented)

Over **transaction-level** records only (settlement-level rows are routed out):

```
target_source   = highest-ranked present source in cash_rank        (default: bank)
target_total    = source_totals[target_source]                      (cash position of record)
ledger_total    = source_totals["ledger"]
net_proposed    = Σ ledger_delta of proposed ledger_adjustments
residual_before = target_total − ledger_total
residual_after  = residual_before − net_proposed
tied_out        = |residual_after| ≤ amount_tolerance
```

A clean reconciliation drives `residual_after` to 0 after the proposed entries. A non-zero
`residual_after` means unresolved breaks remain — surface it; never tune tolerance to force
a tie-out.

## Routing rule (settlement-file / cash-ledger breaks)

Any group containing a **settlement-level** record (`level: "settlement"`, or a settlement/
reserve/fee-batch source) is a settlement-file / cash-ledger break. It is **routed** to
`settlement-break-reconciler`, excluded from the transaction-level tie-out, and given **no**
proposed ledger entry here.

## Hard boundaries (fail closed)

- Never **post, book, or finalize** an entry; every entry is `status: "proposed"` and
  `requires_approval`.
- Never **close/suppress** a break or declare a reconciliation "final".
- Never **resolve a settlement-file break** here — route it.
- Never **fabricate a missing source** or **tune tolerance** to make a break disappear.
