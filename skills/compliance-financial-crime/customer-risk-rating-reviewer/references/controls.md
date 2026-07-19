# Controls — customer-risk-rating-reviewer

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a qualified compliance officer / MLRO must adjudicate every
  finding before any regulated decision, rating change, override approval, trigger disposition,
  review/case closure, or filing.

## Prohibited (fail closed)

- No **rating decision or write**: never set, change, confirm, or write a customer risk rating
  to the system of record. The recomputation is a recommendation for a human.
- No **override approval/validation**: never approve, validate, or extend a downgrade/upgrade
  override. An override's validity is *assessed and evidenced*; approval is human.
- No **trigger disposition**: never clear, dispose, or "assess-as-closed" a sanctions/PEP,
  adverse-media, or monitoring trigger — route it to the specialist + human.
- No **review/case closure** or suppression of a finding outside the deterministic logic.
- No **filing** (SAR, regulatory report, CDD/KYC update) — route to the appropriate draft-only
  skill and human.
- No **threshold/weight/floor tuning to the individual**; use only the versioned methodology.
- No **opaque scoring** presented as decisive; the score is an explainable weighted sum and
  the band mapping is deterministic and documented.

## Required output screens (`scripts/validate_output.py`)

- Every finding has >= 1 cited evidence row (a source row or the methodology contract).
- `recomputed_band` ties out to the deterministic mapping `max_band(band_for_score(score_pct),
  floor_band)`.
- `recommended_review_outcome` equals the deterministic precedence from the finding types
  (escalate > remediate > re-rate > align).
- A `rating_discrepancy` finding exists whenever `recomputed_band != rating_of_record.band`
  (the review may never silently agree with a divergent record).
- `adjudication_required` is `true`.
- No decision/closure/filing/override-approval language (regex screen: "change the risk rating",
  "set the risk rating", "we have re-rated the customer", "approved the override", "close the
  case", "file a SAR", "update the system of record", "is a money launderer", etc.).
- Standing disclaimer present (see `scripts/calculate_or_transform.py` `DISCLAIMER`).
- `recommended_next_steps` (human/specialist routing) present for any non-align outcome.

## Fairness / conduct

- Use only the approved methodology factors; do not introduce protected-class attributes or
  proxies as risk factors.
- Describe factor values and patterns factually; avoid stigmatizing language about the customer.

## Data classification, privacy, records

- **Restricted (AML/BSA — SAR confidentiality; tipping-off controls).** Never disclose a
  potential SAR-related concern to the customer.
- Mask customer identifiers to the last 4 where feasible; minimize PII to what evidences a
  finding.
- Retain recomputation + citations + `methodology_version` per records policy; log the read and
  any downstream adjudication/approval.

## Reproducibility

`review_id` binds the output to the exact inputs and **methodology version**; re-running with
the same case and methodology reproduces the score, band, findings, and recommended outcome.
