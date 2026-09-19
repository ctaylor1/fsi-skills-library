# Exact request and output schema

All listed domain fields are required unless explicitly described as optional. An explicit null
is permitted only where stated; blank text is not null. Amounts are finite JSON numbers or decimal
strings from 0 to 10^15, **at most two decimal places**; booleans are not numbers. Notice and settled
movement cash amounts must be positive. USD only, no FX. Lists have at most 1000 records; listed
ID keys must be unique. IDs and ordinary text must be nonempty. Dates are exact YYYY-MM-DD.
No unlisted top-level fields are accepted. Additional nested descriptive metadata is retained in
the snapshot but does not extend the supported arithmetic or introduce a decision instruction.

## Common envelope
- `schema_version`: `wealth-p0-v1`; `request_id`, `household_id`, `as_of` date.
- `engagement`: capacity advisory/brokerage/private-bank/trust; jurisdiction US; `source_ids`.
- `sources[]`: source_id, reference, owner, as_of, valid_until. Unique source IDs, nonempty text,
  source.as_of <= request.as_of <= source.valid_until. Invalid/stale/future registry entries reject.
- Every material domain object below requires individual `source_ids` referencing this registry.
  Missing, empty, duplicate or unknown item citations produce needs-data, not invented evidence.
- `policy`: version, owner, capacity/jurisdiction matching engagement, effective_date/valid_until
  covering request.as_of, source_ids; `max_nav_age_days` integer 1..3660 and `horizon_date` >= as_of.
  These values are supplied review choices, not universal standards or authenticated approval.
- `upstream_issues[]`: artifact_id, code, message, status unresolved/resolved, source_ids.
  Resolved requires `resolution:{owner,reference,as_of,source_ids}`, as_of <= request.as_of.
  Missing attribution rejects; missing resolution citations remain findings. Explicit [] means the
  reviewer inspected upstream artifacts and found no unresolved issues. Unmapped `unresolved_issues` rejects.
- `currency`: USD.
- `coverage`: source_ids plus explicit boolean/null `positions_complete`, `notices_complete`,
  `movements_complete`, `forecasts_complete`, `other_obligations_complete`. Completeness means the
  entire declared household/account scope, with all notices/movements **since position inception**.
  False or null blocks readiness; no presumed empty inventory.

## Accounts and positions
`accounts[]`: account_id, label, cash_as_of exactly request.as_of, cash_basis exactly
`available-settled-cash-as-of`, available_cash amount/null, protected_reserve amount/null, source_ids.
Cash already reflects every settled historical cash movement. It excludes uncollected distributions,
unsettled proceeds, facilities and unapproved cross-account funding. Protected reserve is additional
cash unavailable for the listed obligations; do not also duplicate it in other_obligations.

`positions[]`: position_id, account_id referencing accounts, fund_id, fund_name, inception_date <=
as_of, commitment_amount amount/null, commitment_basis exactly
`current-operative-total-including-amendments`, reported_uncalled amount/null,
reported_outstanding_calls amount/null, source_ids. Account/fund pairs must be unique: aggregate
same-account interests professionally before extraction. Commitment is the current effective
contractual total including supported amendments, before the separate recallable adjustment below.
Reported balances must first be mapped to this package’s definitions, not raw ambiguous “unfunded”.

Each position also requires:
- `nav:{amount:amount/null,valuation_date:date/null,source_ids}`. Date between inception and as_of.
  Unknown amount/date or age above policy limit produces a finding. No current mark is inferred.
- `eligibility_requirements[]`: criterion_id, description, legal_basis, nonempty unique
  `required_documents:[document identifiers]`, source_ids. These fund/account-specific requirements
  come from the supplied legal applicability review, not a rule chosen by the script. Empty is a gap.
- `eligibility_evidence[]`: criterion_id matching a requirement, status
  documented/incomplete/unknown/not-applicable, rationale, reviewer text/null, review_date date/null
  <= as_of, review_by date/null >= review_date, unique document_refs list (may be empty), source_ids.
  A documented record needs an attributed current review, every required document ID and citations.
  Incomplete/unknown/not-applicable never bypass a supplied required criterion. A documented label
  means an attributed substantive review was performed; the script cannot inspect source prose.
- `manager_diligence`: explicit null or {artifact_id,input_hash,status:review-ready/needs-data,
  review_date<=as_of,review_by>=review_date,source_ids}. input_hash is 64 lowercase hex characters.
  The reference must identify the shared manager-diligence artifact and its request hash. Null,
  needs-data, stale review_by or missing citations blocks readiness. Import all substantive unresolved
  findings into upstream_issues even if the referenced artifact contains a misleading ready label.

## Notices, settled movements and forecasts
`notices[]`: notice_id, position_id, kind call/distribution, purpose
investment/management-fee/expense/proceeds/other, lifecycle notice/partially-settled/settled/cancelled,
notice_date between position.inception_date and as_of, due_date >= notice_date (future allowed),
amount positive, commitment_effect_amount amount/null <= amount, classification and source_ids.
- Call classification: inside-commitment (effect=amount), outside-commitment (effect=0), mixed
  (0<effect<amount). Effect is the portion consuming contractual commitment; fees are not assumed outside.
