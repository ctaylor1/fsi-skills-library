from pathlib import Path
import json, hashlib
P=Path('/tmp/insurance-p2-forward-life')
cases={
'life-underwriting-reviewer': (
'''I am the carrier's life underwriting case manager for synthetic applicant SYN-A71. Please reconcile the pending requirements for application APP-71, show the financial coverage multiple and identify the evidence and specialist follow-up still needed. Do not assign a risk class.''',
'''# Synthetic case-source packet UW-71, version 1; dated 2026-09-18
## application
APP-71 / applicant SYN-A71, individual term life, New York, USD. Requested death benefit 1,450,000; disclosed existing coverage 350,000; disclosed annual income 90,000. Purpose: family income replacement. All amounts are applicant-disclosed.
## criteria
Carrier synthetic reviewed profile UW-NY-TERM-26 v3 applies NY / term_life from 2026-01-01 through 2026-12-31. Required: M1 medical attending_physician_statement no older than 180 days; F1 financial income_verification no older than 90 days. Refer total requested plus existing coverage / annual income above 15 to financial underwriting. This synthetic supplied threshold is not a legal standard.
## aps
Evidence EV-M1: APP-71 / SYN-A71, attending_physician_statement dated 2026-08-20, received. Application answers 'no' to specialist follow-up in last year; physician statement says 'yes', a follow-up on 2026-07-14. Topic: specialist_follow_up. No diagnosis supplied or inferred.
## income-pending
Evidence EV-F1: APP-71 / SYN-A71, income_verification dated 2026-09-15, status pending; employer verification requested but not received.
'''),
'life-annuity-contract-service-reviewer': (
'''I am a carrier annuity service specialist reviewing owner SYN-O22's withdrawal request W-22. Please show proceeds and the account-value and benefit-base changes, identify consent gaps, and prepare an internal review note without executing the withdrawal.''',
'''# Synthetic case-source packet SV-22, version 1; dated 2026-09-18
## contract
Contract AN-22: fixed annuity, owner SYN-O22, beneficiary SYN-B22, collateral assignee SYN-L22. USD account value 180,000 at 2026-09-17.
## request
Request W-22 on AN-22 from SYN-O22: partial withdrawal gross amount 50,000.
## terms
Synthetic reviewed profile SV-NY-26 v2 applies NY / fixed_annuity from 2026-01-01 through 2026-12-31. Authorized actor list contains SYN-O22 only. Required consents: owner SYN-O22 and assignee SYN-L22. The supplied deduction bridge treats gross withdrawal as account-value debit; surrender charge 3,500, signed market-value adjustment +1,250, loan offset 2,000, withholding 4,500. Deductions lie within gross except the signed market-value adjustment. Illustrated guaranteed benefit base before 230,000 and after 166,111.11; this comes from the carrier illustration and is not inferred from the account-value arithmetic.
## consent-owner
Received consent from SYN-O22 for AN-22 / W-22 on 2026-09-17.
## consent-inventory
The case file contains no assignee SYN-L22 consent for AN-22 / W-22 as of 2026-09-18.
'''),
'life-benefit-claim-reviewer': (
'''I am the carrier's life claims reviewer for claim LC-91. Please reconcile the documents, the competing beneficiary records and the supplied benefit arithmetic. Explain what prevents allocation and what needs specialist review. Do not decide entitlement or issue payment.''',
'''# Synthetic case-source packet LC-91, version 1; dated 2026-09-18
## policy
Policy LP-91 insured SYN-I91, issue and effective date 2025-01-10; USD; NY / whole_life.
## death
Reported death of SYN-I91 on 2026-09-03.
## terms
Synthetic reviewed claims profile LC-NY-26 v4 applies NY / whole_life from 2026-01-01 through 2026-12-31. Supplied contestability end 2027-01-10. Requirements D1 death_certificate, C1 claimant_statement; both no older than 90 days at review.
## certificate
Evidence DC-91, death_certificate, LP-91 but insured identifier SYN-I19, received 2026-09-10. Identity conflict is unresolved.
## claimant
Evidence CS-91, claimant_statement, LP-91 / SYN-I91, received 2026-09-12.
## designation-active
Record BEN-91-A, LP-91, version 1, effective 2025-01-10, active: SYN-B1 65%, SYN-B2 35%.
## designation-disputed
Record BEN-91-B, LP-91, version 2, effective 2026-08-15, disputed: SYN-B1 70%, SYN-B3 30%. Signature challenge unresolved; no determination of validity supplied.
## ledger
LP-91 / USD: base benefit 750,000; additional benefits 12,500; loan principal 18,300; loan interest 214.75; prior payments 5,000; interest credit 910.25. These are supplied figures before entitlement review.
'''),
'reinsurance-program-analyzer': (
'''I am a ceded reinsurance analyst for synthetic Cedar Mutual. Compare Programs A and B under the supplied two-event stress and no-loss scenarios. Show layer recoveries, exhaustion, retained losses and supplied costs. These are deterministic comparisons, not a purchase recommendation or modeled probability.''',
'''# Synthetic case-source packet RP-26, version 1; dated 2026-09-18
## profile
Synthetic reviewed profile RP-US-26 v1 applies US / property_cat from 2026-01-01 through 2026-12-31. Currency USD; ground-up occurrence loss basis; treaty and scenario periods 2026-01-01 through 2026-12-31. Layers operate sequentially on remaining loss; shared eligible IDs Q and X. Per-event limits are before participation; aggregate capacity and prior erosion are after participation.
## program-a
A: fixed premium 1,000,000. Additional premiums: STRESS 200,000; ZERO 0. First layer Q quota_share: attachment 0, limit 8,000,000, share 20%, aggregate limit 3,000,000, prior erosion 500,000. Second layer X occurrence_xol: attachment 2,000,000, limit 5,000,000, share 75%, aggregate limit 4,000,000, prior erosion 1,000,000.
## program-b
B: fixed premium 1,600,000. Additional premiums: STRESS 350,000; ZERO 0. First layer Q quota_share: attachment 0, limit 8,000,000, share 25%, aggregate limit 4,000,000, prior erosion 500,000. Second layer X occurrence_xol: attachment 3,000,000, limit 5,000,000, share 100%, aggregate limit 5,000,000, prior erosion 0.
## stress
STRESS is two events in order: EVT1 on 2026-09-01 gross 5,000,000; EVT2 on 2026-09-10 gross 10,000,000. Both explicitly reviewed as eligible for Q and X in both programs. Treat these losses as alternative hypothetical analysis, separate from supplied prior erosion.
## zero
ZERO: event EVT0 on 2026-09-01 gross 0, reviewed eligible IDs Q and X. Each alternative scenario starts again with the supplied prior erosion.
'''),
'reinsurance-contract-administration-reviewer': (
'''I am Cedar Mutual's ceded reinsurance accountant. Reconcile the August paid-loss statement with the bordereau, cash and closing recoverable, and flag collateral and notice exceptions. Preserve claim-level breaks even if the total ties. Do not book entries or send notices.''',
'''# Synthetic case-source packet RA-26, version 1; dated 2026-09-18
## scope
Treaty TR-26, counterparty RE-SYN, period 2026-08-01 through 2026-08-31, USD, ceded_paid_recoverable basis. Reviewed synthetic profile RA-US-26 v2 applies US / property_cat from 2026-01-01 through 2026-12-31. Notice inventory explicitly reviewed complete.
## balances
Opening recoverable 240,000. Closing recoverable 268,750. Both exactly match scope above.
## statement
S1 claim CL-1 charge 70,000; S2 claim CL-2 charge 60,000. Each row exactly matches scope.
## bordereau
B1 claim CL-1 ceded paid loss 65,000; B2 claim CL-2 ceded paid loss 65,000. Each row exactly matches scope.
## cash
R1 claim CL-1 receipt 100,000. Exact scope.
## adjustment
J1 claim CL-2 signed adjustment -1,250. Exact scope. Reason: sourced prior-period correction carried in current period.
## collateral
For exact scope, supplied reviewed required collateral 300,000 and eligible held collateral 275,000; no independently supplied regulatory percentage.
## notice-terms
N1 claim notice due 2026-09-05, dispatched 2026-09-08 per dispatch log below. N2 quarterly statement due 2026-09-15, no dispatch date or evidence as of review. Both treaty TR-26, counterparty RE-SYN.
## dispatch
Dispatch log DL1 records N1 transmitted 2026-09-08. Synthetic record establishes only the supplied evidence, not external authentication.
''')}
for skill,(request,raw) in cases.items():
 d=P/skill;d.mkdir(exist_ok=True)
 (d/'request.md').write_text(request+'\n');(d/'raw-source.md').write_text(raw)
 (d/'design-status.json').write_text(json.dumps({'stage':'case-design-frozen-before-implementation-read','synthetic':True,'package_fixtures_or_tests_read':False,'raw_source_sha256':hashlib.sha256(raw.encode()).hexdigest()},indent=2)+'\n')
print('Frozen 5 fresh requests and raw-source packets.')
