---
name: employee-trading-preclearance-reviewer
description: >-
  Prepare an offline employee personal-trade review plan from a versioned institution policy, account-specific timestamped screening evidence and supplied trading calendar. Suggest a disposition for compliance review; does not grant clearance, authenticate approval, execute steps or notify employees.
license: MIT
compatibility: Offline Python 3.10+ standard-library helpers and supplied evidence; no live connector or operational adapter is bundled.
metadata:
  aws-fsi-category: "Compliance & Financial Crime"
  aws-fsi-skill-type: "Workflow or orchestration skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Plan-validate-execute workflow agent"
  aws-fsi-delivery-wave: "Wave 4 - gated orchestration"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Restricted employee trading and MNPI-related review evidence"
  aws-fsi-jurisdictions: "Supplied institution/jurisdiction profile; no default legal applicability or bundled current-law pack"
  aws-fsi-owner: "Employee Trading Compliance / Control Room"
  aws-fsi-primary-user: "Employee-compliance / control-room analyst"
  aws-fsi-version: "0.1.1"
  aws-fsi-recertification-date: "2027-07-17"
---

# Employee Trading Preclearance Reviewer

Use for review of a proposed personal trade. The package is plan-only and has no execution adapter. An approval token or a user claim of approval does not change that capability. Compliance owners must make decisions in their separately governed operational systems.

Read [domain rules](references/domain-rules.md) for the bounded method and schema,
[source map](references/source-map.md) for evidence requirements, and
[controls](references/controls.md) before preparing a result.

## Workflow

- Require employee/account/trade identity, policy version and source, explicit institutional limits/roles/holding period, and all five mandatory screen results. There are no universal monetary or 30-day holding defaults.
- Screen records must identify the same account and include source, snapshot ID and an offset-aware timestamp. Future or stale records fail validation under the supplied policy age limit. Human reviewers must refresh restrictions and eligibility again before any operational decision.
- A supplied hard-block result produces a deny recommendation. Watch-list or higher notional routes to senior review; above the supplied senior limit produces escalation. No recommendation is a clearance.
- A proposed window ends at the next session in a supplied versioned calendar with timezone and declared complete coverage. No calendar-day increment is described as a trading day. Source/calendar truth still requires review.
- The complete original input affects `input_hash` and `plan_hash`, including account, policy, all screen snapshots, timestamps and calendar. Any change requires a new review plan; supplied approval fields cannot authorize execution.
- Output is `status=review-plan`, `action_mode=plan-only`, pending human review and `execution.state=unsupported`. No executable steps, notification, register write or rollback guarantee is generated.

## Input, output and verification

Request/employee/account/instrument, side, finite positive quantity/notional, request date and offset-aware time, explicit institution policy, account-specific screening snapshots, and supplied calendar sessions/coverage/timezone. `price` if supplied is retained in the source hash; notional currency is explicitly USD.

The script returns an immutable native draft with `input_hash` and `source_truth=unverified`.
Retain the original input separately; raw source embedding and added narrative fields are
rejected. Hashing proves repeatability against supplied input, not authenticity or approval.
Human narrative, legal reasoning and any workflow envelope stay separate and need their own
source, audience and professional review.

```sh
python -B scripts/validate_input.py INPUT.json
python -B scripts/calculate_or_transform.py INPUT.json
python -B scripts/validate_output.py OUTPUT.json --input INPUT.json
python -B scripts/test_phase1.py
```

Do not present a native result until detached-input reconstruction passes. Invalid structural
inputs stop calculation; substantive unknowns stay visible. Software tests and synthetic
fixtures establish bounded behavior only, not legal correctness or production acceptance.

## Boundaries and handoffs

`conflicts-of-interest-reviewer` owns conflict analysis. `market-surveillance-alert-investigator` owns suspected market abuse evidence. `investment-mandate-reviewer` owns firm/fund portfolio orders. Holding summaries, investment advice, account-opening consent and ongoing employee-reporting controls are separate jobs.

No live preclearance integration, authenticated approval broker, system-of-record write, clearance issuance, notification, idempotent execution or rollback is implemented. Operational execution remains out of scope even with a supplied token. This does not place or execute trades.

Read [handoffs](references/handoffs.md) before transferring evidence. Apply source-specific
confidentiality, minimization and audience controls; SAR restrictions attach only when the
actual source/use warrants them, not to every generic compliance artifact.

Shared [evidence contract](references/evidence-contract.md) and [source governance](references/source-governance.md) define cross-workflow provenance and authority boundaries.
