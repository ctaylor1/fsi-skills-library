---
name: merchant-acceptance-strategy-designer
description: Design evidence-gated merchant acceptance and acquiring options across supplied markets, channels, customer groups and use cases. Use for local-method coverage, partner responsibilities, acquiring footprint and orchestration objectives; execution, provider selection and conversion claims remain outside this draft.
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
  aws-fsi-primary-user: "Merchant payments / commercial strategy"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Merchant acceptance strategy

## Work product and workflow

Translate the merchant brief into explicit market × channel × customer/use-case segments, required methods, presentment currency, merchant contracting entity and settlement needs. Distinguish a gateway's message role, the acquirer's merchant/network responsibilities and any PSP's contracted services. A provider may perform multiple roles, but record each responsibility rather than inferring it from the name.

Construct plausible options from supplied evidence and label proposed scope. Inspect each option's segment/method evidence, entity eligibility, presentment and settlement currencies, recurring support and mandatory constraints. State country-specific legal, scheme, data-localization, FX and contracting questions for accountable review; a US/EA/UK label does not answer them. Capture checkout, authentication, screening, settlement, reconciliation, refund and dispute owners.

Deliver the evaluated options, coverage gaps, gating questions, partner responsibilities and staged implementation plan. For orchestration, name the objective and outcome denominator, duplicate-payment/retry guardrails, fallback policy and experiment design; this package does not implement routing or estimate uplift. Preserve customer choice, consent and payment-status checks in the design. Escalate a payment already in flight to lifecycle diagnosis instead of proposing another attempt.

No generic claim that a local method improves conversion is sufficient. Reach, conversion and performance gains remain unknown until scope-specific evidence or a measured pilot supports them. A fully evidenced option is ready for human option review, not approved to launch.

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
