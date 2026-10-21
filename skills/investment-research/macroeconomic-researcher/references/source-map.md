# Primary method provenance

The examples are synthetic; no live economic release, proprietary subscription,
or source-authentication service is bundled. Actual observations, publication
times, vintage versions and rights must be supplied with precise citations.
Primary method references checked 2026-10-20:

- [Federal Reserve Bank of St. Louis: real-time periods](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html)
  distinguishes current information about a past period from information known
  at that past time. The package implements a bounded latest-eligible supplied
  release selection; it does not query or reproduce the ALFRED service.
- [St. Louis Fed: series vintage dates](https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html)
  provides the archival release/vintage context. Supplied inventory completeness
  remains separate from actual external publication coverage.
- [BEA: quarterly percent changes at annual rates](https://www.bea.gov/help/faq/122)
  explains compounded quarterly annualization. The independent test uses
  synthetic endpoints; no BEA data is distributed.

These sources support method definitions only. They do not authenticate a
particular research input or authorize institutional use or distribution.
