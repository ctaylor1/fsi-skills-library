---
name: credit-risk-portfolio-analyzer
description: >-
  Analyze an existing credit portfolio — quality distribution, rating migration, delinquency,
  expected loss (PD×LGD×EAD), collateral/LTV, single-name/sector/geography concentration,
  vintage cohorts, and stress-scenario impacts — with transparent, reproducible calculations
  and row-level evidence, surfacing limit/threshold exceptions and a suggested review
  disposition. Use when a credit-risk or portfolio analyst asks to review portfolio quality,
  find concentration or delinquency exceptions, compute expected loss, run a stress scenario
  over the book, or assemble committee-ready evidence. This skill is R3 decision-support: it
  produces findings, cited evidence, and recommendations ONLY. It NEVER makes a credit
  decision (approval / adverse action / denial), sets an allowance or reserve, disposes of or
  waives a limit breach, closes a case, files a regulatory report, or writes any system of
  record — every exception requires human credit-risk adjudication.
license: MIT
compatibility: Amazon Quick Desktop; requires loan/exposure-tape, risk-rating/model-store, collateral-register, risk-limits-config, and scenario-library MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Risk Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Enterprise Risk Management"
  aws-fsi-primary-user: "Credit risk / portfolio analytics"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Credit Risk Portfolio Analyzer

## Purpose and outcome
Given a credit portfolio (a loan/exposure tape with PD/LGD, collateral, delinquency, ratings,
and vintages) plus the versioned limits config and an optional stress scenario, compute a set
of **transparent, reproducible portfolio metrics**, surface **limit/threshold exceptions**
with row-level evidence, and produce a review-ready pack with a **suggested review
disposition** (Stable / Watch / Elevated). A successful output lets a credit-risk officer or
committee see exactly what breached, why, and which exposures drive it — the decision, the
allowance, the limit action, and any filing remain human.

## Use when
- "Analyze this portfolio's credit quality, delinquency, and concentration; show the math."
- "Compute expected loss and tell me where we're over the EL budget."
- "Which single names / sectors / geographies breach concentration limits?"
- "Run the adverse stress scenario over the book and show which limits break."
- A reviewer needs consistent, cited portfolio evidence to attach to a committee package.

## Do not use
- The user wants a **credit decision** ("approve the increase", "issue adverse action",
  "deny the loan"), an **allowance/reserve** set, a **limit breach waived**, a **case
  closed**, or a **filing** → out of scope. Provide evidence and route to the human
  credit-risk officer / committee.
- **Single new-application underwriting/decisioning** → not this skill (this analyzes an
  existing portfolio); route to the relevant banking underwriting workflow and a human.
- **Designing** the stress scenario itself → `stress-test-scenario-designer`.
- **Ongoing monitoring/alerting** of a metric → `concentration-risk-monitor` /
  `key-risk-indicator-monitor` (read-only monitors).
- **Loan-level covenant tracking** → `covenant-compliance-monitor`.
- Questions about **PD/LGD model soundness/validation** → Data, AI & Model Governance skills
  (`model-validation-assistant`, `model-risk-documenter`); this skill consumes model outputs.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits an analysis pack with a
durable `analysis_id`; downstream monitoring, memo-drafting, and enterprise-rollup skills
consume it. It must not duplicate their monitoring, drafting, decision, or filing steps.

## Inputs and prerequisites
- **Portfolio identifier** and a single **`as_of`** date.
- **Exposure tape** — each row with `exposure_id`, `obligor_id`, `ead`, `pd`, `lgd`,
  `days_past_due`, `source_ref`, and (where available) `segment`, `sector`, `geography`,
  `rating`, `prior_rating`, `collateral_value`, `vintage`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- **Versioned limits config** (concentration, delinquency, LTV, EL budget, migration, stress
  thresholds) and, optionally, a **scenario** block (PD/LGD multipliers). See
  [references/domain-rules.md](references/domain-rules.md).
- Read access to the loan tape, rating/model store, collateral register, limits config, and
  scenario library (all read-only).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The loan/exposure tape is the
position of record for balances and delinquency; PD/LGD are governed model outputs consumed
as-is; the collateral register supplies LTV inputs; limits and scenarios are versioned
contracts. Cite every exception's evidence to a source row; if the tape and a model/collateral
snapshot conflict, cite both and flag — never reconcile silently.

