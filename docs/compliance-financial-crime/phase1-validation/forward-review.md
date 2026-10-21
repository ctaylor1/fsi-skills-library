# Independent Phase 1 forward review

Date: 2026-09-21. Scope: offline synthetic native-input/calculation/output review of sanctions investigation, AML alert triage, SAR drafting, exam response packaging, transitional monitoring, the CFC common contract and router. This is a bounded independent forward pass, not a full security audit, legal review, source authentication or professional acceptance.

Final status: **PASS for the bounded independent forward scope — all seven findings resolved, 49/49 final expectations passed.** The historical failures and intermediate results below are preserved. This is not professional or production certification.

## Method and retained evidence

Fresh cases were constructed from the actual SKILL instructions, source-map documentation and native input schemas. Existing golden outputs were not used as expected truth. Original input JSON was retained separately and supplied to every output validator. Each case retains the source scripts used, exact commands, exit codes, stdout/stderr, input and output under archive member `cfc-independent-forward/initial/<case>/`. The initial evidence has not been replaced by later results.

All paths below refer to members beneath `cfc-independent-forward/` in the durable [evidence archive](forward-evidence.tar.gz), unless explicitly described as repository paths. After extraction and changing into that directory, the portable replay drivers are:

```sh
python3 -B run_forward.py independent-rerun
python3 -B run_monitor_router.py independent-rerun
python3 -B run_contract.py independent-rerun
```

The first driver covers 14 native cases; the second covers four monitoring and three routing cases. Each uses the current installed package scripts, writes a new stage directory, and runs `validate_input.py input.json`, `calculate_or_transform.py input.json`, and `validate_output.py output.json --input input.json` with Python 3 and `-B`. The sanctions and monitoring drivers resolve their planned renames if the old paths no longer exist. `results.json` records exact absolute command lines and exit codes. The third driver uses the canonical shared CFC contract and actual installed producer/receiver validators; it does not substitute permissive validator stubs.

All 63 initial native command invocations returned exit 0. That is evidence of deterministic contract acceptance, not evidence that the states below were defensible. Seven observations required repair or explicit resolution; their initial evidence follows, with successful repair replays recorded later.

## Initial findings

| ID | Case and reproducible input | Observed result | Required resolution |
| --- | --- | --- | --- |
| F1 | `aml_invalid_chronology`: `as_of=2026-09-21`; alert period `2026-12-31` through `2026-09-01`; matching open-case period/transaction set and supplied scoped suppression record | `approved-suppressed`, `proposed_only=true`, no chronology gap; all three native checks exit 0 | Invalid or reversed/future observation periods must fail validation or remain needs-data and unavailable for suppression recommendations. |
| F2 | `sar_future_activity`: one transaction occurs `2026-12-01`, after `as_of=2026-09-21`; aggregate, declared period and mapped narrative faithfully match those supplied dates; current content-bound authorization | `ready-for-quality-review`, tie-out pass, no chronology gap; all native checks exit 0 | Date tie-out must also compare occurrence dates with the assessment date; future observations cannot be treated as completed supplied activity. |
| F3 | `sar_unmapped_rationale`: the six narrative fields remain mapped, but `investigation_rationale.summary` is replaced with `Customer deliberately laundered criminal proceeds and violated every AML law.` and citation `unmapped-nonexistent-source`; authorization regenerated for this exact input | Unsupported rationale passes through under `status=present`; package remains `ready-for-quality-review` | Apply the declared exact-evidence mapping boundary to material rationale claims, or withhold/flag the unmapped rationale and return needs-evidence. A nonempty citation string does not establish source mapping. |
| F4 | `exam_conflicting_approval_records`: valid content-bound approval plus second record for the same role with `status=rejected`, future date, wrong request ID and invalid digest | Both output approval records are labelled `approved`; the response remains draft-ready | Validate and preserve each approval record individually. A valid record for a role must not rewrite a different rejected or unbound record into an approval. Whether contradictory valid records block readiness needs an explicit policy. |
| F5 | `sanctions_future_listing`: list effective date `2026-12-01` after `as_of=2026-09-21`, with retrieval `2026-09-21`; two supplied directly blocked interests total 55% | No gap; `recommend-true-match-escalate`, direct aggregate threshold met | Record a source-chronology conflict/needs-data state. Lower consequence than clearance because restriction assessment is explicitly not performed and escalation remains human-owned; still the list evidence cannot be treated as current without surfacing the contradiction. |
| F6 | `monitor_cluster_and_velocity_boundary`: four transactions, baseline two, multiplier two, zero warning buffer | Velocity result `WARN` at exactly four; SKILL says numeric limit comparisons are inclusive | Make velocity consistent with the documented inclusive threshold contract, or explicitly document a deliberate different equality convention. |
| F7 | `monitor_changed_ledger_dedup`: initial flow is USD 10,000 in / 9,500 out; second run changes outgoing transaction ID from `O1` to `DIFFERENT-LEG` and date from Sep 11 to Sep 19, retaining total and as-of; first fingerprint is in `open_cases` | Second run `new=0`, `deduplicated=1`; both native results validate | Fingerprints must bind the underlying transaction evidence, observation period and actual scenario configuration, not just aggregate evidence plus a config label. Changed ledger evidence is explicitly documented as new. |

