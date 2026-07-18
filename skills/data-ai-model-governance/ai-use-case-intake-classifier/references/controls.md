# Controls — ai-use-case-intake-classifier

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a human governance body must adjudicate the tier and path before
  any approval, exemption, waiver, intake closure, or deployment. The skill recommends; it never
  decides.

## Prohibited (fail closed)

- No **binding governance decision**: do not state or imply that a use case **is approved**, cleared,
  greenlit, exempt, waived, or fit for production/deployment.
- No **intake closure** or **governance sign-off**: the skill does not close the intake or grant
  sign-off; those are human/authorized-body actions.
- No **legality adjudication**: a prohibited-practice indicator forces escalation to Legal/Ethics —
  the skill flags and routes, it does not decide whether the practice is lawful.
- No **down-tiering on a self-declared attribute** that conflicts with the authoritative catalog;
  classify at the more conservative value.
- No **threshold invention**: materiality/scale thresholds come only from the versioned ruleset.

## Required output screens (`scripts/validate_output.py`)

- Every fired factor has ≥1 cited evidence row (field + citation).
- `governance_tier` **and** `recommended_governance_path` equal the deterministic mapping from the
  fired-factor set (see [domain-rules.md](domain-rules.md)).
- `human_adjudication_required` is `true`.
- No binding-decision / approval / clearance / exemption / closure language (regex screen over the
  narrative, notes, and factor reasons — not the disclaimer field).
- `required_reviews` is non-empty.
- Standing disclaimer present: "Provisional classification prepared for human governance adjudication
  only; it does not grant, waive, exempt, or close any governance review, and is not a deployment
  authorization."

## Fairness / conduct

- Classify from declared, structured attributes and the catalog. Do not editorialize about intent or
  whether the team "really needs" the AI. Customer/public-facing and special-category factors exist
  precisely so fairness and privacy reviews are triggered, not skipped.

## Data classification, privacy, records

- **Confidential.** The intake is a *proposal*; keep submitter identity to a role, not a named person.
- Reference the data **classification**, never the underlying customer NPI/PII.
- Retain classification + citations + config version per records policy; log read + routing.

## Reproducibility

`classification_id` binds the output to the exact submission, `as_of`, and **ruleset version**;
re-running with the same submission and config reproduces the fired factors, tier, and path.
