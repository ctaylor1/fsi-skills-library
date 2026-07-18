# Controls — claims-file-reviewer

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a licensed adjuster / claims manager / coverage specialist
  must adjudicate. The skill produces findings and cited evidence; it decides nothing.

## Prohibited (fail closed)

- No **coverage determination** — never state or imply that coverage applies, is confirmed,
  denied, granted, excluded, or not in force. Flag missing citations and period questions;
  attribute the coverage call to the human.
- No **reserve determination or change** — never set, raise, lower, or "recommend" a reserve
  amount. Flag unsupported or divergent reserves for actuarial/adjuster review only.
- No **claim decision, payment, or settlement** — never approve/deny a claim, authorize,
  issue, or recommend a payment or settlement figure.
- No **case closure** and no **filing** (denial letter, SAR, suit) — route to the human and
  the appropriate draft-only skill.
- No **fraud finding** — never assert fraud; if indicators exist, route to
  `claims-fraud-referral-assistant` (draft-only).
- No **system-of-record write** — the skill is read-only.

## Required output screens (`scripts/validate_output.py`)

- Every finding has >= 1 cited evidence row (record, clause, or versioned config rule).
- No determination / action / filing language (regex screen: "coverage is denied", "deny the
  claim", "set the reserve", "issue a payment", "close the case", "file a SAR", "final
  coverage determination", "this is fraud", etc.).
- `review_readiness` equals the deterministic mapping from finding severities
  (any blocking → escalate; any warning → follow_up_required; else documentation_complete).
- Standing disclaimer present: "Review findings and evidence only; not a coverage or reserve
  determination. No claim decision, payment, reserve change, or case closure has been made."
- `reviewer_considerations` included whenever any finding is present.

## Fairness / conduct

- Do not use protected-class attributes or proxies in any finding.
- Describe evidence and gaps factually; avoid prejudicial language about the claimant.
- The claimant's and insurer's interests both bind the claim; surface both-sided
  considerations (a missing document may exist outside the file).

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Minimize claimant medical/PII to what evidences
  a finding; mask identifiers where surfaced.
- Retain the review + citations + `config_version` per records policy; log the read and any
  approval to write the review into a case.

## Reproducibility

`review_id` binds the output to the exact claim inputs, `as_of`, and **config version**;
re-running with the same inputs and config reproduces the findings and readiness band.
