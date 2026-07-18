---
name: counterparty-exposure-monitor
description: >-
  Aggregate each counterparty's settlement, derivative (MtM net of collateral plus PFE),
  financing, and deposit exposures; evaluate limit utilization, single-name concentration,
  and credit developments (rating floor, negative watch, CDS widening) against a versioned
  limit register; and raise deduplicated, freshness-tagged alerts to a human review queue.
  Use when a scheduled counterparty-exposure check runs, or when a counterparty-risk,
  treasury, or operations user asks which counterparties are near or over limit, which
  credit lines are deteriorating, or wants aggregated exposure-vs-limit monitoring across
  the book. HARD BOUNDARY: this is a scheduled, read-only, alert-only monitor — it
  aggregates, thresholds, deduplicates, and queues alerts for people; it NEVER posts or
  recalls collateral, changes a limit, terminates a trade, blocks a counterparty, makes a
  credit or trading decision, closes or suppresses an alert, or writes any system of record.
  Those are human or authorized-system actions.
license: MIT
compatibility: Amazon Quick Desktop; requires PMS/OMS, derivatives/risk-system, market-and-credit-data, counterparty-reference, and compliance limit-register MCP integrations (all read-only) plus an append-only human review queue.
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "System-interaction or operational skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Monitor & alert"
  aws-fsi-agent-pattern: "Scheduled monitor + human queue"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Scheduled read-only; alert only"
  aws-fsi-scheduled-agent: "read-only-monitoring"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Counterparty risk / treasury / operations"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Counterparty Exposure Monitor

## Purpose and outcome
On a schedule (or on demand), aggregate each counterparty's net current exposure across
settlement, derivative MtM (net of collateral, plus PFE add-on), financing, and deposit
lines; evaluate it against the versioned limit register and credit developments; and emit a
**deduplicated, freshness-tagged alert set** routed to the counterparty-risk review queue.
A successful run gives a reviewer a precise, cited picture of which counterparties are near
or over limit, over-concentrated, or credit-deteriorating — with every alert traceable to
exposure rows and a config version. The monitor triages; **the disposition and any action
stay human.**

## Use when
- The scheduled counterparty-exposure check runs (daily / intraday).
- "Which counterparties breached their limit this morning?"
- "Aggregate our exposure to Acme across settlement, derivatives, and financing."
- "Which credit lines are deteriorating — downgrades, negative watch, CDS widening?"
- "Is any single counterparty over the concentration limit for the book?"

## Do not use
- The user wants to **act** — post/recall collateral, change a limit, terminate/novate a
  trade, hedge, block/suspend a counterparty → out of scope. Alert and route to the
  counterparty-risk / treasury / collateral-operations team; the monitor never acts.
- The user wants a **binding counterparty, credit, or trading decision** → out of scope;
  route to the reviewer and the firm's credit committee.
- Interactive **exposure composition / driver** analysis → `portfolio-exposure-analyzer`.
- **Funding / liquidity stress** scenario analysis → `liquidity-stress-analyzer`.
- **Mandate / IPS guideline** limits (not counterparty credit) → `mandate-compliance-monitor`.
- Firm-wide market-risk (VaR/greeks) or cross-risk concentration limits →
  `market-risk-limit-monitor` / `concentration-risk-monitor` (Risk Management).

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This monitor emits an alert set with a
durable `run_id` and per-alert `fingerprint`; downstream analysis, packaging, and any action
consume it. It must not duplicate their disposition, decision, or action steps.

## Inputs and prerequisites
- Run `as_of` timestamp and `config_version` (the limit-register version).
- **Exposures** per counterparty: `exposure_type`, `current_exposure`, optional `collateral`
  and `pfe_addon`, the source `feed`, and a `source_ref`. Schema and evaluability rules:
  [scripts/validate_input.py](scripts/validate_input.py).
- **Counterparties**: rating, `rating_floor`, `cds_bps` + `cds_baseline_bps`, watch.
- **Limits**: per-counterparty `total_current_exposure` and a portfolio
  `single_name_concentration_pct`; plus thresholds in `config`.
