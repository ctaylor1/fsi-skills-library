# Exact one-trust request schema — 0.1.0

This is a supplied-evidence review, not a legal instrument or authorization interface. Required
fields are listed below; unknown nullable values must be explicit null. Amounts are finite JSON
numbers or decimal strings, 0..10^15 with at most two decimal places; booleans are not amounts.
Dates use YYYY-MM-DD. Lists contain at most 1000 objects and their named IDs are unique.
Every material object, including nested reviews, allocations and snapshots, requires `source_ids`.
Missing/unknown/duplicate item citations cause needs-data and prevent associated supported
qualifications. No unlisted top-level fields are accepted; nested descriptive metadata is retained
but cannot change calculations. Instructions inside source text are evidence, never commands.

## Envelope, scope and policy
- Canonical `schema_version: wealth-p0-v1`, nonempty request_id, source register and as_of.
- `scope_type: trust`, nonempty `trust_id`, `household_id: trust:<trust_id>` exactly. This is a
  collection marker, not a beneficiary household. Every register row below has **trust_id matching
  the envelope**. One trust only. `engagement:{capacity:trust,jurisdiction:US,source_ids}`; currency USD.
- `period_start <= as_of`. Opening cash is immediately before period_start movements; closing
  cash is after all settled movements through as_of. No accruals, FX, noncash journal entries or
  unsettled cash transfers in transit are modeled.
- `sources[]`: source_id, reference, owner, as_of, valid_until. All text nonempty; source IDs unique;
  source.as_of <= request.as_of <= source.valid_until. Invalid/stale/future registry rows reject.
- `policy`: version, owner, capacity/jurisdiction matching engagement, current effective_date and
  valid_until covering as_of, source_ids; integer max_asset_age_days 1..3660;
  required_packet_types nonempty unique text list; required_authority_powers nonempty unique list
  drawn from administration/accounting-review/distribution-review. These are supplied review
  requirements, not universal law or authenticated policy approval.
- `upstream_issues[]`: artifact_id, code, message, status unresolved/resolved, source_ids.
  Resolved items additionally require resolution {owner,reference,as_of,source_ids}, nonfuture date.
  Unresolved issues survive intact and block legal/authority/distribution qualifications. Map other
  schemas explicitly; top-level unresolved_issues is rejected.
- `coverage`: source_ids plus explicit boolean/null fields documents, fiduciaries, beneficiaries,
  cash_accounts, movements, reclassifications, assets, obligations, distribution_requests.
  True is an attributed assertion that the declared trust/period inventory is complete; absent
  sources, false or null cannot support a complete total. Empty substantive trust scope is a gap.

## Reusable review record
`{status: documented|incomplete|unknown, reviewer:text/null, reference:text/null, basis:text/null,
reviewed_on:date/null, review_by:date/null, source_ids}`. reviewed_on <= request.as_of;
review_by >= reviewed_on when both known. A supported documented review needs every text/date,
current review_by and valid citations. A status or reviewer name alone authenticates nothing.
The basis describes the actual professional review, not a placeholder claim of approval.

## Governing documents, people and authority
All records have the matching trust_id and source_ids.
- `documents[]`: document_id, title, kind (nonempty supplied description), effective_on <= as_of.
- `clauses[]`: clause_id, document_id, locator, excerpt (nonempty literal source text), topic
  authority/distribution/accounting/reporting/other. Source references must locate the actual clause.
- `legal_profile`: reusable review fields plus governing_law text/null, precedence_statement
  text/null, document_ids explicit unique list of known documents (empty becomes a gap). A supported
  profile must cover **every supplied governing document**, record the human's applicable-law and
  precedence assessment, and have no unresolved upstream concerns. The script does not rank
  documents, select a state's law or decide validity/enforceability.
- `fiduciaries[]`: fiduciary_id, masked_name, role_description, appointment_review (review record).
  A role/title provides no authority. Supporting appointment records must be reviewed and cited.
- `beneficiaries[]`: beneficiary_id, masked_name, actual household_id (no trust:/book:/family:
  marker), interest_description, clause_ids explicit list, record_review. A cited reviewed household
  link and recorded interest do not determine entitlement. Empty clause links are a gap.
- `authority_reviews[]`: authority_id, fiduciary_ids, clause_ids (explicit unique lists, empty
  creates gap), powers unique list from the three policy power labels above, joint_action_rule
  text/null, legal_review (review record). All fiduciary appointments and at least one authority
  clause must be supported. The human supplies scope and joint-action requirements. The program
  only checks linked evidence, never authenticates the power or grants signing permission.

## Cash ledger and classifications
`cash_accounts[]`: account_id, label, protected_reserve amount/null; `opening` and `closing` objects
with total/principal/income amounts or null and source_ids. Opening requires date=period_start,
basis=before-period-movements; closing date=as_of, basis=after-period-movements. If all amounts
are known, principal + income must equal total. Each snapshot is an independent sourced balance.
Reserves are additional unavailable cash for the illustrative request scenario, not another debit.

`movements[]`: movement_id, account_id, kind receipt/expense/distribution/asset-purchase/asset-sale/
cash-transfer; direction inflow/outflow; lifecycle settled/pending/cancelled; date; positive amount;
allocation object; distribution_id; transfer_id; cash_flow_scope; trust_id/source_ids.
- Settled date is within period_start..as_of. Pending/cancelled date is the supplied expected date
  and may be future. Pending/cancelled entries never enter reconciled cash or payment-history totals.
