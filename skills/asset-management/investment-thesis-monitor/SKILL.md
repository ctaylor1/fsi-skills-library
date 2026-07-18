---
name: investment-thesis-monitor
description: >-
  Track a book of active investment theses on a schedule against their documented KPIs,
  catalysts, consensus estimates, price targets/stops, news, and filings, and flag fresh
  evidence that confirms or challenges each thesis as a deduplicated, escalation-banded alert
  queue for the covering analyst or PM. Use when a research analyst or portfolio manager wants
  a read-only scheduled check of whether anything broke or validated a thesis this period —
  "did the ACME thesis hold up", "flag any theses at risk", "run the thesis monitor",
  "which positions had a catalyst miss or stop breach". HARD BOUNDARY: this is a scheduled,
  read-only, ALERT-ONLY monitor — it never trades, rebalances, trims/adds, exits or hedges a
  position, closes or retires a thesis, stages an order, writes a system of record, or gives
  personalized investment advice. Every escalation band is a triage suggestion a human decides
  and acts on.
license: MIT
compatibility: Amazon Quick Desktop; requires thesis-register/controlled-content, PMS/OMS, market-data, research/estimates, and versioned-config MCP integrations (all read-only).
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
  aws-fsi-primary-user: "Research analyst / portfolio manager"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Investment Thesis Monitor

## Purpose and outcome
On a schedule, evaluate each active thesis in a research book against its **documented**
expectations — KPIs, catalysts, consensus estimates, price target/stop, and monitored risks —
using only **fresh** evidence, and compute explainable **confirming/challenging signals**.
Package the results into a **deduplicated, escalation-banded alert queue** with cited evidence
for the covering analyst and PM. A successful run tells a human, quickly and reproducibly,
which theses had fresh evidence that confirms or challenges them this period — and which need
attention first. The decision and any action remain human.

## Use when
- "Run the scheduled thesis monitor over my book and flag anything that changed."
- "Did any KPI, catalyst, estimate, or price move break the ACME long thesis this week?"
- "Which theses had a catalyst miss, an estimate cut, or a stop breach?"
- "Surface theses that are playing out (target reached, KPI beat) vs. at risk."
- A scheduled runner needs a consistent, cited alert queue with a suggested escalation band.

## Do not use
- The user wants to **act** — trim/add/exit/hedge/rebalance a position, place or stage an
  **order**, or **close/retire a thesis** → out of scope. Emit the alert with evidence and
  route to the **PM / trading desk** (and, for a formal review, `investment-committee-memo-builder`).
- The user wants **personalized investment advice** ("should I buy more?") → prohibited;
  route to a **licensed investment professional**.
- A **deep earnings read-through** of a specific result → `earnings-results-analyzer`; a
  **re-model** under revised drivers → `scenario-sensitivity-generator` or `dcf-modeler`; a
  full **re-research** → `coverage-initiation-researcher`.
- **Mandate / investment-guideline limit** monitoring → `mandate-compliance-monitor`;
  **counterparty exposure** limits → `counterparty-exposure-monitor` (sibling monitors).
- A **write-up** of the thesis for commentary → `fund-commentary-drafter`; performance
  contribution → `performance-attribution-builder`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This monitor emits an alert queue with a
durable `monitor_run_id` and per-alert `alert_key`; downstream analysis/drafting skills and
the human reviewer consume it. It must not duplicate their analysis, drafting, or any action.

## Inputs and prerequisites
- A **scheduled-run snapshot** for the active thesis book: `as_of` (run cutoff),
  `config_version`, optional `config`, `prior_alerts` (for dedup), and `theses[]`.
