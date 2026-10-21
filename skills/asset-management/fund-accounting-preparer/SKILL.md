---
name: fund-accounting-preparer
description: "Prepare balanced journal/trial-balance movements, supplied ACT/365 accruals and class NAV workpapers against an identified system-of-record benchmark. Use for draft fund-accounting review; never post, strike or release authoritative NAV."
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
  aws-fsi-primary-user: "Fund accountant"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-21"
---

# Fund accounting workpapers

Prepare balanced journal/trial-balance movements, supplied ACT/365 accruals and class NAV workpapers against an identified system-of-record benchmark. Use for draft fund-accounting review; never post, strike or release authoritative NAV.

## Supported methods

- `journal_trial_balance`: Require balanced opening signed-debit trial balance and each balanced journal, then roll movements into account closing balances. Credits are negative balances; each journal line has exactly one positive debit or credit.
- `accrual`: Straight-line ACT/365 expense accrual = principal times annual decimal rate times actual days excluding start /365. No compounding, amortization or day-count selection.
- `nav_workpaper`: Common net assets = supplied assets minus common liabilities. Allocate by supplied weights summing exactly1, then subtract separate class expenses. Reconcile summed class NAV against a supplied external accounting-engine result; calculate indicative NAV/share.

## Workflow

1. Triage the actual job, object, measurement period, currency, vehicle and accountable practitioner. Read [schema](references/schema.md) before collecting data. This package is development software awaiting institutional acceptance.
2. For investigation, reconcile the supplied source records and version/economic/known-at dates using [source map](references/source-map.md). Preserve unknowns and upstream issues. Do not construct missing facts to make an input validate.
3. Apply [domain rules](references/domain-rules.md). Run `python3 -B scripts/validate_input.py INPUT.json`, then `python3 -B scripts/calculate_or_transform.py INPUT.json`. The native scripts consume supplied JSON; they do not connect to enterprise systems.
4. Validate with `python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json`. Retain the detached original in approved storage. Validation binds the full input and configuration; it does not authenticate evidence, approve methodology or grant action authority.
5. Review calculations, unavailable measures and exceptions with the responsible professional under [controls](references/controls.md). Use the separate [output template](assets/output-template.md) for narrative; do not add it to native JSON. Route unresolved specialist jobs using [handoffs](references/handoffs.md), retaining the source-bound result and original-input reference.
6. Re-run after any source/rule/version/cutoff change. Return to triage if the request exceeds the documented method. A successful calculation is a workpaper, not completion of the downstream workflow.

For NAV parallel review, read [engine contract](references/engine-contract.md) and retain
the actual system-of-record run, method/version contract and acceptance evidence. Source
references alone do not authenticate institution approval.

## Boundaries and validation

A supplied external benchmark is mandatory for NAV mode and remains unverified source evidence. No journal-to-valuation or class-flow equalization engine, FX, fair-value policy, tax or authoritative strike/post.

The [eval manifest](evals/evals.json) includes executable native goldens/negative cases and declarative trigger, routing, source and authority evaluations. Independent domain regressions supplement reconstruction checks. Natural-language evaluation, actual source authentication, domain SME/control review, accessibility, legal/model review where applicable and deployment acceptance remain separate gates. No posting, trading, payment, investor acceptance, external delivery or system-of-record change occurs.
