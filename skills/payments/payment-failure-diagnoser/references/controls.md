# Controls — payment-failure-diagnoser

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the diagnosis goes to a customer
  or a case/system of record.

## Prohibited (fail closed)

- No **payment action** or instruction to act: modify, repair, resubmit, re-present, reverse,
  release, cancel, hold, return, refund, or authorize a payment. The diagnoser reads and
  routes only.
- No **fraud or sanctions/AML determination** or statement/implication that a payment **is**
  fraud, a confirmed sanctions match, or a "true hit". Reason codes (`59`, `AC06`, `RR04`,
  `R16`) are scheme/bank responses, not determinations.
- No **case closure, filing, or dispute submission** — route to the appropriate downstream
  skill and human.
- No **route tuning to the individual**; use only the versioned root-cause→route config.
- No **invented meanings** for unknown reason codes; keep the raw code and route to
  investigation / message interpretation.

## Required output screens (`scripts/validate_output.py`)

- Root cause present with a `category` and ≥1 cited evidence row.
- Every leg carrying a `reason_code` is interpreted (non-empty `category`).
- `suggested_route` equals the deterministic mapping from `root_cause.category`.
- `retry_eligible` equals the deterministic policy for `root_cause.category`.
- No action/decision language (regex screen: "reverse the payment", "release the
  hold/funds", "resubmit the payment", "repair the message/payment", "refund the customer",
  "confirmed sanctions", "true hit", "this is fraud", "clear the hold", "approve the
  payment/refund/reversal", etc.).
- Standing disclaimer present: "Diagnostic assessment only; not a payment instruction,
  repair, or fraud/sanctions determination. No payment has been modified, resubmitted,
  reversed, or released."
- Cautions present whenever `retry_eligible` is true or the category is a duplicate /
  screening-hold risk (`system_timeout`, `duplicate`, `screening_hold`).

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII; cardholder data).** Mask PAN/account to last 4;
  never emit full PAN, CVV, track, or PIN data.
- Minimize customer data to what evidences the root cause.
- Retain diagnosis + citations + code-set/config versions per records policy; log read + approval.

## Reproducibility

`diagnosis_id` binds output to the exact trace, code-set version, and routing-config version;
re-running with the same inputs and versions reproduces the interpretation, root cause, and
route.
