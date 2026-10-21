---
name: fund-investor-operations-reviewer
description: "Review supplied subscription/redemption cutoff and AML-evidence status and calculate indicative units or cash only for timely evidenced orders. Use for fund dealing workpapers; no investor acceptance, AML clearance, units issuance or cash transfer."
license: MIT
compatibility: "Python3.10+ standard library; offline supplied JSON only. Live enterprise sources, licensed data, approved system-of-record engines and deployment access are separate prerequisites."
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Reconcile & validate"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Phase 2 - AM foundations"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential investment context; internal review"
  aws-fsi-jurisdictions: "Supplied vehicle/jurisdiction context; no automatic legal applicability pack"
  aws-fsi-owner: "Asset Management performance and fund operations"
  aws-fsi-primary-user: "Transfer-agent oversight / investor operations"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-21"
---

# Fund investor dealing review

Review supplied subscription/redemption cutoff and AML-evidence status and calculate indicative units or cash only for timely evidenced orders. Use for fund dealing workpapers; no investor acceptance, AML clearance, units issuance or cash transfer.

## Supported methods

- `dealing_review`: Compare timezone-aware order receipt to supplied cutoff. Require current supplied-cleared AML evidence and NAV at the exact supplied valuation timestamp before indicative pricing. Subscription units=(cash-fee)/NAV; redemption net cash=units times NAV-fee. Late/unresolved orders remain unpriced.

## Workflow

1. Triage the actual job, object, measurement period, currency, vehicle and accountable practitioner. Read [schema](references/schema.md) before collecting data. This package is development software awaiting institutional acceptance.
2. For investigation, reconcile the supplied source records and version/economic/known-at dates using [source map](references/source-map.md). Preserve unknowns and upstream issues. Do not construct missing facts to make an input validate.
3. Apply [domain rules](references/domain-rules.md). Run `python3 -B scripts/validate_input.py INPUT.json`, then `python3 -B scripts/calculate_or_transform.py INPUT.json`. The native scripts consume supplied JSON; they do not connect to enterprise systems.
4. Validate with `python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json`. Retain the detached original in approved storage. Validation binds the full input and configuration; it does not authenticate evidence, approve methodology or grant action authority.
5. Review calculations, unavailable measures and exceptions with the responsible professional under [controls](references/controls.md). Use the separate [output template](assets/output-template.md) for narrative; do not add it to native JSON. Route unresolved specialist jobs using [handoffs](references/handoffs.md), retaining the source-bound result and original-input reference.
6. Re-run after any source/rule/version/cutoff change. Return to triage if the request exceeds the documented method. A successful calculation is a workpaper, not completion of the downstream workflow.

## Boundaries and validation

Fund terms, domicile, applicable law, receipt chain, share class, AML/KYC and approved NAV must be established by accountable operators. Supplied-cleared is evidence text, not this skill issuing AML clearance. No gates, swing pricing, dilution or acceptance engine.

The [eval manifest](evals/evals.json) includes executable native goldens/negative cases and declarative trigger, routing, source and authority evaluations. Independent domain regressions supplement reconstruction checks. Natural-language evaluation, actual source authentication, domain SME/control review, accessibility, legal/model review where applicable and deployment acceptance remain separate gates. No posting, trading, payment, investor acceptance, external delivery or system-of-record change occurs.
