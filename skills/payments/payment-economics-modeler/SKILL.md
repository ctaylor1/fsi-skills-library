---
name: payment-economics-modeler
description: Model supplied merchant, issuer, acquirer, PSP or bank payment economics using explicit attempt volumes, completion rates, adoption and displacement, disjoint pricing and costs. Produce scenario unit economics, sensitivities and break-even; use the separate cost analyzer for incurred merchant fees.
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
  aws-fsi-primary-user: "Payments finance / product strategy"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Payment scenario economics

## Work product and workflow

Choose one participant perspective and one reporting currency/period. Separate attempted orders/payments from successful outcomes and value; do not use authorization as proof of settlement or retry count as new demand. Register explicit assumptions for completion, basket value, pricing, losses, funding, FX, operations and customer incentives or rewards. Each fee component must identify disjoint economic coverage so bundled and unbundled charges cannot be counted twice.

Build the baseline method mix, then allocate a supplied adoption fraction of the SAME attempt population to one new method. Specify which existing methods lose those attempts; displacement shares sum to one and cannot exhaust more than the available baseline population. No growth, cannibalization benefit, FX conversion or retry effect is invented. Expected successes may be fractional model quantities.

Calculate participant-specific revenue and cost components by attempt, success, successful value or full model period. Merchant merchandise margin captures economic consequences of changed completion; it is a supplied contribution rate, not gross transaction value treated as profit. For issuers, interchange is revenue; for acquirers it is cost. Other participant profiles have different required categories. Missing cost or rate stays unknown; an inapplicable item needs an explicit zero with documented rationale.

Compare modeled contribution, cost per attempt and cost per success; retain method-level calculations and sources. Test feasible adoption levels and report the crossing point only within available displacement. Baseline contracts and their fixed costs remain incurred; adding the new method adds its fixed costs even at zero adoption. This makes the bounded model linear in adoption. Contract termination, tiered pricing, credit-balance interest, tax, discounting, refund cohorts, multi-currency conversion and nonlinear volume responses need an extended reviewed model and must not be squeezed into unsupported assumptions.

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
