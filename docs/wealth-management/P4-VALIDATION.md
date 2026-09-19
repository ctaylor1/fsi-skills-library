# Wealth management P4 quality-validation record

Date: 2026-09-17. **The quality-validation phase is implemented; behavioral acceptance is not achieved.** The catalog remains 239 packages, including 27 wealth-management packages. No practitioner coverage was removed or added in P4.

P4 measures actual model work against frozen synthetic advisor cases, supplements it with executable multi-package handoffs, and retains failures. Source fidelity remains a release blocker: several model-created structured inputs contain unsupported facts even when the accompanying memo is cautious and the scripts validate. A separate internal-audience packaging defect also remains open.

## What was evaluated

- Twelve realistic cases cover all 27 practitioner destinations and the router, using 73 synthetic source records, 111 rubric items per condition and 50 independently checked arithmetic expectations.
- The initial experiment contains 24 fresh model runs: each case with its relevant skills and without skills. Both conditions receive the same substantive task and source packet. Rubrics and expected outputs stay outside model workspaces.
- Six additional cold runs repeat three cases after focused instruction changes, retaining both conditions. They are regression observations on previously seen cases; they are not holdouts and do not replace the initial scores.
- Three separate agents grade actual delivered reports and retained structured artifacts with source/line evidence. Root reviews material judgments. Reviewers can see the condition; one wrote the cases, others authored supporting code or skills. They did not generate the evaluated outputs. No qualified wealth-professional acceptance or blinded human grading occurred.
- The requested model was **GPT-5.5, high reasoning**, using the existing authenticated Codex CLI 0.151.0. The installed runtime rejected the configured Astra model; no installation or saved configuration was changed. Exact server-resolved model identity/snapshot is unavailable, so all records honestly retain unknown actual identity and zero metadata-comparable pairs. Results are descriptive observations, not causal uplift or statistical evidence.

The [implementation](P4-IMPLEMENTATION.md), [protocol](p4/PROTOCOL.md), [cases](p4/cases) and [rubrics](p4/rubrics) define scope and reproduction. Operational skill files are frozen per experiment. The baseline lacks those files, but has the same local reading/computation/drafting affordances. Relevant skills were preselected: this does not test routing from the full catalog.

## Initial model results

All **24/24 runs completed and were reviewed**, with zero failed executions, missing runs, unreviewed items or artifact-validation errors. All **222 initial item decisions** retain evidence.

| Condition | Rubric items passed | Items failed | Cases passing every item | Cases with a failure |
| --- | ---: | ---: | ---: | ---: |
| With skills | 105/111 | 6 | 6/12 | 6/12 |
| Without skills | 81/111 | 30 | 2/12 | 10/12 |

| Case | Workflow | With skills: items passed | Baseline: items passed | Material observation |
| --- | --- | ---: | ---: | --- |
| P4-01 | Prospect/referral and onboarding | 9/9 | 9/9 | Both complete this case. |
| P4-02 | Household balances, risk and goals | 9/10 | 3/10 | With: invented priorities. Baseline: partial totals, funding and lineage gaps. |
| P4-03 | IPS and retirement income | 8/9 | 8/9 | With: invented priorities. Baseline: missing original issue code/message. |
| P4-04 | Construction, comparison and recommendation | 8/9 | 6/9 | With: unsupported performed-review attribution. Baseline: first-year costs and applicability/lineage gaps. |
| P4-05 | Rebalancing and tax | 8/9 | 7/9 | With: unsupported IRA classification. Baseline: incomplete lot economics/issue code. |
| P4-06 | Estate and protection | 8/9 | 8/9 | With: unsupported designation state/citation. Baseline: capacity context omitted. |
| P4-07 | Performance and fees | 8/8 | 6/8 | With: fee variance correct. Baseline: wrong fee variance and missing handoff context. |
| P4-08 | Client review and follow-up | 10/10 | 8/10 | With: rubric complete. Both: additional internal-audience packaging risk; baseline also loses origin/context. |
| P4-09 | Service and investor protection | 8/8 | 8/8 | Both complete; baseline window-boundary qualification accepted explicitly. |
| P4-10 | Manager diligence and private markets | 9/9 | 6/9 | With: complete. Baseline: commitment totals, dated no-receipt funding schedule and capacity context omitted. |
| P4-11 | Advisor book and lending | 9/10 | 6/10 | Both omit explicit maturity resource-gap analysis; baseline also has a reserve/cash error and other omissions. |
| P4-12 | Family governance and trust | 11/11 | 6/11 | With: complete. Baseline: calculation/provenance omissions plus an additional internal-audience risk. |

