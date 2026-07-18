# Controls — policy-wording-comparator

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a licensed human must adjudicate before any coverage or compliance
  conclusion, form approval, filing, bind, case closure, or system-of-record write.

## Prohibited (fail closed)

- No **coverage determination** — never state or imply that coverage applies, is granted, is denied,
  or that an exclusion does or does not apply.
- No **compliance determination** — never state that a form "is compliant", certify compliance, or
  clear the form against a regulation.
- No **form approval, filing, or bind** — never approve a form, clear/approve it for filing, say it is
  ready to file, file it, or bind coverage. Filing and approval are authorized-system / licensed
  actions.
- No **review closure** — never close the review, mark it complete, or state that no further review is
  required. The suggested track is a triage hint for a human, not a disposition.
- No **materiality tuning to the deal** — use only the versioned config; do not relax thresholds to
  reach a desired answer.

## Required output screens (`scripts/validate_output.py`)

- Every `material` finding has >= 1 cited evidence row; every evidence row has a non-empty citation.
- Every `escalate` finding is also `material` (internal consistency).
- `suggested_review_track` equals the deterministic mapping: any escalate -> `Legal/compliance review
  required`; else any material -> `Standard review`; else `No material changes`.
- No decision/closure/filing/coverage language (regex screen: "approved for filing", "ready to file",
  "file the form", "form is compliant", "is compliant with", "coverage applies", "coverage is denied",
  "the exclusion does not apply", "bind coverage", "close the review", "no further review", etc.).
- A non-empty `legal_review_handoff` is present when the track is `Legal/compliance review required`.
- Standing disclaimer present: "Comparison evidence only; not a coverage, compliance, or filing
  determination. A licensed professional must adjudicate; no form has been filed, approved, or bound."

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Manuscript and specimen wording may contain insured
  names/numbers — mask policy/account numbers to last 4; minimize customer data to what evidences a
  finding.
- Retain the comparison + citations + `config_version` per records policy; log read + any approval.

## Reproducibility

`comparison_id` binds the output to the exact subject/baseline forms, their editions, and the
**config version**; re-running with the same inputs and config reproduces the findings and the
suggested track. Materiality is rule-driven, never a per-form opinion.
