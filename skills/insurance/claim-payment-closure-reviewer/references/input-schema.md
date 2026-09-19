# Native input and output contract

Top level: `case_id`, calendar `as_of`, `context` with capacity, represented_party,
object_id, jurisdiction and line_of_business, versioned `sources`, explicit
`unresolved_issues`, optional `upstream_artifacts`, `rule_profile`, and native `data`.
Each source has source_ref and version, with optional source as_of. Duplicate source
IDs reject; distinguish versions explicitly. All domain evidence rows reference the
source registry through source_refs. Missing business amounts are JSON null; numeric
strings or numbers must be finite. Booleans are not monetary numbers.

Rule profile: profile_id, version, source_refs, effective_from, effective_to,
jurisdictions and lines_of_business. The profile is supplied reviewed evidence, not
a built-in legal opinion. Dates must be YYYY-MM-DD. The complete example documents
native field names and supported enums alongside the method reference.

Output: standardized case/context/as_of, source_document, findings, native results,
status, completeness, evaluability, unresolved_issues and insurance artifact. Status
ready-for-review is a draft readiness state only. Null means unknown/unavailable,
not zero. Review findings may exist in an otherwise evaluable draft. No output
selects a professional outcome or executes an action.

Closure reopening conditions are structured evidence rows: `reopen_triggers` must be a nonempty array of objects with nonblank `trigger`, `owner`, `routing`, and resolvable `source_refs`. A string, blank row, or unassigned owner/routing blocks closure readiness, even when all payments are settled.

## Native `data` sections

Supply `payment_request`, `authority`, `history_review` and `closure` as objects;
`payment_history` and `gates` are arrays of objects. Missing information generally
creates a gap. Use explicit empty arrays for completed negative searches, never
null or an omitted array as evidence that nothing exists. Identity fields should
be stable deidentified identifiers. The helper does not authenticate approvals,
verify bank details, perform sanctions screening or query a payment system.

### Payment request and authority

| Field | Contract |
| --- | --- |
| `payment_request.payment_id` | Nonblank proposed/reviewed transaction identity. |
| `payment_request.claim_id` | Nonblank claim identity, exactly matching `context.object_id`. |
| `payment_request.payee_id` | Nonblank payee identity. |
| `payment_request.obligation_id` | Nonblank stable underlying obligation identity, so a new payment ID does not hide a duplicate obligation. |
| `payment_request.amount` | Positive finite number or decimal string. Null/missing is unknown; zero creates a gap; negative, boolean, malformed or nonfinite values reject. |
| `payment_request.currency` | Nonblank currency label. |
| `payment_request.source_refs` | Registered request/obligation evidence. |
| `authority.claim_id`, `authority.payee_id` | Must exactly match the request. |
| `authority.limit` | Nonnegative finite amount; requested amount must not exceed it. |
| `authority.currency` | Must exactly match request currency. |
| `authority.approval_state` | Must equal `approved` for draft readiness; this records supplied evidence, not approval granted by the assistant. |
| `authority.approver` | Nonblank recorded approver. |
| `authority.effective`, `authority.expiry` | Calendar dates whose inclusive interval contains review `as_of`. |
| `authority.source_refs` | Registered delegation and approval evidence. |

Missing identity/authority facts, mismatched currency/claim/payee or unavailable
current authority block payment readiness. Exceeding the amount limit is a review
blocker. Malformed non-null dates reject; missing/null dates produce a gap. This is
the supported claim/payee/amount/date authority model, not a complete enterprise
multidimensional delegation engine.

### History and operational gates

`history_review` contains `complete: true` and nonempty `source_refs` documenting
that relevant history is complete for this review. A genuine no-history result uses
`payment_history: []` plus that attestation. Missing/null history is a gap; a non-list
history rejects.

Every `payment_history[]` row contains unique nonblank `payment_id`, nonblank
`claim_id`, `payee_id`, `obligation_id`, `currency`, a nonnegative finite `amount`,
nonempty `source_refs`, and `state` equal to `pending`, `submitted`, `settled`,
`cancelled` or `failed`. Missing/duplicate payment IDs or invalid state reject.
Missing other facts produce gaps; malformed monetary values reject. History is a
current transaction snapshot, not multiple events with the same payment ID.

A pending/submitted/settled row blocks another payment when either its payment ID
matches the request or its claim and obligation IDs match the request. Cancelled
and failed rows do not trigger that duplicate rule. This check is not a live
processor idempotency guarantee.

Each `gates[]` row contains unique nonblank `gate_id`, `category`, `state` and
`source_refs`. The seven required category names are `coverage`, `payee_verification`,
`sanctions`, `liens`, `settlement_document`, `bank_verification` and `authority`.
Additional categories can be retained and reviewed; they do not substitute for a
missing required category. These are the helper's operating evidence categories,
not universal legal requirements.

`state` must be `pass`, `fail`, `unknown` or `not_applicable`; invalid/missing state
rejects. Fail or unknown blocks payment readiness. A `not_applicable` row additionally
requires nonblank `reviewer_rationale`; it is not inferred. Registered evidence is
required for every gate, including not-applicable assertions. Duplicate/missing gate
IDs reject; missing required categories create gaps.

### Closure and reopening

| `closure` field | Contract |
| --- | --- |
| `source_refs` | Registered closure-review and reconciliation evidence. |
| `open_obligations` | Array of outstanding obligations. Only an explicit empty array supports closure. Missing/null is unknown; a non-list rejects. The helper preserves entries and does not itself discover omitted obligations. |
| `remaining_case_reserve` | Nonnegative finite reviewed balance. Exactly zero is necessary for closure readiness; null/missing is unknown. A nonzero balance requires reviewed disposition, not an automatic release. |
| `payment_reconciled` | JSON `true` recording reviewed reconciliation; insufficient by itself without settled-history matches below. |
| `required_payment_ids` | Nonempty array of payment IDs required for closure, including the reviewed request's payment_id. Each must match a settled history row for the request claim. |
| `reopen_triggers` | Nonempty array of structured rows described below. |

For the reviewed request's settled match, payee, obligation, currency and amount must
also match exactly (numeric amount comparison). The request being ready for payment
review does not imply that payment is settled. A duplicate-payment finding alone
can coexist with ready closure review because it prevents repeating a payment that
has already settled. Other pre-closure blockers still prevent closure readiness.

Each `reopen_triggers[]` row has nonblank `trigger`, `owner`, `routing` and a nonempty
array of registered `source_refs`. A free-text string, blank row, missing owner or
unresolved routing creates a gap and blocks closure. No trigger is monitored or
executed automatically. Preserve the responsible role and actual handoff route.

## Native results and independent readiness

`payment_review_status` and `closure_review_status` each equal `blocked` or
`ready_for_authorized_review`. Payment readiness is computed before closure findings,
so an open recovery or unresolved reopening plan can block closure without blocking
an otherwise supported new payment review. Conversely, a settled payment can support
closure while its duplicate-payment finding blocks another payment.

Results also retain `payment_request`, `duplicate_transactions`, `gate_matrix`,
`open_obligations`, `reconciled_payment_ids` and structured `reopen_triggers`.
`payment_executed`, `claim_closed` and `claim_reopened` remain false. An overall
needs-data/needs-review artifact or inherited unresolved issue must remain visible
alongside either local readiness value; neither value grants execution authority.
