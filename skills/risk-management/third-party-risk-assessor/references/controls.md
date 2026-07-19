# Controls — third-party-risk-assessor

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only
  analysis.
- **Human approval:** `required` — mandatory human/committee adjudication before any vendor
  decision, filing, commitment, posting, closure, attestation, or system-of-record change.
  This skill produces evidence and recommendations only; it never adjudicates.

## Prohibited (fail closed)

- No **vendor decision**: never approve, reject, onboard, renew, terminate, offboard, or
  risk-accept a third party, and never state that any such decision has been made.
- No **case closure, filing, attestation, or sign-off**, and no write to a system of record
  (vendor register, GRC tool, contract system).
- No **binding risk-appetite or limit decision**; recommend, do not decide.
- No **personalized investment/credit advice** on the vendor's securities or debt; the
  financial-condition dimension is a factual solvency read for risk assessment only.
- No **threshold tuning to the individual vendor**; use only the versioned config.
- No **opaque composite score** presented as decisive; every band is explainable, evidenced,
  and traceable to the deterministic rules in `domain-rules.md`.
- No assertion of **misconduct, sanctions status, or intent** — route those questions to the
  compliance/financial-crime skills and human specialists.

## Required output screens (`scripts/validate_output.py`)

- Every material finding (dimension severity ≥ 2) has ≥ 1 cited evidence row.
- `suggested_risk_tier` equals the deterministic mapping from the dimension severities,
  recomputed with the same versioned `high_dimension_count` threshold the engine used (read
  from the pack `config`), so a tightened config cannot tie out against a stale hard-coded value.
- No prohibited decision / closure / filing / risk-acceptance / sign-off language (regex
  screen) in the narrative, notes, dimension reasons, or recommended actions.
- Standing disclaimer present: "Assessment evidence and recommendations only; not an
  approval, rejection, or risk-acceptance decision. Human adjudication and sign-off are
  required before any onboarding, renewal, termination, or system-of-record change."
- When material findings exist, `recommended_actions` include an explicit human-adjudication
  note and `evidence_gaps` is present.

The output screen is the archetype's **prohibited-decision gate** and the R3 fail-closed
control: a pack that asserts a vendor decision, closes/files the assessment, drops the
disclaimer, or leaves a material finding unevidenced fails and is not delivered.

## Fairness / conduct

- Do not use protected-class attributes or proxies in scoring. `elevated_risk_jurisdictions`
  is a configured, sanctions/geopolitical-risk list owned by ERM/compliance — not an ad hoc
  judgment — and it flags for **enhanced review**, never a decision.
- Describe findings factually; avoid stigmatizing language about a vendor or its personnel.

## Data classification, privacy, records

- **Confidential** (vendor commercial, control, and financial data; possible references to
  customer-data exposure). Minimize to what evidences a finding; do not copy raw customer
  data into the pack.
- Retain the assessment + citations + `config_version` + `framework_version` per records
  policy; log the read and the adjudication decision made by the human/committee (recorded by
  that authorized system, not by this skill).

## Reproducibility

`assessment_id` binds the output to the exact inputs, `as_of` date, and **config/framework
versions**; re-running with the same inputs and config reproduces the bands and the suggested
tier.
