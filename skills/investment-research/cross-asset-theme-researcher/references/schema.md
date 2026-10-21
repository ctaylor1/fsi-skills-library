# Native theme intake and output

Use [the synthetic input](../evals/files/input.json) with the common evidence
context: request_id, purpose, internal-review audience, economy/sector/portfolio
subject with actual id, as_of, use_on, knowledge_cutoff, information_barrier,
sources, evidence_refs and unresolved_issues. Strict JSON rejects duplicate
keys and nonfinite constants. Unknown native fields are rejected. Full-original
output reconstruction is required; raw source documents are not embedded.

Required domain fields:

- theme_id and hypothesis object with statement, driver, transmission, and
  future horizon_date.
- evidence array: unique evidence_id, role (`support` or `counter`), statement,
  known_at, nonempty precise evidence_refs; optional driver_observation_ids.
- coverage object with at least two unique required_asset_classes from rates,
  credit, equity, fx, commodities and real-assets; explicit inventory_complete
  boolean. Missing requested exposures and absent counter-evidence are partial
  research, not fabricated coverage.
- falsifiers array: unique test_id, testable description, monitor, due_on,
  status (`not-tested`, `observed`, `not-observed`), known_at and evidence_refs.
  Untested rows require null known_at and empty refs. Tested results require
  dated precise evidence. No falsifiers or an overdue untested row is a gap.
- scenarios: nonempty unique scenario_id, label, future horizon_date matching
  the hypothesis, known_at, nonempty assumptions, evidence_refs, nonempty shocks.
  Each shock has unique driver_id within its scenario, finite value and unit
  (`basis-point`, `percentage-point`, `percent`). Probabilities and automatic
  forecast classification are not accepted.
- exposures: unique exposure_id, asset_class, instrument_id, method, driver_id,
  sensitivity, shock_unit, response_unit, known_at, evidence_refs, mechanism and
  nonempty limitations. Method is linear, modified-duration or qualitative.
  Linear and duration sensitivities must be finite numbers; duration must be
  nonnegative. Numeric response_unit is percent-price-change,
  percent-income-change or yield-basis-point. Qualitative requires null
  sensitivity, response_unit `qualitative` and a nonempty qualitative_response.
  FX exposure requires quote_convention (for example USD per EUR). Non-FX
  exposure does not accept it. No weights, notional positions or trades are
  accepted.

Optional `driver_observations` is an array of exact macro selected rows with
observation_id, series_id, label, geography, frequency, measure_kind, unit,
price_basis, price_base, seasonal_adjustment, annualization, period_end,
release_at, vintage_id, value (finite or explicit null), evidence_refs. Same
series-period competing vintages reject. Period ends and explicit basis enums
are checked; real/index rows require a price base. These historical rows do
not become shocks, estimated coefficients or causal evidence automatically.
A reviewed adapter must separately validate producer native output against its
retained full original. Without that proof, rows remain supplied observations.

Every analytical citation must appear in top-level evidence_refs. Row knowledge
must precede the research cutoff and as_of; sources must precede the cited row
knowledge, preserving date versus aware timestamp precision. Ineligible source
permissions, identity, timing or validity withhold all results under the shared
evidence standard.

Results retain the hypothesis, driver observations, evidence, falsifiers,
scenarios, scenario_responses and required/supplied/missing coverage. Response
rows carry identity, driver, actual shock, method, units, caveats and null with
an unavailable_reason where computation is unestablished. Explicit fields keep
causality_established, probabilities_estimated and portfolio_allocation_proposed
false. Supplied falsifier observations can challenge the hypothesis; no engine
result approves a portfolio action or publication.
