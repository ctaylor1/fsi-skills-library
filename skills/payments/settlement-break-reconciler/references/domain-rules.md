# Domain Rules — settlement-break-reconciler

How settlement records are matched, tied out, classified into a **break taxonomy**, and
turned into **proposed-only** corrections. Tolerances and fee/reserve rates are configuration
(versioned, owned by the settlement/finance operations control owner), not hard-coded
judgments. The firm's settlement reconciliation standard and the card-network operating rules
take precedence over this summary.

## Tie-outs (per matched `match_key`)

| Tie-out | Test (within tolerance) | Break when it fails |
| ------- | ----------------------- | ------------------- |
| Gross | network gross == processor gross | `AMOUNT_MISMATCH_GROSS` |
| Fee | processor fee == gross × scheduled `rate_bps` | `FEE_VARIANCE` |
| Reserve | processor reserve == gross × scheduled `reserve_bps` | `RESERVE_VARIANCE` |
| Net calc | processor net == gross − fees − reserve | `NET_CALC_MISMATCH` |
| Cash | bank cash == processor net | `NET_CASH_MISMATCH` |
| Ledger | ledger net == processor net | `LEDGER_POSTING_MISMATCH` |

Tolerances (`config`, defaults): `amount_tolerance_abs`, `fee_tolerance_abs`,
`reserve_tolerance_abs`, `cash_tolerance_abs`, `net_calc_tolerance_abs` = 0.50 each;
`cash_settlement_lag_days` = 2. Impact is signed (e.g. bank − processor for cash) so the
direction of the difference is preserved.

## Break taxonomy

| `break_type` | Fires when | Impact |
| ------------ | ---------- | ------ |
| `AMOUNT_MISMATCH_GROSS` | Network and processor gross differ | processor − network gross |
| `FEE_VARIANCE` | Processor fee ≠ scheduled fee | actual − expected fee |
| `RESERVE_VARIANCE` | Processor reserve ≠ scheduled reserve | actual − expected reserve |
| `NET_CALC_MISMATCH` | Processor net ≠ gross − fees − reserve | net − calc |
| `NET_CASH_MISMATCH` | Bank cash ≠ processor net | bank − net |
| `LEDGER_POSTING_MISMATCH` | Ledger net ≠ processor net | ledger − net |
| `MISSING_IN_BANK` | Settled but no bank cash, **outside** the cash lag window | settled net |
| `MISSING_IN_LEDGER` | Settled but not booked in the ledger | settled net |
| `MISSING_IN_SETTLEMENT` | Bank/ledger entry with no settlement record | entry amount |
| `DUPLICATE` | Same `match_key` appears twice in one source | duplicated amount |
| `CURRENCY_MISMATCH` | Sources disagree on the settlement currency | 0 (flag) |

Breaks are **independent and additive**; each is reported with its own evidence. There is no
opaque composite score.

## Reconciling items (not breaks)

| `type` | Meaning |
| ------ | ------- |
| `TIMING_DIFFERENCE` | Settled within `cash_settlement_lag_days` of `period.end` with cash not yet received — an expected in-transit item. Reported under `reconciling_items` with an `in_transit_amount`; it is **not** counted in `total_break_impact` and gets **no** correcting journal. |

Distinguishing timing from a true `MISSING_IN_BANK` is the core period-completeness control:
do not raise a cash break for funds that are simply not due yet.

## Proposed corrections (draft-only, never posted)

Each break yields exactly one proposed correction with a deterministic `correction_id`
(`COR-<break_id>`), `status: "proposed"`, and `requires_approval: true`:

| Break | Proposed correction |
| ----- | ------------------- |
| `MISSING_IN_LEDGER` | Journal: Dr Settlement Clearing / Cr Merchant Payable |
| `LEDGER_POSTING_MISMATCH` | Journal: adjust ledger net to processor net |
| `NET_CASH_MISMATCH` | Journal: difference to Cash Suspense pending investigation |
| `FEE_VARIANCE` | Dispute/adjust: query processor fee vs schedule |
| `RESERVE_VARIANCE` | Journal: adjust reserve to schedule |
| `AMOUNT_MISMATCH_GROSS`, `NET_CALC_MISMATCH`, `MISSING_IN_BANK`, `MISSING_IN_SETTLEMENT`, `DUPLICATE`, `CURRENCY_MISMATCH` | Investigation item (no journal until root cause is known) |

## Hard boundaries (fail closed)

- Never **post**, book, execute, or apply a correction; never write a system of record.
- Never mark a break **reconciled/cleared** as a state change — report status; the human
  dispositions.
- Never **force a match** or tune tolerances to make a break disappear.
- Correcting journals are **proposals for approval**, not instructions to a posting engine.
