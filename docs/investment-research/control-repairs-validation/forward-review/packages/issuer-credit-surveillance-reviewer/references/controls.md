# Controls and review boundary

## Executable controls

Input validation rejects unsupported object/list shapes, non-finite JSON and invalid domain values before arithmetic. Numeric booleans are not numbers. Output validation reconstructs the whole output from a separately retained original, checks the complete canonical input hash and keeps source_truth unverified. A changed output, hidden extra field, embedded original or substituted original fails. Native output cannot carry unchecked authored narrative.

Maturities require instrument ID, legal issuer ID, matching currency, amount, source and exact-date/year consistency. Repeated instrument rows require consolidation in a reviewed adapter. Spreads must reference a market source and identified instrument/issuer, spread type and currency. Agency opinions must reference a rating-agency source and identify issuer vs instrument object; the packet assigns no rating. Covenant flags require instrument/document/version. Source-type mismatches fail before computation. Approval person/role strings are assertions; distinct preparer/reviewer labels do not authenticate people.

## Declared institutional controls

References, source classifications, approved/eligibility flags, identity labels and recorded roles are caller assertions. These helpers do not authenticate providers or people, verify licenses, retrieve complete source documents, enforce an information barrier, determine applicable law or certify professional review. Institution-owned source-access controls, confidentiality/MNPI restrictions, retention, legal/compliance review and action authorization remain required where applicable. No system-of-record write, live publication, transaction, lender approval or external delivery is bound.

## Partial evidence and escalation

Packet sections, metrics, basis, source assertions, tie-outs, changes, source-linked maturity/instrument detail, reported rating object identity, covenant instrument/document/version, flags, approvals and unresolved issues are retained. `support_status` is `PARTIAL` for unresolved data/review gates, otherwise `SUPPLIED_INPUT_REVIEW`. Neither means institutional acceptance. A faithful partial can pass reconstruction while its data/review gates stay held. Action fields remain reported-only / none / unchanged.

Software validation proves faithful bounded computation only. Distinguish method/instrument/sector/accounting/jurisdiction applicability, practitioner acceptance, institutional acceptance, deployment acceptance and authenticated action authority. A faithful partial may be usable evidence while its data/review gates remain held. Never fill a missing input from a synthetic fixture.
