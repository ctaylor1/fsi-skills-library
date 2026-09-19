---
name: payment-provider-evaluator
description: Compare supplied acquirer, gateway, PSP, issuer-processor and infrastructure evidence against explicit weighted requirements and mandatory gates. Produce traceable diligence and comparable-rate groups; unknown or proposed capabilities cannot establish support and scores do not select a provider.
license: MIT
compatibility: Python 3.10+ offline JSON decision support. No external connectors or write actions bundled.
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Payments Phase 2"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Confidential commercial and operating evidence; no payment credentials required"
  aws-fsi-jurisdictions: "US; EA; UK; other jurisdictions explicitly unsupported"
  aws-fsi-owner: "Payments product and finance"
  aws-fsi-primary-user: "Payments procurement / product owner"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Payment provider evaluation

## Work product and workflow

Start with the decision owner's operating requirements, mandatory gates and explicit weights. Include participant role, entity/country/method/currency eligibility, lifecycle capability, settlement/reconciliation, refund/dispute support, service continuity, data/security, exit/portability and commercial inclusions where relevant. Missing criteria are discovery work, not evidence a provider passes. Preserve requirements as supplied and call out gaps; do not silently invent weights.

Map each provider assertion to one requirement. Keep supported, unsupported and unknown distinct. An inspected evidence classification requires a registered source; a sales proposal, assumption, missing row or absent source remains unknown for scoring. Supplied inspected status is not an independent certification. In the narrative distinguish tested behavior, contract commitment and stated product scope.

A mandatory unsupported/unknown requirement excludes a provider from the evidence shortlist regardless of score. Compute a point score only if weighted evidence is complete; otherwise show the supported-weight lower bound and unknown-weight interval. Preserve input order, report no automatic ranking and select no provider. Ask a concrete diligence question for every unresolved requirement.

Group price evidence only by identical currency, pricing unit and stated scope. Per-attempt is not per-success; monthly fixed is not transaction variable; one-time charges are not recurring. Even identical groups are individual quoted rates, not total economics. Route minimums, tiers, bundled charge inclusions, FX and volume assumptions to economics after normalization. Selection, due diligence acceptance and contracting remain human decisions.

## Portable input and native tools

Use [references/input-schema.md](references/input-schema.md) before shaping JSON. Register evidence and assumptions with source IDs, dates and review due dates. Preserve request identity and every unresolved upstream issue. The common envelope accepts US, EA (euro area) and UK; another jurisdiction returns unsupported. This is a bounded analytical regional scope, not a country-level legal clearance. Never relabel another country's artifacts to obtain a supported result.

Run from this package directory:

```sh
python scripts/validate_input.py evals/files/request.json
python scripts/calculate_or_transform.py evals/files/request.json > /tmp/payment-analysis.json
python scripts/validate_output.py /tmp/payment-analysis.json --input evals/files/request.json
python scripts/regression_tests.py
```

Review [references/domain-rules.md](references/domain-rules.md) for decision and calculation boundaries, [references/source-map.md](references/source-map.md) for evidence selection, [references/controls.md](references/controls.md) for authority and stale-source behavior, and [references/handoffs.md](references/handoffs.md) for adjacent work. Render the inspectable result using [assets/output-template.md](assets/output-template.md). The JSON result retains the exact supplied request and recomputes during output validation; the hash proves internal lineage consistency, not authenticity.

The helper implements offline deterministic transformations of supplied structured evidence. It does not retrieve sources, inspect provider systems, authenticate attestations, or send the draft. Keep unknowns visible in the narrative even where partial arithmetic is available. Natural-language evaluation specifications are separate from executable regressions in [evals/evals.json](evals/evals.json).
