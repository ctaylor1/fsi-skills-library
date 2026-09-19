# Wealth management P4 quality validation

Authorized 2026-09-17. P4 evaluates the existing P0–P3 portfolio through realistic advisor scenarios, fresh model runs and executable handoffs. It adds no practitioner skill and does not treat a package's presence or passing fixture tests as evidence of professional quality.

## Evaluation design

- Twelve synthetic source packets cover the router and all 27 practitioner destinations, including the manager-diligence package in Asset Management. Coverage means a workflow appears in a scenario; it does not mean every mode or jurisdiction is tested.
- Expected outcomes and critical failures are recorded in separate rubrics before execution. Evaluated models receive the source packet and task, never the rubric, expected output or earlier validation report.
- Each case has a with-skill and without-skill condition. Both receive the same source facts and task. The with-skill condition receives the relevant operational instructions, references, scripts and templates; the baseline receives none of those resources. This measures the package's combined assistance, not the isolated effect of its prose.
- Each run starts in a fresh temporary workspace. Model/runtime identity, settings, timestamps, prompt and source hashes, frozen skill files, actual responses and tool events are retained. A failed or absent run remains a failure or missing observation.
- A separate agent reviews each response against each rubric item, citing response evidence and stating any uncertainty. Root review adjudicates material findings. These are model-assisted reviews, not qualified wealth-professional acceptance.
- Initial outputs remain preserved. Any focused revision or skill repair receives a separate record and cannot replace the initial result.

## Realistic cases and boundaries

The cases cover onboarding and relationship mapping; household reconciliation and risk; policy and retirement; portfolio proposals and recommendation evidence; tax-aware transitions; estate/protection; performance and fees; client review and follow-up; servicing and investor protection; manager/private-market review; practice workload and lending; and family/trust coordination.

Inputs include incomplete, conflicting and audience-restricted evidence. Financial assumptions are explicitly supplied synthetic facts; the scenarios do not ask the model to invent tax law, legal authority, approval or client consent. A malicious instruction embedded in a source record tests whether the model treats it as evidence rather than authority.

## Executable handoffs

The separate handoff suite executes current package scripts and maps actual upstream outputs into downstream requests. It checks identity, source references, unresolved concerns and action boundaries, including household versus family/trust/book scopes. Test-specific adapters illustrate deliberate field mapping; they are not production integrations or a universal pipeline.

## Reproduction and results

The detailed [protocol](p4/PROTOCOL.md), [cases](p4/cases), [rubrics](p4/rubrics) and [validation record](P4-VALIDATION.md) describe the executed sample and its limits. Earlier authoring results remain in [P3 validation](P3-VALIDATION.md).

The model runner follows the documented [non-interactive execution](https://learn.chatgpt.com/docs/non-interactive-mode) and [CLI controls](https://learn.chatgpt.com/docs/developer-commands?surface=cli), with per-run configuration overrides rather than changes to the user's installation or saved configuration.

## Corrections and follow-up design

The initial frozen snapshot remains the basis of the 24-run comparison. Source-fidelity failures prompted three instruction changes, versioned **0.2.1**, in household financial planning, IPS drafting and recommendation evidence review. They require field-level support for priority ranks, account membership and evidence-specific reviewer/date attribution, with explicit unknowns where support is absent. Four regressions confirm the existing calculators preserve those unknowns; financial formulas and input schemas are unchanged.

Two separate experiments repeat cases P4-02/P4-03 and P4-04, respectively, under fresh contexts with the same substantive prompts, source packets and rubrics. Each also repeats its baseline: **six additional outputs**, reported separately. These are targeted regression observations on previously seen cases, not holdout evidence or proof that the general extraction problem is solved. Subsequent findings remain in the results and remediation backlog rather than being silently removed by tuning the initial experiment.

## Acceptance limits

A small, single-runtime sample can reveal defects and provide a reproducible baseline. It cannot establish statistical reliability, general superiority over a baseline, source authenticity, jurisdictional completeness or production fitness. With-skill gains and regressions must both remain visible. Institution-specific SME/control-owner review, repeated holdout evaluations, authenticated access and approvals, live connectors and production monitoring remain separate acceptance work.
