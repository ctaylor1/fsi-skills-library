# Controls — policy-procedure-gap-analyzer

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a human must adjudicate every finding before any regulated
  decision, remediation sign-off, filing, attestation, or system-of-record change. The skill
  produces findings, evidence, and recommendations only.

## Prohibited (fail closed)

- No **compliance determination or attestation** — never state or imply the program/firm
  "is compliant", "fully compliant", "meets all requirements", or that "no gaps exist";
  never **certify**, **attest**, or **sign off**.
- No **finding closure or remediation sign-off** — never mark a finding closed or remediation
  complete; that is a human adjudication.
- No **filing/submission** — never file or submit to a regulator or examiner; route to the
  appropriate draft/package skill and the accountable human.
- No **system-of-record write** — never rewrite the policy/procedure; recommend and route.
- No **comparator/threshold tuning to make a gap disappear**; use only the versioned config.
- No **opaque scoring** presented as decisive; every finding is explainable and evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every finding has ≥1 cited evidence row (non-empty citation).
- Each finding's `severity` equals the deterministic mapping from `finding_type` +
  `criticality`.
- `severity_counts` tie out to the findings list; `remediation_priority` ties out to the
  counts.
- No determination / attestation / closure / filing language (regex screen: "fully
  compliant", "we attest", "no gaps exist", "finding closed", "remediation complete", "filed
  with the regulator", "submitted to the examiner", "signed off", etc.).
- Standing disclaimer present: "Gap-analysis findings and recommendations only; not a
  compliance determination, attestation, or filing. Human adjudication required."

The bad fixture `evals/files/analysis_pack_with_determination.json` carries determination and
closure language and **must fail closed** (exit 1).

## Data classification, privacy, records

- **Restricted (AML/BSA — SAR confidentiality; tipping-off controls).** Do not reproduce SAR
  contents or name subjects; reference records by pointer, not payload.
- Minimize data to what evidences a finding; paraphrase regulatory text, do not reproduce it.
- Retain the analysis + citations + `config_version` per records policy; log the read and the
  human adjudication decision.

## Reproducibility

`analysis_id` binds the output to the exact requirement/control inputs, `as_of`, and
**config version**; re-running with the same inputs and config reproduces the findings,
severities, and priority.
