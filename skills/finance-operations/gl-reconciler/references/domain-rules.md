# Domain Rules — gl-reconciler

Deterministic GL-to-subledger reconciliation: how records are matched, how disagreements are
classified into a fixed **break taxonomy**, how the result **ties out**, and how corrections
are **proposed** (never posted). Tolerances, materiality, and the suspense account are
configuration (versioned, owned by Finance & Controllership), not hard-coded judgments.

## Matching (deterministic)

Records are grouped by `match_key`. Within a key, GL and subledger rows are sorted by
`(date, entry_id)` and paired positionally. For each pair:

- currency/amount agree within `amount_tolerance` **and** dates within `date_tolerance_days`
  → **matched** (no break);
- amounts differ beyond `amount_tolerance` → **amount_mismatch**;
- amounts agree but dates differ beyond `date_tolerance_days` → **timing_difference**.

Leftover rows on a key that already produced a pair are **duplicate**; leftover rows on a key
with no counterpart at all are **unrecorded_in_gl** (subledger-only) or **unsupported_in_gl**
(GL-only).

## Break taxonomy

| Break type | Fires when | `gl_impact` | Proposed correction |
| ---------- | ---------- | ----------- | ------------------- |
| `timing_difference` | Matched amounts, posting dates differ beyond cutoff (in-transit / cutoff) | 0 (nets in-period) | **None** — documented reconciling item; clears next period |
| `amount_mismatch` | Matched key, GL and subledger amounts differ beyond tolerance | GL − subledger | Adjust GL to agree to subledger |
| `unrecorded_in_gl` | Subledger item with no GL counterpart (not in transit) | − subledger amount | Record the item in the GL |
| `unsupported_in_gl` | GL entry with no subledger support | + GL amount | Reverse / substantiate the GL entry |
| `duplicate` | Extra copy of a matched item on one side | ± that side's amount | Reverse the duplicate |

`gl_impact` is the signed amount by which the GL differs from the subledger because of that
break. Each break carries a `material` flag (`abs(gl_impact) >= materiality_threshold`).

## Tie-out invariants (enforced by `scripts/validate_output.py`)

1. `sum(break gl_impact) == gl_total − subledger_total` — the classified breaks **fully
   explain** the difference; `residual == 0`. If they do not tie, the reconciliation fails
   closed.
2. Each correctable break's `adjustment_amount == −gl_impact` — the proposed correction
   exactly offsets the break.
3. Every proposed correction is **balanced** (`sum(dr) == sum(cr)`) and its net effect on the
   reconciled account equals `adjustment_amount`.
4. `corrected_gl_total` (GL + proposed adjustments) agrees to the subledger, leaving only
   documented reconciling items (timing) outstanding.

## Idempotency & lineage

`input_fingerprint` = SHA-256 of the normalized inputs + config. `reconciliation_id` =
`glr-{entity}-{account}-{as_of}-{fingerprint[:8]}`. It has **no timestamp or random
component**, so identical inputs reproduce an identical reconciliation. Every break traces to
its GL/subledger source rows via `lineage` citations.

## Hard boundaries (fail closed)

- **Propose, never post.** Every correction is `status: "PROPOSED"`. The skill never posts,
  books, or writes a journal entry to the GL or any system of record.
- **Do not decide which side is right.** A break is a disagreement to be evidenced and routed,
  not adjudicated by the skill.
- **Do not net or suppress breaks** to force a tie. If breaks do not explain the difference,
  surface the residual rather than fabricating a plug.
- **Tolerances and materiality come from the versioned config**, never tuned per-reconciliation
  to make a break disappear.
- **Timing differences are documented, not corrected** — proposing a JE for an in-transit item
  would double-count it next period.
