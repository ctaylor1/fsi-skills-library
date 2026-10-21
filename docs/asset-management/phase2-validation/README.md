# Phase 2 validation evidence

This directory records the authorized September 21, 2026 AM foundation implementation.
The final machine-readable summary is `validation-summary.json`. Package and arithmetic
validation are bounded technical evidence; professional, source and deployment acceptance
remain unestablished.

## Final result

AM Phase 2 bounded validation passed: **443 native evaluations**, **563 portable checks
across 83 packages**, and **54 AM packages with zero structural errors/warnings**. The
repository snapshot ran 609 tests: 606 passed and three catalog-inventory assertions
failed on the concurrently added compliance router. The earlier full-library executable
snapshot had 13 failures in changing compliance packages. AM scope is complete;
whole-library validation is not clean. See [machine-readable results](validation-summary.json).

## Evidence layers

- `repository-tests.log`: whole-repository Python regression run. Domain test modules include independent expected calculations, chronology/rights boundaries, legacy compatibility and native handoffs.
- `portable-packages.json` and `portable-checks.log`: isolated copies of all 83 affected investment packages, with sibling imports unavailable and no repository PYTHONPATH. Every declared native command is checked against its expected exit/output.
- `package-checks.log`: full-library executable-evaluation snapshot. Compliance/financial-crime files were changing concurrently outside this AM work; failures there are reported separately and are not concealed by AM results. `unrelated-checks.json` records immutable baseline/current probes for the original AML/sanctions failures. A whole-library clean release is not claimed.
- `structure-and-resources.log`, `static-checks.json` and `preservation.json`: catalog/ownership/handoff checks, generated-resource consistency, syntax/JSON/local links, catalog regeneration and SHA-256 preservation of earlier Phase 1, Insurance, Payments and Wealth evidence.
- `business-authoring.json`, `operations-authoring.json` and `private-authoring.json`: intermediate authoring checks and source/method references. Their hashes capture those checkpoints; final package manifests and `implementation-hashes.json` identify the accepted AM implementation snapshot.

## Independent forward reviews

Separate reviewers built fresh synthetic requests from the published contracts and
manual arithmetic expectations. They did not treat regenerated calculator outputs as
independent numerical oracles.

- [Portfolio and governance findings](portfolio-independent/findings.md): fresh cases across eight packages. The original failures are retained in `results-initial.json`; the repaired replay is `results.json`.
- [Private-market review](private-independent/review-notes.md): eight schema-driven requests with manually expected results, detached validation and a retained formatting-harness correction. Additional audience and actual-date regressions are included in the private test module.
- [Operations review](operations-independent/summary.md): fresh cases across eight packages and 14 modes, including manually checked returns, accounting, entitlements and ETF/index arithmetic. Initial schema rejection and corrected contract-reference input are both retained.
- [Business review](business-independent/summary.md): 54 fresh/replay/mutated requests and 299 current assertions, with native outputs, adverse mutations and before/after chronology repairs. The final summary distinguishes observed defects from successful repaired replays.

The reviews exposed missing provenance/control links, contradictory disclosure scope,
empty tax-lot scope, unresolved obligation/service completion and actual-event chronology
gaps. Repairs require real supplied references, retain unknown completion and compare
actual event dates with review/cutoff/source-known dates. Volatility constraints compare
exact variance with the squared limit before rounding. Unsupported optimization, complex
waterfalls, nonconventional IRR and production actions remain explicit gaps.

## Native integration example

[Rebalance to trading review](handoff-example/README.md) retains the detached producer
request, immutable native artifact, complete field mapping, receiver request, handoff
and actual receiver result. The integration tests cover all 40 new/expanded native modes
and reject rehashed fabricated quantities, omitted mappings, implicit rescaling and
missing original inputs. Passing a receiver schema does not authorize an order.

## Reproduction

From the repository root with Python 3.10+ and repository validation dependencies:

```bash
python tools/validate_skills.py
python tools/check_handoffs.py
python tools/check_asset_management.py --scope-only
python tools/build_asset_management_index.py --check
python tools/sync_investment_resources.py --check
python -B -m unittest discover -s tools -p 'test_*.py'
python tools/run_selftests.py skills/asset-management
python tools/run_asset_management_portable.py --output /tmp/am-portable-results.json
```

The explicit `--scope-only` option validates AM inventory plus all approved migrations when
unrelated categories are being edited concurrently. The default checker still requires
the whole-library package/catalog bijection; no release check is disabled.

Do not refresh a lock or golden merely to hide a failure. Record changed method behavior,
check it against independent expectations, then regenerate the relevant versioned current
package artifacts. Historical Phase 1 evidence is unchanged. Initial Phase 2 logs are
retained with `initial-` prefixes; the first router failures were stale Phase 1 expected
scope/counts, corrected to the new declared routes after independent route assertions.
