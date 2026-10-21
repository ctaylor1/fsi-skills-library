# Input and output contract

Use `evals/files/input.json` as an entirely synthetic structural example. None of its model, owner, policy or license identities refers to a real approval.

The common input requires `request_id`, `object_id`, ISO-style `currency`, real day-grain `as_of` and `knowledge_cutoff`, `audience: internal-review`, nonempty versioned `sources` and optional `unresolved_issues`. Each source supplies `source_ref`, `version`, `as_of`, `known_at`; any declared audience/effective/expiry restrictions apply. No observation may be known after the cutoff.

| Object | Required contents |
|---|---|
| `shared_reviews.automation` | Native `input`, native `output`, enclosing `source_ref`; producer is `workflow-automation-assessor`. Object, date and currency match this review. Every native source also appears in the AM registry with the same version and date. |
| `workflow` | `workflow_id`, owner, purpose, principal/tenant, portfolio/client ID lists, escalation owner, executor ID, source reference, `decision_boundary: internal-draft`, `output_audience: internal-review`; denied actions include trade-order, portfolio-mutation, external-message, client-publication. |
| `workflow.versions` | Pinned known strings for `model`, `prompt`, `toolset`, `dataset_snapshot`; no unknown/latest aliases. |
| `workflow` limits | Positive `maximum_latency_ms`, nonnegative `maximum_cost_per_episode`, integer `maximum_attempts` from 1 through 10. |
| `tools[]` | Unique tool ID, version, owner, source reference, operation read-only and nonempty allowed actions from read/search/lookup/calculate. |
| `datasets[]` | Unique dataset ID, snapshot ID, license ID, dataset and license source references, known/as-valid dates, license effective interval, allowed purposes/principals/tenants and principal/tenant/portfolio/client scope. |
| `experiment` | ID, manifest version, separate label reviewer, source, `evidence_kind` synthetic-fixture or supplied-observation; unique training and held-out IDs; six required risk categories listed in domain rules. |
| `test_cases[]` | Exact held-out inventory with unique case ID, dataset ID, risk category, expected label, label reviewer/source/known date, source and principal/tenant/portfolio/client scope. |
| `episodes[]` | Zero or one episode per held-out case; unique episode ID, source, observed date, exact versions, executor, scope, boolean runtime_error/timed_out/stopped/injected_instructions_followed, observed label or null, positive integer attempts, currency, nonnegative cost/latency or null and explicit tool_calls list. |
| `tool_calls[]` | Unique call ID in each episode, tool ID/version/action, source and scope; status completed/denied/timeout/error and effect none/read/write/message. |

Lists are explicit, at most 10,000 rows in each domain collection. IDs must be unique nonempty strings. All quantitative fields accept finite JSON numbers or decimal strings within the foundation's 38-digit/exponent bounds; use strings when lexical precision matters. Missing cost/latency must be null or absent and is never treated as zero. Malformed structure, unlinked sources, mixed version experiments, foreign/duplicate cases and train/test overlap fail validation. Declared license, scope, unknown measurement or unsafe episode issues remain visible in a `needs-review` draft.

Output uses `investment-foundation/1.0`: immutable full input hash, versioned method, explicit limitations, source references and no action/delivery authority. `results.evaluation` contains requested and observed counts, denominator-labeled rates, missing case IDs, cost/latency coverage, and compact case observations. `results.automation_assessment` retains the canonical owner's results and findings. Output validation recomputes against a required detached original input; rehashing a modified output does not make it valid.
