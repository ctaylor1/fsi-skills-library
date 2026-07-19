# Controls — stablecoin-payment-controls-reviewer

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only
  analysis.
- **Human approval:** `required` — mandatory human adjudication before any regulated
  decision, launch approval, compliance attestation, case closure, filing, or
  system-of-record write based on this review.

## Prohibited (fail closed)

- No **launch approval, go-live sign-off, or "cleared to launch"** statement.
- No **compliance determination or attestation** ("certify compliant", "controls are
  adequate", "fully compliant with the GENIUS Act / MiCA / NYDFS", "we attest").
- No **sanctions/AML finding or hit disposition** ("no violations", "confirmed hit") — the
  skill reports the *control state* factually and routes hits/alerts to the adjudication and
  investigation skills.
- No **case/finding closure** ("case closed", "close the finding", "mark remediated",
  "waive the control").
- No **filing or system-of-record write** ("file the attestation", "submit to the
  regulator", "post to the register", "write to the system of record").
- No **threshold tuning to the program**; use only the versioned config.
- No **opaque scoring** presented as decisive; findings are explainable and evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every finding (`fail`/`gap`) has ≥1 cited evidence row.
- `suggested_disposition` equals the deterministic mapping from `controls_evaluated`
  (see [domain-rules.md](domain-rules.md)).
- No approval / attestation / closure / filing language (regex screen).
- Standing disclaimer present: "Control-review evidence only; not a compliance
  determination, launch approval, or attestation. No finding has been closed and no filing
  or system-of-record change has been made."
- `remediation_prompts` present when any finding fired.

## Case states / segregation of duties

- This skill occupies only the **evidence + recommendation** state. Adjudication, approval,
  filing, and closure are separate, human/authorized-system states.
- A durable `review_id` binds the pack; downstream skills reference it rather than
  recomputing findings.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII; cardholder data).** Keep customer/counterparty
  identifiers, wallet addresses, and PANs out of narrative free-text.
- Minimize data to what a `source_ref` requires to evidence a control.
- Retain review + citations + `config_version` per records policy; log read + adjudication.

## Escalation

- Any critical-control defect (reserve backing, reserve quality, attestation currency,
  qualified custody, sanctions screening, travel rule, on-chain reconciliation) →
  `Material Gaps - Escalate` and route to the accountable human owner and compliance.

## Reproducibility

`review_id` binds output to the exact inputs, period `as_of`, and **config version**;
re-running with the same inputs and config reproduces the findings and disposition.
