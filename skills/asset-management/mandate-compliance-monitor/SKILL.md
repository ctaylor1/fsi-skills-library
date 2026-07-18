---
name: mandate-compliance-monitor
description: >-
  Scheduled, read-only monitor that tests asset-management portfolios and proposed trades
  against versioned mandate, guideline, regulatory, concentration, ESG, and restriction
  rules, classifies each result PASS/WARN/BREACH with cited evidence, deduplicates against
  already-open exceptions, checks position freshness, and packages severity-ranked alerts to
  human compliance queues. Use when a scheduled run (or a compliance officer / portfolio
  manager on demand) needs to surface mandate breaches, pre-trade limit hits, restricted
  holdings, or ESG-exclusion exceptions with source-linked evidence. HARD BOUNDARY: this
  monitor ALERTS ONLY — it never blocks, cancels, or releases a trade; never buys, sells,
  rebalances, or trims a position; never grants, tracks, or closes a cure or waiver; never
  suppresses or closes an alert; and never writes to any book of record. Disposition and
  remediation are human actions.
license: MIT
compatibility: Amazon Quick Desktop; requires PMS/OMS positions & proposed-trades, mandate/IPS rule-library, market & reference data, restricted-list, and prior-alert MCP integrations (all read-only).
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
  aws-fsi-primary-user: "Investment compliance / portfolio manager"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Mandate Compliance Monitor

## Purpose and outcome
Given a set of portfolios, their proposed/pending trades, and a **versioned rule library**,
evaluate every portfolio against every configured mandate, guideline, regulatory,
concentration, ESG, and restriction limit; classify each result **PASS / WARN / BREACH**;
attach cited evidence; deduplicate against already-open exceptions; flag stale positions;
and emit **severity-ranked alerts** to human compliance queues. A successful run lets an
investment-compliance officer or portfolio manager see, with evidence, exactly which limits
are breached (or about to be), which proposed trades would breach, and what is new since the
last run — so a **human** can decide and remediate. This is a **scheduled, read-only,
alert-only** monitor: it packages exceptions, it does not resolve them.

## Use when
- A scheduled compliance run needs to screen mandates for breaches and near-breaches.
- "Which portfolios are over their issuer / sector / asset-class limits right now?"
- "Would this proposed trade breach the mandate before we work the order?" (pre-trade check)
- "Are we holding anything on the restricted list, or anything the ESG mandate excludes?"
- A reviewer wants a consistent, cited exception queue with new-vs-still-open separation.

## Do not use
- The user wants the monitor to **fix** a breach — place/block a trade, rebalance, trim, or
  grant a cure/waiver → out of scope; this monitor alerts only. Route the human to
  `portfolio-rebalancing-assistant` (manager-directed remediation) and their entitled OMS.
- **Deeper exposure / look-through analysis** behind a concentration alert →
  `portfolio-exposure-analyzer`. **Liquidity / liquidation-horizon** questions →
  `liquidity-stress-analyzer`. **Counterparty / settlement / collateral limits** →
  `counterparty-exposure-monitor`.
- **Best-execution review** of a flagged order → `best-execution-reviewer`.
- The **rule itself changed** (regulation update) and the library must be re-baselined →
  `regulatory-change-impact-analyzer`.
- Personalized **investment advice** (what to buy/sell) → out of scope; not licensed advice.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a cited exception pack
with a durable `run_id` and per-alert `fingerprint`s; downstream analysis, rebalancing, and
escalation skills consume it. It must not duplicate their disposition or remediation steps,
and it never closes an exception itself.

## Inputs and prerequisites
- One or more **portfolios** with `portfolio_id`, `mandate_id`, `nav`, `holdings_as_of`, and
  holdings (each with `security_id`, `issuer`, `sector`, `asset_class`, `market_value`, and
  where available `rating`, `country`, `esg_score`, `is_restricted`).
- **Proposed / pending trades** per portfolio for pre-trade checks (optional).
- The **versioned rule set** (`config_version`) for each mandate: concentration, regulatory,
  guideline, restriction, and ESG limits with their `warn_buffer_pct`.
- `max_staleness_days` for freshness, and the **prior open-alert** fingerprints for
  deduplication. Schema and validation: [scripts/validate_input.py](scripts/validate_input.py).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **rule library is the
definition of record** for every limit; PMS/OMS positions are the holdings book of record;
reference data resolves classifications. Cite every alert's evidence to a source row and the
rule to its `config_version`. Never infer a limit from holdings or an assertion.

