# Controls and review boundary

## Executable controls

Input validation rejects unsupported object/list shapes, non-finite JSON and invalid domain values before arithmetic. Numeric booleans are not numbers. Output validation reconstructs the whole output from a separately retained original, checks the complete canonical input hash and keeps source_truth unverified. A changed output, hidden extra field, embedded original or substituted original fails. Native output cannot carry unchecked authored narrative.

Unknown principal, coupon, maturity and security must remain distinct from zero and unsecured. Currency totals never cross currencies. Validate exact output against the original schedule, including every contributing instrument and all buckets. Entity association and source authenticity remain analyst review responsibilities.

## Declared institutional controls

References, source classifications, approved/eligibility flags, identity labels and recorded roles are caller assertions. These helpers do not authenticate providers or people, verify licenses, retrieve complete source documents, enforce an information barrier, determine applicable law or certify professional review. Institution-owned source-access controls, confidentiality/MNPI restrictions, retention, legal/compliance review and action authorization remain required where applicable. No system-of-record write, live publication, transaction, lender approval or external delivery is bound.

## Partial evidence and escalation

`instruments[]` retains identity, amount, currency, coupon, maturity, security assertion and source reference. `by_currency` holds each currency inventory and coverage flags. A single-currency packet exposes those fields at the top level; mixed-currency top-level totals and averages are null. `total_debt` is null if principal coverage is incomplete; `known_principal` is a labeled subtotal. Unknown maturity uses an `undated` bucket and withholds full WAM and near-term totals. Unknown coupon withholds full WAC; separately labeled known-subset averages retain their own denominators. Missing principal stays in detail and `excluded_instruments`.

Software validation proves faithful bounded computation only. Distinguish method/instrument/sector/accounting/jurisdiction applicability, practitioner acceptance, institutional acceptance, deployment acceptance and authenticated action authority. A faithful partial may be usable evidence while its data/review gates remain held. Never fill a missing input from a synthetic fixture.
