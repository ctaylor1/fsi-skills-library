# Construction schema v0.1

Common `wealth-p0-v1`: request_id, household_id, ISO as_of, engagement
{capacity: advisory|brokerage|private-bank|trust, jurisdiction: US}, sources
[{source_id, reference, owner, as_of, valid_until}]. Sources must span the review date.
Numeric inputs are finite nonnegative numbers, never numeric strings or booleans; omitted/null
material numbers remain unknown. Structural containers and identifiers are required.

- `portfolio_value`, `currency`: positive sizing value and one stated currency; no FX.
- `mandate`: policy_id, version, owner, source_ids, method exactly
  `proportional-within-model-sleeve`; cash_min, cash_max, max_position_weight (fractions0..1);
  explicit restricted_security_ids list (empty means sourced none); class_bands list with
  unique asset_class, min_weight, max_weight and source_ids. Cover all model asset classes.
- `universe`: nonempty unique security_id records, asset_class, eligible boolean/null,
  max_weight fraction and source_ids. Unknown eligibility never permits allocation.
- `models`: one or more unique model_id, version, source_ids, cash_weight, approval_record
  {status: recorded-approved, owner, reference, source_ids}, allocations
  [{security_id, weight, source_ids}]. Weights plus cash must equal one. Approval fields record
  supplied evidence and do not authenticate approval. An unknown record leaves the draft unresolved.

Output `result`: input_snapshot, candidates, method, selected_candidate:null, scope. Each candidate
has its originating model, generated holdings with model/current deviation weights and sizing
amounts, cash, class weights, unallocated remainder, explicit constraint checks and local findings.
Unknown economics remain null. Candidate amounts are rounded presentation figures; continuous weights
are authoritative and trade increments/fees are deferred to transition planning.

The validator rebuilds the whole artifact from the snapshot, checking model totals, caps,
restrictions, coverage, constraints, unknowns, hashes and non-action posture.


## Required upstream issue contract
`upstream_issues` is an explicit list of `{artifact_id, code, message,
status: unresolved|resolved, source_ids}`. Identifiers and message must be nonempty strings;
source_ids must be a list resolving to the envelope registry. Missing/malformed issue structures
reject input; missing/unknown citations remain source-gap findings. Any unresolved issue forces
needs-data regardless of local arithmetic or model consistency. Resolved records remain in the
result and handoff context; status is a supplied reviewer representation, not authenticated closure.
Use an empty list only after reviewing the originating artifacts for material unresolved concerns.

Output `result.upstream_issues` and `result.handoff_context.upstream_issues` preserve every record;
the context also preserves household, date, capacity and source registry. Original code and artifact
identity accompany propagated findings. Recomputing output detects omitted issues/context relative
to the held input. It cannot detect a consistently rewritten source artifact or falsely claimed resolution.
Top-level `unresolved_issues` from another schema is rejected until explicitly mapped; it is never
silently ignored. Earlier draft inputs without this list require source review before migration.
