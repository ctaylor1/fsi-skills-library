# Investment calculation engine contract — v1

An engine may execute locally or remotely. Neither location establishes approval.
The deploying institution owns method scope, independent benchmarks, version acceptance,
licensing and authorization. No engine connector is bundled by this contract.

## Required calculation record

- Engine ID, implementation/version and method ID/version; supported instruments and
  method scope; reference to institutional acceptance (unverified unless authenticated).
- Complete input digest and separately retained source references/snapshot IDs.
- Economic as-of and knowledge cutoff, valuation basis, currency, units, calendars,
  assumptions, rounding, tolerances, model and benchmark versions.
- Result origin: `local-analysis`, `external-analysis` or `supplied-system-of-record`.
  The last is a supplied designation, never a claim this library certified the record.
- Result status: `complete`, `partial`, `unsupported`, `unavailable` or `failed`.
  Coverage and unresolved issues accompany all partial results.
- Independent reconciliation result, residuals and approved tolerance references.
- Draft/review/action states separate from technical calculation success.

Do not relabel a volatility calculation as VaR/ES; a linear sensitivity shock as full
repricing; a supplied total tie-out as NAV preparation; or public-market attribution as
private-fund performance. A simplified alternative needs a separate explicit method
selection, assumptions and review. Engine failure cannot silently choose it.

## Local implementation gate

Specify units and domains; reject non-finite/invalid inputs; preserve missingness;
use independently constructed numerical cases and boundary cases; validate model
assumptions; reconstruct outputs from original inputs. Hashes and reconstruction do
not prove the source observations or the chosen assumptions are correct.
