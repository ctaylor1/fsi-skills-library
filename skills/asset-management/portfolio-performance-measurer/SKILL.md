---
name: portfolio-performance-measurer
description: "Calculate supplied-value chain-linked TWR, dated Modified Dietz and conventional cash-flow XIRR with explicit fee basis and source-bound controls. Use for portfolio return workpapers; no valuation engine, attribution or GIPS certification."
license: MIT
compatibility: "Python3.10+ standard library; offline supplied JSON only. Live enterprise sources, licensed data, approved system-of-record engines and deployment access are separate prerequisites."
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Reconcile & validate"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Phase 2 - AM foundations"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Confidential investment context; internal review"
  aws-fsi-jurisdictions: "Supplied vehicle/jurisdiction context; no automatic legal applicability pack"
  aws-fsi-owner: "Asset Management performance and fund operations"
  aws-fsi-primary-user: "Performance analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-21"
---

# Portfolio performance measurement

Calculate supplied-value chain-linked TWR, dated Modified Dietz and conventional cash-flow XIRR with explicit fee basis and source-bound controls. Use for portfolio return workpapers; no valuation engine, attribution or GIPS certification.

## Supported methods

- `twr`: Chain geometrically contiguous subperiod returns from valuations at every external-flow boundary. Opening-after-flow values must equal the previous closing-before-flow plus boundary flow. The final post-period flow is zero.
- `modified_dietz`: Compute (ending minus beginning minus net flows) divided by beginning plus day-weighted end-of-day flows. Nonpositive denominator is unavailable; this is a money-weighted period estimate, not exact TWR.
- `money_weighted`: Annual ACT/365 investor-sign XIRR including terminal value. Net same-day flows, require one negative-to-positive sign transition, then bisect over [-0.999999,1000000]. Nonconventional signs, out-of-domain roots or nonconvergence are unavailable.

## Workflow

1. Triage the actual job, object, measurement period, currency, vehicle and accountable practitioner. Read [schema](references/schema.md) before collecting data. This package is development software awaiting institutional acceptance.
2. For investigation, reconcile the supplied source records and version/economic/known-at dates using [source map](references/source-map.md). Preserve unknowns and upstream issues. Do not construct missing facts to make an input validate.
3. Apply [domain rules](references/domain-rules.md). Run `python3 -B scripts/validate_input.py INPUT.json`, then `python3 -B scripts/calculate_or_transform.py INPUT.json`. The native scripts consume supplied JSON; they do not connect to enterprise systems.
4. Validate with `python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json`. Retain the detached original in approved storage. Validation binds the full input and configuration; it does not authenticate evidence, approve methodology or grant action authority.
5. Review calculations, unavailable measures and exceptions with the responsible professional under [controls](references/controls.md). Use the separate [output template](assets/output-template.md) for narrative; do not add it to native JSON. Route unresolved specialist jobs using [handoffs](references/handoffs.md), retaining the source-bound result and original-input reference.
6. Re-run after any source/rule/version/cutoff change. Return to triage if the request exceeds the documented method. A successful calculation is a workpaper, not completion of the downstream workflow.

## Boundaries and validation

Source valuations, external-flow completeness and fee basis need performance-owner review. No benchmark attribution, valuation, composite construction or performance advertising approval.

The [eval manifest](evals/evals.json) includes executable native goldens/negative cases and declarative trigger, routing, source and authority evaluations. Independent domain regressions supplement reconstruction checks. Natural-language evaluation, actual source authentication, domain SME/control review, accessibility, legal/model review where applicable and deployment acceptance remain separate gates. No posting, trading, payment, investor acceptance, external delivery or system-of-record change occurs.
