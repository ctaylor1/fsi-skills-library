# Adjacent-Skill Handoffs — employee-trading-preclearance-assistant

This skill owns the **plan → validate → approve → execute → verify → audit** lifecycle for an
employee personal-trade **preclearance decision**. It does not investigate market abuse, it
does not adjudicate conflicts, and it does not act on firm/fund portfolio orders.

## Upstream (hands a preclearance request here)

| Upstream source | Handoff artifact |
| --------------- | ---------------- |
| Employee / control-room intake submitting a personal-account dealing request | `request_id`, employee/account, instrument, side, quantity, notional, request date |
| `conflicts-of-interest-reviewer` confirming an actual/potential conflict for the issuer | Conflict finding fed in as the `conflicts_mnpi` screen result |

## Downstream / lateral (route instead of acting)

| Skill | When |
| ----- | ---- |
| `market-surveillance-alert-investigator` | The pattern suggests possible market abuse (trading on MNPI, front-running) — a surveillance investigation, not a preclearance decision |
| `surveillance-alert-triager` | A surveillance alert needs first-line triage and packaging before investigation |
| `conflicts-of-interest-reviewer` | The core question is whether a conflict exists and how to document/mitigate it, not whether to clear a trade |
| `sanctions-match-adjudicator` | The issuer/counterparty raises a potential sanctions match to disposition |
| `transaction-monitoring-alert-investigator` | The matter is an AML transaction-monitoring alert, not an employee personal-trade preclearance |
| `mandate-compliance-monitor` | The request is a firm/fund portfolio trade tested against mandate/guideline rules, not an employee personal account |
| Chief Compliance Officer / human policy-exception process | Notional over the senior authority limit, a hardship/override request, or any decision outside the deterministic preclearance ruleset |

## Duplicate-execution prevention

- Only this skill records the preclearance decision and issues the clearance; upstream/lateral
  skills must not also write the register.
- Execution is keyed by `plan_id` + step idempotency keys — re-invocation never double-applies
  a decision or issues a second clearance window.
- If another workflow already decided the request, the `record_decision` precondition ("no
  prior open decision") fails and this skill halts rather than overwriting.
