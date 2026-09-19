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

- `projection`: `{start_age, end_age, opening_balance_basis, opening_balance_date, source_ids}`. Start integer 18..110, end start..120, years inclusive. Basis exactly `current-at-as-of`; balance date must equal envelope `as_of`. First retirement spending occurs immediately at this date. No unmodeled accumulation period is assumed.
- `spending`: `{annual_net_amount, annual_inflation, source_ids}`. Amount is first-year after-tax spending; inflation effective annual decimal [-0.5,1]. Healthcare expenses must be included here if modeled.
- `model`: `{version, tax_method, benefit_method, limitations, source_ids}`. Tax method exactly `effective-withdrawal-rate-proxy`; benefit method exactly `supplied-income-schedules-no-entitlement-calculation`. Limitations rows `{topic, treatment, description, source_ids}` must cover exactly `rmd`, `tax-brackets-and-capital-gains`, `benefit-entitlement`, `survivor-and-household-changes`, `healthcare-and-long-term-care`.
  Treatment is `not-modeled` for the first four topics and `included-only-in-supplied-spending` for healthcare. Declaring an excluded tax/benefit method modeled is rejected.
- `accounts`: nonempty rows `{account_id, type, balance, annual_return, effective_withdrawal_tax_rate, source_ids}`. Type taxable, tax-deferred, tax-free; unique IDs. Return effective annual decimal [-0.99,1], net of modeled fees. Whole-withdrawal tax proxy decimal [0,0.95]; tax-free accounts require 0 in this model. For taxable accounts this is not a statutory capital-gains rate on the entire distribution; obtain a suitable external effective proxy or leave it unknown.
- `income`: required explicit array, empty allowed. Rows `{income_id, label, annual_gross_at_start, start_age, end_age, annual_cola, effective_tax_rate, source_ids}`. Ages integers 18..120 ordered, inclusive. Annual amount is denominated at this income's start age; COLA decimal [-0.5,1] applies from that age. Effective income-tax proxy [0,0.95]. Schedules are supplied assumptions and do not establish legal benefit entitlement. If the schedule already began, accumulated COLA through the modeled age is applied.
- `withdrawal_policy`: `{strategy, account_order, source_ids}`. Strategy `spending-gap` or `fixed-percentage`; account_order lists every account once. Fixed-percentage additionally requires `annual_percentage` decimal [0,1], applied to beginning-of-year portfolio as a gross withdrawal budget. Omit this field (or use null) for spending-gap to prevent an ignored assumption.
- `scenarios`: nonempty rows `{scenario_id, label, return_adjustment, inflation_adjustment, return_sequences, source_ids}`. Include `base` with both adjustments 0 and empty sequences. Adjustments decimals [-1,1]; combined returns and inflation must lie in [-0.99,1]. `return_sequences` is explicitly present, empty allowed; rows `{account_id, annual_returns, source_ids}`. Each nonempty sequence provides effective total annual returns for early modeled years, overriding return plus adjustment for those years only. At most one sequence per known account, no returns beyond the horizon.

Every source/model assumption is retained in the full input snapshot. Result includes projection,
spending, versioned model limitations, withdrawal policy and complete scenario assumptions in
addition to the annual results. An incomplete scenario is `not-evaluable`; a complete independent
scenario remains available. A missing shared income list, tax proxy or scope declaration prevents
unsupported projections across scenarios. Read `standing_note` with every table.
