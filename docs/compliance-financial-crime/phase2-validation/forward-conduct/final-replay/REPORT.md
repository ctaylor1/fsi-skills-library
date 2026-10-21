# Independent final conduct replay

**Bounded final replay: 211 checks passed, 0 failed.** No remaining method defect was reproduced in these cases. Earlier evidence remains unchanged: the initial independent state is **91/94**, and the first repaired-method replay is **139/140**. Their inputs, expectations, original outputs, reports, commands, hashes and method snapshots were not modified.

This final replay executed **28 cases**: 18 unchanged prior replay intakes, five separately amended exact-decimal intakes, and five independent boundary intakes. **24 valid cases** passed each actual installed input/calculation/detached-output CLI. **Four malformed cases** were rejected and emitted no native result. All **five edited-output validator calls** rejected changes. Measured execution is **84 primary CLI calls + 5 edited-output validator calls = 89 installed CLI invocations**. Assessment counts are 211 expected/actual assertions, rather than 211 distinct cases or commands.

## Exact decimal precision repair

| Supplied threshold representation | Exact observed count ratio | Final comparison | Meaning |
| --- | --- | --- | --- |
| Unchanged long numeric JSON literal `0.33333333333333333334` | 1/3 | null | Valid partial intake; original decimal precision is unestablished after float parsing and exact decimal evidence is requested |
| New source-bound exact string `"0.33333333333333333334"` from the same retained raw lexeme | 1/3 | true | The finite exact threshold is above one third and the string is preserved intact |
| New source-bound exact string `"0.3333333333333333"` | 1/3 | false | Exact one third is above this shorter finite threshold, despite the same displayed rate |
| Integer 0, zero harms of ten observed | 0 | true | Exact integer boundary |
| Integer 0, one harmed of ten observed | 1/10 | false | Exact integer boundary |
| Integer 1, all ten observed harmed | 1 | true | Exact integer boundary |
| Floating numeric 1.0 | 1/10 | null | Floating input remains partial under the explicit exact-value contract |
| 256-character plain decimal string `0.` followed by 254 threes | 1/3 | false | Maximum documented character length remains supported exactly |

Plain strings with exponent notation, an exact value above one, and 257 characters were independently rejected. The fourth rejected case is the retained original harms-greater-than-denominator intake.

The long-decimal source value is not recovered by guessing from a parsed float. The final amendment reads the retained raw original JSON with a lexical-preserving parser and compares the threshold's numeric lexeme to its original mapped fact. It then supplies a separate newly asserted exact-string source fact with the same characters. Each exact-string amendment has `amendment.json`, threshold lineage, detached input, raw-fact references and before-run expected outcomes. The raw long threshold `0.33333333333333333334` and expected true comparison were frozen before the actual installed calls.

The new supplement remains synthetic and supplied-unverified. Original numeric source files and their lexical lineage remain separately immutable. The amended JSON also retains unused original numeric source records; ordinary JSON serialization can display their parsed floating representation. The active amended threshold claims and their newly mapped source facts carry the exact strings. Any earlier amendment wording about old registry facts being untouched refers to retained parsed records, not a claim that their numeric JSON spelling was preserved in the new serialization; see `serialization-note.json`.

## Legacy positive expectations remain incomplete

Eight unchanged customer intakes contain fractional numeric JSON thresholds. Every final criterion comparison is null. Their prior pre-run expectations are copied byte for byte into `prior-pre-run-expectations.json`; initial expectations are also retained where available. The separate final pre-run contract expectations explicitly document precision-incomplete intake. These checks are **not credited as successful prior positive or negative threshold comparisons**.

Original intakes without typed count units continue to withhold harm/coverage metrics. Explicit mixed event/customer units also remain unsupported. Otherwise supported unique-customer observed rates can still be calculated while the floating-threshold comparison is withheld with a specific precision issue. `assessment.json` lists every legacy case, its metric-scope state and comparison status.

Five separately named `*-exact-decimal` cases add string evidence. In the realistic unique-customer case, ALL retains harm 3%, coverage 80%; vulnerable customers retain harm 15%, coverage 50%; both exceed exact string criterion `"0.02"`. Known zero harms with a positive denominator meet that criterion; zero/unknown denominators remain null. Missing SWITCHERS, value/support barriers, missing vulnerability and overlapping cohort limits remain visible. Exact decimal evidence does not rescue the deliberately mixed event/customer metric.

