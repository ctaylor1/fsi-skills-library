# Native macro intake and output

Start from [the synthetic input](../evals/files/input.json). The public script
trio reads strict JSON: duplicate keys, NaN and infinity are rejected. Retain the
full original separately for output reconstruction; no raw source document is
embedded in the result. Unknown native fields are rejected.

The common context requires request_id, purpose, internal-review audience,
economy or sector subject with actual id, as_of, use_on, knowledge_cutoff,
information_barrier, sources, evidence_refs and unresolved_issues. Source records
follow evidence-standard.md. Precise row references must be declared at the top
level. Source knowledge must be no later than the cited row release/knowledge
time with matching date or aware timestamp precision.

Required macro fields:

- `series_inventory_complete`: explicit boolean for supplied requested scope.
- `requested_series_ids`: nonempty unique list; omitted supplied series create
  partial coverage, not inferred observations.
- `series`: nonempty uniquely identified series. Each has series_id, label,
  geography, frequency (`monthly`, `quarterly`, `annual`), measure_kind (`level`,
  `index`, `rate`), unit, price_basis (`real`, `nominal`, `not-applicable`),
  price_base, seasonal_adjustment (`seasonally-adjusted`,
  `not-seasonally-adjusted`, `not-applicable`), annualization (`annual-rate`,
  `period-level`, `not-applicable`) and observations. Real and index series
  require a specific price_base; `unknown` basis text is rejected.
- `observations`: nonempty rows with globally unique observation_id, period_end,
  release_at, vintage_id, value (finite number or explicit null), evidence_refs.
  Period ends must be calendar month/quarter/year ends; the reported period
  cannot postdate its release. Same period and release instant duplicates reject.
- `calculations`: unique calculation_id, series_id, from_period, to_period,
  operation (`difference`, `percent-change`, `annualized-percent-change`).
  Start must precede end. A referenced series must exist. Eligible endpoints may
  be absent; the result then has null value and an explicit issue.
- `outlooks`: possibly empty; unique outlook_id, kind (`scenario`,
  `analyst-forecast`, `consensus`), series_id, future period_end, value (number or
  null), known_at, nonempty assumptions, evidence_refs. Only consensus accepts
  and requires consensus_provider. No probability field is accepted.
- `research_questions`: nonempty unique question_id rows with question,
  required_calculation_ids, interpretation and counter_evidence. The latter two
  require text or explicit null. They are supplied judgments for analyst review,
  never engine-authenticated conclusions.

`results.selected_observations` flattens each immutable series basis plus its
latest eligible observation fields. The exact keys are series_id, label,
geography, frequency, measure_kind, unit, price_basis, price_base,
seasonal_adjustment, annualization, observation_id, period_end, release_at,
vintage_id, value and evidence_refs. This is the only supported producer shape
for an explicitly reviewed macro-to-theme driver observation handoff; native
packets are not interchangeable merely because fields have similar names.

Other results contain excluded observation identities/reasons (never their
values), supplied revision deltas, calculations and endpoint lineage, requested
series coverage, explicitly typed outlooks, and question review gaps. An
ineligible top-level referenced source withholds the entire projection under
the shared evidence standard, including sources used by excluded releases.
The complete original remains bound by input_hash. Thus excluded future release
metadata does not bypass source permissions or assert historical availability.
