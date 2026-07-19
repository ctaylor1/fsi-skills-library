# Controls — senior-investor-protection-screener

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a trained human (advisor + branch supervisor / compliance /
  senior-protection team) adjudicates before any regulated decision, hold, filing, trusted-
  contact outreach, or system-of-record change. This skill produces evidence + a recommended
  disposition and stops.

## Prohibited (fail closed)

- No **determination** that financial exploitation or abuse has occurred, or that the client
  has **diminished capacity / lacks capacity / is incapacitated**. The skill surfaces
  indicators for human review; it never diagnoses or concludes.
- No **regulated decision or account action**: placing/lifting a FINRA Rule 2165 **temporary
  hold**, freezing/blocking/rejecting a disbursement, releasing a wire, or restricting an
  account.
- No **filing or report**: SAR, report to Adult Protective Services / a state securities or
  APS agency, or any regulatory notification.
- No **trusted-contact outreach as an executed action** and no client/third-party contact —
  the skill may *recommend* the reviewer consider these pathways.
- No **case closure**, clearance, or "no further action" disposition.
- No **personalized investment, legal, or tax advice**; no suitability approval.
- No **threshold tuning to the individual**; use only the versioned config.

## Required output screens (`scripts/validate_output.py`)

- Every fired signal has >= 1 cited evidence row.
- `suggested_disposition` equals the deterministic mapping from the fired-signal set
  (Monitor / Review / Escalate — see [domain-rules.md](domain-rules.md)).
- No determination/decision/filing/closure language (regex screen: "confirmed exploitation",
  "is being exploited", "lacks capacity", "place a temporary hold", "freeze the account",
  "file a SAR", "report to Adult Protective Services", "notify the trusted contact", "case
  closed", "no further action required", etc.).
- Standing disclaimer present: "Screening evidence only; not a determination of financial
  exploitation or capacity, and no hold, report, or account action has been taken."
- Benign-explanation prompts included when any signal fired.
- A non-compliant pack **fails closed** (exit 1); see `evals/files/pack_noncompliant.json`.

## Fairness / conduct

- Age and specified-adult status gate *which protections apply*; they are never themselves a
  concern signal and never a proxy for a negative conclusion about the client.
- Do not use protected-class attributes or proxies as signals.
- Describe patterns and observed indicators factually; avoid stigmatizing or diagnostic
  language about the client, the caregiver, or any third party.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask account numbers to last 4.
- Minimize client data to what evidences a fired signal.
- Retain screening + citations + config version per records policy; log the read and the
  adjudication decision made by the human (recorded outside this skill).
- Senior Safe Act: escalation to a supervisor/compliance is the intended human pathway; this
  skill only assembles the evidence that supports it.

## Reproducibility

`screening_id` binds output to the exact inputs, baseline window, observation set, and
**config version**; re-running with the same inputs and config reproduces the signals and the
suggested disposition.