## Workflow
1. **Load & validate** — pull the versioned rules, positions, proposed trades, restricted
   list, and prior open alerts for the run; validate with `validate_input`.
2. **Check freshness** — compute `staleness_days` per portfolio; mark any exceeding
   `max_staleness_days` as stale and raise a freshness alert. Never drop or silently refresh.
3. **Evaluate rules (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to classify each
   portfolio×rule PASS/WARN/BREACH, computing both **position** breaches (current book) and
   **pre-trade** breaches (a proposed order would newly breach). Each alert carries measured
   value, limit, and cited evidence.
4. **Score & route** — map each alert to a deterministic `severity` and routing `queue` per
   the documented mapping ([references/domain-rules.md](references/domain-rules.md)). This is
   a triage suggestion for a human, not a compliance determination.
5. **Deduplicate** — fingerprint each alert and split **new** vs **still-open** against the
   prior open-alert baseline so persistent breaches do not re-alert every run.
6. **Package the queue** — emit the alert pack (summary, per-alert evidence, escalations,
   freshness, disclaimer) to the compliance queues for human disposition.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every alert is well-formed with cited evidence; severity
and queue tie out deterministically; deduplication partitions new vs still-open; stale
portfolios are flagged (never suppressed); **no autonomous-action / decision language** is
present; the standing disclaimer is present; and escalation counts tie out. Fail closed on
any miss.

## Human approval
`external-delivery`: human approval is required before an alert pack is delivered outside the
compliance function or written to a case/system of record. The scheduled read and the
internal queue are the monitor's only outputs. **Every disposition — cure, waiver, trade,
block, or closure — is a human action**; the monitor never performs or recommends one.

## Failure handling
- **Stale positions** (older than `max_staleness_days`) → flag the portfolio, mark its
  alerts `stale_input`, treat results as low-confidence; do not present as current.
- **Missing / ambiguous limit** → report the gap; never invent or guess a threshold.
- **Missing classification** (no sector/asset_class/esg_score) → evaluate only the rules the
  data supports; label the rest not-evaluable via input warnings.
- **Positions vs. rule-library conflict** (e.g., asset-class tagging) → cite both; do not
  resolve silently.
- **No prior open-alert baseline** → deduplication is disabled; report everything as new and
  say so. **Tool timeout** → return alerts computed so far with an "incomplete" flag; assume
  no automatic retry.

## Output contract
1. **Summary** — run id, as-of, portfolios/rules evaluated, counts (new, deduplicated, warn,
   breach), and stale portfolios.
2. **Alerts** — per alert: portfolio, rule, scope/bucket, status, breach_type
   (position/pre_trade/freshness), measured vs limit, severity, routing queue, cited
   evidence, and `is_duplicate` / `stale_input` flags.
3. **Escalations** — severity buckets with counts and target queues.
4. **Data freshness** — per portfolio staleness and stale flag.
5. **Machine-readable** — alerts + `new_alerts` / `still_open` fingerprints + `run_id`.
6. **Standing disclaimer** — "Monitoring alert only; no trade, block, waiver, cure, or
   system-of-record change has been made. Mandate exceptions require human compliance review
   and disposition."
See [references/controls.md](references/controls.md).

## Privacy and records
Holdings and proposed trades can be **MNPI / client-confidential**. Minimize data in the pack
to what evidences an alert. Retain each run's alerts + citations + `config_version` per
records policy; log the read, the queue emission, and any external-delivery approval. Route
alerts only to approved compliance queues; never exfiltrate holdings or trade intentions.

## Gotchas
- **An alert is not a decision or an action.** A BREACH justifies *review*, never a
  monitor-initiated trade, cure, waiver, or alert closure.
- **Passive vs. active breaches.** A `position` breach is often market-driven (passive) and
  typically carries a cure period the monitor does not own; a `pre_trade` breach is the
  active signal worth catching before the order is worked. Both are alerts, not blocks.
- **Deduplicate, don't silence.** Still-open items must remain visible as open; the
  fingerprint logic prevents re-alerting, not tracking.
- **Stale data is dangerous.** A "clean" run over week-old positions can hide a live breach —
  always surface staleness rather than presenting stale results as current.
- **Limits are versioned config, not judgement.** Never tune a threshold to a portfolio or
  infer "what's acceptable here"; cite the rule and its `config_version`.
- **Boundary buckets.** A holding exactly at the limit (e.g., 5.00% vs a 5% cap) is WARN, not
  BREACH — the engine breaches only when strictly over (or under, for floors).
