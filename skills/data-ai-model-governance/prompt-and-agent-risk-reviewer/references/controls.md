# Controls — prompt-and-agent-risk-reviewer

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a human adjudicator (accountable AI risk owner) must
  decide before any deployment, risk acceptance, exception, attestation, or review closure.

## Prohibited (fail closed)

- No **approval** of an agent for deployment, release, or go-live.
- No **risk acceptance** or **exception/waiver** grant.
- No **control attestation** or **sign-off**.
- No **review closure** or case closure; the review stays open for human adjudication.
- No **autonomous decision** presented as binding; the rating and disposition are
  recommendations, deterministically derived and explainable.
- No **filing** to the risk register / model-risk system — route to
  `ai-risk-assessment-builder` and the human.

## Required output screens (`scripts/validate_output.py`)

- Every fired finding has a `control_id`, ≥ 1 cited evidence row, and remediation guidance.
- `recommended_rating` equals the deterministic max-severity mapping from fired findings.
- `recommended_disposition` equals the deterministic mapping from the rating.
- No approval / risk-acceptance / attestation / closure language (regex screen: "approved
  for production", "risk is accepted", "exception granted", "sign-off", "we approve", "we
  attest", "review is closed", "go-live approved", etc.).
- Standing disclaimer present: "Risk review evidence and recommendations only; not an
  approval, risk acceptance, or attestation. Deployment requires human adjudication by the
  accountable AI risk owner."
- Human-adjudication note present ("human adjudication").

## False-positive / false-negative discipline

- **False negatives are the dangerous class here.** Undocumented control blocks are treated
  as controls-not-evidenced (findings fire) rather than assumed present; gaps are surfaced
  in `data_gaps` so the reviewer knows the spec was under-documented.
- Thresholds/severities come only from the **versioned control catalog**, never tuned to
  make a specific agent pass.
- Findings are **explainable and additive** — each cites the exact locus; there is no opaque
  composite score.

## Data classification, privacy, records

- **Confidential.** The review reasons over configuration, not customer data; do not paste
  live secrets, tokens, or customer PII into the review. Redact any embedded secrets found
  in a system prompt and flag them as a finding.
- Retain the review + citations + `control_catalog_version` per records policy; log the read
  and the routing of recommendations to the human adjudicator.

## Reproducibility

`review_id` binds the output to the exact agent-spec revision (`as_of`) and
`control_catalog_version`; re-running with the same spec and catalog reproduces the findings,
rating, and disposition.
