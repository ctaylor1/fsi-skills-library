# Commitment and liquidity conventions

These are explicit package accounting conventions for review of supplied evidence. The fund’s
agreements and administrator records must be professionally reconciled to them. An administrator
may use “unfunded” for a differently timed balance, so compare only mapped quantities. The exact
schema and lifecycle invariants are in [schema.md](schema.md).

## Commitment ledger
Use gross settled movements since inception and the current operative commitment total, including
supported amendments. Do not add a snapshot of cumulative paid capital to its constituent payments.
For each position:

```
settled_inside_calls = sum(settled call commitment_effect_amount)
settled_recallable_distributions = sum(settled distribution commitment_effect_amount)
remaining_commitment_including_unpaid_calls = operative_commitment
    - settled_inside_calls + settled_recallable_distributions
reserved_commitment_in_unpaid_calls = sum(call notice effect - settled call effect)
uncalled_commitment = remaining_commitment_including_unpaid_calls
    - reserved_commitment_in_unpaid_calls
outstanding_calls = sum(call notice cash - settled call cash)
uncalled_plus_outstanding_calls = uncalled_commitment + outstanding_calls
```

Cancelled notices contribute no unpaid amount. The final quantity includes known unpaid
outside-commitment expenses once; it excludes hypothetical forecasts and future unknown expenses.
**Do not add remaining commitment to outstanding calls:** inside-commitment unpaid calls are
already inside the remaining amount. Notice-only recallable distributions do not restore the
remaining amount until receipt in this convention. Preserve separately the known unpaid distribution.
A negative uncalled amount is an unresolved reconciliation/contract question, not extra credit.

Example: commitment 500,000; settled inside calls 225,000; settled recallable distributions 10,000;
inside unpaid calls 75,000; outside unpaid fees 5,000. Remaining is 285,000; reserved 75,000;
uncalled 210,000; cash payable 80,000; uncalled plus payable 290,000. Adding remaining and all
payables would incorrectly produce 365,000.

Unknown effect allocations or incomplete since-inception inventories suppress commitment totals.
Known observed cash subtotals remain labeled observed, not asserted complete. Reported uncalled
and call-payable statement values are required for reconciliation; unknown values are findings.
The comparison tolerance is one cent to accommodate supplied statement presentation; source amounts
otherwise use exact cents and Decimal arithmetic. No fee, tax basis, return or NAV model is inferred.
Supported totals also require cited inventory coverage and contributing account, position, notice
and movement records. An overall needs-data status does not excuse an unsupported component label:
uncited raw observations stay visible, while complete balances and policy-current NAV subtotals are
withheld. A legal requirement and its review evidence must both be cited before a documented review
qualification is shown. See the component citation contract in [schema.md](schema.md).

## Dated funding review
Start with each account’s current settled available cash minus a separately stated protected reserve.
Historical payments/receipts are already in that cash and are never applied again. Sort unpaid call
notices and separate unpaid obligations by effective date (overdue items use request.as_of), type,
and ID. Deduct known obligations for the committed schedule. The scenario additionally deducts
active **incremental** call forecasts, never superseded/cancelled forecasts. Both stop at the supplied
policy horizon; later events remain visible as excluded. Superseded forecast links must identify a
call for the same position. There is no probability model or assumption that every commitment is
called by the horizon.

Unsettled distribution notices receive no spending credit, even if scheduled earlier than a call.
This is a conservative review convention, not a prediction or a statement about legal payment rights.
Unknown in-horizon obligations make affected later balances unknown. Missing global inventory
coverage suppresses relevant complete schedules while retaining observed events. Missing forecast
coverage suppresses only the scenario, but remains a global finding. Account deficits always surface;
a positive household sum does not make another account’s cash available or grant transfer authority.

## NAV, eligibility and manager context
Keep dated supplied NAV with age and the policy freshness limit. Stale/unknown NAV is a finding;
retain post-valuation movements without adding them mechanically to infer current value. Fund NAV
subtotals include only fully known components current under policy and may mix valuation dates;
component dates must remain visible. They are not common-date performance values or available cash.

Each supplied fund/account legal criterion has documentary requirements and an attributed review.
Check metadata, recency, citations and listed document coverage. Never compute investor eligibility
from assets, a checked box or a copied status. A required criterion marked not-applicable remains a
question until a professional revises the applicable requirement with sources. No accredited-investor,
qualified-purchaser, retirement or entity classification is selected by this script.

Consume manager-diligence artifacts; retain open/stale reports as findings and map their specific
issues into upstream_issues. The absence of an imported issue cannot be authenticated by the script.
All ready labels describe supplied-data completeness for human review only.
