# Controls — portfolio-risk-diversification-check

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the profile goes to a client or a
  system of record. Internal analytical use may be reviewer-sampled.

## Prohibited (fail closed)

- No **personalized investment advice** or **recommendation** to buy, sell, hold, allocate,
  rebalance, trim, or add to any security or asset class.
- No **suitability** / "right for you" judgment; no "good/bad investment" characterization.
- No **forecast** of returns, prices, or performance; no price targets; no "guaranteed" or
  "will outperform" language.
- No **binding decision**, order, or system-of-record write of any kind (read-only skill).
- No **threshold tuning to the individual portfolio**; use only the versioned config.
- No **opaque composite score** presented as decisive; every check is explainable and evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every flagged check has ≥ 1 cited evidence row.
- `diversification_band` equals the deterministic mapping from `flagged_checks`
  (see [domain-rules.md](domain-rules.md)).
- No advice/recommendation/forecast language (regex screen: "you should", "we recommend",
  "recommend buying/selling", "rebalance", "trim your", "good investment", "strong buy",
  "price target", "guaranteed returns", "will outperform", "expected to rise",
  "increase your allocation", "suitable for you", etc.).
- Standing educational disclaimer present: "Educational risk analysis only; not personalized
  investment advice or a recommendation to buy, sell, or hold any security."
- `educational_prompts` included when any check flagged.

## Fairness / conduct

- Describe exposures factually; do not stigmatize a strategy or investor.
- Do not use an investor's protected-class attributes or proxies as inputs to any check.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask account/portfolio identifiers (last 4).
- Minimize customer data to the holdings and buckets that evidence a flagged check.
- Retain the analysis + citations + config version per records policy; log the read and any
  external-delivery approval. Never exfiltrate holdings data.

## Reproducibility

`analysis_id` binds the output to the exact positions, `as_of`, reference-data inputs, and
**config version**; re-running with the same inputs and config reproduces every metric, the
flagged set, and the band.
