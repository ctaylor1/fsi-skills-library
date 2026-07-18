# Controls — coverage-initiation-researcher

- **Risk tier:** R2 — analytical / drafting. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — supervisory analyst and research committee
  approval required before the draft is published, sent to a client, or written to the
  research system of record. Internal analytical use may be reviewer-sampled.

## Prohibited (fail closed)

- No **personalized investment advice** ("you should buy/sell/hold", "my recommendation to
  you") — the draft evidences a thesis; it does not advise a person.
- No **approved rating or price target**. A proposed rating stays `draft-unapproved`; the
  skill never issues an "official rating", "approved rating", or "price target". Those are a
  supervisory analyst + research committee decision (Reg AC / FINRA Rule 2241 posture).
- No **guarantees or certainty language** ("guaranteed", "risk-free", "cannot lose", "will
  definitely double/outperform").
- No **MNPI** in the draft. Operate on public/approved-internal sources only; respect the
  information wall. If `mnpi_attestation` is not true, do not proceed to delivery.
- No **fabricated evidence**. Every section claim, forecast series, and valuation input is
  cited; uncited content blocks readiness rather than being smoothed over.

## Required output screens (`scripts/validate_output.py`)

- All eight required sections present and evidenced (no missing / unevidenced sections).
- `readiness` equals the deterministic mapping (see [domain-rules.md](domain-rules.md)).
- Valuation complete: method values cited, weights sum ≈ 1.0, a blended draft midpoint exists.
- No advice / decision / approved-call language (regex screen over narrative + notes).
- `proposed_rating.status == 'draft-unapproved'` unless both approvals are recorded.
- `mnpi_attestation` present and true.
- Standing disclaimer and the DRAFT banner present.

Any miss fails closed (exit 1); the draft is not presented or delivered until corrected.

## Conduct / independence

- Keep research independent of banking: do not tailor the thesis to win or protect a mandate.
- Describe risks and downside as fully as upside; the draft is balanced, not promotional.
- Attribute conclusions to evidence, not to a house view that has not been approved.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Enforce the information wall.
- Retain the draft + citations + `config_version` per records policy; log the read and the
  external-delivery approval. Never exfiltrate client-confidential or wall-crossed data.

## Reproducibility

`coverage_id` binds the draft to the exact dossier inputs, `as_of`, and **config version**;
re-running with the same inputs and config reproduces the section scorecard, forecast checks,
draft valuation range, and readiness band.
