---
name: transaction-monitoring-scenario-designer
description: >-
  Design a transaction-monitoring scenario or controlled tuning proposal from a supplied risk hypothesis, population, data lineage, entity mapping, parameters, evaluation plan and change controls. Produces a source-bound proposal and readiness gaps; no rule activation or engine execution.
license: MIT
compatibility: Offline Python 3.10+ standard-library supplied-JSON helpers; no connector, engine execution or live matching service is bundled.
metadata:
  aws-fsi-category: "Compliance & Financial Crime"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Restricted; source-specific confidentiality and audience limits"
  aws-fsi-jurisdictions: "Supplied reviewed institution/activity/jurisdiction profile; no approved current-law pack"
  aws-fsi-owner: "Transaction Monitoring Design Lead / BSA Control Owner"
  aws-fsi-primary-user: "Transaction monitoring professional and accountable reviewer"
  aws-fsi-version: "0.1.0"
  aws-fsi-implementation-date: "2026-10-04"
  aws-fsi-recertification-date: "2027-10-04"
---

# Transaction Monitoring Scenario Designer

Draft a scenario that explains which supplied risk it addresses, who and what it covers, and why its proposed logic and parameters could detect the target behavior. The native object is `transaction_monitoring_scenario_design`; its identity is the scenario ID. A proposed configuration is withheld when a required design gate remains unsupported. A complete draft remains a proposal for the accountable owner.

Use this for a new scenario, population extension, changed aggregation/window, threshold tuning proposal or versioned engine change. Read [domain rules](references/domain-rules.md) and [input schema](references/input-schema.md) when framing the design; use [source map](references/source-map.md) for method references and [controls](references/controls.md) before drawing a readiness conclusion.

## Risk, data and logic

Start from the institution's supplied risk and expected customer/product behavior. Explain the detection hypothesis, eligible/excluded population and plausible legitimate activity; a typology name alone cannot justify a rule. Tie each proposed parameter to its unit, currency and rationale. Record aggregation keys, event identities, window boundaries/timezone, direction, gross/net treatment, missing values, late arrivals and exclusions in the supplied logic specification. There are no default thresholds or weights.

Define the exact dataset/version and identifier namespace behind the entity crosswalk. Retain link conflicts and ambiguity, mapping/graph versions, source evidence and identity limitations. Shared address, similar name, agent or counterparty labels, and graph edges remain assertions requiring reviewed matching evidence. No identity resolution algorithm is bundled.

For each needed field, obtain source/version, lineage and transformation, owner, null handling, event identity rule, scoped expected/loaded counts and same-currency amount reconciliation, data-through date and a reviewed freshness criterion. Exact reconciliation does not establish source completeness; record outages, fields omitted and unobserved populations. Missing or mismatched reconciliation blocks the proposed engine configuration.

## Evaluation and change proposal

Require frozen backtest and distinct untouched holdout identities/windows, training and holdout item IDs, sample-selection/label methods, leakage and independence evidence, bias/cohort dimensions, measurable metric definitions and owner-reviewed acceptance basis. Describe precision/recall against accepted target labels, coverage and label unknowns, sensitivity to candidate parameters, drift and latency. This helper checks supplied plan consistency; it performs no backtest, model validation or statistical inference. Route those substantive methods to their actual owners.

Retain supplied real-time event-time/ingestion-time, watermark, late-arrival, SLA, replay/idempotency and outage controls; versioned vendor documentation/access limits; statistical model classification, drift and validation ownership; copilot retrieval/citation, prompt-injection isolation, human oversight and confidentiality requirements; and sourced graph mappings as applicable. The helper records these supplied controls, without verifying their implementation.

Identify prior and proposed configuration references, owner/approver role, planned date, shadow/reconciliation gate, rollback trigger/configuration/owner and review cadence. Planned dates are not completed execution. Keep incumbent/parallel-run and rollback arrangements in the proposal for human acceptance. The helper cannot activate a configuration even when supplied approval text exists.

## Native deliverable

Use [output schema](references/output-schema.md) for the immutable result and [output template](assets/output-template.md) for a separately authored human narrative. The result retains risk-to-scenario design, lineage/reconciliation requirements, parameter proposal, evaluation plan, controlled change, technology requirements, engine observations, benchmark references, material blockers and unknown metrics. Engine observations and benchmarks have distinct IDs, versions and facts; references are not detection proof or law.

```sh
python3 -B scripts/validate_input.py INPUT.json
python3 -B scripts/calculate_or_transform.py INPUT.json > OUTPUT.json
python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json
python3 -B scripts/test_phase3.py
python3 -B scripts/run_evals.py
```

Keep the original input detached. Output validation recomputes the complete native result; edited fields, extra narrative and self-rehashed substitutions fail. Structural/duplicate/scope errors stop intake. Valid null or unsupported evidence produces a partial draft with dependent configuration withheld. Read [handoffs](references/handoffs.md) before using another package.

## Professional ownership

The Transaction Monitoring Design Lead and BSA Control Owner accept the risk coverage, proposed logic, parameters, data and change gates. Legal applicability, substantive model/independent validation, privacy/access approval and production acceptance remain with qualified owners. `human_review_required=true`, `action_taken=false`, `approval=not_requested` and `execution=not_performed` remain distinct. No connector, matching service, scheduler, configuration writer, alert action or case/SAR conversion is bundled.

The retained `transaction-monitoring-scenario-evaluator` keeps its five-rule replay method. Do not rename it, alias it to this design workflow, convert its PASS result into design acceptance, or implicitly transform its object. The [foundation contract](references/foundation-contract.md), [evidence contract](references/evidence-contract.md) and [source governance](references/source-governance.md) preserve scope and provenance. Synthetic software checks establish bounded behavior only; source truth and professional acceptance remain unverified.