`initial/summary.json` and `initial/monitor-router-summary.json` contain the full results. Individual `scripts/` copies permit inspection of the exact implementation responsible for each initial result while other agents repair the working tree.

## Bounded checks that passed

- **Sanctions:** two separate supplied direct blocked interests of 30% and 25% aggregate to 55%; ownership is a separate zero-weight nexus and restriction authority remains with the officer. A stale snapshot (Sep 10 versus Sep 21 assessment) becomes needs-data. This does not validate indirect ownership, legal status of supplied owners or list authenticity.
- **AML triage:** an exact duplicate without scoped authorization remains a possible duplicate; missing screening status produces needs-data/Unrated; a matching synthetic scope-bound approval permits only a proposed suppression state. No case or queue is modified.
- **SAR:** exact mapped supplied facts can reach draft quality review; an extra unsupported `narrative_inputs.why` claim is withheld and returns needs-evidence. Required human sign-offs remain pending. The gross amount is 3,000 across the two supplied legs and is not represented as unique proceeds.
- **Exam package:** evidence dated January through June supports the exact assertion for that period; moving evidence commencement to March causes unsupported-assertion. Both complete and partial packages remain draft-not-submitted.
- **Monitoring:** a dense three-transaction rolling cluster is found despite an earlier outlier. Missing transaction currency produces NOT_EVALUABLE and needs_data, with `evaluation_complete=false`. Aggregate flow ratio is explicitly labelled as having no time linkage.
- **Router:** a planned primary remains planned_capability_gap even when supporting skills/data are declared; a filing request returns action_requires_separate_authorization; absent institution context remains needs_context. Routing never launches a skill or performs an action.

## Shared CFC contract and audience review

Twelve independent expectations passed in `initial/contract/results.json`:

1. A valid native SAR output plus explicit FIU context produces a common packet, still partial and human-review-required.
2. A different detached original input is rejected by producer reconstruction.
3. A missing source version is rejected.
4. SAR classification downgrade is rejected.
5. SAR customer audience is rejected.
6. An invented native filing field is rejected even after the outer envelope is rehashed.
7. Dropping a source issue is rejected even after the outer envelope is rehashed.
8. An exactly mapped same-context handoff is accepted with `authority_granted=false`.
9. Changing a receiver transaction amount is rejected against the detached mapping source.
10. Dropping inherited unresolved issues is rejected.
11. Changing to a regulator audience is rejected.
12. Changing the institution is rejected.

The accepted test is a same-reporting-case transfer, not proof of an automatic triage-to-investigation-to-SAR chain. Actual native validators ran in separate processes. Supplied reviewer names, source references, source versions and access labels are still unverified declarations; no legal disclosure basis, issuer authentication, professional acceptance or source truth was established.

## Status

