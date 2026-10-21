# Triage, investigation and handoffs

Triage whether the request is cohort health pricing before investigating data.
For health cohort renewal PMPM, use this package. P&C prospective rate support goes
to `pc-rate-adequacy-analyzer`; life/annuity pricing to `life-annuity-pricing-modeler`.
Those packages should route health member-month pricing here rather than substituting
P&C exposure or life decrement methods. Provider contracting/access evidence goes
to `health-provider-network-reviewer`, which may supply reviewed facts but no pricing
assumptions. Filing-packet completeness goes to `insurance-rate-form-filing-packager`
only after the accountable actuary supplies selected, reviewed support; neither
package submits a filing. Claims payment or clinical decisions are outside scope.

Transmit case ID, represented party/capacity, cohort and product, market/program,
base/projection/valuation dates, source versions/locators, supplied assumptions,
null dependencies and unresolved issues. Preserve native artifact plus separate
practitioner draft. A receiver validates actual mapped input; an artifact is not a
ready-made receiver input. Source context changes need an explicit reviewed mapping.
No handoff turns conditional premium into an approved rate or automatically fills
missing actuarial judgment.
