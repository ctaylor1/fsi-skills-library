---
name: transaction-monitoring-effectiveness-reviewer
description: >-
  Review supplied transaction-monitoring effectiveness evidence for an exact population, scenario/version, period and cohort. Separates engine detections, data coverage, accepted labeled-sample precision/recall, unknowns and operational measures; does not infer crime, SAR conversion, population inference or assurance.
license: MIT
compatibility: Offline Python 3.10+ standard-library supplied-JSON helpers; no connector, engine execution or live matching service is bundled.
metadata:
  aws-fsi-category: "Compliance & Financial Crime"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Restricted; source-specific confidentiality and audience limits"
  aws-fsi-jurisdictions: "Supplied reviewed institution/activity/jurisdiction profile; no approved current-law pack"
  aws-fsi-owner: "Transaction Monitoring Effectiveness Review Lead / Independent Testing Owner"
  aws-fsi-primary-user: "Transaction monitoring professional and accountable reviewer"
  aws-fsi-version: "0.1.0"
  aws-fsi-implementation-date: "2026-10-04"
  aws-fsi-recertification-date: "2027-10-04"
---

# Transaction Monitoring Effectiveness Reviewer

Review whether supplied evidence supports specific monitoring measures for an exact population, period, scenario/engine version and cohort. The native object is `transaction_monitoring_effectiveness_review`; its identity is the review ID. Keep observed detections, population observation coverage, labeled-sample precision/recall and operational measures distinct. The helper issues no overall effectiveness or assurance opinion.

Use this for a bounded monitoring effectiveness review, before/after evidence challenge or evaluation of an institution-supplied test result. Read [domain rules](references/domain-rules.md), [input schema](references/input-schema.md) and [source map](references/source-map.md) when choosing the method; read [controls](references/controls.md) before comparing results.

## Population and observation evidence

Bind the exact population definition, unit and IDs to expected/received count reconciliation, versioned extract/reference, event window, cohort, data-through date and supplied freshness criterion. Determine whether omitted feeds, delayed events, exclusions, duplicate economic items or entity mapping uncertainty prevents comparable coverage. Dataset/identifier namespace, crosswalk/graph reference and versions, conflict/ambiguous-link counts and limitations stay explicit. An agent/counterparty label or graph edge does not resolve identity. Duplicate IDs and known scope/version/window mismatches stop native intake.

Require source-bound engine observations for the same scenario/engine version and population/cohort. Preserve event and observation dates; observation time must be supported by source receipt/cutoff. A missing/unknown observation is not a non-detection. Output the known observed detection fraction with its exact count denominator, then independently assess observation coverage of the supplied reconciled population. Neither measure establishes illicit activity or exhaustive risk coverage.

## Reference labels and sampling

Record exact selected sample IDs, selection frame/method and limitations, accepted label definition/domain/version, adjudication record/review references and owner. Positive/negative mean the reviewed target reference; they never mean guilty/innocent, SAR-filed/not-filed, or legal criminal truth. Do not use alert disposition or a benchmark's labels as automatic ground truth. Audit findings may identify known misses but do not establish the number of all misses or a representative negative population.

Review independence using operational involvement, conflict/reporting-line evidence and an explicit reviewed assessment. Role names alone are insufficient. Keep training overlap, selection/label leakage, holdout/cohort differences, nonalerted sample selection and unknown labels visible. Labels are admissible only under the supplied accepted method and exact reference scope/version. Count TP/FP/FN/TN only for eligible selected items; unknowns and missing selected observations remain separate. Any selected unknown withholds full-sample precision/recall. No unlabeled item becomes negative.

Compare a supported sample metric only with supplied exact-decimal institutional criteria and their owner/review basis. Retain exact numerator and denominator; rounded display values do not drive comparisons. A probability sampling design, interval estimate or population inference requires the separate accepted statistical method; this helper performs none. Different versions, windows, populations, reference protocols or cohorts require an explicit review and comparable evidence, not pooled counts.

## Operations, technology and deliverable

Use operational completed-review, minutes, costs, currency, accounting and outcomes evidence only when actually supplied for the same scenario/version/population/window/cohort. Output unit measures with their bases; faster closure, fewer alerts and lower cost alone cannot establish effectiveness. Preserve capacity, delay, quality and cost tradeoffs in the narrative only when supported. Unknown cost can remain an optional unknown metric while independent supported detection/sample measures survive.

Retain supplied versioned real-time/SLA/late-arrival evidence, vendor limits and change controls, model classification/drift/validation, copilot provenance/human review and graph/data mapping controls. Readiness of those controls remains an accountable-owner assessment. An unsupported material control requirement withholds favorable criterion comparisons; it does not erase observed facts.

Use [output schema](references/output-schema.md) for native results and [output template](assets/output-template.md) for separate narrative. Preserve material blockers and unknown metrics, source bindings, engine observations and distinct benchmark IDs/domains/versions/context. Do not import benchmark reference counts into institutional observations or thresholds.

```sh
python3 -B scripts/validate_input.py INPUT.json
python3 -B scripts/calculate_or_transform.py INPUT.json > OUTPUT.json
python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json
python3 -B scripts/test_phase3.py
python3 -B scripts/run_evals.py
```

Native validation requires the detached original and recomputes the complete result. Edited fields, additional narrative and self-rehashed substitutions fail. Valid partial evidence retains unknowns and withholds only dependent measures/conclusions. Read [handoffs](references/handoffs.md) before transferring evidence.

## Professional ownership

The Transaction Monitoring Effectiveness Review Lead and Independent Testing Owner accept the label method, population comparability and testing mandate. Model validation, statistical assurance, legal applicability and production acceptance remain with their professional owners. No scheduler, engine connector, matching algorithm, data extractor, alert closure, rule deployment, SAR conversion or filing is implemented. `human_review_required=true`, `action_taken=false`, `approval=not_requested` and `execution=not_performed` remain distinct.

The retained `transaction-monitoring-scenario-evaluator` keeps its five-rule replay method; its PASS/WARN/BREACH output is not this effectiveness review or an accepted reference label. Preserve it and require an explicit reviewed conversion if ever justified. The [foundation contract](references/foundation-contract.md), [evidence contract](references/evidence-contract.md) and [source governance](references/source-governance.md) govern source/audience/context limits. Synthetic checks establish bounded software behavior; source truth and professional acceptance remain unverified.
