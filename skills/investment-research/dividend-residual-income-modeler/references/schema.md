# Native intake

The paired synthetic input in evals/files/input.json is the maintained field example. The top-level request context requires issuer/security identity, as_of, actual use_on, knowledge_cutoff, internal purpose/audience, information_barrier, versioned sources and precise evidence_refs. Source references on every economic input must also be declared in the top-level evidence_refs. Dates, permissions and full retained input remain mandatory.

Method fields and numeric domains are validated in scripts/domain.py before calculation. currency is explicit; valuation units and diluted shares must match. No implicit FX, annualization, rounding conversion or evidence retrieval occurs.

Per-share analysis requires valuation_subject {security_id, share_class, share_count_basis}. These are supplied explicit identities; do not infer a common share class from an issuer name or dilute/basic label. Reconciliation method rows must carry the exact same valuation_subject and actual share count as the top-level request.

Timing must be explicitly valuation_timing=annual-period-index. Discount origin is immediately before forecast period 1; the first annual label must be the review year or following year, and subsequent periods consecutive. as_of remains an evidence/review date and is not a calibrated discount origin. No actual stub-period or date-specific spot valuation is produced. A mid-year convention discounts operating flows at t-0.5; terminal value remains at t=N. Do not present this indexed illustration as a date-calibrated market value.
