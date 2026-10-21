# Native intake

The paired synthetic input in evals/files/input.json is the maintained field example. The top-level request context requires issuer/security identity, as_of, actual use_on, knowledge_cutoff, internal purpose/audience, information_barrier, versioned sources and precise evidence_refs. Source references on every economic input must also be declared in the top-level evidence_refs. Dates, permissions and full retained input remain mandatory.

Method fields and numeric domains are validated in scripts/domain.py before calculation. currency is explicit; valuation units and diluted shares must match. No implicit FX, annualization, rounding conversion or evidence retrieval occurs.

Per-share analysis requires valuation_subject {security_id, share_class, share_count_basis}. These are supplied explicit identities; do not infer a common share class from an issuer name or dilute/basic label. Reconciliation method rows must carry the exact same valuation_subject and actual share count as the top-level request.

Each valuation carries explicit valuation_timing and discount_origin. A spot-as-of method requires discount_origin equal to its supplied valuation_date; an indexed method retains immediately-before-forecast-period-1 plus first_forecast_year. Reconciliation compares all timing fields and withholds a combined range or pairwise spread for incompatible origins. SOTP segment timing must match the group basis; no implicit indexed-to-spot conversion occurs. Asset NAV accepts spot-as-of only.
