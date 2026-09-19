---
name: payment-acceptance-performance-analyzer
description: Analyze population-level payment conversion, authorization, retries and chargeback trends with unique order and attempt denominators, matched currency/channel/method cohorts and mature outcomes. Review routing experiment assignments and supplied guardrails; use payment diagnosis for a single transaction.
license: MIT
compatibility: Python 3.10+ offline JSON analysis. No connectors, live decisions or write actions bundled.
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Payments Phase 3"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Confidential pseudonymous payment and control evidence; no credentials"
  aws-fsi-jurisdictions: "US; EA; UK; other jurisdictions explicitly unsupported"
  aws-fsi-owner: "Payments analytics and merchant acceptance"
  aws-fsi-primary-user: "Acceptance analytics / payments product"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Payment acceptance performance

Start from the population extraction, not just successful processor rows. Reconcile unique orders/instructions to unique attempts with stable IDs; retain orders with no attempt. Register dates, channel, currency, payment method and customer segment. An order can retry, but a retry is not a new customer conversion. Normalize authoritative outcomes before running; conflicting IDs/outcomes fail validation. This bounded helper accepts one method cohort per order; mixed-method attempts require a reviewed attribution model instead of being silently assigned to the last method.

Compare baseline and current periods only within the same currency/channel/method/segment. Show attempt authorization and unique-order completion separately, with unknown/pending outcome bounds. Approval is not completion, settlement, funding or revenue. Report both denominator sizes and unmatched cohorts; time trends, issuer/provider mix and retry policies can explain observed differences. A period delta is a fraction, not relative uplift or causal attribution.

For chargebacks, use completed orders whose supplied maturity due date has passed AND a known chargeback outcome. A no-chargeback observation must extend through maturity. Pending, unknown and still-maturing cohorts remain excluded, not labeled clean. This is an analytical policy supplied by the owner, not a universal network deadline. Retain gross payment/chargeback face value separately from disjoint recorded processing costs, net fraud loss and chargeback fees; gross value is not margin or loss. Economic coverage keys prevent counted-twice costs. Missing cost coverage limits any all-in statement.

For routing experiments, preserve supplied order-level assignments through retries and provider fallback; summarize by assignment (intention to treat), identify missing assignments and contamination, and evaluate only the owner's supplied guardrails. Keep currencies and customer cohorts separate. The helper does not prove randomization, sample balance, power, statistical significance or causal uplift. Write supported hypotheses and a proposed controlled experiment with owner, primary metric, guardrails, exposure cap, observation horizon and stop/review criteria. Never deploy a routing or retry change.

## Native artifacts and validation

Read [references/input-schema.md](references/input-schema.md) before normalizing data and [references/domain-rules.md](references/domain-rules.md) for calculation limits. Use [references/source-map.md](references/source-map.md) for lineage/freshness and [references/controls.md](references/controls.md) for action boundaries. Preserve durable request identity and unresolved issues in [references/handoffs.md](references/handoffs.md); a transport envelope is not native target readiness.

```sh
python scripts/validate_input.py evals/files/request.json
python scripts/calculate_or_transform.py evals/files/request.json > /tmp/payment-analysis.json
python scripts/validate_output.py /tmp/payment-analysis.json --input evals/files/request.json
python scripts/regression_tests.py
```

Use [assets/output-template.md](assets/output-template.md) to render the result with source evidence and limitations. The regional scope is a bounded analytical interface, not a legal permission or local rulebook. Read [references/payment-contract.md](references/payment-contract.md) for lifecycle and handoff semantics. Unknowns and source conflicts remain open for human review.
