# Controls — suitability-reg-bi-reviewer

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a qualified supervisor / principal must make the
  best-interest / suitability determination and any approval before the recommendation is acted
  on. The skill produces evidence and recommendations only; it never adjudicates.

## Prohibited (fail closed)

- No **best-interest or suitability determination** or statement/implication that the
  recommendation **is suitable**, **is in the customer's best interest**, or **meets/satisfies
  the best-interest standard**.
- No **approval, clearance, or rejection** of the recommendation; no **trade clearance** or
  order placement; no **supervisory sign-off**.
- No **case closure** and no **filing** (e.g., regulatory form, report) — route to the human.
- No **personalized investment advice** or product recommendation of the skill's own.
- No **relaxing a required check to the individual**; use only the versioned config and the rule.
- No **opaque scoring** presented as decisive; every satisfied check is explainable and evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every **satisfied** check has ≥1 cited evidence row (evidence traceability).
- `disposition` equals the deterministic mapping recomputed from the checks (tie-out):
  Insufficient-evidence if any blocking obligation is `not_evaluable`; else Gaps-identified if
  any check is a `gap`; else Evidence-complete.
- **No prohibited decision/approval/action/closure/filing language** (regex screen: "recommendation
  is approved", "approve the recommendation", "cleared for execution", "is/deemed suitable", "not
  suitable", "meets the best-interest standard", "case closed", "sign off", "principal approval
  granted", "file/submit the report", etc.).
- Standing disclaimer present: "Reg BI and suitability evidence review only; not a best-interest
  determination, a suitability approval, or supervisory sign-off. No recommendation has been
  approved and no order has been placed. A qualified supervisor or principal must adjudicate."
- `open_items` (remediation prompts) present whenever the disposition is not Evidence-complete.

## Fairness / conduct

- Do not use protected-class attributes or proxies in any obligation check.
- Describe gaps factually; do not characterize the advisor's intent or the customer's competence
  (senior/vulnerable concerns route to `senior-investor-protection-screener`).

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask account numbers to last 4.
- Minimize customer data to what evidences a check.
- Retain review + citations + **config version** per records policy; log the read and the
  routing to the supervisor.

## Reproducibility

`review_id` binds the output to the exact inputs and **config version**; re-running with the
same packet and config reproduces the checks and disposition.
