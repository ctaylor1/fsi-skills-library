---
name: payment-fraud-control-evaluator
description: Design payment journey and threat control options, and replay baseline/proposed multi-rule portfolios over supplied transactions with mature-label, value, friction and rule-interaction analysis. Preserve the separate legacy single-predicate comparison. Draft decision support only; never deploy controls or decide a live payment.
license: MIT
compatibility: Python 3.10+ offline JSON analysis. No connectors, live decisions or write actions bundled.
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Payments Phase 3"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential pseudonymous payment and control evidence; no credentials"
  aws-fsi-jurisdictions: "US; EA; UK; other jurisdictions explicitly unsupported"
  aws-fsi-owner: "Payments fraud strategy and risk"
  aws-fsi-primary-user: "Fraud-strategy analyst / control owner"
  aws-fsi-version: "0.3.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Payment fraud controls

For strategy, map actual participant journeys, intent and payee changes, authentication/authorization, execution and post-payment recovery to explicit threat scenarios. Specify preventive, detective and responsive control options, their signal, owner, escalation/response, failure mode and evidence metric. Missing control categories surface as review gaps; a category checklist does not establish effectiveness. A reviewed compensating-control or risk-acceptance rationale belongs in the human strategy, never an automatic clearance. Authentication does not establish genuine customer intent; APP deception, account takeover, mule activity and operational abuse can require different controls and owners.

For portfolio evaluation, bind baseline/proposed rule IDs to versions and source evidence. Use only approved read-only extracted features available by the transaction decision date; later-observed features quarantine replay to prevent hindsight leakage. The deterministic module supports one numeric predicate per rule and block/review actions, with block taking precedence over review. If any selected predicate cannot be evaluated because its feature is absent, retain unknown for the entire portfolio row. Explicitly document whether this bounded semantics matches the actual engine; do not approximate nested rules, velocity windows, cascading models or stateful features by invented values.

Keep mature fraud/legitimate labels apart from pending/unknown/not-yet-mature outcomes. A legitimate label must have been observed through the supplied maturity date. Report sample and mature-evaluable counts, excluded labels and features, three-way confusion categories, currency-separated observed fraud face value and net recorded loss by replayed action. Fractions describe this sample. Retrospective blocked-fraud face value is not avoided loss: historical controls censor outcomes, labels are delayed, and an alternative control can change customer/adversary behavior.

Show rule trigger counts, exclusive triggers, pairwise overlaps and transaction-level action transitions. Portfolio actions count once despite overlapping rules. Model review and legitimate-block friction using separate sourced unit costs; keep these assumptions separate from observed loss and face value. Apply only supplied review/false-positive appetite limits. Exceeding a limit requires owner review, not automatic refusal or deployment approval.

Conclude with uncertainty, data-selection/label-quality issues, fairness/cohort tests, operational capacity, proposed shadow/challenger experiment, monitored guardrails, observation horizon, rollback and human change approval requirements. No live allow/block/review instruction, deployment, customer communication or rule activation is produced.

## Native artifacts and validation

Read [references/input-schema.md](references/input-schema.md) before normalizing data and [references/domain-rules.md](references/domain-rules.md) for calculation limits. Use [references/source-map.md](references/source-map.md) for lineage/freshness and [references/controls.md](references/controls.md) for action boundaries. Preserve durable request identity and unresolved issues in [references/handoffs.md](references/handoffs.md); a transport envelope is not native target readiness.

```sh
python scripts/validate_input.py evals/files/request.json
python scripts/calculate_or_transform.py evals/files/request.json > /tmp/payment-analysis.json
python scripts/validate_output.py /tmp/payment-analysis.json --input evals/files/request.json
python scripts/regression_tests.py
```

Use [assets/output-template.md](assets/output-template.md) to render the result with source evidence and limitations. The regional scope is a bounded analytical interface, not a legal permission or local rulebook. Read [references/payment-contract.md](references/payment-contract.md) for lifecycle and handoff semantics. Unknowns and source conflicts remain open for human review.

## Legacy predicate comparison

The prior one-current/one-proposed predicate comparison remains an explicitly separate compatibility module. Read [references/legacy-module.md](references/legacy-module.md) only when reproducing an old labeled-sample estimate. It does not gain label-maturity, portfolio, strategy or source-bound controls from the new workflow. Prefer the native portfolio contract for new evaluations.
