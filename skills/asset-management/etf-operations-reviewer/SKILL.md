---
name: etf-operations-reviewer
description: "Legacy basket arithmetic; explicit multicurrency clean/accrued bond values, one-to-one custom substitutions and source-bound derivative engine result challenge; no basket publication/settlement. Draft-only; use explicit extension and detached source validation."
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
  aws-fsi-primary-user: "ETF operations / capital-markets control team"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-09-21"
---

# ETF basket and secondary-market control review

Reconcile supplied ETF creation/redemption baskets, cash, units, fees and AP/cutoff evidence; calculate same-date premium/discount and quoted spread. Use for ETF operational workpapers; no basket acceptance, order routing or settlement.

## Supported methods

- `basket_control`: Value each supplied constituent per creation unit, add cash balance and compare with creation-unit shares times NAV/share. Scale quantities by integral units. AP cash includes fees paid on creation and deducted on redemption; fees are outside NAV basket tie-out.
- `secondary_market`: For same-date positive NAV and quote values, calculate market-price premium/discount to NAV and quoted bid/ask spread divided by midpoint.

## Workflow

1. Triage the actual job, object, measurement period, currency, vehicle and accountable practitioner. Read [schema](references/schema.md) before collecting data. This package is development software awaiting institutional acceptance.
2. For investigation, reconcile the supplied source records and version/economic/known-at dates using [source map](references/source-map.md). Preserve unknowns and upstream issues. Do not construct missing facts to make an input validate.
3. Apply [domain rules](references/domain-rules.md). Run `python3 -B scripts/validate_input.py INPUT.json`, then `python3 -B scripts/calculate_or_transform.py INPUT.json`. The native scripts consume supplied JSON; they do not connect to enterprise systems.
4. Validate with `python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json`. Retain the detached original in approved storage. Validation binds the full input and configuration; it does not authenticate evidence, approve methodology or grant action authority.
5. Review calculations, unavailable measures and exceptions with the responsible professional under [controls](references/controls.md). Use the separate [output template](assets/output-template.md) for narrative; do not add it to native JSON. Route unresolved specialist jobs using [handoffs](references/handoffs.md), retaining the source-bound result and original-input reference.
6. Re-run after any source/rule/version/cutoff change. Return to triage if the request exceeds the documented method. A successful calculation is a workpaper, not completion of the downstream workflow.

## Boundaries and validation

Any missing constituent price or NAV makes aggregate tie-out unavailable. Supplied AP/custom approval labels are not authenticated. Signed cash balances are allowed. In the legacy no-extension methods, derivatives, FX and calendar controls are unsupported; select the explicit specialized-basket extension for supplied-engine derivative values, FX conversion and reviewed calendar evidence. Signed constituent quantities and actual creation/redemption execution remain unsupported.

The [eval manifest](evals/evals.json) includes executable native goldens/negative cases and declarative trigger, routing, source and authority evaluations. Independent domain regressions supplement reconstruction checks. Natural-language evaluation, actual source authentication, domain SME/control review, accessibility, legal/model review where applicable and deployment acceptance remain separate gates. No posting, trading, payment, investor acceptance, external delivery or system-of-record change occurs.

## Phase 4 specialist extension

Select `extension: specialized-basket` explicitly for the bounded specialist method. Read [the Phase 4 contract](references/phase4-method.md), then use the existing input/calculation/output commands with a detached original input. The earlier schema remains available when `extension` is omitted. Unknown extensions fail. Use [the specialist review template](assets/phase4-template.md) and retain every residual, source gap and unsupported method. Source-linked calculations do not establish professional acceptance or execution authority.
