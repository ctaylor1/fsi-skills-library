# Controls — financials-normalizer

## Version 0.2.0 contract

The native result is a closed calculation record. Retain the original input separately and validate with `python3 scripts/validate_output.py RESULT.json --input ORIGINAL.json`; `--selftest` loads both bundled examples. Computation validates input first. Finite JSON numbers, valid dates, supported domains and unique identifiers are enforced; duplicate JSON keys are rejected. Output validation reconstructs from the original and rejects omitted, altered or extra results, including flags/counts/statuses. Keep author narrative and workflow envelopes outside the native result. Source binding establishes deterministic fidelity to supplied inputs, not source authenticity, data rights, economic validity, institutional acceptance or independent assurance.

Each adjustment requires an explicit statement, known period and mapped reported account; an absent starting value cannot default to zero. Preserve its rationale, source and supplied approver in the adjustment ledger. Check reported balance-sheet anchors separately for each period. Reconstructed normalized identities require complete, disjoint mapped component coverage; raw anchor agreement cannot prove adjusted statements balance. Incomplete reconstruction prevents Model-ready. This maps extracts only; it does not convert accounting frameworks or provide an accounting opinion.


- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the normalized dataset is
  delivered to a downstream model/report, an audit file, or any system of record. Internal
  analytical use may be reviewer-sampled. The skill never posts a figure or books anything.

## Prohibited (fail closed)

- No **accounting or audit judgment**: never state or imply the statements **are**
  GAAP/IFRS-compliant, materially correct, accurate, reliable, or "fairly stated". Produce the
  mapping and tie-out evidence; attribute any conclusion to the human reviewer.
- No **investment / credit recommendation** off the normalized figures (buy/sell/rating,
  creditworthiness, "good/bad investment", price target).
- No **restatement, re-booking, or posting** of any figure to the GL, subledger, or system of
  record. The output is model-ready data with provenance, not a journal or a ledger write.
- No **borrower credit spreading** into a bank credit template — a separate workflow
  (`financial-spreading-assistant`).
- No **threshold tuning to an extract** to make it pass; use only the versioned config.
- No **opaque scoring** presented as decisive; checks are explainable and evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every fired finding has ≥ 1 cited evidence row (with a non-empty citation).
- `suggested_readiness` equals the deterministic mapping from the fired findings (any
  high-severity finding, or ≥ `escalate_finding_count`, → `Hold - tie-out break`).
- No prohibited decision/advice/restatement/posting language (regex screen: `gaap/ifrs
  compliant`, `materially accurate/correct/misstated`, `financials/statements are
  accurate/correct/fairly stated`, `audit opinion`, `is a (strong) buy/sell`, `buy/sell
  rating`, `we recommend investing`, `investment advice/recommendation`, `creditworthy`,
  `post … to the general ledger/system of record`, `restate/re-book the …`, etc.).
- Standing disclaimer present: "Normalization output only; not an accounting, audit, or
  investment judgment, and not a system-of-record posting. Source figures are mapped and tied
  out, not restated or re-booked; a human reviewer must accept the normalized mapping before
  use."
- `review_considerations` included when any finding fired.

## Conduct / integrity

- Preserve the **source of record**: the reported statement figure is never overridden; a
  normalized value carries provenance back to the exact source cell.
- Describe tie-out breaks and unexplained adjustments **factually**; do not impute intent
  (e.g. "management mismarked to inflate assets") — that is an investigation conclusion, not a
  normalization.

## Data classification, privacy, records

- **Confidential (financial records).** May include issuer- or deal-confidential,
  pre-release financials (MNPI risk); minimize to what evidences the mapping and findings, and
  respect information-barrier / need-to-know controls.
- Retain the normalization + provenance + citations + `config_version` per records policy; log
  the read and any `external-delivery` approval. Never exfiltrate issuer/deal data.

## Reproducibility

`normalization_id` binds the output to the exact source extract, `as_of`, mapping, and
**config version**; re-running with the same inputs and config reproduces the normalized
dataset, the tie-outs, and the readiness band.
