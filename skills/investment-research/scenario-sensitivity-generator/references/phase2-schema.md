# Phase2 native schema and method

Phase2 mode engine dcf-forecast performs an actual locally bundled DCF rerun using the full retained base_input and explicit wacc,terminal_growth or bridge overrides. Each scenario is independently revalidated and recomputed. Outer and base model contexts must match exactly. It does not rerun integrated operating assumptions or claim to be a general model engine.

The paired examples are evals/files/phase2-input.json and phase2-valid.json. The executable field contract is scripts/phase2_domain.py. Run the standard input, calculation and detached-original output commands on these files. Top-level evidence references gate every calculation; no source authentication or approval follows from a passing arithmetic check.

Per-share analysis requires valuation_subject {security_id, share_class, share_count_basis}. These are supplied explicit identities; do not infer a common share class from an issuer name or dilute/basic label. Reconciliation method rows must carry the exact same valuation_subject and actual share count as the top-level request.

Timing must be explicitly valuation_timing=annual-period-index. Discount origin is immediately before forecast period 1; the first annual label must be the review year or following year, and subsequent periods consecutive. as_of remains an evidence/review date and is not a calibrated discount origin. No actual stub-period or date-specific spot valuation is produced. A mid-year convention discounts operating flows at t-0.5; terminal value remains at t=N. Do not present this indexed illustration as a date-calibrated market value.
