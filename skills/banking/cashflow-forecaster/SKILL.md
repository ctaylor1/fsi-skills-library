---
name: cashflow-forecaster
description: >-
  Build a transparent base / upside / downside cash-flow forecast from an account's
  transaction history plus explicit user assumptions, exposing the key drivers, the
  per-period running balance, and the uncertainty around them. Use when a consumer, SMB
  owner, or relationship manager asks to "forecast my cash flow", "project my balance",
  "what's my runway", "show a best/worst case", or wants a scenario cash-flow model with
  drivers and tie-outs. This skill models and explains only; it NEVER gives financial,
  investment, tax, or credit advice, NEVER makes or implies a credit/eligibility decision,
  and NEVER guarantees a future balance — those are advisory, lending, or human decisions.
license: MIT
compatibility: Amazon Quick Desktop; requires core-banking transactions/balances, product-terms/loan-servicing, CRM, document-intelligence, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Banking"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Model & calculate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 1 - stabilize existing"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Banking product & credit operations"
  aws-fsi-primary-user: "Consumer / SMB owner / relationship manager"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Cashflow Forecaster

## Purpose and outcome
Given an account's transaction history, an opening balance, a horizon, and explicit user
assumptions, build a **deterministic, source-linked cash-flow forecast** with three
scenarios — **base, upside, downside** — each showing the per-period inflow/outflow, net
flow, and running balance, plus the ranked **drivers**, an **uncertainty band**, and
**tie-outs**. A successful output lets a customer or relationship manager see the likely
range of future balances, the lowest projected point, and what drives it — so a human can
plan. The forecast is an artifact for planning; any decision or advice remains human.

## Use when
- "Forecast my cash flow / project my balance for the next N months."
- "What's my runway?" / "When might I dip below zero?"
- "Show me a base, best, and worst case from my transactions."
- A relationship manager wants a consistent, cited scenario model with drivers and tie-outs.

## Do not use
- The user wants **advice or a recommendation** ("should I invest / refinance / pay off my
  loan?") → out of scope; model the cash flow and route the decision to a licensed human.
- The user wants a **credit or eligibility decision** ("do I qualify for a loan?", "am I
  approved?") → out of scope; route to the authorized lending workflow.
- **Standardized credit spreads / financial statements** → `financial-spreading-assistant`.
- **Long-horizon retirement income / drawdown** → `retirement-income-scenario-modeler`.
- General "explain my statement" with no forecast → `bank-statement-analyzer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a forecast with a
durable `forecast_id`; downstream planning/spreading skills and human advisory/lending
workflows consume it. It must not cross into advice, eligibility, or posting.

## Inputs and prerequisites
- **Entity/account identifier**, an **opening balance** (as-of), a **horizon**
  (`horizon_periods`), and the **period** grain (`month` or `week`).
- **Transaction history** sufficient to establish recurring levels (default: several
  periods), each row with date, amount, direction, and category/counterparty where
  available. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- **Assumptions** (optional) — explicit one-off items (a planned tax payment, an expected
  bonus), each with an `offset`, `amount`, `direction`, and `provenance`.
- Read access to core-banking transactions/balances, product terms, CRM; approved
  scenario-factor config (see [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Core-banking transactions/balances
are the position of record for history; product terms add scheduled obligations; CRM and
document intelligence supply user-asserted one-offs. Every derived value is
`derived-from-history`; every one-off is `user-supplied` — provenance is always explicit.

## Workflow
1. **Scope & validate** — confirm the account, opening balance, horizon, and period; load
   history; validate with `validate_input`. Heed thin-history warnings.
2. **Spread history (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to bucket history
   into periods, derive recurring `avg_inflow` / `avg_outflow`, compute net-flow volatility,
   and rank drivers by contribution.
3. **Project scenarios** — apply the versioned scenario factors (base/upside/downside) to the
   recurring levels and add user-supplied one-offs at their period offsets; accumulate the
   running balance from the opening balance for each scenario.
4. **Tie out** — confirm each scenario reconciles (`opening + Σ net == ending`) and the
   history tie-out reconstructs the raw transaction sum.
5. **Write the pack** — per-scenario tables, ending/lowest balances, drivers, the uncertainty
   band, the assumptions register with provenance, and the interpretation prompts.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: all three scenarios present; each ties out; endings are
monotonic (`downside ≤ base ≤ upside`); every assumption carries provenance; no advice /
guarantee / credit-decision language; the standing disclaimer is present; drivers reported.
Fail closed on any miss.

## Human approval
`external-delivery`: human approval required before the forecast is sent to a customer or
written to a plan/case/system of record. No approval is needed for the analyst's own read.
The skill never writes a system of record and never makes a decision.

## Failure handling
- **Thin history** (few periods) → state that recurring levels and volatility are
  low-confidence; do not overstate certainty; list what history is missing.
- **Ambiguous account/identity** → stop and confirm; never forecast the wrong account.
- **Missing categories** → attribute drivers by counterparty or `Uncategorized`; say so.
- **Assumption outside horizon** → record it but do not apply it; warn.
- **Stale/conflicting sources** → cite both; do not resolve silently.
- **Tool timeout** → return the scenarios computed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — account (masked), horizon, opening balance, base/upside/downside ending
   balances, and the lowest projected balance and when it occurs.
2. **Scenarios** — per scenario: per-period inflow/outflow/one-off/net/running balance, the
   ending and lowest balance, and the tie-out.
3. **Drivers** — ranked categories/counterparties with signed net and share.
4. **Uncertainty** — the per-period band and its method (an estimate, not a probability).
5. **Assumptions register** — every value with `derived-from-history` or `user-supplied`
   provenance (and a citation where a document sourced it).
6. **Machine-readable** — scenarios + tie-outs + `forecast_id` for downstream skills.
7. **Standing disclaimer** — "Forecast for planning purposes only; not financial, investment,
   tax, or credit advice, and not a guarantee of future account balances. Assumptions are
   estimates and actual results will vary."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask account numbers (last 4). Minimize customer data in the output to what
the forecast needs. Retain the forecast + assumptions + `config_version` per records policy;
log the read and any external-delivery approval. Never exfiltrate customer data.

## Gotchas
- **A forecast is not a promise.** Present the range and the downside honestly; never
  guarantee a balance or say the account "will not overdraft".
- **Not advice, not a lending decision.** Modeling that surplus exists is not a
  recommendation to invest it, and a healthy forecast is not loan approval — route those.
- **Assumption provenance is load-bearing.** Keep `derived-from-history` and `user-supplied`
  values distinct; a user one-off must never silently overwrite the historical record.
- **Short history hides seasonality.** A few months cannot see annual patterns (tax, tuition,
  seasonal revenue) — surface this rather than projecting a smooth line.
- **Do not tune factors to a person.** Scenario factors come from the versioned config, not
  from guessing what a given customer's future "should" look like.
- **Watch scheduled obligations.** Loan payments, fee/rate resets from product terms belong in
  the outflow, not just discretionary spend.
