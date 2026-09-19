---
name: instant-payment-risk-monitor
description: >-
  Evaluate supplied instant-payment event snapshots against configured fraud velocity, transaction-limit and aggregate pass-through indicators. This is scheduled offline alert analysis, not inline payment prevention. Partition by entity/account/currency/rail, enforce event windows and surface stale feeds and unresolved financial-crime or liquidity work. No decisions or payment/account actions.
license: MIT
compatibility: Python 3 standard library; offline JSON input/output. Production source integrations, scheduling, case persistence and external actions are not implemented.
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "System-interaction or operational skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Monitor & alert"
  aws-fsi-agent-pattern: "Scheduled monitor + human queue"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Scheduled read-only; alert only"
  aws-fsi-scheduled-agent: "read-only-monitoring"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Payments risk / fraud operations"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Instant Payment Risk Monitor

## Purpose and outcome
Produce human-review alerts from supplied instant-payment snapshots. The package does not schedule itself, consume live feeds, prevent a payment inline, perform sanctions matching or evaluate settlement liquidity. Pending snapshots describe possible threshold crossings only; they are not a guarantee that an intervention remains possible.

## Inputs and prerequisites
Explicit offset-aware `as_of`, `window_minutes`, `max_staleness_minutes`, versioned rules and accounts. Each account declares legal entity, account ID, currency, scheme, feed timestamp and source reference; each payment carries ID, currency, scheme, status, direction, amount and timestamp. Known legacy financial-crime/liquidity rules and funding positions can be supplied only to surface unresolved handoffs. Screening outputs are cited upstream references, not locally adjudicated matches.

## Workflow
1. Validate finite amounts, explicit currency/rail/entity/account scope, duplicate IDs and offset-aware timestamps. Unknown payment status is an error, never settled by default.
2. Evaluate events in `(as_of - window_minutes, as_of]`; list excluded older/future events. Keep account/entity/currency/rail partitions separate.
3. Evaluate configured velocity, transaction-limit and descriptive aggregate pass-through indicators. Apply an optional rule `schemes` scope.
4. Record feed staleness/future feed dates; mark affected alerts and emit freshness alerts.
5. Return legacy structuring, sanctions-watchlist and liquidity controls as `not-evaluated` unresolved work. Do not turn an EFT amount near a sample threshold into a legal reporting obligation.
6. Deduplicate against supplied open-alert fingerprints and package severity queues. The application must arrange actual scheduling and retrieval.
7. Send evidence to human risk review; no block, hold, release, return, reversal, filing or closure occurs.

## Output contract
Offline snapshot execution mode, enforced window, input hash, excluded events, partitioned alerts, feed freshness, new/still-open fingerprints, severity counts and unresolved handoffs. Alert fingerprints include entity/account/currency/rail. Monetary measurements use Decimal calculations and serialize as decimal strings where applicable.

## Adjacent-skill handoffs
Fraud/scam investigation → `payment-fraud-and-scam-investigator`; financial-crime evidence → AML or `sanctions-match-adjudicator` workflows as appropriate. Payment settlement liquidity requires specialist operations review; a dedicated capability is not implemented in this phase. Enterprise ALM stress analysis does not substitute for intraday rail funding. Legacy settlement positions remain visible as unresolved work.
Read [handoffs](references/handoffs.md) before transferring evidence.

## Source hierarchy and rules
Read [source-map](references/source-map.md) for authority and access boundaries, [domain-rules](references/domain-rules.md) for calculations and status meaning, and the [payments contract](references/payment-contract.md) for evidence, time, money and handoff semantics.

## Human approval and controls
This package prepares analysis or drafts only. It grants no execution authority. Human review requirements concern downstream regulated decisions or external actions, not running these offline checks. Use [controls](references/controls.md) for limits; protect customer and cardholder data, use masked identifiers, and retain source/version context with the review record.

## Validation and failure handling
Run `python3 -B scripts/validate_input.py INPUT.json`, then `python3 -B scripts/calculate_or_transform.py INPUT.json`, then `python3 -B scripts/validate_output.py OUTPUT.json`. Run `python3 -B scripts/test_regressions.py` for changed behaviors. Structural errors stop the CLI. Missing substantive evidence or rule applicability stays explicitly unresolved; do not repair it by inventing inputs. The fixtures are synthetic. Passing software checks does not establish professional acceptance or deployed-agent quality.
