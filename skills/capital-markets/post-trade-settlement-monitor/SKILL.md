---
name: post-trade-settlement-monitor
description: >-
  Scheduled, read-only monitor for post-trade settlement: read clearing/CSD and OMS status
  for a book of instructions, apply versioned thresholds to detect unmatched-near-cutoff,
  cutoff breaches, settlement fails, fail aging, buy-in exposure, material cash/position
  impact, and CSDR penalty accrual, then deduplicate, stamp data freshness, prioritize by
  severity, and package a human alert queue with drafted escalation routes. Use when
  settlement operations or the middle office needs an intraday or pre-cutoff sweep of fails,
  aging, cutoffs, and cash impacts, or asks "what is failing / aging / at risk of missing
  settlement today". HARD BOUNDARY: this monitor only raises prioritized, deduplicated,
  freshness-stamped alerts to a human queue; it NEVER matches, affirms, cancels, settles,
  releases, initiates or executes a buy-in, disputes a penalty, contacts a
  counterparty/custodian/client, closes or suppresses an exception, decides
  fault/reportability, or writes any book of record.
license: MIT
compatibility: Amazon Quick Desktop; requires post-trade/clearing, OMS/EMS, market/reference-data, settlement-config, and alert-queue MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Capital Markets"
  aws-fsi-skill-type: "System-interaction or operational skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Monitor & alert"
  aws-fsi-agent-pattern: "Scheduled monitor + human queue"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Scheduled read-only; alert only"
  aws-fsi-scheduled-agent: "read-only-monitoring"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Capital Markets operations & compliance"
  aws-fsi-primary-user: "Settlement operations / middle office"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Post-Trade Settlement Monitor

## Purpose and outcome
On a schedule (intraday cadence plus pre-cutoff sweeps), read the settlement status of a book
of instructions, apply the configured, documented threshold rules, and produce a
**prioritized, deduplicated, freshness-stamped alert queue** for settlement operations. Each
alert carries cited evidence, a fixed severity, and a **drafted** escalation route. A
successful output lets a human reviewer see, in priority order, exactly what is failing,
aging, near a cutoff, materially cash-impacting, or accruing penalties — and route it. The
monitor **never acts, decides, closes, or writes**; every disposition and action stays human.

## Use when
- A scheduled run or pre-cutoff sweep needs to surface today's settlement exceptions.
- "What is failing, aging, or at risk of missing the settlement cutoff right now?"
- "Which fails have buy-in exposure or material cash impact?"
- "Sweep the book for CSDR penalty accruals over the materiality threshold."
- Settlement ops wants a consistent, cited, de-duplicated exception queue each cycle.

## Do not use
- The user wants to **act** — match, affirm, cancel, settle, release, initiate/execute a
  buy-in, dispute a penalty, or contact a counterparty/custodian → out of scope; raise the
  alert and route to the entitled human/system.
- **Investigate and repair a matching/economics break** → `trade-break-resolver`.
- **Fund or optimize collateral** against fail/buy-in exposure → `margin-collateral-optimizer`.
- **Fix a regulatory transaction-reporting data-quality issue** →
  `transaction-reporting-quality-checker`.
- **Explain an underlying trade confirmation** (no exception) → `trade-confirmation-explainer`.
- A **corporate-action-driven** entitlement mismatch needing election work →
  `corporate-action-election-assistant`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits an alert queue with a
durable `run_id`; downstream resolution/funding/reporting skills and human operations consume
it. It must not duplicate their investigation, repair, funding, or action steps.

## Inputs and prerequisites
- A **settlement snapshot**: run `as_of` datetime, `config_version`, market, and the
  `instructions[]` under monitor — each with instruction/trade IDs, ISD, direction, quantity,
  cash, status, cutoff time, and `source_ref` + `source_as_of`. Optional `penalty_accrued`.