Initial independent forward status: **PARTIAL — seven native observations awaiting repair or resolution; shared/router bounded checks passed.** Initial failures are preserved. Replays after implementation changes must be reported separately below rather than overwriting this record.

## Extended customer and governance probes

At the implementation owner's request, ten additional fresh synthetic cases were run after the package-path migration. Evidence is separately retained under `extended-initial/`; driver: `python3 -B run_customer_governance.py <new-stage>`. No existing golden input/output was used.

| Case | Independent expectation | Observed result |
| --- | --- | --- |
| `cdd_complete_scope` | Supplied complete individual profile, documents, cross-source checks and fresh documented empty screening results may use the bounded standard track | Standard-CDD; adjudication required; source truth remains unverified |
| `cdd_future_screening` | Empty hits with future coverage date must not establish completed current screening | Needs-Data; sanctions coverage remains unknown |
| `cdd_conflicting_identity` | One positive and one negative source identity check must not produce a clean conclusion | identity_mismatch fired; EDD-Recommended under the explicit supplied test policy |
| `cdd_future_identity_document` | A verified assertion on a document issued after as-of cannot establish current document verification | unverified_identity fired; Remediate-First |
| `risk_complete_factors` | Weights 40/60, both values 1 on a four-point scale, independently yield 25/100 | score_pct 25.0; Low; Align-No-Change on supplied policy terms |
| `risk_missing_factor` | Removing a required factor must not shrink the denominator and yield a cleaner rating | score_pct null; Remediate-Data-First |
| `risk_future_factor` | A factor observed after as-of is unavailable at the assessment date | score_pct null; Remediate-Data-First |
| `regulatory_proposed_past_dates` | A proposal must not become an overdue binding obligation merely because supplied effective/deadline dates have elapsed | No elapsed-compliance-deadline finding; proposed state retained |
| `regulatory_unknown_implementation` | An elapsed active deadline with unknown implementation does not prove an implementation breach | No elapsed-compliance-deadline finding; explicit unknown implementation limitation |
| `regulatory_future_publication` | Source publication after the assessment date must be rejected | Input and calculation both exit 1; no native output is produced |

All ten expectations passed. The first nine complete native round trips (27 commands) returned exit 0; the invalid future-publication intake was rejected. Running its output validator on the absent output also failed, and does not count as a valid-output check. These cases support the stated limited behavior only; they do not validate actual customer classifications, methodology quality, legal applicability, approval authority or operational source truth.

## First repair replay — monitoring and common contract

Evidence: `after-repair/`, retained separately from `initial/`. The implementation owner reported the monitoring changes ready; the original independent inputs were replayed against the migrated `transaction-monitoring-scenario-evaluator` and its extracted, pinned `scenario_replay.py`.

- **F6 resolved on replay:** velocity at four transactions against baseline two and multiplier two now returns BREACH; the rolling structuring cluster still returns BREACH.
- **F7 resolved on replay:** changing outgoing transaction ID/date while retaining aggregate totals now produces `new=1`, `deduplicated=0`. The earlier result was `new=0`, `deduplicated=1`.
- Missing-currency behavior and all three router checks remain correct. All 21 monitoring/router command invocations exited 0.
- All original 12 common-contract expectations still pass. Two further tests constructed exact detached mappings around modified receiver provenance: dropping one source record and replacing its version. Both are rejected with `receiver workflow dropped source provenance records`. Evidence is in `after-repair/contract/additional-results.json`; driver `run_contract_additional.py`. Total: 14 passing contract expectations.

Status after this replay: F6 and F7 resolved; F1–F5 still awaiting their separate repair replay. No initial evidence was overwritten.

## Second repair replay — sanctions, AML, SAR and exam packaging

Evidence: `after-repair-native/`. The original 14 cases were replayed without changing their inputs. This resolved the five remaining behavioral observations:

