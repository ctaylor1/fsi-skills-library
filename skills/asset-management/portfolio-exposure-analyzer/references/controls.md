# Controls — portfolio-exposure-analyzer

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the pack goes to a client, an
  investment committee, or a case/report/system of record.

## Prohibited (fail closed)

- No **mandate-compliance determination** or statement/implication that the portfolio **is
  in breach of**, **violates**, or is **non-compliant** with a mandate, guideline, or limit.
  Report exposures factually against documented limits; route adjudication to
  `mandate-compliance-monitor` and a human.
- No **trade, rebalance, hedge, or divestment** — proposed, staged, or executed — to cure an
  exposure.
- No **personalized investment, tax, or legal advice** (no "you should buy/sell/trim/hold").
- No **limit tuning to the portfolio**; use only the versioned config.
- No **opaque score** presented as decisive; exposures are explained and evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every finding has ≥ 1 cited evidence row.
- No determination/action/advice language (regex screen: "in breach of", "non-compliant",
  "violates the mandate/limit", "rebalance", "sell down", "trim the position", "divest",
  "place the order/trade", "we recommend selling/…", "you should buy/sell/…",
  "guaranteed return", etc.).
- `suggested_priority` equals the deterministic mapping from the finding set
  (see [domain-rules.md](domain-rules.md)).
- Standing disclaimer present: "Exposure analysis and evidence only; not a mandate-compliance
  determination or investment advice. No trade or portfolio action has been taken or
  recommended."
- `considerations` included whenever any finding fired.

## Fairness / conduct

- Describe concentrations factually; do not editorialize about the manager's judgment.
- Distinguish **active** (vs benchmark) from **absolute** exposure so a benchmark-driven
  weight is not framed as a defect.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Holdings can be market-moving and
  client-identifying; minimize to what evidences an exposure. Do not exfiltrate holdings.
- Retain the exposure analysis + citations + `config_version` per records policy; log the
  read and any external-delivery approval.

## Reproducibility

`exposure_id` binds the output to the exact holdings, `as_of`, and **config version**;
re-running with the same inputs and config reproduces the exposures, findings, and priority.
