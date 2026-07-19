# Controls — agent-audit-trail-reviewer

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — human adjudication required before any regulated decision,
  control attestation, issue filing, closure, or system-of-record write.

## Prohibited (fail closed)

- No **control attestation** or statement that a control **is/was effective or ineffective**,
  that the run **passed/failed the audit**, or that the agent **is/was compliant** — those are
  adjudications.
- No **compliance determination** or pass/fail verdict on the run.
- No **closure** of a finding, issue, case, or review.
- No **filing / logging / writing** to the audit, risk, or issue system of record.
- No **certification or sign-off**.
- No **autonomous action** taken or recommended-as-executed on behalf of the reviewer.
- No **threshold tuning to the individual run**; use only the versioned policy/config.
- No **opaque scoring** presented as decisive; findings are explainable, evidenced rules.

## Required output screens ([../scripts/validate_output.py](../scripts/validate_output.py))

- Every finding has ≥ 1 cited evidence row.
- Each finding's `severity` equals the deterministic severity for its `type`
  (see [domain-rules.md](domain-rules.md)); severities are recomputed to resist tampering.
- `disposition` equals the deterministic mapping from the recomputed severity counts.
- `reproducibility` block is coherent (`complete` ⇔ empty `missing_fields`).
- `human_adjudication_required` is `true`.
- Standing disclaimer present: "Control-review evidence only; not a control attestation or
  adjudication. No finding has been closed, filed, or written to a system of record; human
  adjudication is required."
- **Prohibited-decision screen**: no autonomous decision / closure / filing / attestation
  language (e.g., "control is effective", "passed the audit", "the agent is compliant",
  "we closed the finding", "filed the issue", "certified", "signed off"). Advisory,
  future-tense recommendations to a human ("route to an adjudicator to decide whether to
  close") are intentionally allowed. A non-compliant pack **fails closed** (exit 1).

## Fairness / conduct

- Describe control gaps factually and attribute any control-failure conclusion to the human
  adjudicator. Do not stigmatize the agent's owner or operator.
- Do not use protected-class attributes or proxies in any finding.

## Data classification, privacy, records

- **Confidential.** Trails may embed prompts, retrieved content, and outputs (customer data
  or model IP). Minimize reproduced payloads; cite event IDs/refs instead of pasting content.
- Retain the review + citations + `policy_version` per records policy; log the read and the
  adjudication hand-off.

## Reproducibility

`review_id` binds the output to the exact run trail and **policy version**; re-running with
the same trail and policy reproduces the findings, severities, and disposition. Severity and
disposition mappings are deterministic and documented, never inferred per run.
