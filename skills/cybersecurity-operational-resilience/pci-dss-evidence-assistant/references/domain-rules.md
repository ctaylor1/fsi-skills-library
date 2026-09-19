# Domain rules — PCI evidence collection

PCI DSS v4.0.1 requirement 3.2.1 concerns account-data retention/minimization; the prohibition on storing sensitive authentication data after authorization is 3.3.1. Do not label non-storage automatically N/A. Issuer-specific applicability and exceptions need assessor review.

This package measures supplied reference presence and collection recency only. It does not evaluate PCI testing procedures, assessment-period coverage, samples, control effectiveness, CDE scope, or sufficiency. `sufficiency_assessed` and `period_coverage_assessed` remain false. It covers only the supplied requirement subset, not the full standard.

States: `needs-data` for unmapped requirements or any asserted N/A pending review; `evidence-gap` for mapped controls with no in-scope references; `evidence-stale` for missing/invalid/future dates or old references; `evidence-present` when each mapped control has at least one recent reference. The last state is not a compliance or sufficiency conclusion.

Default recency windows (days): scans 90; pen test/risk assessment/policy/training 365; configuration/access review 180; log-review 30; other 365. These are illustrative collection policy, not PCI-required operating/test cadence. A recent daily-log artifact cannot substantiate a whole assessment period. A production program must supply an approved freshness policy separately from the applicable PCI testing procedures; firm policy cannot override the standard.

The output preserves the eight-section draft template, requirement/control/source index, gaps, owners and unresolved review slots. It never signs, submits or attests an AOC, ROC or SAQ.