“Pass” means all predeclared rubric items passed in this one response. A failed item can represent unsupported data, incorrect arithmetic, incomplete requested analysis or lost provenance; those are distinguished in the retained rationale. Item percentages alone must not obscure critical findings or additional unscored diagnostics.

## Findings and targeted follow-ups

1. **Unsupported facts in structured inputs.** Initial skill-assisted P4-02 and P4-03 invented priority rankings; P4-04 copied an applicability reviewer/date into evidence-specific performed-review fields. P4-05 classified an unspecified spouse IRA as tax-deferred. P4-06 encoded absent collected bank-designation evidence as `none-recorded` and cited the wrong source for protection engagement context. Valid source IDs and reconstructed outputs did not establish that the input facts were supported.
2. **Focused corrections helped, without resolving the general problem.** Household planning, IPS drafting and recommendation evidence review are now version 0.2.1. They require field-level source comparison and explicit unknowns for priority, account membership and evidence-review attribution. Four regressions verify existing null handling; schemas and financial calculations are unchanged. Follow-up IPS and recommendation runs passed their full rubrics. The household follow-up preserved null priorities/account links but invented upstream artifact `RISK-BIRCH-OPEN`, causing source-fidelity and handoff failures. This remains open.
3. **Financial errors and omitted risk results.** P4-07 without skills subtracted a credit from both expected and assessed fees, reporting a -$34.25 variance. The supported comparison is $900 assessed versus $884.25 expected, a +$15.75 variance. The skill-assisted response calculated that correctly. Other baseline failures include omitted first-year costs, lot-loss details and original issue IDs/codes. The P4-11 baseline misstated the cash gap after reserve; both versions omitted the required explicit maturity resource-gap analysis. A 12-month loan projection does not answer a 24-month maturity question by itself.
4. **Internal-audience packaging remains a separate blocker.** P4-08's actual standalone joint-client emails excluded the restricted inheritance/dispute content. Both conditions nevertheless placed Mira-only H4 information in a broader internal packet; the baseline explicitly addressed the service manager/advisor, and the skill-assisted output overstated isolation. No disclosure was sent. The narrow predeclared client-email privacy item passes; this additional packaging defect is retained visibly outside the rubric rather than retroactively changing scores. The P4-12 baseline also put restricted guarantee information in a facilitator brief addressed to unspecified internal reviewers, although its separate family draft was clean. A separate file or section label does not by itself establish audience isolation.

All **6/6 targeted follow-up runs completed and were reviewed**. Across the three with-skill reruns, 26/28 items passed and two of three responses met every item; baselines passed 19/28 items and none met every item. These results remain separate from the initial sample.

| Case after correction | With skills | Baseline | Result |
| --- | ---: | ---: | --- |
| P4-02 | 8/10 | 4/10 | Priority/account unknowns preserved; invented upstream origin still fails CIT and HAND. |
| P4-03 | 9/9 | 8/9 | Null priorities preserved and all required IPS/retirement work present. |
| P4-04 | 9/9 | 7/9 | Evidence-specific reviewer/date unknowns preserved; all required work present. |

### Grading qualifications and adjudication