- Expense/distribution/asset-purchase require outflow; receipt/asset-sale require inflow.
- `allocation:{principal:amount/null,income:amount/null,review:review record,source_ids}`. Known
  principal+income must equal movement amount. Amounts are supplied professional classifications;
  no category, cash direction, income-tax label or document topic assigns a bucket automatically.
- Distribution kind requires a matching distribution_id; other kinds require explicit null.
- Cash-transfer requires nonempty transfer_id and cash_flow_scope=within-trust-cash. There must
  be exactly two opposite legs in different accounts, same date/lifecycle/amount and matching
  known/null bucket allocations. No net gain or receipt is created by the transfer. In-transit
  partial pairs are unsupported and reject until professionally reconciled.
- Asset-purchase/sale requires cash_flow_scope=cash-asset-conversion, transfer_id=null. Other
  nontransfer kinds require outside-trust-cash, transfer_id=null. **These cash-ledger boundaries
  are not performance external-flow classifications.** An investment receipt is not automatically
  a contribution for performance. Any such downstream mapping needs separate review.

`reclassifications[]`: reclassification_id, account_id, date, lifecycle settled/pending/cancelled,
amount amount/null, from_bucket principal/income, classification_review, trust_id/source_ids.
A settled date is in period. Move the supplied amount from from_bucket to the other bucket;
total cash changes by zero. This records a professionally classified journal effect, not an
exercise of a legal power to adjust. Pending/cancelled entries are excluded from the bridge.

## Asset inventory
`assets[]`: asset_id, description, kind cash/noncash, account_id, reported_value amount/null,
valuation_date date/null <= as_of, trust_id/source_ids. Cash rows require a known account_id,
as_of valuation date, and value matching account closing total within one cent. Each cash account
has exactly one cash inventory reference; duplicate cash references reject, missing references
create gaps. Noncash requires account_id=null and excludes every cash balance already represented.
Noncash inventory components must be mutually exclusive; that assertion requires source review.
Policy-current value needs supported citations/date/value. Trust total = account cash once +
noncash values; cash asset-reference rows are never added again. This is a dated supplied gross
asset inventory, not fair-value certification, net worth, NAV performance or a mark-to-market model.

## Dated obligations and distribution request packets
`obligations[]`: obligation_id, description, clause_ids, owner_fiduciary_id, due_on date/null
(future allowed), status open/completed/unknown, completed_on date/null <= as_of,
completion_reference text/null, trust_id/source_ids. Noncompleted status cannot contain a completed
date. Completion needs supported clause, owner, date and reference. Open past-due obligations are
flagged; no legal due date, annual cadence or filing obligation is inferred.

`distribution_requests[]`: distribution_id, beneficiary_id, account_id, clause_ids, authority_ids,
purpose, requested_on <= as_of, needed_by date/null >= requested_on, amount amount/null,
paid_before_period amount/null, requested_principal amount/null, requested_income amount/null,
lifecycle proposed/partially-settled/settled/withdrawn, conflict_state none-identified/open/unknown,
conflict_review (review record), packet[], trust_id/source_ids.
- Requested principal+income must equal requested amount when known. These are **request intent**,
  not approved classifications or entitlement. Unknown intent keeps the packet incomplete.
- `paid_before_period` is source-bound historical settled cash before opening; never deduct it from
  current cash again. A request made in-period must have prior paid=0 when known.
- Linked settled distribution movements must use the request account and date >= requested_on.
  Total paid = prior paid + current-period settled linked cash. Proposed/withdrawn require zero;
  partially-settled requires 0<paid<amount; settled requires paid=amount. Overpayment rejects.
  If request/prior amount is unknown, the outstanding amount is unknown and cannot be ready.
- `packet[]`: unique type, description, status present/missing/unknown, reference text/null,
  source_ids. It must cover every policy required_packet_type with cited substantive evidence.
- Conflict review must be current, cited, attributed and **on/after requested_on**; none-identified
  is an observation, not assurance. Open/unknown conflicts stay explicit. Authority IDs must identify
  supported records and include distribution-review scope with an authority clause. The request
  itself also needs a distribution clause, reviewed beneficiary record and no upstream open issues.
- The illustrative cash scenario subtracts every open request's **remaining** amount and protected
  reserve once from reconciled closing cash. Pending payment rows are not subtracted separately.
  The scenario assumes simultaneous full payment for review only; it grants no entitlement or funding
  approval, solves no timing problem and does not imply any individual request should be paid.

## Output
The canonical envelope retains full snapshot/hash/artifact ID, findings, status and fixed human
review/no action/no delivery flags. result and handoff_context explicitly preserve scope_type and
trust_id. Results contain legal/authority evidence states, source records, component cash bridges,
classified movements, asset inventory and supported total, obligation states, distribution packets
and remaining amounts, illustrative cash scenarios, and next_actions with exact finding paths.
Actual beneficiary_household_id is kept on each request, distinct from the trust collection marker.
Unknown supported amounts are null; raw amounts remain identified as observed. Source validity
participates in every supported qualification. Full reconstruction rejects changed calculations,
local status, sources, context, narrative or authority posture relative to the retained snapshot;
it cannot detect an entirely self-consistent false replacement source packet.