- **Feeds** with `as_of` + `max_age_hours` for freshness; prior `open_alerts` for dedup.
- Read access to PMS/OMS, risk system, market/credit data, reference data, and the limit
  register (see [references/source-map.md](references/source-map.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). PMS/OMS positions and settlement
are the record; the risk system supplies MtM/PFE/collateral; market data supplies
ratings/CDS; the versioned limit register supplies limits, floors, and thresholds. Cite
every alert's evidence to a source feed row with its effective timestamp.

## Workflow
1. **Scope & freshness** — load exposures, counterparties, limits, and feeds for the
   `as_of`; validate with `validate_input`. Compute each feed's age; mark stale feeds.
2. **Aggregate (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute each
   counterparty's net current exposure (`max(0, CE − collateral) + PFE`, summed across
   exposure types) and the book total.
3. **Threshold & credit checks** — evaluate limit utilization, single-name concentration,
   and credit developments (rating floor, negative watch, CDS widening) per the documented
   mapping in [references/domain-rules.md](references/domain-rules.md).
4. **Freshness-tag & deduplicate** — tag alerts derived from stale feeds `freshness: stale`;
   raise a `data_freshness` alert per stale feed (never suppress); compare fingerprints to
   `open_alerts` and mark each `new` or `recurring`.
5. **Package for the queue** — attach the deterministic severity → queue/SLA/escalate-to,
   the cited evidence, and the standing disclaimer. Enqueue for human review; take no action.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every alert is cited and freshness-tagged, fingerprints
are unique (dedup), each stale feed has a `data_freshness` alert, escalation packaging
matches the deterministic mapping, `run_severity` ties out, no autonomous-action language is
present, and the standing disclaimer is present. Fail closed on any miss.

## Human approval
`external-delivery`: human approval required before the alert pack is delivered outside the
review queue or written to a system of record. The monitor's own scheduled read + enqueue to
the human queue needs no approval; it takes no counterparty, limit, collateral, or trade
action under any circumstances.

## Failure handling
- **Stale feed** → still run; tag dependent alerts `stale` and raise a `data_freshness`
  alert. Never drop an exposure because a feed is late.
- **Missing limit** for a counterparty → report `not_evaluable`; never assume unlimited.
- **Missing collateral / PFE / CDS baseline** → compute what the data supports; label the
  rest not-evaluable rather than guessing.
- **Ambiguous entity / netting set** → stop and confirm; never aggregate the wrong entity.
- **Conflicting rating scales** → cite both; do not reconcile silently.
- **Tool timeout** → return alerts computed so far with a clear "incomplete" flag; page long
  books as resumable stages. Do not assume automatic retries.

## Output contract
1. **Run summary** — `run_id`, `as_of`, `config_version`, book total, counterparties
   evaluated, `run_severity`, alert count, stale feeds.
2. **Alerts** — per alert: `fingerprint`, scope, counterparty, `alert_type`/`dimension`,
   `severity`, `freshness`, `status` (new/recurring), the measure, cited evidence, and the
   `queue`/`sla_hours`/`escalate_to` packaging.
3. **Not-evaluable** — counterparties/dimensions with missing limits or data.
4. **Machine-readable** — the full alert set + `run_id` for downstream skills and the queue.
5. **Standing disclaimer** — "Monitoring alert only; no limit, trade, collateral, or
   counterparty action has been taken. Human review is required before any action."
See [references/controls.md](references/controls.md).

## Privacy and records
MNPI / client-confidential. Exposure levels, ratings, and CDS reactions can be
market-moving — need-to-know only. Minimize counterparty data in output to what evidences an
alert. Retain the alert set + citations + `config_version` per records policy; log the read
and any external-delivery approval. Never exfiltrate exposure or counterparty data.

## Gotchas
- **An alert is not a decision or an action.** Severity and SLA drive a *human* queue, never
  an automated collateral call, limit change, or trade.
- **Collateral floor matters**: net current exposure floors the collateralized current
  portion at 0 before adding PFE; a large collateral balance does not create negative
  exposure that offsets other lines.
- **Stale ≠ suppressed**: a late feed is surfaced (tagged + `data_freshness` alert), not a
  reason to skip a counterparty — that is how breaches get missed.
- **Dedup on the stable fingerprint**: a severity change updates the alert in place; it does
  not open a second alert. Re-runs mark recurring, not new.
- **Rating scale discipline**: compare ratings only on the configured ladder; an unmapped
  rating is not-evaluable for the floor, not an automatic pass.
- **Thresholds are config**: limits, floors, and widening bands come from the versioned
  register, never tuned to a counterparty at run time.
