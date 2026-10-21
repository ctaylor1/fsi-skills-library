# Professional and output controls

Accountable function: **Employee Trading Compliance / Control Room**. Data classification: **Restricted employee trading and MNPI-related review evidence**.

- This package produces a draft/review plan. Human professionals retain legal interpretation, regulated decisions, waivers, sign-off, filing and closure authority.
- Do not execute writes, notifications, filings or approvals through this package. Neither source hashes nor supplied reviewer/token fields authorize an action.
- Reject malformed inputs and non-finite numeric values. Preserve substantive missingness rather than turn it into a favorable result.
- Reconstruct the exact native result with `validate_output.py OUTPUT --input ORIGINAL`. No ignored output fields, inline raw-source snapshot, edited finding, unsupported narrative, or self-rehashed substitute is accepted against the original.
- Keep professional narrative/workflow envelopes separate. Match evidence to a defined audience and purpose; minimize employee/customer data and preserve applicable SAR, MNPI, privacy, privilege and retention restrictions only where warranted.
- Use independently expected behavioral cases. Passing software/evaluation checks proves no source truth, independence, legal sufficiency, human acceptance, production readiness or live connector behavior.

No live preclearance integration, authenticated approval broker, system-of-record write, clearance issuance, notification, idempotent execution or rollback is implemented. Operational execution remains out of scope even with a supplied token. This does not place or execute trades.
