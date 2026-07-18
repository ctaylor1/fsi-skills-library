---
name: fpa-variance-analyzer
description: >-
  Explain actual-to-budget, forecast, and prior-period variances by driver, apply a versioned
  materiality screen, quantify run-rate impacts, and draft management commentary with cited
  evidence. Use when an FP&A analyst or finance business partner asks "why is opex over
  budget", "explain the revenue variance by driver", "what's the run-rate impact", or needs
  review-ready variance commentary for a management/board pack. This skill analyzes and drafts
  only; it NEVER makes a management decision (headcount, funding, budget approval), commits or
  reforecasts a guidance number, restates actuals, or posts a journal — those are human /
  authorized-system actions.
license: MIT
compatibility: Amazon Quick Desktop; requires ERP/GL + consolidation, subledger, FP&A/planning, document-intelligence, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Finance & Operations"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Confidential (financial records)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Finance & Controllership"
  aws-fsi-primary-user: "FP&A analyst / finance business partner"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# FP&A Variance Analyzer

## Purpose and outcome
Given a period's posted actuals and the comparison bases (budget, forecast, prior period),
compute each line's variance, screen for **materiality**, verify any supplied **driver
decomposition ties out**, quantify a **run-rate impact** for recurring items, and produce
**cited, review-ready draft commentary** with a suggested review priority. A successful output
lets a finance business partner review and finalize variance commentary quickly — the
commentary is a draft, and every decision or company communication downstream remains human.

## Use when
- "Why did opex come in over budget this month?" / "Explain the revenue variance by driver."
- "What's the run-rate impact if this cost variance is recurring?"
- "Draft the variance commentary for the June management pack."
- A business partner needs consistent, cited variance write-ups against budget/forecast/prior.

## Do not use
- The user wants a **management decision** ("should we cut headcount / defund this / approve
  the budget") → out of scope; provide the variance and route the decision to the finance
  business partner and management.
- The user wants to **commit or reforecast guidance** ("set full-year guidance to $X") → out
  of scope; that is an approved company communication, not an analysis.
- The variance is actually a **GL-to-subledger break / posting error** needing reconciliation
  and a correcting journal → `gl-reconciler`; posting/certification → `month-end-close-orchestrator`.
- Actuals and plan are on **inconsistent charts of accounts** and need mapping first →
  `financials-normalizer`, then return here.
- The user wants the finished **management/board report** assembled → `management-reporting-packager`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a variance pack with a
durable `analysis_id`; downstream packaging/reconciliation/audit skills consume it. It must not
duplicate their packaging, reconciliation, posting, or decision steps.

## Inputs and prerequisites
- **Entity, period, and `as_of`**, plus the `basis` that drives the materiality screen
  (default `budget`).
- **Line items** with account, `account_type` (`revenue`/`expense`), posted `actual`, and
  `budget`; `forecast`/`prior` where available; optional approved `drivers[]` and a
  `persistence` flag (`recurring`/`one_time`/`timing`). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to ERP/GL + consolidation and FP&A/planning; versioned materiality/attribution
  config (see [references/domain-rules.md](references/domain-rules.md)).
- Actuals from a **closed or explicitly stated soft-close** period; label the close status.

## Source hierarchy
See [references/source-map.md](references/source-map.md). Posted GL/consolidation actuals are
the position of record; the FP&A system supplies plan/forecast/prior and approved drivers;
subledgers provide decomposition detail. Cite every material finding to source rows; never
substitute a forecast, spreadsheet, or prior narrative for a posted actual.

## Workflow
1. **Scope & validate** — confirm entity/period/basis and close status; load lines; run
   `validate_input`. Note which comparisons and attributions are evaluable.
2. **Compute variances (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute
   `vs_budget`, `vs_forecast`, `vs_prior` per line and set favorable/unfavorable from account
   type (never from the raw sign).
3. **Screen materiality** — flag lines exceeding the absolute or percent thresholds (with the
   `min_base` floor on the percent test). Only material lines get commentary.
4. **Attribute & tie out** — for each material line with drivers, verify `sum(drivers)` ties
   out to the variance (`ok` / `fail` / `unattributed`). Never fabricate a driver to force a
   tie-out.
5. **Quantify run-rate** — for recurring material lines, estimate the run-rate impact over the
   periods remaining; label it an estimate, not a reforecast.
6. **Draft commentary** — plain-language, factual explanation per material finding + cited
   evidence + suggested review priority + alternative-explanation caveats. Attribute any
   decision or forward statement to the human.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every material finding has cited evidence; `ok` attribution
independently ties out; run-rate impacts are labeled estimates; the priority maps
deterministically; no decision/commitment/restatement/advice language is present; the
disclaimer and caveats are included. Fail closed on any miss.

## Human approval
`external-delivery`: human review required before the commentary is sent to business leaders,
written into a management/board pack, or committed to a system of record. No approval is needed
for the analyst's own read. The skill never posts, reconciles, commits a forecast, or decides.

## Failure handling
- **Open/soft-close period** → label actuals provisional; do not present variances as final.
- **Missing forecast/prior** → compute only the supported comparisons; mark the rest
  "not evaluable"; do not infer a base.
- **No drivers on a material line** → report `unattributed`; do not fabricate a decomposition;
  escalate for a human to explain.
- **Drivers that don't tie out** → report `fail` with the gap; do not force a reconciliation.
- **Inconsistent charts of accounts** → stop and route to `financials-normalizer`.
- **Stale/conflicting sources** (GL vs planning) → cite both; do not resolve silently.
- **Tool timeout** → return the material findings computed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — entity, period, basis, close status, count of material findings, suggested
   review priority.
2. **Findings** — per material line: account, variance vs budget/forecast/prior,
   favorable/unfavorable, materiality reason, driver attribution status + tie-out, run-rate
   estimate, cited evidence rows, and factual draft commentary.
3. **Caveats** — alternative explanations (timing, reclass, accrual true-up, FX, allocation).
4. **Not-evaluable** — comparisons/attributions the data does not support.
5. **Machine-readable** — findings + evidence + `analysis_id` for downstream skills.
6. **Standing disclaimer** — "Variance analysis and draft commentary only; not a management
   decision, forecast commitment, or restatement of the financial records. Human review is
   required before external delivery."
See [references/controls.md](references/controls.md).

## Privacy and records
Confidential financial records. Minimize data to what evidences a material finding. Report
salary/compensation at the aggregate account level; never expose individual pay in commentary.
Retain the analysis + citations + `config_version` per records policy; log the read and any
external-delivery approval. Never exfiltrate financial data.

## Gotchas
- **Sign is not direction.** An over-budget expense is *unfavorable* even though the variance
  number is positive; favorable/unfavorable comes from account type, not the raw sign.
- **Percent on a tiny base lies.** A 50% variance on a $2k base is not material — the
  `min_base` floor exists so trivial lines don't dominate the commentary.
- **Run-rate is an estimate, not a forecast.** Annualizing a monthly variance is context for a
  human; it must never be presented as a reforecast or committed guidance.
- **Don't fabricate drivers.** If the decomposition doesn't tie out or isn't supplied, say so
  (`fail`/`unattributed`) — a plausible-sounding made-up driver is worse than an open item.
- **One-time vs recurring changes everything.** A one-off port surcharge in a run-rate line
  distorts the annualized number; separate it before quantifying run-rate.
- **Config is not a dial for the answer.** Thresholds come from the versioned config, never
  tuned to make a specific line look material or immaterial.