- `open_alerts[]` (already-open alert dedup keys) for deduplication; optional `config` block.
- Schema and evaluability rules: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to clearing/CSD, OMS/EMS, reference data, and versioned config
  (see [references/source-map.md](references/source-map.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Clearing/CSD status is the position
of record for whether an instruction settled; OMS supplies economics; reference data resolves
securities, cutoffs, and the market calendar; config is a versioned contract. Cite every
alert to a source row and its feed timestamp; on source conflict, cite both and flag it.

## Workflow
1. **Scope & validate** — load the snapshot for the book; validate with `validate_input`
   (fails closed on structural problems; warns where a rule is not evaluable).
2. **Compute alerts (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to apply the
   threshold rules (cutoff, fail, aging bands, buy-in window, cash materiality, penalty
   accrual). Each fired alert returns cited evidence and a fixed severity.
3. **Deduplicate** — mark any alert whose key is already open as `duplicate` (no re-page);
   raise genuinely new escalations (including a fail that ages into a higher band) as `new`.
4. **Stamp freshness** — flag rows older than the staleness window; surface them for re-pull,
   never suppress them.
5. **Prioritize & package** — set each item's severity to the max of its alerts, assign the
   deterministic suggested route, sort the queue, and record `actions_taken: []`.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: escalation packaging (severity + route + cited evidence),
deterministic severity tie-out, correct deduplication, consistent freshness handling, an
empty `actions_taken` with **no action/decision language**, and the standing disclaimer. Fail
closed on any miss.

## Human approval
`external-delivery`: human approval required before any alert leaves the internal
settlement-ops queue (e.g., emailing a counterparty, custodian, or client). Internal queueing
for the ops reviewer is the default and needs no approval. The monitor never takes a
settlement action.

## Failure handling
- **Stale feed** → flag the row stale and require a re-pull; do not raise false confidence and
  do not suppress the alert.
- **Missing cutoff time** → cutoff alerts are "not evaluable"; still compute fail/aging alerts.
- **Missing cash/penalty** → skip only the impacted alert; label it not evaluable.
- **Source conflict** (OMS vs clearing) → cite both; do not resolve silently.
- **Ambiguous instruction/identity** → stop and flag; never alert on the wrong instruction.
- **Tool timeout** → return the alerts computed so far with a clear "incomplete" flag; page
  long books as resumable stages.

## Output contract
1. **Run summary** — market, `as_of`, monitored count, alert count, new vs deduplicated,
   stale count.
2. **Queue** — per item: instruction/trade IDs, severity, is_new, stale, suggested route, and
   each fired alert (type, fixed severity, plain-language reason, cited evidence, dedup state).
3. **Freshness** — `as_of`, staleness window, and `stale_instruction_ids`.
4. **Machine-readable** — the full queue + `run_id` + `deduped_against` + `actions_taken: []`
   for downstream skills.
5. **Standing disclaimer** — "Monitoring alerts only; no settlement action has been taken. A
   human must review, decide, and act."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask account numbers to last 4; minimize data in each alert to what
evidences the exception. Retain the run + citations + `config_version` per records policy; log
the read and any external-delivery approval. Never exfiltrate book or counterparty data.

## Gotchas
- **An alert is not a decision.** High severity justifies *queue priority*, never an at-fault,
  reportability, or buy-in decision, and never a settlement action.
- **T+1 compresses the window.** Under T+1, unmatched-near-cutoff and cutoff-breach alerts are
  time-critical; the schedule must include pre-cutoff sweeps or the alert arrives too late.
- **Business-day aging needs the market calendar.** The bundled fallback counts Mon–Fri only;
  wire the deployment holiday calendar or aging bands will be off around holidays.
- **Deduplication suppresses re-paging, not the exception.** A `duplicate` mark means "already
  queued", not "resolved"; the underlying fail stays open until a human resolves it.
- **Staleness must surface, not hide.** A stale feed is flagged for re-pull; never let missing
  freshness quietly drop a fail from the queue.
- **Thresholds are config, not judgment.** Use the versioned config; never tune bands to a
  desk or counterparty.
