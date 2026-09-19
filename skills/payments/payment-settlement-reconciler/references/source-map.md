# Source roles and provenance

| Source | What it supports | What it cannot establish alone |
| --- | --- | --- |
| Network clearing/settlement file | Stated cleared gross for the scoped batch | Bank receipt or correct ledger posting |
| Processor/acquirer report | Reported components, fees, reserve and net | Contractual fee correctness or bank cash |
| Bank statement/credit evidence | Observed cash and value date | Correct upstream gross, fees or ledger |
| Internal ledger | Recorded amount and posting date | Correctness of its own booking |
| Scoped effective contract schedule | Expected fee/reserve for its stated formula | Uncovered pricing structures or periods |
| Funding advice/contract due-date source | Declared expected amount/date | Cash received |
| Merchant export | Supplied observations, clearly labeled | Authenticated system evidence |

Preserve each source separately when figures disagree. There is no universal source winner
that can be used to balance every check. Citations use source:source_ref@date; schedule and
funding-date checks retain their own references. Content hashes do not authenticate sources.

Source retrieval, account/entity mapping, immutable evidence storage and authorization are
deployment integrations. Bundled code reads local JSON and never invokes a network connector.
