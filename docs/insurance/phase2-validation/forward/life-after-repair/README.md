# After-repair replay: life and reinsurance forward cases

Result: **PASS**. Replayed all five unchanged original cases plus the separately sourced same-day annuity valuation variant against the current package files. Raw packets, requests and native inputs were copied byte-for-byte; the original valuation date was not changed.

- **18/18 native CLI steps passed:** input validation, calculation and output validation for each of six inputs.
- **26/26 independent arithmetic comparisons passed.** The independent checker was reused with only its evidence-directory path changed; no package implementation is imported.
- **All six `results` objects are unchanged.** The four other original package outputs and the same-day annuity variant are entirely unchanged, including the effect of the shared-foundation integration.
- The original annuity output now adds exactly one finding, `valuation_date_stale`, explicitly naming original snapshot **2026-09-17** and review **2026-09-18**. Its `value_scenario` remains null; the missing assignee consent remains unresolved. Only `findings`, inherited `unresolved_issues`, and the artifact containing those changes differ.
- The separate same-day variant still yields **$41,250 proceeds** and **$130,000 account value after gross withdrawal**, with consent missing and no transaction instructions.
- The exact same-day requirement is now expressly documented in the service package's SKILL, source map and domain rules. The earlier documentation/usability finding is resolved for this reproduction.

Package source hashes were captured before and after all native replay steps and matched. Copied input/source hashes matched their originals. Artifact hash readback passed. These hashes establish content consistency, not source authentication.

See `summary.json` for exact output comparisons, `unchanged-input-hashes.json` for byte-level original checks, `package-hashes-before.json` / `package-hashes-after.json` for runtime stability, and `artifact-hashes.json` plus `hash-readback.json` for saved evidence integrity. Each package folder contains the copied raw evidence, unchanged input, newly generated actual output, native command logs and independent numeric checks. `arithmetic-command.json` records the unchanged checker logic and its result.

No repository source was edited, no live case or external action was exercised, and no professional acceptance is claimed. The original forward-evaluation evidence under `/tmp/insurance-p2-forward-life` remains unchanged.
