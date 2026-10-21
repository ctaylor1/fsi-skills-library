# Privacy Impact Assessment Assistant — Phase 1 method

- Supply the jurisdiction and reviewed legal profile with rationale and sources. US context does not automatically establish GDPR applicability; sensitivity under institution policy does not automatically make data an Article 9 category.
- Each of the eight evidence sections carries claim IDs/text/citation references. Each citation resolves to a supplied registry locator, version and excerpt. Section-level citation presence cannot compensate for unsupported individual claims. Excerpts still require substantive human review.
- Open section gaps prevent ready-for-adjudication. Missing jurisdiction/profile or any required risk factor also yields `needs-information`; absent factors never produce Low. Explicit adverse legal indicators yield `blocked` pending counsel review, not an illegality determination.
- The numeric method is an inherent-risk triage indicator only. `residual_risk_band` remains `not_assessed` because the calculator does not test mitigation effectiveness. Complete inputs may produce Low/Medium/High; those labels are not legal DPIA thresholds.
- `prior_consultation_indicated` remains null: no Article 36 decision follows from the score. Qualified reviewers assess applicability, remaining risk, measures and any consultation obligations in context.
- Supplied approval records are labelled `supplied-unverified`, never authenticated/obtained by this package. Ready-for-adjudication means structured evidence completeness for human review, not approval or substantive sufficiency.

## Supplied schema

Processing context, config/template identifiers, assessment ID, jurisdiction/legal profile, all explicit risk factors, evidence sections with individually cited claims, source registry and institutional reviewer/approval roles. Missing substantive evidence remains a visible gap.

The authoritative executable shape check is `scripts/validate_input.py`. `scripts/calculate_or_transform.py`
contains the bounded calculation. The worked source fixture is `evals/files/pia_case_example.json`;
it is explicitly synthetic and must not be used as current law or institutional policy.

No jurisdictional law pack, legal-basis decision, mitigation-effectiveness validation, processing approval, authenticated sign-off, consultation submission, filing or system change is implemented. Supplied sources are unverified; standard template coverage is not legal compliance.
