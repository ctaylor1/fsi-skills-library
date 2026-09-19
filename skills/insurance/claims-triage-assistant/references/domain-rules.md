# Domain rules — Claims Triage Assistant

- Complexity defaults: liability types base 3; property/business interruption 2; auto physical damage/theft/other 1. Exposure adds 1/2/3 at 25k/100k/250k; injuries +2, fatality +3, litigation +3, coverage question +2, more than two parties +1. S1 >=7, S2 >=3, else S3.
- Urgency defaults: fatality +3, injuries/CAT/deadline/business interruption each +2, vulnerability +1. U1 >=5, U2 >=2, else U3. Targets are illustrative 4 hours/1 business day/3 business days, not controlling legal periods.
- Deadline distance is supplied statutory_deadline_date minus `as_of`, including overdue dates. It is never measured from the claim report date. Source and legal applicability still require human confirmation.
- Unknown liability adds investigation and review needs while all urgency and other specialist routes remain available. Unknown claim-type mapping suppresses the severity band only. Missing exposure is explicitly provisional, never a known zero exposure.
- Coverage flags route to a human coverage specialist. The pre-placement coverage-gap skill is not a claim-coverage interpreter.
- Fraud/subrogation/complex-file routes are recommendations to native receiving schemas, not executable assignments. CAT, litigation, vulnerable-customer support and investigation remain human routes.
- Referral wording must not imply that fraud has been ruled out or third-party fault established. A supplied recovery-potential flag supports screening while responsibility remains unresolved.
- `refer-specialist` takes precedence when routes exist; otherwise needs-data for unresolved classification and draft-ready for complete classification. Human adjudication remains required in every case.

## Scope limit
P&C handling triage from supplied facts. Defaults are examples requiring deployment approval; no jurisdiction-wide deadline engine or claim coverage/valuation opinion.
