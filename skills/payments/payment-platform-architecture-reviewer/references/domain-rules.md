# Payment architecture review criteria

A flow has identified component endpoints, a lifecycle stage, a state entity and
an authoritative component. Data models retain stable identifiers and distinct
states. Multiple authoritative claims require resolution; application status is not
bank cash or ledger truth. The component owner must be explicit, including outsourced
processing and third-party state stores.

Money-changing flows require a declared idempotency key, business scope, retention,
atomic enforcement and changed-payload behavior. Reusing a key with a different
payload must reject conflict or enter manual review. An uncertain response does not
prove failure: use authoritative status followed by reconciliation or no retry with
manual reconciliation. Never create a new key merely to force another payment.
The design must define the behavior; a JSON declaration is not a tested guarantee.

Reconciliation identifies the source/target, match keys, entity/account/currency
partition, owner and exception queue. Posting flows declare a ledger invariant and
linked reversal model. The package reviews declared designs, not accounting entries
or executable constraints. It cannot establish exactly-once delivery or balanced
production books from a document.

NFRs require metric, numeric target, unit, owner and measurement plan. Percent and
ratio rates have different scales; unknown targets remain gaps. Values such as zero
RPO/RTO or 100 percent availability are declared ambitions until tested. Architecture
options retain benefits, tradeoffs, component changes and acceptance evidence without
invented scoring or automatic selection.

Migration must address in-flight instructions, writer ownership, financial
reconciliation and entry/exit evidence. Shadow comparison cannot perform a second
financial execution. Application rollback does not reverse completed settlement.
The plan distinguishes rollback of new intake from recovery/servicing for completed
or uncertain payments. These review criteria are engineering conventions, not a
complete legal or resilience framework.
