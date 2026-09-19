# Source contract

Required: merchant_id, statement_period, currency and nonempty transactions. Each transaction has unique txn_id, positive amount, interchange_fee, assessment_fee, processor_fee, source_ref; optional currency must match the statement and optional status must be settled. The input is explicitly a settled-sale statement, not an event log. processor.monthly_fees is a list of amount/source_ref and optional matching currency. An explicit empty list asserts no fixed fees; absent list means unknown.

Optional original config, contract and qualification fields remain in lineage but do not drive invented benchmarks. Decimal totals are serialized as strings. Output retains source_snapshot and input_hash; output validation recomputes the bounded core. Supplied data plus a matching hash do not independently authenticate a statement.
