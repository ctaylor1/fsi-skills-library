# Native input and output

Use the common supplied-evidence context in `evals/files/input.json`: request identity,
one subject, analysis/use dates, knowledge cutoff, audience, information barrier,
versioned source inventory, top-level evidence references and inherited issues.
Sources are supplied metadata, never authenticated access or truth.

`review_scope` requires every field below. A required inventory item cannot exclude
its corresponding check. Empty requirement lists mean the caller did not request
those items; they do not prove no relevant risks, disclosures or checks exist.

- `required_checks`: nonempty subset of `sections`, `claim_evidence`, `arithmetic`,
  `contradictions`, `comparability`, `risks`, `disclosures`.
- `required_sections`, `required_claim_ids`, `required_arithmetic_ids`,
  `required_risks`, `required_disclosures`: lists of unique required identifiers.
- `inventory_complete`: explicit Boolean declaration about the supplied inventory.
  False blocks readiness. True is a declaration, never independent completeness.

`packet` requires `packet_id` and seven inventory arrays:

- `claims`: unique `claim_id`, `kind` (`fact`, `forecast`, `judgment`), `subject_id`,
  `text`, `known_at` and `evidence_refs`. Empty citations are accepted as a finding.
  A numeric claim adds `value` (finite number or explicit null) and `basis` with
  `currency`, `units`, `accounting_basis`, `consolidation_scope`, `period_end`
  (YYYY-MM-DD), `measure`. These fields must be supplied and known.
  Forecasts require `forecast: {"horizon":"YYYY-MM-DD","assumptions":["..."]}`.
  Judgments require a nonempty `rationale`. No forecast or judgment is silently
  treated as an observed fact. Maximum 5,000 supplied claims.
- `sections`: unique `section_id` and `claim_ids`.
- `arithmetic_checks`: unique `check_id`, `operation` (`sum`, `difference`, `ratio`,
  `percent-change`), `operand_claim_ids`, `reported_claim_id`, nonnegative absolute
  `tolerance`. Sum needs at least two operands; other operations need exactly two.
  All references must exist; the reported claim cannot be its own operand.
- `contradictions`: unique `contradiction_id`, at least two `claim_ids`,
  `description`, `status` (`open` or `resolved-supplied`). A supplied resolution
  requires nonempty `resolution_evidence_refs`; it remains pending adjudication.
- `comparability_groups`: unique `group_id`, at least two `claim_ids`.
- `risks`: unique `risk_id` and supporting `claim_ids`.
- `disclosures`: unique `disclosure_id` and supporting `claim_ids`.

All row evidence references must also appear at top level for permission gating.
Foreign packet fields, supplied pass flags and invented approval objects are rejected.
`requested_action`, if supplied, must be `review`.

The standard source-bound result contains `results.packet_id`, `reviewed_checks`,
`excluded_checks`, requested `coverage`, independently recomputed
`arithmetic_results`, structured `findings`, and `readiness`:
`blocked`, `review-required`, or `complete-for-supplied-scope`.
Findings retain severity and adjudication status. `publication_approved` and
`model_approved` are always false. `native_producer_validation` is explicitly
`not-performed-by-this-method`: only an external reviewed adapter can validate a
producer original and actual native output. `results` is withheld when common
source eligibility fails. Keep the detached original for full-output reconstruction.
