# Normal servicing decisions

- Void: this bounded adapter supports only unsubmitted draft/authorization states. Release requests require policy and actual response evidence; no completed refund is inferred.
- Refund/return: require settled/posted original evidence, an exact link and independent servicing permission. They are new linked funds movements and cannot restore the original ledger state by rollback.
- Reversal: requires a distinct applicable scheme/provider permission, original-state scope and deadline. ACH reversal is restricted error correction; it is not a general-purpose refund or a repair bypass. The code never invents a reversal right.
- Cancellation/recovery: a request may fail or recover only part of the amount. Counterparty agreement and actual outcome evidence remain necessary; no guaranteed recovery is stated.

Deduct completed and pending services from original capacity. An in-flight return cannot be ignored while creating a refund for the same funds. Ledger duplicates or another currency make capacity unknown. A different destination requires new-payee review.

A repair permission binds correction of an established defect. It cannot authorize a refund, reversal or recovery. Consumer error-resolution clocks and issuer statutory redress remain with the issuer dispute workflow and applicable legal profiles. This plan does not decide whether a customer has a refund right.
