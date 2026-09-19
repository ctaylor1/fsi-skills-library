# One-trust review and financial identities

## Evidence and authority
The supplied legal profile must cover every governing document and give an attributed current
applicable-law and precedence assessment. The program preserves this statement without choosing
an interpretation. A clause must retain its document, locator and excerpt. A role/title alone
cannot qualify authority: require appointment review, linked authority clauses, named fiduciary
IDs, reviewed powers and joint-action requirements. Required power coverage comes from supplied
policy. An authority record is evidence for human review, never a signing credential.

Beneficiary records link actual household IDs and recorded interest descriptions. The software
checks documentary completeness, not entitlement, identity authentication or the correct reading
of a dispositive provision. Unresolved upstream concerns prevent legal/authority/distribution
qualifications; supported financial arithmetic may still be useful while legal questions remain.

## Cash, principal and income
Opening balances precede every period_start movement. Closing balances follow every settled
movement through as_of. Preserve pending/cancelled rows but exclude them from all cash bridges.
For each account and bucket:

```
expected_total_cash = opening_total + settled_inflows - settled_outflows
expected_principal_cash = opening_principal + signed settled principal allocations
                          + reclassifications into principal - reclassifications out
expected_income_cash = opening_income + signed settled income allocations
                       + reclassifications into income - reclassifications out
reconciliation_difference = independently_reported_closing - expected_closing
```

A reclassification changes total cash by zero. An internal transfer has exactly two opposite
same-date/lifecycle legs in different cash accounts with matching amounts/allocations. It changes
account balances and leaves total trust cash unchanged. Unsupported transfers in transit reject.
Purchasing an asset reduces cash but does not automatically create a loss; the separate noncash
inventory contains the supplied dated asset value. No asset-return or total-wealth bridge is inferred.

Numbers use Decimal cents. Known movement allocations must add to gross cash. Known principal and
income snapshot amounts must add to total cash. Reconciliation differences greater than one cent
are findings. The one-cent reporting comparison tolerance is a package convention, not a legal rule.
Missing amounts, classifications, human classification review or citations make affected supported
bridge components null. A known total cash bridge can remain available while bucket allocations
are unknown. Raw balances remain identified as observed, not complete or legally classified.

## Asset inventory
Cash inventory rows reference cash accounts and independently tie to closing cash; they are not
added again. Gross reported trust assets = supported account cash once + supported noncash values.
Every cash account needs one cash inventory reference. Noncash rows must not overlap each other
or contain embedded cash counted elsewhere; source review establishes that inventory fact.
Uncited, unknown or stale values cannot support a complete asset total. Dated values within the
supplied policy age limit may have different dates and are not a common-date price estimate.
Liabilities are not modeled; gross asset inventory is not net trust equity or spendable cash.

## Obligations and distribution requests
Obligation dates and scope come from exact clauses and professional review. A completed label
needs supporting owner, date and completion reference. Past-due open duties are questions for the
administrator; no annual review, tax return or court deadline is generated from a generic rule.

A request's amount and desired principal/income split are intent only. The packet requires current
beneficiary/authority/clause evidence, all policy-required documents, a conflict review dated on or
after the request, and preserved upstream issues. No documented status decides that a beneficiary
may receive funds or that a trustee should pay. The two fixed outputs are entitlement not-determined
and payment_approval not-given.

For each request, prior settled cash + current-period settled linked payments must reconcile to
its lifecycle. Prior paid cash is already inside the opening balance and is never deducted again.
Remaining requested amount = original request - prior paid - period paid; withdrawn requests have
zero remaining after their zero-payment lifecycle check. Unknown history leaves remaining null.
Do not treat a pending movement as settled or subtract it again as another open request.

The cash scenario assumes every open request is paid in full together from its assigned account:
reconciled closing total - protected reserve - supported remaining requests. This is a clearly
labeled arithmetic stress illustration, not timing optimization, legal availability, entitlement,
authorization, a distribution recommendation or permission to use another account's cash.
