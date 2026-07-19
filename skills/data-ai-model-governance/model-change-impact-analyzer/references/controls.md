# Controls — model-change-impact-analyzer

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — mandatory human adjudication before any revalidation is
  waived, the change is approved, or the change is deployed. The skill recommends; a human
  (model owner / independent validation / change-governance forum) decides.

## Prohibited (fail closed)

- No **change decision**: never approve, clear, waive revalidation for, close, attest, or
  sign a change; never authorize or perform a **deployment/release**.
- No **autonomous regulated decision** and no **system-of-record write** (registry update,
  approval posting, change closure) — those are downstream, human-gated actions.
- No **banding tuned to a desired outcome**; use only the versioned config thresholds.
- No **inferred change**: a dimension not declared in the change record is `not_evaluable`,
  never silently "no change / no impact".
- No **opaque score** presented as decisive; findings are explainable and evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every fired dimension has ≥1 cited evidence row (before/after + source ref).
- `impact_band` equals the deterministic banding of the fired dimensions + critical flags +
  materiality, recomputed with the **same versioned banding config the engine used** (carried
  on `pack.config`, merged over documented defaults) — never from hard-coded thresholds;
  `recommended_revalidation_scope` matches the band mapping.
- **Prohibited-decision screen** (regex): rejects "change is approved", "approved for
  deployment", "we approve", "cleared to release", "deploy the change now", "waive
  revalidation", "no revalidation is required", "signed-off", "attestation complete",
  "close the change", "auto-approve", "no further review needed", etc.
- Standing disclaimer present: "Impact assessment and revalidation recommendation only; not
  a change approval or deployment authorization. No model change has been approved, deployed,
  or attested."
- `adjudicator_prompts` included when any dimension fired.

## Fairness / conduct

- Threshold/cutoff and control changes on regulated decisioning models must surface the
  fair-lending / adverse-action (e.g., ECOA/Reg B) impact for the adjudicator; never
  conclude a fairness outcome.
- Describe changes factually; do not editorialize about the requester's intent.

## Data classification, privacy, records

- **Confidential** governance data. Use de-identified/reference model attributes; do not
  embed customer NPI/PII or proprietary internals beyond what evidences a fired dimension.
- Retain assessment + citations + config version per records policy; log the read and any
  adjudication that consumes the pack.

## Reproducibility

`assessment_id` binds output to the exact change record, model version, and **config
version**; re-running with the same inputs and config reproduces the findings and band.
