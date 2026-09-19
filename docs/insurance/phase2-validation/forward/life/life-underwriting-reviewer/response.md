# Draft life underwriting review: APP-71

As of September 18, 2026, this NY term-life application needs additional evidence and specialist review. Prepared for the carrier life underwriting case manager, representing Synthetic Carrier; applicant SYN-A71. The authorized underwriting function owns the decision.

The supplied amounts produce a coverage-to-income multiple of **20**: ($1,450,000 requested + $350,000 existing) / $90,000 disclosed annual income. That exceeds the supplied profile's referral threshold of 15. The amount is a comparison using disclosed income, not proof of income, financial need, insurability, or a recommended benefit. See [application](raw-source.md#application), [criteria](raw-source.md#criteria) and `actual-output.json:results.financial_review`.

The attending physician statement EV-M1 matches APP-71 / SYN-A71 and is within the supplied 180-day window. Income verification EV-F1 remains pending and does not satisfy F1; obtain the employer verification and preserve its date and identity. See [APS](raw-source.md#aps), [pending income](raw-source.md#income-pending) and `results.evidence_checks`.

The application's 'no' and physician statement's 'yes' for specialist follow-up conflict. Ask the underwriting specialist to reconcile the dated follow-up and its relevance; this review makes no diagnosis or automatic declination inference. Retain both values. Refer the 20-times disclosed-coverage multiple and missing income confirmation to financial underwriting. See `results.disclosure_reconciliation` and findings `disclosure_conflict` / `financial_referral`.

The native artifact is **needs-data**; input validation, calculation and output validation passed. Independent arithmetic agrees. No risk class, medical diagnosis, issue decision or business action was produced. Reviewer disposition remains open outside this artifact. Evidence: [native input](input.json), [validated output](actual-output.json), [independent check](independent-arithmetic.json).
