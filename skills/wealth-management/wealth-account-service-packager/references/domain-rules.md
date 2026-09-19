# Domain rules and input schema

## Common required contract
The top-level `schema_version` is `wealth-p0-v1`; supply `request_id`, `household_id`, exact ISO
`as_of`, `engagement` with `capacity` (advisory, brokerage, private-bank or trust), US
`jurisdiction`, and item-level `source_ids`. `sources` is a nonempty register of unique
`{source_id, reference, owner, as_of, valid_until}`. Every registry source must satisfy
`source.as_of <= request.as_of <= source.valid_until`; stale/future evidence rejects input.

`policy` requires nonempty `version`, `owner`, matching `capacity`/`jurisdiction`, current
`effective_date`/`valid_until`, `source_ids`, and the domain configuration below. Policy
version/owner/date fields describe supplied records; they do not authenticate institutional approval.
`upstream_issues` is an explicit array (empty is permitted) of
`{artifact_id, code, message, status: unresolved|resolved, source_ids}`. Unresolved issues
propagate into findings; resolution claims remain attributed supplied evidence.

Each material object below requires `source_ids`, including nested assumptions, conditions,
beneficiaries, resources, observations and criterion definitions. Unknown or missing item sources
produce `needs-data`. Numeric unknowns remain null; no conversion of blanks into zero.
Registers are arrays of at most 1000 objects, IDs unique within each register. IDs are opaque,
not account numbers. Text identifiers must be nonempty. Numeric values must be finite and
booleans do not count as numbers. Currency-supported workflows accept USD only; no FX defaults.

The snapshot/hash binds the supplied JSON, not the underlying source truth. Output validation
rebuilds the entire domain result and compares all content, identities, arithmetic and findings,
in addition to checking the canonical envelope. A self-consistent replacement snapshot could
still be false: compare it with approved source systems during human review.

## Service domain records

`policy.service_requirements` maps each of transfer/distribution/authority/beneficiary to an
explicit nonempty list of unique requirement keys. The sourced firm/custodian policy defines
which identity/authority, consent, signatures, tax, eligibility, destination, sanctions or
specialist records it requires; the script does not invent a universal regulatory checklist.

- `parties[]`: unique `party_id`, masked `display_name`, `source_ids`.
- `accounts[]`: unique `account_id`, registration individual/joint/ira/trust/entity, `currency`
  USD, nonempty `owner_party_ids[]`, `available_cash` (nonnegative number or null), `positions`
  (list or null), `source_ids`. Positions contain unique `security_id`, nonnegative numeric
  `quantity`, `source_ids`. Null positions means unknown; an empty list asserts a supplied empty schedule.
- `requests[]`: unique `service_request_id`, supported `type`, `account_id`,
  `requested_by_party_id`, historical ISO `requested_date`, `source_ids`, `details` below.
- `conditions[]`: unique `condition_id`, `service_request_id`, firm-defined `requirement`,
  `status` received/missing/conflicting/not-applicable, `description`, `source_ids`.
  Required evidence must have exactly one `received` record. A not-applicable exception remains
  open for operations review; it cannot silently waive the supplied requirement.

Each `details` object also requires `source_ids`:

| Type | Detail fields |
| --- | --- |
| transfer | method cash/in-kind; transfer_scope full/partial; destination_ref_masked; nonempty destination_owner_party_ids; amount for cash or null; positions for in-kind |
| distribution | positive amount or null, currency USD, payee_ref_masked, purpose, tax_instruction_ref (source locator or null) |
| authority | subject_party_id, change add/remove/replace, authority_scope; replaces_party_id for replace |
| beneficiary | change replace/remove, beneficiaries[] with party_id, tier primary/contingent, numeric share 0–1 and source_ids |

In-kind positions have unique `security_id`, positive numeric `quantity`, `source_ids`.
An in-kind full transfer requires an explicit schedule matching supplied holdings; it never
implies “all” from a blank. Cash full transfers also require an explicit amount; no account
balance is converted into an instruction. A beneficiary `remove` request means remove all
recorded designations and has an empty schedule; targeted removals use an explicit replacement
schedule. Each nonempty replacement tier totals exactly one; no normalization occurs.

## Packaging and arithmetic

Resolve parties/accounts/request-condition links. Ownership differences, unknown tax instructions,
missing holdings and absent/conflicting conditions remain questions. Compare cash requests with
supplied available cash and in-kind quantities with holdings. Also add all cash requests for
an account and all in-kind quantities per account/security to find concurrent shortfalls;
individual request checks alone do not establish aggregate funding. No execution order, cash
settlement, account funding, tax default, asset eligibility or custodian acceptance is inferred.
No quoted account owner or condition status establishes a requestor's actual authority.

`service_packages` retains exact requests, account evidence, all supplied conditions and a
required-condition matrix. `aggregate_cash_requests` shows decimal-string totals;
`operations_open_items` contains every finding including aggregate constraints.
Every package has `instruction_status: draft-not-submitted`; top-level result also records
`submission_status: not-submitted`. `review-ready` describes a complete supplied evidence
package for operations, never readiness or permission to submit an instruction.

A replace-authority request must name a distinct existing `replaces_party_id` resolving to the party register; otherwise it remains incomplete. Full cash transfers with unknown/nonempty holdings or amounts different from supplied available cash require scope review; the package never infers liquidation.

Every supplied conflicting condition is unresolved, including conditions outside the configured required list. Such conflicts prevent review-ready and are retained for operations.
