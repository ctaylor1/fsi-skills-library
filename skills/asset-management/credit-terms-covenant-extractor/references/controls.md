# Controls — credit-terms-covenant-extractor

- **Risk tier:** R2 — analytical / utility. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the extraction package is
  delivered to a portfolio manager/analyst outside the requester or written to a system of
  record. No approval needed for the requester's own read.

## Prohibited (fail closed)

- No **covenant-compliance determination** — never state or imply a covenant is met,
  breached, satisfied, tripped, violated, or that an event of default has occurred, and never
  compute a covenant test result or headroom. Route testing to `covenant-compliance-monitor`.
- No **interpretation of ambiguous language** — cross-references, defined terms with
  carve-outs, "subject to" / "as defined" / "to be determined" language, and conflicting
  candidates are surfaced as `needs_review`, never resolved to a definitive value.
- No **investment advice or view** — no buy/sell/hold, overweight/underweight, "safe to
  invest", rating opinion, or thesis change.
- No **ongoing monitoring** — this is a point-in-time extraction from a fixed document; route
  surveillance/monitoring to `credit-surveillance-packet`.
- No **uncited term** — a field without a page-level citation is not extracted.

## Required output screens (`scripts/validate_output.py`)

- Every `extracted`/`needs_review` field has a positive-integer page and a citation string.
- No determination/advice language in generated prose (regex screen over narrative, notes,
  and per-field `reason`; verbatim source text in `raw_value` / `value.raw` is **not**
  screened — the skill quotes source but must never ADD a determination).
- No silently-resolved ambiguity: any field whose source text carries an ambiguity marker
  must be `needs_review`, never `extracted`.
- Standing disclaimer present: "Extracted terms and citations only; no compliance
  determination, covenant test, or investment advice has been made."
- Durable `extraction_id` (`ctce-*`) present; each `needs_review` entry carries a reason.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Credit documents frequently contain
  material non-public information; treat all inputs and outputs as MNPI and restrict to
  entitled research users.
- Minimize output to the extracted terms, their citations, and needs_review reasons. Do not
  copy large verbatim passages beyond the cited clause span.
- Retain the extraction + citations + `doc_version` + rule-set version per records policy; log
  the read and any external-delivery approval. Never exfiltrate document text.

## Reproducibility

`extraction_id` binds the output to the exact document (`doc_id`, `doc_version`,
`effective_date`) and the versioned normalization rules; re-running the same document with the
same rules reproduces the fields, statuses, and citations. Normalization is deterministic — no
model-based guessing of a term's meaning.
