# Independent fresh insurance forward evaluation

Five original synthetic practitioner requests were designed and raw evidence frozen before implementation logic was examined. No packaged eval/test/golden fixtures or prior audits were read. All repository interactions were read-only apart from ordinary interpreter caches; evidence was saved under this temporary directory.

## Results

- 18 of 18 native CLI checks passed across five original cases and one separately sourced same-day valuation variant.
- 26 of 26 independent arithmetic comparisons passed; those checks import no package logic.
- Four original cases delivered their requested bounded arithmetic with correct evidence/workflow states. The original annuity case returned a null value scenario because its account value preceded review by one day; the package requires exact same-day values. The documentation and generic gap finding do not explain that restriction. The original source was retained, and a distinct sourced variant verified the arithmetic.
- All cases retained human review and no-action boundaries. This is a bounded synthetic forward evaluation, not source authentication or professional acceptance.

Each package directory contains `request.md`, frozen `raw-source.md`, `input.json`, `actual-output.json`, native validation outputs, `commands.json`, `response.md`, `mapping-notes.json`, `independent-arithmetic.json`, `status.json`, and `source-hashes.json`. The service package also contains its original-date finding and separate same-day supplement/input/output/checks. `summary.json` records readback and counts. Source hashes verify content consistency only.

## Package-specific observations

| Package | Original output status | Observed result |
|---|---|---|
| life-underwriting-reviewer | needs-data | Pending income evidence retained; 20-times disclosed ratio and literal disclosure conflict referred. |
| life-annuity-contract-service-reviewer | needs-data | Consent gap retained; undocumented exact-date requirement suppressed original scenario; distinct same-day variant yielded $41,250 proceeds and $130,000 account value. |
| life-benefit-claim-reviewer | needs-data | Wrong-insured certificate rejected; disputed designation prevented allocation; before-entitlement bridge $739,895.50. |
| reinsurance-program-analyzer | ready-for-review | Four supplied program/scenario pairs reconciled; sequential inuring and aggregate exhaustion matched independent arithmetic. |
| reinsurance-contract-administration-reviewer | needs-review | Total roll-forward tied at $268,750 while +$5,000/-$5,000 claim breaks remained; collateral and notice exceptions retained. |

No production source, live customer case, execution flow, or external professional review was exercised.

## Integration drift

The root agent announced a shared-foundation change after these native runs: upstream-context mismatch and future-upstream-artifact checks. No retained case supplies upstream artifacts. Final integrated replay belongs to the root verification; this report does not assume unchanged output without that replay. Package hashes were collected at final readback, rather than in an immutable pre-run snapshot. See `integration-drift.json`.
