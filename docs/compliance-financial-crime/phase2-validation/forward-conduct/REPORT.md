# Independent initial forward conduct evaluation

Initial evaluation status: **PARTIAL**. Four assigned packages produced useful bounded review outputs, but three independently frozen practitioner expectations failed. This report assesses the original outputs retained here, before root-agent repairs. It is not a statement about the later live package state.

The evaluator read the four current skill instructions, evidence/foundation contracts, native schemas and executable methods. It did not read implementation-agent notes, existing package evaluation outcomes, or earlier Phase 2 validation results. Realistic synthetic raw facts and supported/unknown expectations were saved before invoking the installed CLI scripts. No packages, shared resources or catalog files were edited by this evaluator.

## Results and bounded usefulness

There are 12 well-formed synthetic cases, one deliberately malformed count case, and three retained initial ABC harness errors. All 12 well-formed cases passed the actual installed input validator, calculator and detached-original output validator. The malformed count was rejected and emitted no native result. Four outputs edited to claim approval, action and extra narrative were rejected by their actual output validators. The initial-run package file hashes did not change between input freeze and completion of those calls.

The independently authored assessment has 94 checks: 91 passed and 3 failed. This count includes the 12 CLI triplets, scope/date/audience retention, complete claim locators, boundary fields, inherited issues, domain assertions, four edited-output checks, and preservation checks. Three checks account for the initial harness enum errors; these are not package findings. See `assessment.json` for every check and exact actual/expected value.

| Practitioner job | Useful observed output from the realistic case | Initial limitations found |
| --- | --- | --- |
| Information barriers | Exact named actor, information set, purpose, operation and planned period comparison; five known access mismatches; standalone list-removal authority gap; unknown classification retained; no access/list changes | A classification unknown suppressed an independently known actor mismatch. A list-removal proposal embedded in an access request escaped separate list-change authority review. |
| Anti-bribery/corruption | 62,500 / 25,000 = 2.500000000000, four review triggers, incomplete diligence, supplied government-link concern and both counterexplanations retained; matched service evidence stays draft; mixed currency, unknown benchmark and zero benchmark withhold ratio | Actual beneficiary, payment routing, policy applicability, diligence quality and government connection are supplied assertions. The schema/native output does not substantively authenticate or investigate them. Unknown/conflict reasons are visible globally even when the row's `review_reasons` is empty. |
| Authorized misconduct investigation | Chronology independently ordered from 27 September to 1 October; supporting, contrary and neutral records plus the alternative automation hypothesis retained; contradiction remains unresolved; neutral interview plan within supplied scope; personal-phone forensic proposal outside scope | The method organizes supplied hypotheses/plans; it does not generate or authenticate an independent investigative theory, collection authority, neutral questions, privilege or HR/legal adjudication. |
| Customer conduct outcomes | ALL harm 24/800 = 3%, coverage 80%; vulnerable harm 9/60 = 15%, coverage 50%; supplied 2% criterion exceeded; value/support barriers retained; missing SWITCHERS; zero denominator differs from zero harm; overlapping cohorts never summed | Explicit repeated-event numerator versus unique-customer denominator yielded a numeric customer harm proportion rather than withholding it. Selection bias and causal harm stay unassessed. |

The vulnerable observed rate is 12 percentage points above ALL and five times ALL's observed rate. These are comparisons of overlapping observed groups, not independent populations or proof of causal harm. The native calculator leaves professional interpretation and targeted actions to the accountable owner.

## Three reproducible initial failures

1. **Known actor mismatch disappears under unrelated missing classification.** `ib-partial-known-mismatch/original-input.json` identifies requested actor EMP-999 and supplied authority actor EMP-102, each exactly mapped to its source fact. Classification is null. The initial result's `/results/request_reviews/0/reasons` contains only `unsupported or missing classification`; neither that list nor global issues contains an actor mismatch. Initial `/results/request_reviews/0/scope_consistent_with_supplied_authority` is null. The comparison was correctly withheld, but the independently established actor problem was lost. Failed check: `ib_partial_actor`.

2. **Access-only mandate hides a proposed restricted-list removal.** `ib-access-with-list-proposal/original-input.json` has operation `access`, supplied authority scope `["access"]`, and source-bound list proposal `Remove ORION common equity from restricted list after granting access`. The initial result gives `scope_consistent_with_supplied_authority=true`, `review_state=scope-consistent-draft`, and `reasons=[]`. The list proposal is copied but receives no separate authority gap or explicit list-change decision. Actual execution remains false. Failed check: `ib_embedded_list`.

