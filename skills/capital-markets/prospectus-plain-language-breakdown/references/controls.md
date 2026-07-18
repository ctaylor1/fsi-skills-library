# Controls — prospectus-plain-language-breakdown

- **Risk tier:** R2 — analytical / explanatory. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the breakdown is delivered to a
  client or written to a system of record; not required for the user's own read.

## Prohibited (fail closed rather than do these)

- No investment **advice, recommendation, opinion, or solicitation** — do not tell the reader
  to invest/buy/subscribe/redeem, or characterize the offering as good/bad, cheap/expensive,
  safe/risky, or "worth it".
- No **suitability / Reg BI / best-interest** judgment (that is advice; route to
  `suitability-reg-bi-reviewer`).
- No **offer or solicitation** of the security, and no restatement of past performance or
  forward-looking statements as an expectation or projection of your own.
- No **fabrication** of a disclosure the document does not make; no **softening** of risk
  language; no **blending** of share classes or of multiple documents.
- No **fee-reasonableness / benchmarking** conclusion (that is `fee-and-charge-reviewer`).

## Required deterministic screen (R2 guardrail)

`scripts/validate_output.py` enforces, and **fails closed** on any breach:

1. **Completeness** — every required topic (fees, strategy, liquidity, conflicts, risks,
   obligations) is either covered as a section **or** explicitly recorded in `data_gaps`.
2. **Citation coverage** — every covered topic section carries a non-empty page citation;
   `source_pages`, where present, are positive integers.
3. **No advice / no solicitation** — the narrative and every section are scanned for
   advice/recommendation/solicitation phrasing (recommend, should invest/buy/subscribe,
   suitable, good/bad investment, guaranteed, will outperform, great opportunity, etc.). Any
   hit fails closed.
4. **Standing disclaimer present** — "Plain-language summary only; not investment advice, a
   recommendation, a solicitation, or an offer. Read the full prospectus before investing."

## Data classification, privacy, records

- Classification: **Highly Confidential (customer NPI/PII)** — a breakdown prepared for a
  specific client may carry client context.
- Mask any account/holder identifiers to last 4 in all output. Keep the filed document and
  breakdown within the approved environment; never exfiltrate.
- Retain the breakdown + citations per records policy. Log: source read, `breakdown_id`
  creation, and any external-delivery approval (who/when).

## Reproducibility

Given the same source document and effective date, the breakdown must be reproducible: the
`breakdown_id` binds the output to the exact document version, sections, and page citations
used.
