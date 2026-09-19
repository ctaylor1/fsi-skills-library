# Source and input contract

The scripts accept only the shared `wealth-p0-v1` envelope:

| Field | Required value |
| --- | --- |
| `schema_version` | `wealth-p0-v1` (the common contract remains version 1 in P1) |
| `request_id`, `household_id` | Nonempty internal, de-identified strings |
| `as_of` | Exact `YYYY-MM-DD` |
| `engagement` | `{capacity: advisory|brokerage|private-bank|trust, jurisdiction: US}`; select the capacity for this task |
| `sources` | Nonempty array of `{source_id, reference, owner, as_of, valid_until}` with unique IDs |
| `upstream_issues` | Required explicit list of received handoff issues; `[]` only after reviewing all received handoffs |
| `currency` | `USD`; no conversion or mixed-currency calculation |

Each source must satisfy `source.as_of <= request.as_of <= source.valid_until`. Use immutable,
version-identifying references (for example a statement snapshot ID, profile version or model
version). Each material domain object and list row requires nonempty unique `source_ids`
resolving to this registry. Scalar facts inherit their containing object's source IDs. Explicit
assumption/template versions are required below. Sources and versions are supplied evidence
metadata: the scripts do not authenticate a source, policy approval, professional capacity or
access permission. Contradictory sources require human resolution.

Wrong types, duplicates, invalid ranges, non-finite numbers, booleans used as numbers and stale
registry sources are structural errors. Absent material fields and unresolved item-level sources
produce `needs-data`. Amounts are finite nonnegative USD values in whole cents, at most 1e12;
percentages use the units stated below. Lists described as required must be present; an allowed
empty list explicitly means none, while a missing list means unknown. Do not encode missing
facts as zero, empty strings or invented defaults.

The CLI validator returns exit 0 when structure is valid, even if findings remain. Always read
findings and output status. Exit 0 is not financial readiness or professional approval.

## Upstream issue inventory

`upstream_issues` is required at the top level in both integrated and focused modes. Each row is
`{artifact_id, code, message, status: unresolved|resolved, source_ids}`. Preserve the originating
artifact, original concern, source IDs and supplied status; do not reclassify or suppress a concern
to obtain review-ready. Missing inventory/status/source evidence remains a finding. Unresolved
rows create `upstream-unresolved` findings with origin metadata; complete independent calculations
remain conditional evidence and do not clear ownership, authority or other upstream conflicts.

A row marked resolved additionally requires `resolution: {owner, reference, as_of, source_ids}`
from the responsible external reviewer. The dated, cited resolution must not postdate the request.
This records supplied resolution evidence; it does not authenticate it or constitute this skill's
adjudication. A bare resolved label cannot clear a finding. The complete inventory is carried in
`result.upstream_issues` and the full input snapshot, and is covered by output reconstruction.

## Domain schema

Required top fields: `ips_id` nonempty, `revision` integer 1..100000,
`supersedes_artifact_id` explicit null for revision 1 or a required prior artifact ID for revision >1,
`template`, and `mandate`. Template is `{template_id, version, required_sections, source_ids}`;
`required_sections` must equal the following 13 keys in order.

All blocks and every nested substantive row require `source_ids`. Required text must contain
actual documented content, not merely a citation, a presence boolean or “TBD.”

| Mandate key | Required content |
| --- | --- |
| `purpose` | `text`; nonempty unique `account_ids` |
| `governance` | `decision_authority`, `capacity_basis`; nonempty `parties` rows `{party_id, role, responsibility, source_ids}` |
| `objectives` | `return_objective`, `spending_objective`; nonempty `items` rows `{objective_id, description, priority: integer 1..100, source_ids}` |
| `risk_profile` | `profile_artifact_id`, `governing_constraint`, `human_reviewer`, `assessment_reference`; six `dimensions` rows `{dimension, assessment, source_ids}` for willingness, loss-capacity, liquidity, horizon, experience, constraints; explicit `unresolved_findings` list (empty allowed), each `{description, source_ids}` |
| `time_horizon` | `months` integer 0..1440, `stage` |
| `liquidity` | `reserve_amount`, `annual_distribution`, explicit `events` (empty allowed), rows `{event_id, date, amount, purpose, source_ids}` |
| `tax` | `assumptions_version`, `limitations`, `account_treatments` rows `{account_id, registration, treatment, source_ids}` covering exactly the purpose account IDs |
| `constraints` | Explicit boolean `none_identified`, explicit `items` list (empty only when true), rows `{constraint_id, description, source_ids}` |
| `allocation` | Nonempty rows `{asset_class, target_pct, min_pct, max_pct, benchmark, source_ids}`; percentages 0..100; asset classes unique after case/whitespace normalization |
| `rebalancing` | `method`: calendar, threshold or hybrid; `frequency`, `tax_cost_constraints`, `exception_owner`; `threshold_percentage_points` in (0,100] required for threshold/hybrid |
| `monitoring` | `portfolio_benchmark`, `frequency`, `owner`, nonempty unique string `review_triggers` |
| `approvals` | Exactly one `{role, party_id, source_ids}` for advisor, supervisor and client; each party/role must match a governance assignment; optional status must be `pending` |
| `disclosures` | Actual `text`, `version` |

Supplied risk assessments and human governing constraint are preserved and attributed; this
assembler does not verify their professional adequacy or derive an overall rating. Carry upstream
conflicts forward; never replace them with an empty findings list simply to obtain review-ready.
The draft contains all source-bound content, a readable Markdown rendering, template/revision
lineage, allocation checks and pending approvals with null effective dates. Generated content is
reconstructed exactly by `validate_output.py`.

### Missing priority and identity evidence

A required domain field may be unknown. Supply `priority: null` when the source
has no human-assigned rank; list order is not ranking evidence. Supply
`account_ids: null` for an asset pool with unknown account membership. These
values yield missing-evidence findings rather than permission to invent facts.
Keep independently supported amounts and conflicts visible in the draft while
marking any tool calculation withheld because of those gaps. See the
source-to-input check in SKILL.md.
