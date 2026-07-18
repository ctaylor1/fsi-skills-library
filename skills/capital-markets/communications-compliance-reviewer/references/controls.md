# Controls — communications-compliance-reviewer

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a registered principal must review and adjudicate before any
  regulated decision (approval, filing, customer commitment, posting, review closure, or
  system-of-record change). This skill produces findings + cited evidence + a recommended
  disposition; it never decides, files, or closes.

## Prohibited (fail closed)

- No **supervisory approval** of a communication (approved/cleared/fit for use, principal
  approval granted, green-lit).
- No **filing** of a communication (e.g., with FINRA/SEC) and no statement that it was filed.
- No **review closure** / disposition ("review closed", "no further review needed", sign-off
  complete).
- No **confirmed-violation** characterization; describe the finding factually and attribute the
  decision to the registered principal.
- No **threshold/claim-library tuning to an individual author or campaign**; use only the
  versioned config.
- No **opaque scoring** presented as decisive; findings are explainable and evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every finding has ≥1 cited evidence row (matched text / disclosure gap / supervision or
  retention field, with a `comm:{source_ref}@{date}` citation).
- No approval/decision/closure/filing language (regex screen: "approved for use", "cleared for
  distribution", "principal approval granted", "this communication is approved", "review is
  closed", "no further review needed", "filed with FINRA", "we have filed", "meets all
  requirements", etc.).
- `recommended_disposition` equals the deterministic mapping from finding severities
  (Escalate / Remediate / Advisory / No-exceptions).
- Standing disclaimer present: "Advisory compliance review only; not a supervisory approval,
  regulated determination, or filing. A registered principal must independently review and
  adjudicate this communication before any use, distribution, regulatory filing, or review
  closure."
- Remediation prompts included when any high/medium finding fired.

A non-compliant pack (approval/closure/filing language, or missing disclaimer) **fails closed**
with exit 1 — see `evals/files/review_pack_prohibited.json`.

## Fairness / conduct

- Review the communication, not the person. Describe patterns and gaps factually; avoid
  stigmatizing language about the author or recipients.
- Do not use protected-class attributes or proxies in any finding.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Communications may contain customer identifiers
  and account references — mask account/card numbers to last 4 and minimize customer data to
  what evidences a finding.
- Retain the review + citations + `config_version` per records policy; log the read and any
  escalation routing. Never exfiltrate communication content or customer data.

## Reproducibility

`review_id` binds the output to the exact communication, classification, and **config
version**; re-running with the same input and config reproduces the findings and the
recommended disposition.
