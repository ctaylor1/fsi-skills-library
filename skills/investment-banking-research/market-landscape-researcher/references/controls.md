# Controls — market-landscape-researcher

- **Risk tier:** R2 — analytical / research synthesis. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — banker/analyst review required before the brief is
  sent to a client, added to a pitch/coverage deliverable, or written to a system of record.
  No approval is needed for the analyst's own internal read.

## Prohibited (fail closed)

- No **investment advice or recommendation**: no buy/sell/hold call, no analyst rating
  (buy/sell/hold, overweight/underweight, conviction list), no **price target**, no
  "you should buy/sell/invest".
- No **personalized investment, legal, or tax advice** for any client or reader.
- No **valuation conclusion or trading view** presented as a decision (route valuation to the
  modeling skills; this skill maps structure and evidence).
- No **MNPI leakage or selective disclosure**: do not import non-public deal information into a
  brief intended for external delivery; keep client-confidential context in the internal draft
  only and flag it.
- No **guaranteed-return / will-outperform** language or other forward performance promises.
- No **unattributed load-bearing figure**: every market-share, sizing, or trend claim that
  carries weight must cite a source; do not rest a load-bearing figure solely on a tier-4
  source.

## Required output screens (`scripts/validate_output.py`)

- All **eight dimensions** present (value chain, competitors, customers, regulation,
  technology, economics, transactions, strategic implications), each with ≥1 **cited** finding.
- **Concentration tie-out**: HHI, CR4, and the market-structure band recompute deterministically
  from the `competitors` share table (reproducibility).
- **No prohibited investment-advice/decision language** (regex screen across narrative, notes,
  limitations, and every dimension finding).
- **Standing disclaimer present**: "Market research for informational purposes only; not
  investment advice, a recommendation, or an offer to buy or sell any security."
- **Limitations / uncertainty section present** (ranges, unattributed tail, stale/low-tier
  sources, as-of caveat).

## Fairness / conduct

- Describe competitors and their positions factually; do not disparage, and do not infer intent
  from market structure.
- HHI bands are **market-structure descriptors** using the standard 1500 / 2500 thresholds —
  they are not a competition-law opinion and not an investment view.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Wall off non-public deal context from
  any externally delivered brief; label internal-only material.
- Minimize client identifiers in the brief to what the analysis requires.
- Retain the brief + citations + `config_version` per records policy; log the read and any
  external-delivery approval. Never exfiltrate MNPI or client data.

## Reproducibility

`landscape_id` binds the brief to the exact inputs, `as_of`, and **config version**; re-running
with the same brief and config reproduces the concentration, coverage, and completeness
scorecards and the dimension map.