- P4-02 baseline transparently included a disputed asset range rather than supplying the required supported partial totals. Its balance/partial-total failures are failures of the predeclared method, not fabricated source values.
- Missing issue codes are provenance failures where the rubric explicitly requires them; they do not automatically mean the substantive concern was cleared.
- P4-09 supplies a seven-day window without an explicit calendar-boundary convention. The baseline explicitly gives both $800 with September 10 included and $0 with it excluded, excludes proposed transactions and preserves unknown observations. Root accepted the history item because the required result is present with a transparent boundary qualification. The source ambiguity is retained; the frozen packet/rubric was not edited.
- P4-10 baseline identifies the June 30 NAV and explicitly states that it exceeds the 60-day freshness threshold, but does not state the exact 79-day age. The semantic freshness criterion passes; that is not a claim that every numerical expectation was printed.
- The report evaluates the actual intended-audience deliverables and retained structured assertions, not just short final messages or claims that validation passed. Internal calculation traces do not substitute for missing requested professional analysis.

## End-to-end handoffs and software verification

**20 new handoff tests pass across five chains and 14 distinct packages.** They run actual package CLIs, validate upstream outputs before consumption and map explicit synthetic identities and sources into downstream requests:

| Chain | Important checks |
| --- | --- |
| Discovery → reconciliation → risk → IPS | $720,000 assets/$90,000 debt/$630,000 net; $65,000 liquidity gap; willingness and capacity remain separate; no effective mandate |
| Generated IPS → client review → follow-up | Original issue identity/message/source, owner and date survive; meeting outcomes come from separately supplied minutes |
| Family governance → trust administration → account service | Reviewed family/beneficiary linkage; $49,000 closing cash; $4,000 outstanding request; unresolved authority leaves qualified amount unknown |
| Private markets → lending | $8,000 shared-cash shortfall stays separate from $15,000 forecast deficit; cash is not reused; no financing option selected |
| Construction → comparison → recommendation | Caps/cost comparisons, unknown expenses and original breaches survive; missing per-check concerns are detected |

Negative controls demonstrate that locally valid artifacts can still drop cross-artifact source/subject/issue content. These test-only adapters establish the declared mappings; they are not production connectors, a universal pipeline or live source authentication.

Final observed checks:

- **1,082/1,082 package evaluation commands passed.** This count includes nested package regressions; it is not a count of real-model evaluations.
- **264 repository test methods passed**, including 32 evaluation-harness, 8 runner, 3 case-integrity and 20 handoff tests.
- **42/42 independent lending replay checks passed.**
- **239 packages validated, 0 errors / 0 warnings; 0 dangling handoff references.** Canonical helper copies match in 26 contract, 3 analysis and 6 workflow packages; catalog count stays 239.
- Scoped lint and whitespace checks passed. Four new package regressions preserve unknown source fields; the initial test-count expectation mismatch was corrected and the full suite rerun successfully.

Retained logs and replay results are in [software checks](p4/results/software-checks). Changes remain uncommitted; earlier P0–P3 work is preserved.

## Evidence, runtime audit and limits

All three archived experiments were read back through the artifact validator and report **complete-reviewed**, zero errors. Their combined **30 fresh sessions and 278 item decisions** are retained. Initial model outputs and failures remain intact. See the [evidence index](p4/results/README.md), [machine-readable archive/usage index](p4/results/artifact-index.json) and [initial results](p4/results/initial.json).

- [initial archive](p4/results/wealth-p4-20260917.zip) (3,151,243 bytes).
  - Archive SHA-256: `ea30a344372489109191a4ca0fa492590e293400f67190c19d7aba541c1a77d5`.
  - Frozen manifest SHA-256: `6bbbaa4829af5617e6f8791a6fe85cb8b858475f0c31403925e196af86d1b6c5`.
  - Skill snapshot SHA-256: `24fccb40dd3ac6634cd1194271200d60b83826c146f9673dd9dfbbc037ead927`.
