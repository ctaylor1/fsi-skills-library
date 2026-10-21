# Native intake

The paired synthetic input in evals/files/input.json is the maintained field example. The top-level request context requires issuer/security identity, as_of, actual use_on, knowledge_cutoff, internal purpose/audience, information_barrier, versioned sources and precise evidence_refs. Source references on every economic input must also be declared in the top-level evidence_refs. Dates, permissions and full retained input remain mandatory.

Method fields and numeric domains are validated in scripts/domain.py before calculation. currency is explicit; valuation units and diluted shares must match. No implicit FX, annualization, rounding conversion or evidence retrieval occurs.
