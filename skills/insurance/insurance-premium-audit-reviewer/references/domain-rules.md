# Method and applicability

The supported method computes each row as audited exposure / supplied unit size × supplied rate × supplied combined modifier. Sum unrounded rows, add the explicit fixed charge, apply the supplied minimum premium, then round once to cents using decimal half-up. Compare that result to the reported audit; subtract the deposit to show the audit adjustment. These are configurable method conventions, not a universal rating algorithm. Explicit zero minimum/charge is supported; absent values stay unknown.

Use one currency and one rate period covering the complete policy period. Every exposure requires a reviewed class mapping, exposure basis and source record; do not choose payroll inclusions, exclusions, overtime treatment, owner treatment or subcontractor rules. Use the applicable manual and supplied audit schedule to establish those facts. Midterm rate/classification changes, retrospective rating, tiered minimums and other assessment orders require a different method before calculating. A reconciliation break is not permission to bill.

Separate exposure verification, classification specialist review and finance approval. The result is a technical audit draft, never a coverage or classification decision.

## Primary-source context checked 2026-09-18

- [California DWC employer FAQ](https://www.dir.ca.gov/dwc/faqs.html) — California workers compensation context: classification, payroll, experience and other factors affect premium; this is not a source of the insured-specific audit rate or method.

The Python method is a bounded engineering convention. No linked model, historical opinion or consumer guide replaces a current adopted rule, policy endorsement, contract or institution-approved procedure. Resolve applicability and exact effective version with the accountable professional before preparing a production profile.
