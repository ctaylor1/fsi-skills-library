# Independent Phase 4 specialist and regional evaluation

The evaluator authored fresh synthetic requests and arithmetic expectations from the public native schemas. Target eval fixtures, regression implementations and golden outputs were not consulted. All runs were offline. The evaluator did not edit target implementation code. This is bounded native/model-behavior evidence, not professional acceptance, source authentication or deployment readiness.

## Coverage and counts

The main evaluation contains **69 named cases, 182 native CLI calls and 240 passing assertions**. After the author corrected one finding, **two original cases were replayed unchanged: 6 CLI calls and 17 passing assertions**. Combined: **188 calls, 257 passing assertions, zero assertion failures**. An earlier schema-orientation pass of **20 calls** is retained separately and excluded from those totals. Named cases include authority and independent-source artifact-tampering checks.

- `stablecoin-settlement-assessor`: equal delivered fiat amounts and quote-bound cost comparison; missing redemption rights/cost; incorrect principal or chain scope; pilot availability; unequal delivered value. The independent positive case compares USD 65 fiat cost with USD 28 stablecoin cost, producing a USD 37 arithmetic difference without adoption authority.
- `payment-business-model-analyzer`: gross versus reported-net presentation, monetary versus transaction-count denominators, missing deductions, differing currencies and overlapping economic coverage. Both independent comparable segments yield net revenue 7,000, take rate 70 basis points and contribution after allocated fixed costs 2,800.
- Bank regional module: Pix, UPI and Interac domestic credit-push proposals; exact recipient binding, unsupported product scope and Interac Autodeposit name evidence.
- `cross-border-payment-designer`: a US–UK chain, fee allocation, direct/inverse and expired FX quotes, exact recipient account, intermediary identity/account transitions, regulatory entity scope and sanctions scope. Positive arithmetic is USD 1,000 principal plus USD 5 payer charge = USD 1,005 debit; (1000−2) × 0.8−3 = GBP 795.4 receipt.
- Liquidity corridor module: USD/EUR funding with exact conversion, separate account balances, failed funding, late credit, inadequate or unknown source cash, FX mismatch, cross-entity agreement and access windows. The positive case ends at USD 2,000 and EUR 100; removal stress produces an EUR 800 shortfall.
- All five native contexts: execution rejection, upstream unresolved evidence, inert source instructions, false authority/action, exact retained snapshot, output recomputation, authority tampering and independent-input substitution.

## Initial schema adjustments

`commands-initial.json` preserves the initial orientation pass. That read occurred while the regional author was finalizing the contracts. It omitted required fee jurisdiction in the corridor request and placed Interac delivery fields at proposal level. The author clarified that Interac delivery mode/name evidence belong inside `beneficiary_review`. The current corridor schema also makes regulatory entity coverage and the ordered delivery chain/account-transition evidence explicit.

The evaluator retained initial requests, outputs and rejections, then authored the additional fields from the current public schemas. These were input/schema alignment changes, not retroactive successful claims about the initial pass. Initial schema versions were not separately hash-snapshotted, so no initial-to-final schema hash equivalence is claimed.

## Finding and unchanged retest

The independent valid chain contained customer collection USD 1,005, correspondent delivery GBP 798.4 and final payout GBP 795.4. Changing only the intermediate correspondent amount to GBP 1 still produced `comparison_ready: true` with no gaps. The evaluator reported this as a material funding-conservation concern; the implementation author confirmed and fixed it by reconciling intermediary declared amounts against the supported gross principal basis and suppressing readiness for mismatches.

Original contradictory evidence remains in `cross-intermediate-amount-observation.json`, its `-output.json` companion and `intermediate-amount-observation.json`. The original positive case is `cross-current-schema-complete-chain.json` and its output. `after-corridor-fix/` retains independent replays of those exact inputs, including byte-identity assertions. The positive case still reaches comparison readiness; GBP 1 now produces `needs-evidence` and false comparison readiness. Endpoint arithmetic and no-action boundaries remain intact.

## Evidence and source disposition

- `commands.json`, `assertions.json`: main specialist/regional cases.
- `corridor-commands.json`, `corridor-assertions.json`: current corridor boundaries and artifact tampering.
- `source-hashes.json`: main-pass snapshot of script files in the five evaluated packages. This manifest covers scripts, not public schema/documentation files.
- `after-corridor-fix/commands.json`, `assertions.json`, `summary.json`: six replay calls, seventeen passing assertions and final count reconciliation.
- `after-corridor-fix/source-hashes.json` and `source-changes.json`: comparison with the main script snapshot. Only cross-border `scripts/domain.py` and `scripts/regression_tests.py` changed in that interval.

That two-file delta is specifically **main script snapshot to final replay snapshot**. It does not mean that schemas or other documentation were unchanged during the earlier author/evaluator collaboration. The schema clarifications above predate the final replay and are outside the script-only hash comparison. No additional tests or target edits were made for this report.
