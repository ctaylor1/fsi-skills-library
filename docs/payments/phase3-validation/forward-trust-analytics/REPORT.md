# Independent Phase 3 trust and analytics forward evaluation

2026-09-18. Independently authored synthetic operational scenarios. Read the four target
SKILL/schema/native helpers; did not read their evaluation specifications, test code,
fixtures, goldens or prior conclusions. No repository edits or external actions.

47 native CLI calls and 90 assertions passed for declared command exits, original-input
output binding, and substantive domain behaviors. Sixteen cases are retained with exact
commands/stdout/stderr, original JSON, calculated JSON, assertion results and source hashes.
One additional behavioral defect was observed, separately documented below; passing the
90 assertions does not mean this additional defect passed.

## Merchant acceptance and routing response

Two of four unique orders completed in each period. Attempts rose from three to six, so
attempt approval fell from 2/3 to 2/6 while observed customer completion stayed 2/4. One
order per period had no attempt and remained in the denominator; another outcome remained
unknown, giving a completion bound of 50–75%, not an automatic failure classification.
The current completed orders have immature dispute labels, so their mature chargeback
rate is unknown. The routing experiment retains assignment even when one B order falls
back to provider A, reports contamination, and makes no causal uplift claim. Partial
costs cannot establish all-in profitability. Cost coverage overlap rejects validation;
future-dated outcome observations quarantine metrics; stale extraction stays a gap.

Practitioner next step: reconcile extraction coverage, resolve unknown order outcomes,
review the fallback crossover and wait for owner-defined maturity before a routing
change decision. A randomized assignment declaration alone does not prove balance,
power or a causal treatment effect.

## Fraud portfolio response

The proposed risk-block plus velocity-review portfolio counts overlapping rules once per
transaction. Two sample transactions trigger both rules. A recently observed pending
fraud label stays outside mature confusion/loss metrics, while a missing risk feature
makes the portfolio action unknown even when another predicate can be evaluated.
USD and GBP review costs remain separate: USD5 for one review, GBP8 for one review.
USD has four sampled transactions but only two mature evaluable rows. Retrospective
blocked face value never becomes causal avoided loss. Hindsight features quarantine the
entire replay; missing GBP review-cost assumptions yield null cost rather than zero.

Practitioner next step: investigate feature availability, retained unknown actions and
maturing labels; assess operational capacity and legitimate-block costs by cohort; use
an owner-approved shadow/challenger pilot rather than deploying from this replay.

## Recurring credentials response

A scoped network-token use and account-updater event have complete supplied references,
but the result never establishes payment authorization, SCA or liability shift.
A successful passkey login is insufficient when its login-session binding differs from
the renewal's instruction/payer/payee/amount. An account update cannot revive revoked
consent, and an expired token remains an evidence gap even with successful authentication.

Practitioner next step: retain original token requestor and merchant domains, exact
renewal intent, scoped authentication applicability and updater consent evidence. Treat
these as supplied review declarations; no cryptographic assertion or identity provider
was actually verified by the offline helper.

## Bank collection response

An accepted, exactly bound FedNow RFP leads only to preparation of a separate initiation
review. It creates no funds movement. Changed amount bindings and expired requests stay
gaps. A pay-by-bank credit-push scenario on ACH remains nonauthorizing.

Defect: two different invoice requests and immutable message IDs reuse one
payer_response.response_id with different amounts and exact bindings. Both rows receive
`assemble-separate-native-initiation-review` without an identity-conflict gap. A response
identifier cannot unambiguously identify both supplied response records. Reproducer:
`collection-conflicting-response-id.json`; outcome: corresponding `-output.json` and
`response-id-conflict-observation.json`. Reported to implementation owner; evaluator did
not modify the target code. Follow-up result belongs in a separate retained record.

## Evidence and limits

`run_evaluation.py` constructs every scenario from independently chosen values and runs
input/calculation/output validation. `commands.json` lists all exact argv and paths;
`assertions.json` contains 90 declared assertions. `source-hashes.json` captures current
implementation/document hashes after this run, not independent source authentication.
These tests cover synthetic behavior and arithmetic, not bank/network integration,
professional sign-off, live source truth, statistical effect sizes or deployment acceptance.

## Final collection fix verification

The implementation owner added nonempty unique response-ID validation and clean malformed
response rejection. The unchanged original conflicting-response reproducer now fails
both input validation and calculation with structured JSON and exit 1. Original defective
output and all initial evidence above remain intact.

A separate `final-fix-verification/` directory retains **14 additional native calls and
39 passing assertions**, covering the unchanged adversarial request, unchanged valid
request with original-input output validation, malformed list/string responses, malformed
object/empty response IDs, and rejection of a tampered payment_authorized output.
Twenty-six relevant source files hashed identically before and after this verification.

The collection identity defect is resolved in this inspected implementation. Total
retained activity is **61 native calls and 129 passing assertions**, with the initial
unasserted defect retained separately rather than overwritten as a clean initial run.