- [planning-followup archive](p4/results/wealth-p4-followup-20260917.zip) (1,440,680 bytes).
  - Archive SHA-256: `92951048099118096f8a8069e46eac3603b72991c32be9a10abc0f9876027902`.
  - Frozen manifest SHA-256: `97d05d69a9f65fd3d8eda0103d139e1141cc2e847e73ac090e44a09d3a90d1a5`.
  - Skill snapshot SHA-256: `5835509ea797f010959fb37ad207b33ce38a718e32f944d882f0b827e87bff59`.
- [attribution-followup archive](p4/results/wealth-p4-attribution-20260917.zip) (1,268,627 bytes).
  - Archive SHA-256: `3563180e517308417847b35f67c68fef8f10e1b1bdae684521a2c1632cc98a51`.
  - Frozen manifest SHA-256: `df6c0d50393c20a2ce0753dc0380d7f3cff2aeea316cbafd0a507fee7cbdd011`.
  - Skill snapshot SHA-256: `e8850845ab1aa6b4929bdb104f92e8d146c2c070496b86f5c56442c20b420dba`.

Observed initial-run resource use (local wall time, excluding grading):

| Condition | Median run seconds | Reported input tokens | Cached input subset | Reported output tokens |
| --- | ---: | ---: | ---: | ---: |
| with-skill | 319.5 | 7,858,925 | 7,109,632 | 185,297 |
| without-skill | 161.4 | 1,496,660 | 1,223,680 | 93,501 |

Token counts are service-reported repeated context usage, not unique document size or monetary cost. Cached input is already included in input tokens. Supervisor/reviewer work and smoke checks are excluded.

Archives include immutable case/skill snapshots, prompts, source packets, actual reports and structured artifacts, raw model events, runtime records, per-item reviews, reviewer notes and tool-policy audits. The initial launched runner and final capture/harness code are retained separately. Generated deliverables were added to the evidence interface after observing that final messages linked substantive reports; cases, rubrics, prompts and original bytes were not changed. Reviews bind the actual separate artifacts rather than synthesized answers.

Fresh workspaces, ephemeral sessions and disabled host context/network features reduce contamination. Audited traces show local source reads, calculations and drafting; no observed external business action or hidden-rubric access. Two baseline runs made unsuccessful local Git-status probes; some runs recovered from a missing `python` alias using `python3`. The host-skill-discovery feature emitted an experimental-feature warning. This is trace evidence, not proof of a hermetic filesystem or independently authenticated backend identity. Runtime use of the model service is distinct from prohibited model-initiated network/business actions.

This small, purposive, single-requested-runtime sample is not a reliability estimate. There is no repetition study, randomization, full-catalog routing test, unseen holdout set, cross-model comparison, real-client source authentication, live connector execution or institution-specific professional acceptance. Passing fixtures, rubric scores and cryptographic hashes cannot supply those properties.

## Prioritized remaining quality work

| Priority | Required work | Exit evidence |
| --- | --- | --- |
| Q0 | Prevent unsupported facts and provenance from entering structured input, including account treatment, designation status and invented origin IDs | Independent field-to-source checks on new natural-language holdouts; no critical source-fidelity failures; unknowns remain usable without fabricated completion |
| Q0 | Separate internal audiences and source registries in actual delivered artifacts | Negative tests for every intended audience, including service managers and family members, with no restricted content, hints or hidden-item counts |
| Q1 | Close demonstrated omissions/arithmetic and preserve original issue identities through all handoffs | Repeated blinded holdouts with correct fees, lot bridges, first-year costs, subject/capacity, maturity resource gaps beyond the modeled horizon and original issue lineage |
| Q1 | Establish independent professional acceptance and a reproducible supported model identity | Qualified advisor/control-owner review, recorded disagreements/adjudication and retained server-reported runtime identity where available |
| Q2 | Broaden routing, mode, institution and runtime coverage | Unseen full-catalog routing tests, repeated scenarios and documented cross-model/firm-policy variation |

P4 is an implemented measurement and diagnostic baseline. These open items govern acceptance of future deployments; the current results do not certify the library for unsupervised wealth-management work.
