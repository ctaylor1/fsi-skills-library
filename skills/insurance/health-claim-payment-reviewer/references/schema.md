# Native schema

The required envelope is `case_id` (durable nonblank text), `as_of` (YYYY-MM-DD),
`context` {capacity, represented_party, object_id, jurisdiction, line_of_business},
`sources` [{source_ref, version, as_of, locator}], `unresolved_issues` (explicit list
of open questions), and `data` (object). Source IDs are unique, source dates known
and no later than review as_of. Every evidence row has nonempty `source_refs`
resolving those source IDs and a nonblank `locator` identifying actual source text.
The source locator and a reviewer name do not authenticate evidence.

`data.owner`, `market`, `program`, `product` are nonblank actual scope values.
The profile belongs at **data.profile**. Required profile keys: `profile_id`,
`version`, `reviewed_by`, `source_refs`, `jurisdictions`, `lines_of_business`,
`effective_from`, `effective_to`, `method`, `markets`, `programs`, `products`,
`rule_basis`, `limitations`. Arrays explicitly contain the actual scope. Profile
dates are inclusive around as_of; every criterion/code/contract/clock separately
has inclusive dates around its event basis. A region alone cannot select a rule.

Inventories are explicit arrays of objects with unique nonblank ID keys. Absent or
null inventories are unknown, never confirmed empty. Unknown factual values may
be null and produce dependent gaps; malformed non-null dates/numbers/types fail
structural validation. All required evidence fields must be supplied to obtain an
evaluable result. Decimal inputs use exact decimal strings; integer JSON numbers
are allowed. Fractional JSON floats, booleans, NaN and infinity are rejected.
Null numbers remain unknown. Numeric values are nonnegative unless stated signed. Arithmetic supports up to 256
significant digits and exponent magnitude 1000; overflow or any rounding requirement
fails closed rather than silently truncating.
`source_refs` and explicit string arrays contain nonblank references/tokens.

Optional `upstream_artifacts` and `context_mappings` follow workflow-contract.md.
One reviewed source-bound mapping is required for changed capacity, represented
party, object, jurisdiction or line. Unresolved upstream/input issues withhold
dependent arithmetic. Output retains immutable source_document, findings, native
results and artifact. Native decimal outputs are strings; unavailable values are
null. No output may promote action, approval, human review or execution flags.

## Payment data

`context.capacity` is `payer-payment-integrity-review`; `line_of_business` is
`health`; context.object_id is the single claim_id. `data.profile.method` is
`health-claim-payment-v1`. `data.currency` is one nonblank currency identifier.
No currency conversion or implicit rounding is supported.

Reusable **line identity** means claim_id, line_id, provider_id, product,
service_id, service_on. **Code identity** means provider_id, product, service_id,
code, code_version, modifiers. All identity fields are nonblank strings except
modifiers (explicit unique string array, including []), and service_on (YYYY-MM-DD).
Modifier arrays are ordered exact identities: never sort or deduplicate to repair a
mismatch. Values are opaque; fixtures contain no actual CPT/UB codes or descriptions.