- Distribution classification: recallable (effect=amount), non-recallable (effect=0), mixed
  (0<effect<amount). Effect is the supported amount restoring callable commitment, not income or tax basis.
- Unknown effect is null and always a finding, even if a classification label is provided.
- Gross call and distribution notices stay separate. Do not enter netted obligations, noncash/deemed
  capital, in-kind distributions, clawback rights, secondary transfers or unsupported commitment releases.

`movements[]`: movement_id, notice_id, settled_date from notice_date through request.as_of,
amount positive, commitment_effect_amount amount/null <= amount, external_flow_scope
within-household/outside-household, source_ids. These are **settled** payments/receipts only;
pending movements stay unpaid on the notice. External scope is explicitly relative to the supplied
household valuation perimeter, independent of inside/outside commitment and fund reporting scope.
A fund investment funded from another included household account is within-household. Do not
map these amounts automatically into performance cash flows without the target valuation perimeter.

For each notice, sum linked cash settlements. Notice/cancelled states require zero settlements;
partially-settled requires 0<sum<notice amount; settled requires exact equality. Overpayment rejects.
Known settled commitment effects cannot exceed notice effect; remaining commitment effect cannot
exceed remaining cash, and fully settled effects must equal notice effect. Unknown effects produce
unknown commitment totals. Partial payments use their actual supplied effect allocation, never pro-rata guessing.

`forecasts[]`: forecast_id, position_id, expected_date >= as_of, amount amount/null, lifecycle
active/superseded/cancelled, scope exactly `incremental-to-notices`, superseded_by_notice_id,
source_ids. Superseded requires an existing **call** notice for the same position; otherwise this
field is explicit null. Only active forecasts enter the scenario budget. They never change actual
commitment, notice or settled totals. Their scope is a sourced professional assertion that they are
additional to known notices; the script cannot discover semantic duplicates hidden in documents.

`other_obligations[]`: obligation_id, account_id, description, due_date (past/future allowed),
amount amount/null, lifecycle unpaid/settled/cancelled, scope exactly
`excludes-private-capital-notices`, source_ids. Only unpaid enters the forward budget. Exclude
private calls, protected reserves and anything already included in available settled cash.

## Output
The canonical envelope includes full input hash/artifact ID, evidence context, status and findings,
with human_review_required true, action_taken false and delivery_status not-delivered.
`result` retains input_snapshot, policy, upstream_issues, handoff_context and scope; plus:
- positions: original record, ledger completeness, observed settled cash totals, outstanding calls,
  remaining commitment including unpaid calls, reserved commitment, uncalled commitment,
  uncalled_plus_outstanding_calls, NAV age/current-under-policy, post-NAV movements and eligibility evidence.
- notice_ledger: original notices, linked settlements, outstanding cash/commitment effect.
- settled_movements: original date/scope/citations enriched with kind, position/account/fund IDs.
- forecasts, other_obligations; fund_summaries with known-only commitment totals and policy-current
  NAV subtotal (component valuation dates remain in positions; it is not a common-date valuation).
- account_liquidity: cash after reserve, dated schedule, known-obligation and forecast-scenario
  balances, plus excluded_beyond_horizon. household_liquidity aggregates accounts as information;
  transfer_authority_assumed is false and an account shortfall remains a finding despite aggregate excess.
- specialist_questions derived from every finding; eligibility_decision not-determined and
  investment_recommendation not-made. Monetary outputs are two-decimal strings; unknowns are null.

All result content is reconstructed from the full snapshot during output validation. This detects
edits/omissions relative to that snapshot; it cannot authenticate a self-consistent false replacement
input, prove document content or establish professional authority.

## Citation qualifications within the result
`ledger_complete` and supported position balances require cited coverage, engagement/policy,
account/position identity and every contributing notice/movement. Unknown commitment effect
amounts suppress commitment balances independently of otherwise supported cash amounts. Uncited
coverage cannot support a complete funding schedule or complete fund NAV subtotal.

Notice-ledger arithmetic is explicitly `calculation_basis: observed-supplied-records`, with
`evidence_supported` stating whether the notice and its linked movements have valid citations.
Raw position/NAV/evidence records and observed settled subtotals remain visible even when support
is missing. They are not substitutes for the null supported totals.

`nav_current_under_policy` requires supported policy/context, position/account and NAV evidence.
Eligibility evidence can be `documented-for-human-review` only if both its supplied legal requirement
and substantive review record are cited, with supported position/account and engagement/policy context.
A raw `status: documented` in the original evidence record remains an attributed observation.

Cash opening balance requires supported account/context evidence; the separate
`observed_opening_cash_after_reserve` retains supplied arithmetic without that qualification.
Complete forward budgets require cited coverage and the account's position/notice/movement records.
Each dated event also carries `evidence_supported`: an uncited other obligation suppresses subsequent
known and scenario balances; an uncited forecast suppresses the scenario only. Earlier supported
balances remain visible. An unrelated account's supported schedule is not automatically suppressed.
