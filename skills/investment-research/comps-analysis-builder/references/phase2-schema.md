# Phase2 native schema and method

Phase2 mode adds bank P/E, P/B and P/TBV; insurer P/E and P/B; REIT P/FFO and P/AFFO. Each peer must share the exact denominator definition, accounting/consolidation basis, historical period, currency and units. Nonpositive denominators and stale prices are excluded visibly; the configured minimum count gates the median. These are equity per-share ratios, with no EV bridge or assumption that FFO, book value or distributable capital has been normalized.

The paired examples are evals/files/phase2-input.json and phase2-valid.json. The executable field contract is scripts/phase2_domain.py. Run the standard input, calculation and detached-original output commands on these files. Top-level evidence references gate every calculation; no source authentication or approval follows from a passing arithmetic check.

Per-share analysis requires valuation_subject {security_id, share_class, share_count_basis}. These are supplied explicit identities; do not infer a common share class from an issuer name or dilute/basic label. Reconciliation method rows must carry the exact same valuation_subject and actual share count as the top-level request.