| Field | Required shape / meaning |
| --- | --- |
| `inventory` | Object: complete boolean/null, source-bound statement, source_refs, locator |
| `events` | Array keyed by unique event_id; all claim-line events through review date |
| `events[].event_id`, `chain_id` | Exact event and economic chain identities |
| `events[].event_type` | `original`, `replacement`, or `void` |
| `events[].prior_event_id` | Null only for original; replacement/void binds existing non-void predecessor |
| `events[]` line identity | Full reusable line identity; service date is no later than as_of |
| `events[].code`, `code_version`, `modifiers` | Opaque coded service identity and explicit modifier array |
| `events[].recorded_on` | Known event date, no earlier than service_on and no later than as_of; chain dates nondecreasing |
| `events[].units`, `billed` | Nonnegative exact decimals/null; required for active terminal |
| `events[].code_profile_id`, `contract_id` | Exact profile/contract references; required for active terminal |
| `events[].source_refs`, `locator` | Claim event source bindings |
| `chains` | Array keyed by chain_id; one attested connected path per economic line |
| `chains[].terminal_event_id`, `complete`, `statement` | Exact terminal event, true/false/null and explicit source confirmation of complete history |
| `chains[].source_refs`, `locator` | Chain-attestation bindings |
| `code_profiles` | Array keyed by code_profile_id |
| `code_profiles[]` code identity | Exact match to active terminal identity |
| `code_profiles[].market`, `program` | Exact actual case scope |
| `code_profiles[].version`, `reviewed_by`, `effective_from`, `effective_to` | Known profile labels, inclusive service-date applicability |
| `code_profiles[].file_version`, `replacement_status` | Exact quarterly/replacement identity; only `current` supports calculation |
| `code_profiles[].current_file_statement`, `adoption_basis`, `licensed_use_basis` | Sourced current-file assertion, payer adoption and permitted-use basis |
| `code_profiles[].max_units` | Supplied nonnegative unit ceiling; no code selection or clinical interpretation |
| `code_profiles[].incompatible_codes` | Explicit unique opaque-code array, [] only with complete supplied edit inventory |
| `code_profiles[].source_refs`, `locator` | Rule/profile source bindings |
| `contracts` | Array keyed by contract_id |
| `contracts[]` code identity | Exact terminal provider/product/service/code/version/modifier identity |
| `contracts[].version`, `reviewed_by`, `effective_from`, `effective_to` | Known labels and inclusive dates covering service date |
| `contracts[].method`, `rounding` | Exactly `unit-rate-exact`, `none` |
| `contracts[].rate_per_unit`, `currency`, `allowance_basis` | Nonnegative exact rate, exact case currency, source contract basis |
| `contracts[].source_refs`, `locator` | Allowance source bindings |
| `allocations` | Explicit array keyed by allocation_id; one independently supplied row per active terminal |
| `allocations[].event_id` and line identity | Exact terminal event and full line identity |
| `allocations[].allowed`, `member_cost_share`, `other_payer`, `other_adjustment`, `payable` | Explicit nonnegative decimals/null; never default missing components to zero |
| `allocations[].currency`, `benefit_basis`, `source_refs`, `locator` | Exact currency, source benefit allocation basis and locators |
| `payments` | Explicit array keyed by payment_id; exactly one net ledger snapshot per chain |
| `payments[].event_id`, `chain_id` and line identity | Exact terminal and chain identity |
| `payments[].record_kind` | Exactly `net-payment-snapshot`; historical incremental payment summing unsupported |
| `payments[].net_paid` | Signed exact decimal/null, includes supplied reversals; no inferred ledger netting |
| `payments[].as_of` | Snapshot date no earlier than terminal recorded_on and no later than review date |
| `payments[].currency`, `source_refs`, `locator` | Exact currency and ledger source bindings |

## Results and missingness

`results.lines` retains chain/event identities, chain_resolved, excluded_void,
coding_state, paired_event_ids (active evaluable lines), expected_allowed,
expected_payable, recorded_net_paid, payment_variance,
allocation_identity_difference, medical_necessity and patient_liability.
Coding states: `not_determined`, `no-supplied-edit-flag`, `flagged-for-review`,
`excluded-void`. A clean supplied edit check does not certify correct coding.

A chain has exactly one original, a connected unbranched path, known terminal and
source-attested completeness. Replacement events replace prior events; amounts are
not added across the chain. A void excludes expected service amounts but retains a
net-payment snapshot and flags any nonzero residual balance. Multiple chains sharing
claim_id/line_id are ambiguous even if their providers differ; all dependent line
amounts are withheld. Unresolved chains withhold amounts for other lines too because
paired-code checks may depend on the missing terminal. Every event must belong to a
chain, and allocations cannot refer to superseded/void events.

Expected allowed = terminal units × exact contract rate. It is withheld on coding
edit flags or any identity/date/profile/contract gap. Paired-code checks compare
active terminals with same claim/provider/service date/code version. These are only
the supplied maximum-unit and incompatible-pair edits, not a full NCCI engine.

Independent allowed − member cost share − other payer − other adjustment must equal
independent payable, and independent allowed must equal contract expected allowed.
Expected payable is released only after both identities pass. Recorded net paid is
kept independently when its own bindings pass. Variance = recorded net paid minus
expected payable; positive/negative differences are review signals, not recoveries,
debts or patient liability. Unknown allocation does not erase an independently valid
contract allowance or ledger fact. Any gap withholds whole-case totals. No implicit
currency rounding, contracted lesser-of-billed rule, diagnosis review, benefit
selection, adjudication, notice, recovery, code assignment or payment occurs.
