# Independent fictional source packet, authored 2026-10-04

This is invented review material with no actual member, clinical rule, payer,
licensed code or institutional authority. Reviewer June Avery (fictional clinical
reviewer) and Morgan Ellis (fictional payer coding/payment analyst) expressly review
their following bounded methods and scope for TEST-MARKET / fictional-employer /
PLAN-TEST-Z, US-TEST, health, effective 2026-01-01 through 2026-12-31. Neither
reviewer authorizes a live business decision. All identities are fictional tokens.

## Utilization normal

U1: FICTIONAL-PAYER-Z owns request UR-Z for member MEM-Z, provider PROV-Z,
service SRV-Z, requested service 'fictional imaging review', explicitly non-drug,
service date 2026-10-10. Receipt 2026-10-01T12:00:00Z, urgency standard.
Assessment 2026-10-02T12:00:00Z.

U2: June Avery expressly states this is the complete supplied criterion and
observation inventory for request UR-Z and service SRV-Z. Test-only criteria
version 1, effective 2026-01-01 through 2026-12-31, reviewed by June Avery:
B1 benefit/professional-observation: 'reviewer confirms supplied benefit evidence';
C1 clinical/numeric-threshold: 'fictional previous-therapy duration at least six
weeks', threshold 6, comparator ge, unit weeks. These are fictional criteria only.

U3: Observation OB1 dated 2026-09-30 binds B1/UR-Z/SRV-Z: professional reviewer
June Avery, qualified clinical reviewer role, explicitly states met; contrary false.
Observation OC1 dated 2026-09-30 binds C1/UR-Z/SRV-Z: documented therapy duration
8 weeks; contrary false.

U4: Rule CLOCK-Z v1 is expressly reviewed by June Avery for TEST-MARKET /
fictional-employer / PLAN-TEST-Z, non-drug, standard urgency, with effective dates
2026-01-01 through 2026-12-31. Administrative target is 48 exact elapsed hours
from request-received. No pause, business calendar, extension or legal deadline
assertion applies in this fictional local exercise.

## Utilization adverse variant

Same case and supplied rule/benefit observation, but source request U1 lacks urgency.
U3's numeric observation OC1 is instead a contrary note: 'the outside provider
reports that prior-therapy duration is undocumented'; no numeric duration is given.
The source statement declares the submitted records complete, while the factual
value itself is missing. Do not invent urgency or clinical evidence.

## Claim-payment normal

P1: FICTIONAL-PAYER-Z claim CL-Z, line L1, provider PROV-Z, product PLAN-TEST-Z,
service SRV-P, service date 2026-09-20, currency USD. Original event O-Z in economic
chain CH-Z was recorded 2026-09-21, units 3, billed 120. Replacement event R-Z
recorded 2026-09-22 replaces O-Z, units 2, billed 90. Both carry opaque fictional
code SYN-X, code version SYN-2026-Q3, no modifiers. Morgan Ellis confirms this is
all event history through the review date, with R-Z the sole terminal.

P2: Supplied code profile CP-Z, version 1 / file version TEST-Q3-REPLACEMENT-1,
effective 2026-07-01 through 2026-09-30, is expressly reviewed current by Morgan
Ellis and adopted only for this fictional payer test. Source permission covers only
fictional SYN-X, not any licensed real code set. Exact identity matches
PROV-Z / PLAN-TEST-Z / SRV-P / SYN-X / SYN-2026-Q3 / modifiers []. It applies to
TEST-MARKET / fictional-employer. Max units 4; complete incompatible-code list [].

P3: Contract CT-Z version 1 is reviewed by Morgan Ellis, effective 2026-01-01
through 2026-12-31, same provider/product/service/code/version/modifier identity.
Method unit-rate-exact; no rounding; USD rate per unit 32.125. The fictional
contract basis is exactly units times rate, with no lesser-of-billed rule.

P4: Independent allocation AL-Z for terminal R-Z, exact claim/line/provider/product/
service/date identity, USD allowed 64.25, member cost share 14.25, other payer 0,
other adjustment 0, payable 50. This independently reviewed fictional benefit
allocation is supplied explicitly, including every zero.

P5: Ledger snapshot PAY-Z as of 2026-10-03 for CH-Z / terminal R-Z and same
line identity: record kind net-payment-snapshot, USD net paid 51, including any
reversals. It is the only complete net snapshot, not an incremental payment event.

## Claim-payment adverse variant

The independent allocation source P4 omits member cost share entirely. All other
fields are unchanged, including the source's supplied payable 50. Its value must
remain unknown; do not back-solve member cost share from other totals. The ledger
still independently states net paid 51 and contract rate remains supplied.
