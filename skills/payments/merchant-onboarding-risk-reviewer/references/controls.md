# Controls — merchant-onboarding-risk-reviewer

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a merchant-risk adjudicator (or the delegated authority /
  risk committee) must decide before any approval, decline, boarding, condition sign-off,
  filing, or system-of-record change. This skill recommends and evidences; it never decides.

## Prohibited (fail closed)

- No **onboarding decision**: the skill never approves, declines, boards, onboards, or
  rejects a merchant, and never states that any of these has happened.
- No **case closure**: it never closes or suppresses the onboarding case/review.
- No **filing or system-of-record write**: no SAR filing, no boarding-system write, no card-
  network submission, no core/acquiring platform change.
- No **autonomous sanctions/adverse-media adjudication**: it consumes screening status and
  routes hits to the sanctions/adverse-media specialists; it does not clear or dismiss a hit.
- No **threshold tuning to the applicant**; use only the versioned config lists/thresholds.
- No **opaque score** presented as decisive; findings are explainable and individually cited.

## Required output screens (`scripts/validate_output.py`)

- `fired_findings` ties out to `findings[].fired` (no tampering).
- Every fired finding has >= 1 cited evidence row.
- `recommendation` equals the deterministic mapping from the fired-finding set
  (blocking → Decline; incomplete → Escalate-Insufficient-Evidence; elevated →
  Approve-with-Conditions; none → Approve). See `references/domain-rules.md`.
- `recommendation` is one of the four allowed bands and `adjudication_required` is `true`.
- `Recommend-Approve-with-Conditions` carries a non-empty `conditions` list.
- No onboarding-decision / case-closure / filing language in narrative, notes, finding
  reasons, or conditions (regex screen).
- Standing disclaimer present (verbatim): "Recommendation and evidence only; not an
  onboarding decision. No approval, decline, boarding, filing, or system-of-record change
  has been made. Human adjudication is required."

## Fairness / conduct

- Base findings on business-model, activity, ownership, screening, and jurisdiction risk —
  not on protected-class attributes or proxies for them.
- Describe risk factually; avoid stigmatizing language about the merchant or its owners.
- High-risk-geography and PEP findings drive **enhanced due diligence**, not an automatic
  decline; the human adjudicator weighs mitigants.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII; cardholder data).** Minimize owner PII in the
  output to what evidences a fired finding; reference registry/screening records by ref.
- Retain the review + citations + `config_version` per records policy; log the read and the
  adjudicator's decision (captured by the approval broker, not by this skill).

## Reproducibility

`review_id` binds the output to the exact application inputs and the **config version**;
re-running with the same inputs and config reproduces the findings and recommendation.