- **F1:** the reversed/future AML period now fails input validation, produces a safe needs-data result when the calculator is called directly, and fails output validation against the invalid original. No suppression recommendation is produced. A subsequent implementation-owner hardening pass is adding direct calculator intake rejection; this intermediate replay remains preserved.
- **F2:** future SAR activity is needs-evidence with assessment-date chronology breaks.
- **F3:** the unsupported rationale is withheld and needs-evidence. The old positive SAR input also correctly becomes incomplete because it lacks the newly explicit rationale evidence mapping.
- **F4:** the rejected/unbound exam approval record remains rejected, has failed scope checks, and produces needs-approval. It is no longer relabelled approved by another record for the same role.
- **F5:** a future sanctions list effective date is visible as `list entry not yet effective as of assessment`, with needs-data.

Three new conforming SAR cases were constructed separately: exact rationale facts plus `investigation_rationale.evidence_ids` produce ready-for-quality-review; changing only transaction chronology produces needs-evidence solely for amount/chronology tie-out; changing only the rationale to an unsupported guilt claim withholds the rationale and produces needs-evidence. Their complete input/calculation/output checks pass. These inputs do not replace the originals.

All 14 contract expectations were rerun against the updated native validators and still pass. `intermediate-acceptance.json` at this stage records 23 assertions passing: seven corrected behaviors, the new positive SAR case, 14 contract expectations, and retained-evidence integrity. All 378 original evidence files still match their earlier SHA-256 manifest. At this intermediate stage, archive creation was deferred until the direct-calculator structural gate and final replay below.


## Final replay and durable evidence

The final `final-replay/independent-acceptance.json` records **49/49 passing expectations**: 34 native scenario outcomes, 14 common-contract expectations and unchanged original evidence hashes. All seven original behavioral findings are resolved. The 34 scenarios include two deliberate structurally invalid inputs: reversed AML chronology and future regulatory-source publication. Both input validation and direct calculation reject them with exit 1; no JSON native output is produced, and no valid-output check is claimed for these two inputs. The other 32 scenarios pass their native input/calculation/detached-output round trips and their independent state expectations.

The implementation owner separately identified fractional sanctions ownership arithmetic (`0.01 + 32.16 + 17.83`) near the exact 50% boundary and changed aggregation to decimal arithmetic with focused boundary regressions. This is an additional implementation-owner finding and validation; it is not included in the 49 independent expectations above. The independently tested 55% multi-owner case remains correct in the final replay.

Durable artifact: [forward-evidence.tar.gz](forward-evidence.tar.gz), 1,337,163 bytes. SHA-256:

```text
908011ac05faed8cd72de0551f7f5a329be1e19fbb8735f4d46c234081da35f7
```

The archive includes all original inputs and failures, their native source snapshots, initial hash manifest, every repair stage, current portable drivers, driver history, exact command logs and the final acceptance file. Its content manifest covers 1,135 files. It was extracted into a fresh temporary directory, all 1,135 content hashes matched, and `assess_final.py final-replay` returned 49/49 again. The original 378-file manifest also remained unchanged. No raw generated evidence directories were added to the repository.

To inspect the archive from the repository root, use a new extraction directory:

```sh
mkdir -p /tmp/cfc-forward-evidence-review
shasum -a 256 docs/compliance-financial-crime/phase1-validation/forward-evidence.tar.gz
tar -xzf docs/compliance-financial-crime/phase1-validation/forward-evidence.tar.gz -C /tmp/cfc-forward-evidence-review
cd /tmp/cfc-forward-evidence-review/cfc-independent-forward
python3 -B assess_final.py final-replay
```

To replay against an identified checkout, set `CFC_REPO_ROOT` and choose a new stage name; never overwrite a retained stage:

```sh
export CFC_REPO_ROOT=/Users/taylor/DevRepo/Skills/fsi-skills-library
python3 -B run_forward.py independent-rerun
python3 -B run_monitor_router.py independent-rerun
python3 -B run_customer_governance.py independent-rerun
python3 -B run_sar_conforming.py independent-rerun
python3 -B run_contract.py independent-rerun
python3 -B run_contract_additional.py independent-rerun
python3 -B assess_final.py independent-rerun
```

The forward pass is complete within its authorized offline scope. No live source authentication, institutional source integration, filings, regulator contact, operational changes, legal acceptance or professional acceptance was performed.
