# Phase2 native schema and method

Phase2 mode decomposes historical segment EBIT changes into prior-margin revenue effects and current-revenue margin effects, with unallocated change when zero denominators prevent decomposition. Explicit versioned reviewed-supplied mappings must cover both historical periods. Segment sums are independently reconciled to supplied reported totals. The result remains historical and does not forecast or authorize mappings.

The paired examples are evals/files/phase2-input.json and phase2-valid.json. The executable field contract is scripts/phase2_domain.py. Run the standard input, calculation and detached-original output commands on these files. Top-level evidence references gate every calculation; no source authentication or approval follows from a passing arithmetic check.
