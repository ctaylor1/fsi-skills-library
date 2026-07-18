# Controls — earnings-results-analyzer

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the analysis is delivered to a
  client, published as a note, or written to a system of record. Supervisory-analyst /
  compliance review applies where the firm requires it for published research.

## Prohibited (fail closed)

- No **investment rating** (buy/sell/hold, overweight/underweight, equal-weight, market
  perform, strong buy, conviction list) — assigning one is a human, supervised decision.
- No **price target / target price**, and no statement that sets, raises, or lowers one.
- No **recommendation or personalized advice** ("we recommend buying", "you should buy/sell",
  "we advise selling") — the skill classifies the print; the analyst forms the view.
- No **coverage initiation/upgrade/downgrade** action — route to the coverage skill and the
  human; this analyzer does not rate.
- No **external publication or distribution**, and no **trade/rebalance/allocation** action.
- No **MNPI ingestion** or information-barrier breach to "improve" the read.
- No **opaque scoring** presented as decisive; classifications are explainable and evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every evaluable metric finding cites **both** its `actual` and its `estimate` evidence.
- Every evaluable guidance finding has ≥ 1 cited evidence row.
- `overall_result` equals the deterministic mapping from the findings (headline metrics +
  headline-guidance cut; see [domain-rules.md](domain-rules.md)).
- No rating / price-target / recommendation / advice language (regex screen: "price target",
  "buy/sell/hold rating", "overweight", "underweight", "we recommend buying", "you should
  buy", "initiate coverage", "upgrade to buy", etc.). The standing disclaimer is excluded from
  the scan because it legitimately names these terms.
- Standing disclaimer present: "Factual earnings analysis and cited evidence only; not
  investment advice, a rating, or a price target. No recommendation to buy, sell, or hold has
  been made."
- Thesis considerations included when any finding is evaluable.

## Conduct / independence

- Measure surprise against a **stated estimate source**; do not cherry-pick the baseline to
  manufacture a beat or miss.
- Describe results and commentary **factually**; do not editorialize into a call.
- Respect **quiet periods** and information barriers; use only approved sources.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Draft estimates and pre-publication
  views are non-public; do not exfiltrate.
- Minimize to the figures and language that evidence a finding.
- Retain analysis + citations + **config version** per records policy; log read + approval.

## Reproducibility

`analysis_id` binds output to the exact inputs, estimate source, and **config version**;
re-running with the same inputs and config reproduces the classifications and overall result.