## Workflow
1. **Scope & validate** — confirm the portfolio and `as_of`; load the tape, ratings,
   collateral, limits, and (optional) scenario; run `validate_input`. Fail closed on
   structural errors; record data-quality warnings that make a metric not-evaluable.
2. **Compute metrics (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute quality,
   expected loss, delinquency, concentration (+ HHI), collateral/LTV, migration, vintage, and
   the stress-scenario impact. Every number is explainable and traceable — there is no opaque
   composite score.
3. **Derive exceptions with evidence** — compare each metric to the versioned limits config;
   for each breach, attach the specific exposure rows (and, for aggregates like EL, the top
   contributors) with citations, plus a severity.
4. **Suggest disposition** — map the exception severities to a review band (Stable / Watch /
   Elevated) per the deterministic, documented mapping. This is a triage suggestion for a
   human, explicitly **not** a credit decision.
5. **Assemble the pack** — plain-language narrative + metrics + exceptions + evidence +
   adjudication note + routing + standing disclaimer, plus adjudication prompts (mitigating
   context to weigh).

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every exception has cited evidence; the disposition maps
deterministically from severities; **no autonomous decision / allowance / closure / filing /
system-of-record language** is present; the standing disclaimer and human-adjudication note
are included; and a routing path exists when exceptions fired. Fail closed on any miss.

## Human approval
`required` (R3): a human credit-risk officer / credit risk committee must adjudicate before
any credit decision, allowance/reserve determination, limit action or waiver, case closure,
or regulatory filing. The skill performs no write and stages nothing for execution; it only
reads and analyzes.

## Failure handling
- **Missing model outputs (PD/LGD)** → mark the dependent metric (EL, scenario) not-evaluable;
  do not impute.
- **Thin portfolio / missing dimensions** (no sector, geography, prior_rating, collateral, or
  scenario) → compute only the supported metrics; label the rest not-evaluable; state low
  confidence.
- **Mixed or ambiguous `as_of` dates** → stop and require the analyst to resolve; never mix
  as-of dates silently.
- **Stale/conflicting sources** (tape vs rating/collateral snapshot) → cite both; do not
  resolve silently.
- **Tool timeout on a large tape** → return metrics computed so far with a clear "incomplete"
  flag and resume as a paged stage; never guess the remainder.

## Output contract
1. **Summary** — portfolio (id), `as_of`, total EAD, exposure/obligor counts, count of
   exceptions, suggested disposition band.
2. **Metrics** — quality, expected loss (with PD×LGD×EAD components), delinquency buckets,
   concentration (+ HHI + top names), collateral/LTV, migration, vintage, scenario impact.
3. **Exceptions** — per breach: code, severity, finding, threshold vs observed, cited
   evidence rows, and a recommended human review path.
4. **Adjudication prompts** — mitigating context to weigh (paydowns, appraisals, guarantees,
   restructurings, approved exceptions) so the adjudicator sees both sides.
5. **Not-evaluable** — metrics the data did not support, with the reason.
6. **Machine-readable** — metrics + exceptions + evidence + `analysis_id` for downstream skills.
7. **Standing disclaimer** — "Decision-support analysis only; findings and evidence require
   human credit-risk adjudication. No credit decision, reserve or allowance determination,
   limit action, filing, or system-of-record change has been made."
See [references/controls.md](references/controls.md).

## Privacy and records
Confidential exposure/obligor data. Minimize obligor identifiers in output to what evidences
an exception (obligor code + exposure id, not free-text borrower PII). Retain the analysis +
citations + `config_version` + scenario name per records policy; log the read and any
adjudication handoff. Never exfiltrate the loan tape.

## Gotchas
- **An exception is not a decision.** A critical exception justifies *Elevated review*, never
  a credit approval/denial, an allowance, or a limit action.
- **PD/LGD are model outputs, not this skill's opinions.** Do not re-estimate them; surface
  stale/missing model outputs rather than smoothing over them.
- **Baseline is the whole book at one `as_of`.** Mixing as-of dates or double-counting a
  multi-facility obligor distorts concentration — resolve upstream.
- **Concentration limits scale with the book.** On a small/granular sub-portfolio many names
  can sit near the limit; report the config-driven breach factually, do not re-tune the limit.
- **Round grades and off-scale ratings** are excluded from migration rather than guessed;
  report them as not-evaluable.
- **Scenario multipliers cap at 1.0** for PD and LGD; a stressed EL is an illustration under a
  named, versioned scenario, not a forecast or a capital decision.
