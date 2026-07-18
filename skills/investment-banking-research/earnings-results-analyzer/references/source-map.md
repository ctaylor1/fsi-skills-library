# Source Map — earnings-results-analyzer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Filed release / 8-K / 10-Q / 10-K** (position of record) | Reported actuals and issued guidance | Read-only |
| 2 | **Earnings-call transcript** | Management commentary and language changes | Read-only |
| 3 | **Estimates / consensus** (market-data provider) | The comparison baseline (consensus/broker/in-house estimates) | Read-only |
| 4 | **Research corpus / prior model & note** | Prior guidance, prior estimates, prior thesis context | Read-only |
| 5 | **Coverage config** (versioned) | Beat/miss tolerances, headline-metric set, classification mapping | Read-only |

Never substitute a media headline, a summary aggregator, or a company IR slide caption for
the **filed** figure. If the filing and the transcript (or a data-provider value) conflict,
cite both and flag the conflict for the analyst rather than resolving it silently. Record
which **estimate source** each surprise is measured against; do not mix consensus, in-house,
and whisper numbers.

## Citation format

`{role}:{ref}@{period}` — e.g. `actual:8-K;ex99.1;p1;Revenue@Q2-2026`,
`estimate:consensus;metric=Revenue;period=Q2-2026`, `guidance:8-K;ex99.1;p3;FY26-rev-guide@FY2026`,
`transcript:transcript;Q2-2026;prepared-remarks;p4@Q2-2026`. Every finding cites the specific
figure(s) and, for a surprise, both the actual and the estimate it compares.

## Freshness / effective dates

- Config (tolerances, headline set, mapping) is a **versioned contract**; the output records
  the config version used so an analysis is reproducible.
- Record the **as-of** date and the **estimate source** used; a surprise is only meaningful
  against a stated baseline captured at a stated time (pre-print consensus).
- Restatements and amendments supersede the original release; prefer the latest filed figure
  and note the supersession.

## Least-privilege operations (deployment)

- `filings.get(ticker, period, form)` → reported actuals + guidance ranges from the filing.
- `transcript.get(ticker, period)` → prepared remarks / Q&A text for language comparison.
- `estimates.get(ticker, period, source)` → the consensus/estimate baseline.
- `corpus.prior(ticker)` → prior guidance, prior estimates, prior thesis notes.
- `config.get('earnings', version)` → tolerances + headline set + mapping.
All read-only, deterministic, durable `analysis_id`, below the fixed timeout; page long
transcripts as resumable stages. No write, publish, or trade operation is bound.
