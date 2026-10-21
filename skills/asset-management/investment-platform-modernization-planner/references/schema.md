# Native input and output contract

All examples are synthetic. `evals/files/input.json` is a complete executable ABOR rehearsal example, not a production template with pre-approved thresholds.

## Common evidence context

Require `request_id`, `object_id`, `as_of`, `knowledge_cutoff`, `currency`, `audience: internal-review`, `sources`, and explicit `unresolved_issues`. Dates are real YYYY-MM-DD values. Each source has a unique `source_ref`, `version`, `as_of` and `known_at`; source eligibility and chronology are checked. Every native row has unique `id` within its collection and a registered `source_ref`. Numeric inputs use exact decimal strings; booleans and nonfinite values are invalid. Collection limit is 10,000 rows; numeric domain is at most 38 significant digits and exponent magnitude 38.

`shared_reviews.architecture` contains `input`, `output`, `source_ref`. The input is the actual shared architecture schema (`case_id`, `context`, `sources`, `data`, `unresolved_issues`), and output is that owner's workflow-review envelope. `context.object_id`, `as_of` and `data.currency` must exactly match the AM request. Shared source versions and dates must match the AM registry. No cross-object mapping or implicit currency conversion occurs. Generated `shared_architecture.py` and its dependencies invoke the canonical owner's native calculation and validator.

## AM collections

| Collection | Additional required fields and constraints |
| --- | --- |
| `platforms` | `component_id` in shared architecture; `role` PMS/OMS/EMS/IBOR/ABOR/custodian/market-data; `owner`, `provider`, `provider_contract_version`, `provider_contract_source_ref`, `licensed_purpose`, `record_identity`, `history_retention`, `failure_owner`. Multiple systems may have a role. |
| `excluded_roles` | Explicit list, possibly empty. Each excluded role has `role`, `rationale`, `reviewed_by`; every one of the seven roles is mapped or excluded, never both. |
| `responsibilities` | `platform_id`, `domain`, `book_scope`, `authoritative_state`, `version`, `reconciliation_owner`. One supplied owner per exact domain/book/state key; different current and proposed states are distinct. |
| `requirements` | `architecture_requirement_id` in native requirement fit, `description`, `owner`, boolean `mandatory`, `disposition` met/not-met/unknown. Shared fit and AM disposition both survive. |
| `snapshots` | `platform_id`, `version`, `sha256` lowercase 64-character declared digest, `observed_on`. Digests identify supplied snapshots; this planner does not open or authenticate snapshot payloads. |
| `batches` | `owner`, nonnegative integer `wave`, explicit `depends_on`, `mapping_version`, distinct `source_snapshot` and `target_snapshot` with matching observation dates, `rollback_owner`, `rollback_trigger`, `rollback_runbook`, nonempty unique `expected_grains`, `grain_inventory_reviewed`, boolean `new_writes_after_cutover`. |
| `reconciliations` | `batch_id`, `mapping_version`, nonnegative `tolerance`, `tolerance_reviewed_by`, `tolerance_source_ref`, `source` and `target` observations. Each observation has `snapshot_id`, `source_ref`, exact decimal `value` and all grain fields. |
| `exceptions` | Explicit list, possibly empty. `batch_id`, `owner`, `description`, `status` open/closed/accepted. Closed needs `resolution`, `resolution_source_ref`, `resolved_on`. Accepted remains unresolved. |
| `parallel_runs` | `batch_id`, exact batch mapping/snapshot fields, `window_start`, `window_end`, `owner`, explicit `exception_ids` retaining every batch exception. Snapshot observation dates must lie within the run window. |
| `recoveries` | `run_id`, `owner`, `observed_on` no earlier than run completion, `threshold_reviewed_by`, `threshold_source_ref`, `rollback_status` passed/failed/not-run, nonnegative `observed_rto_seconds`, `rto_limit_seconds`, `observed_rpo_seconds`, `rpo_limit_seconds`. |
| `gates` | `batch_id`, `kind` reconciliation/parallel-run/rollback/security/business-acceptance, `owner`, `status` passed/failed/not-run, `reviewed_by`, `observed_on`, unique `evidence_ids`. Native gate kinds must name all corresponding evidence rows for that batch. Security/business evidence IDs identify supplied external reviews; they are not authenticated by this calculator. |

Every grain contains `fund_id`, `book_id`, `account_id`, `instrument_id`, `lot_id`, `valuation_date`, `measure`, `unit`, `currency`. Explicit scoped placeholders such as an approved `not-lot-tracked` identity are allowed only when backed by the supplied mapping; never aggregate actual lots into a placeholder. Each side must carry the same complete grain and match the batch's explicit inventory. Mixed currencies may be present as separate grains; they are never summed or converted. The common request currency is the shared architecture cost currency.

When `new_writes_after_cutover` is true, also require `delta_replay_evidence`, `delta_replay_source_ref`, `delta_replay_status` passed/failed/not-run, `delta_replay_observed_on` and `delta_replay_run_id`. The run ID must identify a latest-ending parallel run for the same batch, which binds the batch's mapping version and exact source/target snapshots. The replay observation cannot predate that run's completion. These are observed rehearsal results, not permission to replay production writes.

Reconciliation, parallel-run, rollback and business-acceptance gate dates cannot predate any batch exception closure or delta replay. Business acceptance must also postdate all supplied batch snapshot/run/recovery observations. A pre-existing security review is a separate scoped external review; it cannot substitute for the dated business-acceptance gate.

## Results

Output uses `investment-foundation/1.0`, retaining the full input hash without embedding source snapshots. Results retain the platform inventory, exclusions, responsibilities, AM requirements, native shared requirement fit/cost, dependency order and batches, per-grain differences, runs, exceptions, recovery threshold outcomes and human gates. `readiness` is `blocked` while any issue remains, otherwise `evidence-ready-for-human-review`. `cutover_authorized`, `migration_executed`, `production_access_verified` and top-level `action_taken` remain false. Detached input reconstruction is required for output validation.