3. **Declared metric grain mismatch does not withhold a customer harm proportion.** `customer-unit-mismatch/original-input.json` explicitly defines the numerator as repeated support-friction EVENTS and the denominator as unique observed customers. Counts are 42 events, 100 observed customers and 150 eligible customers. The initial result gives `metric_definition_evidence_consistent=true`, `observed_harm_rate=0.42`, and criterion comparison false. It should either withhold the unique-customer harm proportion pending deduplication or separately establish a correctly labeled events/customer metric. Failed check: `cc_unit_mismatch`. The instructions place semantic unit review in the human draft and acknowledge that the native method cannot independently verify those units; this is a demonstrated native limitation against the practitioner expectation, not evidence that exact source mappings prove compatible units.

All three failing native outputs passed exact detached reconstruction. Those validators established that the outputs matched their initial methods, not that the methods satisfied the practitioner expectations.

## Independently chosen challenge results

- The ABC exact boundary used 2,000,000,000,001 / 2,000,000,000,000 = 1.0000000000005 against limit 1. The display rounds to `1.000000000000`, while the unrounded criterion decision correctly remains false.
- ABC conflict/unknown-recipient intake retains both contrary government-link source mappings, returns null for the conflicted link and unknown recipient, and stays `needs-ABC-review`; the independently comparable ratio does not approve payment.
- Investigation `polarity=unknown` is accepted by the executable schema, then retained as unresolved null without crashing or assigning support/contradiction.
- An event on 1 October purporting to come from a source received on 30 September is excluded from eligible timeline/hypothesis support, despite being before the review cutoff.
- Unknown observed count and an empty eligible population withhold harm rate and criterion. Missing vulnerability remains null even when separately established counts support an observed zero rate.
- Harms 101 greater than observed denominator 100 is rejected at intake and calculation.

## Provenance, exact commands and replay

Each case folder contains `raw-facts.json`, `pre-run-expectations.json`, immutable `original-input.json`, `original-output.json`, separate stdout/stderr for all three CLI calls, and `run-record.json` with exact argv, working directory, return codes and artifact SHA256. Original native results remain separate from this human assessment. The top-level `pre-run-manifest.json` freezes input/expectation/raw-fact hashes and all initial package file hashes. `pre-run-corrections.json` separately freezes the three corrected ABC requests. `run-manifest.json` retains every exact command, result hash and edited-output check.

The exact initial sequence for any well-formed case is recorded in its `run-record.json` and has this form:

```sh
python3 -B /Users/taylor/DevRepo/Skills/fsi-skills-library/skills/compliance-financial-crime/information-barrier-reviewer/scripts/validate_input.py /Users/taylor/DevRepo/Skills/fsi-skills-library/docs/compliance-financial-crime/phase2-validation/forward-conduct/ib-partial-known-mismatch/original-input.json
python3 -B /Users/taylor/DevRepo/Skills/fsi-skills-library/skills/compliance-financial-crime/information-barrier-reviewer/scripts/calculate_or_transform.py /Users/taylor/DevRepo/Skills/fsi-skills-library/docs/compliance-financial-crime/phase2-validation/forward-conduct/ib-partial-known-mismatch/original-input.json
python3 -B /Users/taylor/DevRepo/Skills/fsi-skills-library/skills/compliance-financial-crime/information-barrier-reviewer/scripts/validate_output.py /Users/taylor/DevRepo/Skills/fsi-skills-library/docs/compliance-financial-crime/phase2-validation/forward-conduct/ib-partial-known-mismatch/original-output.json --input /Users/taylor/DevRepo/Skills/fsi-skills-library/docs/compliance-financial-crime/phase2-validation/forward-conduct/ib-partial-known-mismatch/original-input.json
```

To reproduce the assessment of retained initial outputs without re-running or overwriting native evidence:

```sh
python3 -B /Users/taylor/DevRepo/Skills/fsi-skills-library/docs/compliance-financial-crime/phase2-validation/forward-conduct/assess_forward.py
```

Root reported subsequent repairs to the information-barrier and customer-unit methods while this initial report was being finalized, and preserved initial source snapshots separately. Running the live package commands now assesses the later package version, and may not reconstruct these initial outputs. Use the recorded initial script hashes and root's preserved source snapshots for historical native-method replay. No post-repair acceptance claim is made here.

## Harness errors and professional limits

The initial ABC request builder supplied descriptive `benefit_type=intermediary service fee`; the executable schema requires enum `intermediary`. All three initial rejections are retained. Separately named `-corrected` cases change only that harness enum and consistent case/fact identifiers; substantive expectations were retained and frozen before re-run. The initial runner then aborted while loading the empty rejected ABC output for an edited-output test; `initial-run_forward.py` and its failure record are retained. The resumed runner loaded existing run records without overwriting original outputs.

This evaluation uses Python 3.14.7 and deterministic, synthetic, supplied evidence. It establishes bounded CLI behavior, exact output reconstruction and the stated initial practitioner findings only. It does not establish source truth, real-model narrative quality, institution-specific legal applicability, authenticated mandates, privilege, independence, professional acceptance, production readiness or receiver handoff compatibility. It performs no access grants, list updates, payments, witness contact, device searches, disciplinary decisions, complaint remedies, live system mutations, commits or external messages.