## Other conduct methods and boundaries

Information-barrier replay continues to retain the known actor mismatch despite unknown classification and the list-change authority gap inside an access-only request. Exact named authority remains an internal scope-comparison draft; access and list execution remain false.

ABC retains the fee/service/diligence/link concerns and plausible counterevidence, rejects non-comparable ratio conclusions, and compares the unrounded 1.0000000000005 ratio against limit one despite display `1.000000000000`. Unknown recipient and conflicting official link remain unresolved; no payment approval or legal guilt determination is generated.

Investigation replay retains source chronology, contrary records, alternative hypotheses and unresolved contradiction. Unknown polarity and impossible source receipt chronology stay excluded from hypothesis support. Interview/collection proposals stay within the supplied evidence scope or are explicitly out of scope; no contact, collection, device search, privilege or HR/legal adjudication occurs.

All 24 valid outputs retained native scope/time/audience/classification, every claim locator, inherited issues and source-assurance/action/approval/execution boundaries. Four edited outputs claiming approval/action/narrative were rejected, as was an exact-decimal output edited to shorten the threshold and reverse its comparison.

## Frozen evidence and replay

`pre-run-manifest.json` records every before-run input/expectation hash and runtime/instruction hashes. The freeze covers six actual runtime scripts per package plus applicable skill/intake/domain/contract/control documentation; generated package manifests awaiting root sync are explicitly excluded. `run-manifest.json` records matching runtime/instruction hashes after execution, exact argv, working directories, return codes, output hashes, and the unchanged prior evidence set. **Before/after hashes match, and no prior evidence file changed.**

`method-snapshot/` preserves the 24 frozen runtime scripts for historical replay. Each case contains input, raw facts, before-run expectations, original final stdout/stderr, output and `run-record.json`. `assessment.json` contains all 211 exact expected/actual assertions. `artifact-hashes.json` lists final replay artifact SHA256 values.

The exact original installed commands for the long exact-string case are retained in its `run-record.json`:

```sh
python3 -B /Users/taylor/DevRepo/Skills/fsi-skills-library/skills/compliance-financial-crime/customer-conduct-outcomes-reviewer/scripts/validate_input.py /Users/taylor/DevRepo/Skills/fsi-skills-library/docs/compliance-financial-crime/phase2-validation/forward-conduct/final-replay/customer-long-decimal-threshold-exact-decimal/input.json
python3 -B /Users/taylor/DevRepo/Skills/fsi-skills-library/skills/compliance-financial-crime/customer-conduct-outcomes-reviewer/scripts/calculate_or_transform.py /Users/taylor/DevRepo/Skills/fsi-skills-library/docs/compliance-financial-crime/phase2-validation/forward-conduct/final-replay/customer-long-decimal-threshold-exact-decimal/input.json
python3 -B /Users/taylor/DevRepo/Skills/fsi-skills-library/skills/compliance-financial-crime/customer-conduct-outcomes-reviewer/scripts/validate_output.py /Users/taylor/DevRepo/Skills/fsi-skills-library/docs/compliance-financial-crime/phase2-validation/forward-conduct/final-replay/customer-long-decimal-threshold-exact-decimal/output.json --input /Users/taylor/DevRepo/Skills/fsi-skills-library/docs/compliance-financial-crime/phase2-validation/forward-conduct/final-replay/customer-long-decimal-threshold-exact-decimal/input.json
```

If live methods later change, use the recorded final runtime snapshots rather than claiming the live package reconstructs these outputs. To recompute the assessment of the saved final outputs without modifying earlier evidence:

```sh
python3 -B /Users/taylor/DevRepo/Skills/fsi-skills-library/docs/compliance-financial-crime/phase2-validation/forward-conduct/final-replay/assess_final.py
```

This is a deterministic synthetic supplied-evidence replay. Source authenticity, policy legitimacy, institutional authority, legal applicability, privilege, investigation independence, causal harm, real-model narrative quality, professional acceptance, receiver compatibility and production readiness remain unestablished. No package, shared resource, catalog or root report was edited by this evaluator. No access grant, list update, payment, contact, device search, discipline, complaint remedy, external message, commit or live system mutation occurred.
