# Lifecycle and routing rules

- Card response `00` and `APPROVED` mean authorization approval, not clearing, settlement, funding, or posting.
- `ACSC`, `ACCC`, or `SETTLED` without independently linked supplied settlement evidence are reported completion only. Never infer beneficiary availability from an unqualified status.
- `PDNG`, `ACSP`, and other progress statuses are not automatically a timeout. No SLA/calendar implementation exists in this adapter.
- A later authorization does not erase an earlier unresolved failure. A traced and evidenced settlement can resolve the trace.
- Format/reference defects on bank traces route to bank exception casework; they do not establish a confirmed permissible repair. Card defects route to human payment operations, never the bank repair planner.
- Unmapped codes remain unknown with the raw code preserved. Native ACH meanings are illustrative; no Nacha retry-window/SEC-code rules are implemented.
- `retry_eligible` remains false. A decline code does not grant permission to retry.
- A complete trace requires an initiation start, contiguous sequence, and evidenced settlement. Other traces retain explicit uncertainty.

A diagnosis is source-bound analysis. Its hash identifies contents and is not proof of source authenticity or an approval.
