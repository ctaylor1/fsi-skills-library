# Investment Research control repairs

Implemented 2026-10-20 under the request to fix the four P1/P2 review findings,
add regression tests and preserve the earlier phase evidence. This is a repair
checkpoint for the existing 42-method portfolio; it adds no skills or adapters.

| Review finding | Implemented correction |
|---|---|
| P1: Future financial periods accepted as current credit evidence | Issuer credit and active surveillance reject reported periods ending after economic `as_of` or the knowledge-cutoff date. Aware cutoffs use their UTC calendar date. Forecast/scenario labels do not bypass the reported-period contract. |
| P1: Duplicate EBITDA adjustment IDs counted twice | Issuer credit rejects repeated adjustment IDs before arithmetic, including identical and conflicting rows. Distinct signed adjustments remain separate; reported EBITDA remains unchanged. |
| P2: Routing metadata disagreed with native support | Corrected five subject declarations and eight added/corrected profile gates, preserving legacy corporate comps and model-reviewer continuity. The structural checker now probes all 42 real public native validators and checks exact profile selectors, including nested model and structured-credit profiles. |
| P2: Undated or stale spreads produced current changes | Active surveillance requires explicit aware observation times and a supplied current-age policy for a spread comparison. Missing, stale, future, unordered or incomparable observations withhold the spread change and its widening alert. Useful financial metrics remain available in a partial result. |

## Timing and identity contracts

The financial-period controls apply to reported observations, not future contractual
maturities or explicit forecasts in other methods. Source eligibility remains a
separate gate: future or denied cited evidence still withholds the analytical
projection rather than acquiring validity from a period check.

Spread observations must match security, currency and basis; strictly increase in
time; fall on or before the cutoff; and have UTC dates no later than economic
`as_of`. Each cited source/version must have sufficiently precise knowledge time
on or after observation and remain eligible at the cutoff. Publication after
observation is valid. Source knowledge never substitutes for observation time.

`spread_freshness_policy.max_current_age_hours` is an explicit finite nonnegative
elapsed-hour limit. It applies to the current observation; a historical prior quote
is not subjected to that current-age limit. Exact equality is eligible. Missing
policy or date-only cutoff/source precision withholds comparison; no midnight or
institutional age limit is invented. Supplied malformed timestamps or policies
reject at intake.

Router selectors are method-selection context. `issuer_type`, `issuer_profile`
and `structured_credit_profile` cannot substitute for one another. The registry
records corresponding native paths, including retained nested models. Selection
does not populate a native request, validate its contents, launch a method or
establish adapter compatibility. Legacy schema dispatch remains explicit.

## Versions and migration

- `issuer-credit-researcher`: 0.1.1.
- `issuer-credit-surveillance-reviewer`: 0.3.1.
- `investment-research-router`: 0.4.1.

Active schemas, examples, eval inventories, manifests, router registry copies,
goldens and current catalogs have been refreshed. The nine reviewed adapters and
canonical shared resources are unchanged. Historical packets retain their original
versions and originals. Previously undated spread intake now returns a partial
result; supply actual observation/source timestamps and the desk's age policy to
request a current comparison. Surveillance routing now requires `issuer_profile`;
structured-credit routing requires its explicit simplified model profile.

The new [validation checkpoint](control-repairs-validation/README.md) records
regressions, public-command reproductions, independent fresh cases, isolated
package checks and byte preservation. Earlier Phase 1–4 implementation and
validation records are unchanged.

## Remaining professional review

These repairs establish bounded software behavior. The native methods still trust
supplied economic identities and source assertions. Separate adjustment IDs can
describe the same economic cost; analysts must reconcile them before accepting
adjusted EBITDA. Instrument amounts/currencies are not automatically reconciled to
consolidated financial debt. Matching quote IDs do not authenticate their issuer
mapping or source content. The fresh review retains those observed semantic limits
rather than treating a reconstructed packet as research acceptance.

Authenticated evidence, broader instrument/model coverage, practitioner and
institutional acceptance, publication and live execution remain separate work.
