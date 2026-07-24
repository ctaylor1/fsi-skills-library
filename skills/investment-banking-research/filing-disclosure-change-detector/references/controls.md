# Controls — filing-disclosure-change-detector

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the change pack is delivered to
  a client, published, or written to a system of record. Internal analytical use may be
  reviewer-sampled.

## Prohibited (fail closed)

- No **materiality determination** — never state or imply a change is material / immaterial,
  "material to investors", or that materiality is established. Detect, cite, and route.
- No **legal-significance determination** — no "violation", "breach", "default",
  "unlawful", "legally significant", "misrepresentation", "fraudulent".
- No **investment implication** — no rating/target/estimate/forecast change, no
  buy/sell/hold/overweight/underweight, no upgrade/downgrade, no bullish/bearish, no
  thesis/valuation/price call, no "should buy/sell/own/avoid".
- No **restatement/reliance conclusion** — detect and quote restatement/non-reliance
  wording; never conclude a restatement occurred or that prior statements are unreliable.
- No **publication or external delivery** and no **system-of-record write** without the
  `external-delivery` approval gate.

## Required output screens (`scripts/validate_output.py`)

- Every finding has a top-level section/exhibit **citation** and ≥ 1 **cited** evidence row.
- `change_summary` (`total_findings` + `by_type`) **ties out** to the findings list.
- `review_routing` equals the deterministic lane mapping from the detected types
  (see [domain-rules.md](domain-rules.md)).
- **No prohibited determination language** in analyst-authored text (narrative, notes,
  finding `observation`). Verbatim source quotes in `evidence` and the standing disclaimer
  are excluded from this screen (quoting the filing is not a determination).
- **Standing disclaimer present:** "Change detection and citations only; not a determination
  of materiality, legal significance, or investment implication. A qualified human makes
  those determinations."

## Information barriers / conduct

- Operate only on inputs the requester is entitled to; respect research information barriers
  and the quiet-period / restricted-list posture of the deployment. Do not merge material
  non-public content across walled sources.
- Describe changes neutrally; do not characterize management intent.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Filings may be public, but the
  *comparison, selection, and timing* can be MNPI-adjacent — treat the pack as confidential.
- Minimize free text to what evidences a finding; quote bounded excerpts, not whole sections.
- Retain the pack + citations + `config_version` + both `accession`s per records policy; log
  the read and any `external-delivery` approval.

## Reproducibility

`job_id` binds the pack to the exact two versions compared and the **config version**;
re-running the same versions with the same config reproduces the findings, `finding_id`s,
`change_summary`, and `review_routing`.
