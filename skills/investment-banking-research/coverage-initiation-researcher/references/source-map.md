# Source Map — coverage-initiation-researcher

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Filed disclosures** (10-K/10-Q/8-K/20-F, prospectus) | Business model, segment data, risk factors, historicals | Read-only |
| 2 | **Market/financial data** | Prices, shares out, consensus estimates, trading multiples | Read-only |
| 3 | **Company disclosure** (transcripts, guidance, investor decks) | Guidance, KPI drivers, catalysts | Read-only |
| 4 | **Internal research corpus** | Sector primers, prior notes, thesis memos, competitive maps | Read-only |
| 5 | **Model outputs** (linked artifacts) | DCF, comps, three-statement outputs feeding forecast/valuation | Read-only |
| 6 | **Coverage config** (versioned) | Required-section set, tolerances, readiness mapping | Read-only |

A management assertion or sell-side estimate never overrides a filed figure. When a
transcript/guidance figure and a filed figure conflict, cite both and flag for the analyst;
never resolve silently.

## MNPI boundary (critical)

This skill operates on **public and approved-internal** sources only. Material non-public
information (MNPI) — deal data rooms, wall-crossed information, unpublished client-confidential
figures — must never enter a research draft. The dossier carries an `mnpi_attestation`; if it
is not true, the draft cannot proceed to delivery. Data classification is Highly Confidential
(MNPI / client-confidential) precisely so the wall is respected.

## Citation format

`{system}:{ref}@{date}` — e.g. `filings:ABCD-10-K-2025@2026-02-20`,
`model:dcf-modeler@2026-07-12`. Every section claim, every forecast series, and every
valuation method cites its source. Uncited claims reduce evidence coverage and block readiness.

## Freshness / effective dates

- Coverage config (required-section set, tolerances, readiness mapping) is a **versioned
  contract**; the output records the `config_version` so a draft is reproducible.
- Record the `as_of` date; prices, estimates, and multiples are point-in-time.
- Forecast and valuation inputs cite the specific model artifact and date they came from.

## Least-privilege operations (deployment)

- `filings.get(ticker, form, period)` → filed disclosure sections.
- `market.quote(ticker, as_of)` / `market.consensus(ticker)` → point-in-time data.
- `research.search(ticker|theme)` → internal corpus (read-only).
- `model.get(artifact_id)` → linked DCF/comps/three-statement outputs.
- `config.get('coverage', version)` → required sections + tolerances + readiness mapping.
All read-only, deterministic, durable `coverage_id`, below the fixed timeout; page long
filings as resumable stages. No write to the research portal or client systems occurs here.