- Each thesis: `thesis_id`, `security`, `direction` (`long`/`short`), `owner`, `thesis_asof`,
  and its documented evidence surfaces — `kpis`, `catalysts`, `estimates`, `market` +
  `targets`, `news_flags` — each evidence row carrying an `observed_at`/`price_asof` and a
  `source_ref`. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the thesis register, PMS/OMS, market data, research/estimates, and the
  versioned monitor config (see [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **thesis register** is the
position of record for what the thesis claims; market data and research provide the current
evidence; config supplies the tolerances and escalation mapping. Cite every fired signal to a
source row and its observation date. Never substitute a headline or price move for the
register's documented expectation.

## Workflow
1. **Load & validate** — read the run snapshot; validate with `validate_input`. Confirm the
   `as_of`, `config_version`, and that each thesis has at least one evidence surface.
2. **Freshness-gate evidence** — age each evidence row against `as_of`; evidence older than
   `max_staleness_days` is `not_evaluable`. A thesis with **no** fresh evidence becomes a
   `freshness_gaps` item, not a breach.
3. **Compute signals (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute the
   confirming/challenging signals (KPI beat/miss, catalyst met/missed, estimate revision,
   target/stop breach, risk news), each with cited evidence.
4. **Band & stance** — map each thesis's fired-**challenging** set to an escalation band
   (Informational / Review / Elevated) per the documented mapping, and tag the thesis stance
   (confirming / challenging / mixed).
5. **Deduplicate & queue** — compare each `alert_key` against open `prior_alerts`;
   continuations are marked `duplicate` and routed to `queue.deduplicated` (not re-escalated);
   new alerts go to `queue.new`; group all by band in `queue.by_escalation`.
6. **Write the queue** — plain-language summary per alert + cited evidence + suggested band +
   freshness gaps + the standing disclaimer. Stage for the analyst; take no action.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: `action_taken == none`; every fired signal has cited,
**fresh** evidence; the escalation band matches the deterministic mapping; deduplication is
applied and the queue partitions the alert keys; no trade/rebalance/exit/close-thesis or
investment-advice language is present; and the standing disclaimer is present. Fail closed on
any miss.

## Human approval
`external-delivery`: human approval is required before the alert queue is delivered externally
(e.g., emailed to the desk) or written to a system of record. No approval is needed for the
covering analyst's own read of the staged queue. The monitor never takes a position or thesis
action.

## Failure handling
- **Stale / missing evidence** → mark the signal `not_evaluable`; never fire on stale data.
  If a whole thesis is stale, surface it as a `freshness_gaps` item to refresh the feed.
- **Register/data conflict** (KPI defined differently, price mismatch) → cite both, flag for
  the analyst; do not resolve silently.
- **Ambiguous thesis/security identity** → stop and confirm; never alert on the wrong name.
- **Missing config** → use documented defaults but record that `config_version` was absent;
  do not tune tolerances to a name.
- **Tool timeout / long book** → return the alerts computed so far with a clear "incomplete"
  flag and resume the remaining theses as a staged run.

## Output contract
1. **Run summary** — `monitor_run_id`, `as_of`, `config_version`, theses evaluated, counts by
   band, new vs. deduplicated.
2. **Alerts** — per alert: thesis, security, direction, owner, stance, escalation band,
   `duplicate` flag, fired signals with cited evidence, `not_evaluable` list, and a
   `data_freshness` block.
3. **Queue** — `new`, `deduplicated`, and `by_escalation` groupings for the analyst.
4. **Freshness gaps** — theses that could not be evaluated (feed to refresh).
5. **Machine-readable** — the full run JSON with `monitor_run_id` for downstream skills.
6. **Standing disclaimer** — "Monitoring alert only; not investment advice or a trading
   decision. No position or thesis action has been taken."
See [references/controls.md](references/controls.md).

## Privacy and records
MNPI / client-confidential. A thesis and its evidence may be material non-public information:
restrict the queue to entitled research/PM users under the firm's information-barrier policy.
Minimize data in each alert to what evidences a fired signal. Retain the run + citations +
`config_version` per records policy; log the read and any external-delivery approval. Never
exfiltrate thesis or position data.

## Gotchas
- **An alert is not a decision.** An Elevated band justifies *review priority*, never a
  buy/sell/hold, a thesis close, or a trade — those are human PM/analyst actions.
- **Stale data is silent.** Old evidence must not fire a signal; a thesis that looks "quiet"
  may simply have a stale feed — that is why `freshness_gaps` is a distinct output.
- **Confirming evidence matters too.** The monitor flags a thesis playing out (target reached,
  KPI beat), not only theses at risk — precision cuts both ways.
- **Direction flips the sign.** A downward estimate revision challenges a *long* but confirms
  a *short*; the signal side is computed from `direction`, not assumed.
- **Deduplicate to protect escalation latency.** A continuing breach is not a new escalation;
  re-raising every run destroys the latency signal and creates alert fatigue.
- **Do not tune tolerances to a name.** Tolerances come from the versioned config, not from
  guessing what "should" trigger for a favored position.
