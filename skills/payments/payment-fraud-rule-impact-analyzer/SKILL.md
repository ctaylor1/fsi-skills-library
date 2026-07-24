---
name: payment-fraud-rule-impact-analyzer
description: >-
  Estimate the illustrative impact of a proposed fraud-rule change by deterministically
  evaluating the current and proposed rule over a labeled transaction sample — block counts,
  decline-rate delta, and the confusion-matrix shift (caught fraud, missed fraud, false
  positives) — for a fraud-strategy analyst to review. Use when an analyst asks to "estimate the
  impact of this fraud rule", "how many transactions would this rule block", "what's the
  false-positive tradeoff", or "compare the current vs proposed rule on this sample". HARD
  BOUNDARY: R3 model/decision-support only — it produces an illustrative estimate on a sample;
  it NEVER deploys, enables, or rolls out a rule, and NEVER makes a block/allow decision on any
  live transaction or customer; a human owns deployment. Routes production error diagnosis to
  payment-api-log-diagnostic-pack.
license: MIT
compatibility: Amazon Quick Desktop; requires a labeled transaction sample, fraud-rule definitions, and reference-data MCP integrations (all read-only). Deterministic stdlib-only computation.
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Model & calculate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Fraud-strategy analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Payment Fraud Rule Impact Analyzer

## Purpose and outcome
Given a labeled transaction sample and a current + proposed fraud rule, deterministically evaluate
both rules, count blocks, compute the decline-rate delta, and produce the confusion-matrix shift
(caught fraud, missed fraud, false positives). A successful output is an illustrative estimate a
fraud-strategy analyst reviews — deployment and any live block/allow decision remain the human's.

## Use when
- "Estimate the impact of this fraud rule", "how many transactions would this rule block".
- "What's the false-positive tradeoff", "compare current vs proposed rule on this sample".
- An analyst needs a consistent, reproducible impact estimate before proposing a change.

## Do not use
- The user wants you to **deploy, enable, or roll out** a rule → out of scope; a human acts.
- The user wants a **block/allow decision** on a live transaction/customer → out of scope.
- Production error diagnosis → route to `payment-api-log-diagnostic-pack`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Emits an impact estimate with a durable
`analysis_id`; it does not deploy rules.

## Inputs and prerequisites
- The **rule_change** (rule_id, current_rule, proposed_rule as field/op/threshold), and a
  **sample** of transactions (txn_id, the rule field, label ∈ fraud|legit). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- The sample must be representative and its labels trusted; the estimate is only as good as the
  sample. See [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The labeled sample is the evidence; rule
definitions from config. The estimate is scoped to the sample and says so.

## Workflow
1. **Validate input** — run `validate_input`; confirm rules and a labeled sample are present.
2. **Compute (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): evaluate each txn
   against current and proposed rules, count blocks, decline rates, and the confusion matrix for
   both, and the deltas.
3. **Assemble the estimate** — counts, decline-rate delta, confusion-matrix shift, sample size.
4. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py) for
   confusion-matrix tie-outs, the no-deployment/no-decision screen, and disclaimer.

## Validation loop
`validate_input` before, `validate_output` after. If the confusion matrix does not sum to the
sample size, or the text contains deployment/live-decision language, **fix or fail closed**.

## Human approval
`required`: no rule deployment/enablement and no live block/allow decision without an authorized
human. The skill only estimates on a sample.

## Failure handling
- **Unsupported operator/field** → fail closed; do not guess how the rule evaluates.
- **Missing label** → the txn is counted in block metrics but excluded from confusion metrics,
  flagged as unlabeled; never impute a label.
- **Tiny/unrepresentative sample** → report the sample size prominently; do not extrapolate to
  production volumes.
- **Tool timeout** → partial + incomplete flag.

## Output contract
1. **Summary** — rule id, sample size, decline-rate now vs proposed and delta.
2. **Block counts** — blocked now, blocked proposed, newly blocked, newly allowed.
3. **Confusion shift** — caught fraud / missed fraud / false positives for both, with deltas.
4. **Machine-readable** — metrics + `analysis_id`.
5. **Standing disclaimer** — "Illustrative sample impact estimate only; not a rule deployment and
   not a block/allow decision on any live transaction or customer."
See [references/controls.md](references/controls.md).

## Privacy and records
Cardholder data + NPI/PII. Do not echo PAN or raw card data; reference txns by id. Retain the
estimate + sample reference + rule versions. Log read + external-delivery approval.

## Gotchas
- **Sample ≠ production.** Every number is scoped to the provided sample; never present it as a
  production forecast.
- **A better fraud-catch rate usually costs false positives** — always report both sides of the
  tradeoff, never just the favorable one.
- **Labels are assumed correct** — surface unlabeled txns rather than guessing.
- **Never phrase an estimate as a decision to deploy or to block a customer.**
