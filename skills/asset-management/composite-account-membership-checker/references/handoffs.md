# Adjacent-Skill Handoffs — composite-account-membership-checker

This skill produces a cited **composite-membership exception queue** (`review_id`, per-exception
`case_ref`) and stops. It does not change membership, restate performance, adjudicate, or write a
system of record. Adjudication and any correction are performed by a human/authorized system.

## Downstream (route the analyst / reviewer to)

| Downstream | When | Handoff artifact |
| ---------- | ---- | ---------------- |
| `performance-attribution-builder` | The analyst needs the composite's return or performance attribution (re)built — the HARD-BOUNDARY route for any recalculation | `review_id` + affected composite/portfolio ids |
| `investment-data-quality-exception-detector` | The exception is really a **source-data defect** (wrong strategy, missing discretion/fee flag, bad dates) rather than a membership-rule breach | `case_ref` + the cited fields |
| `fund-fact-sheet-builder` / `fund-commentary-drafter` | After adjudication, GIPS composite disclosures/reporting need updating | approved composite id + period |
| **Composite management committee / performance operations** (human/authorized system — no skill) | A membership, methodology, or performance **change** must actually be applied to the system of record | adjudicated `case_ref` + approval |

## Upstream / adjacent (may precede or run beside this skill)

| Adjacent | Boundary |
| -------- | -------- |
| `mandate-compliance-monitor` | Monitors mandate/guideline compliance and discretion status; this skill consumes the resulting discretion/fee flags but does **not** re-determine mandate compliance |
| `investment-data-quality-exception-detector` | Cleans the account/composite feed *before* the check; membership rules assume validated inputs |

## Duplicate-execution prevention

- This skill computes and evidences **membership exceptions only**; it must not reach a
  disposition, change membership, or restate performance — those belong to the human analyst,
  the composite management committee, and `performance-attribution-builder`.
- Return/attribution math is never recomputed here; the queue carries the `review_id` so
  `performance-attribution-builder` and downstream reporting reuse the evidence rather than
  re-deriving it.
- Every exception's `case_ref` is durable and idempotent for a fixed input set, so re-running the
  check does not create duplicate cases.
