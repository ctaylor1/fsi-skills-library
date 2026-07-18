---
name: loan-affordability-precheck
description: >-
  Estimate indicative loan affordability from disclosed income, expenses, debt, and requested
  loan terms: compute the amortized monthly payment, front-end and back-end DTI, and residual
  income, map them to an indicative affordability band against versioned thresholds, and
  stress-test for higher rates and lower income. Use when a consumer or loan officer asks "can I
  afford this mortgage / car payment / loan", "what would my DTI be", "run an affordability
  precheck", or wants the assumptions and stress cases shown before starting an application. This
  skill produces a transparent, reproducible estimate and routes the decision to human
  underwriting; it NEVER approves, denies, pre-approves, or determines qualification/eligibility,
  issues an adverse-action decision, commits to lend, or gives personalized borrowing advice.
license: MIT
compatibility: Amazon Quick Desktop; requires loan origination/servicing, core-banking, CRM, document-intelligence, product-terms/credit-policy config, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Banking"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Domain workflow"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 1 - stabilize existing"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Banking product & credit operations"
  aws-fsi-primary-user: "Consumer / loan officer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Loan Affordability Precheck

## Purpose and outcome
Given disclosed income, expenses, existing debt, and a requested loan (principal, rate, term,
product type), compute the **amortized monthly payment**, **front-end / back-end DTI**, and
**residual income**; map them to an **indicative affordability band** using versioned thresholds;
and **stress-test** the result for higher rates and lower income. A successful output lets a
consumer understand roughly where they stand and lets a loan officer decide whether to proceed to a
full, verified application — the credit decision, and any applicant-facing outcome, remains human.

## Use when
- "Can I afford a $320k mortgage at 6.5% over 30 years?" / "What car payment can I handle?"
- "What would my DTI and residual income be with this loan?"
- "Run an affordability precheck and show me the assumptions and a stress test."
- A loan officer wants a consistent, reproducible affordability write-up before intake.

## Do not use
- The user wants a **credit decision** — approve/deny, pre-approval, "do I qualify", eligibility,
  an **adverse-action notice**, a rate lock, or a commitment to lend → out of scope. Produce the
  indicative estimate and route to **human underwriting** / the loan-origination system.
- **Income/asset verification** or document extraction only → `bank-statement-analyzer` (statements)
  or `financial-spreading-assistant` (commercial financials/tax returns).
- **Assembling the application** for submission → `credit-application-packager`; verifying a package
  → `loan-package-completeness-checker`; commercial credit narrative → `credit-memo-drafter`.
- **Personalized investment/retirement/borrowing advice** ("should I borrow against my 401k") →
  out of scope; for retirement income modeling, `retirement-income-scenario-modeler`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits an indicative estimate with a
durable `precheck_id`; upstream skills feed its inputs and downstream skills consume the context on
**verified** data. It must not duplicate their verification, packaging, or decision steps.

## Inputs and prerequisites
- The **requested loan**: type (`mortgage` | `auto` | `personal`), principal, `annual_rate_pct`,
  `term_months`, and for a mortgage the monthly escrow parts (tax, insurance, HOA).
- **Income** (`gross_monthly`, optional `other_monthly`, optional `net_monthly`) and **obligations**
  (`existing_monthly_debt`, `existing_housing_expense`, `monthly_living_expenses`).
- The versioned **threshold/stress config** (`config_version`). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to loan origination/servicing, core-banking, CRM, and document intelligence. These are
  **disclosed** figures for an indicative estimate — not verified underwriting data.

## Source hierarchy
See [references/source-map.md](references/source-map.md). Product-terms/credit-policy config sets the
thresholds; loan origination/servicing and document intelligence supply income/obligation figures
(cited). Where a document and a disclosed figure conflict, cite both and flag — never silently pick.

## Workflow
1. **Scope & validate** — confirm the applicant and the requested loan; load disclosed
   income/obligations; run [scripts/validate_input.py](scripts/validate_input.py). Heed warnings
   (missing net income or living expenses make DTI/residual optimistic).
2. **Compute (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to get the amortized
   payment (+ escrow for a mortgage), front-end / back-end DTI, and residual income. Formulas are
   explainable, not a black box (see [references/domain-rules.md](references/domain-rules.md)).
3. **Map the band** — apply the deterministic, documented mapping from DTIs + residual to an
   **indicative** band (Within typical guidelines / Approaching typical limits / Outside typical
   guidelines). The band describes distance from policy thresholds, not an outcome.
4. **Stress-test** — recompute at higher rates (+2%, +3%) and lower income (−10%, −20%); report each
   scenario's payment, DTIs, residual, and band so the reviewer sees sensitivity.
5. **Write the pack** — plain-language explanation + the assumptions + the band + the stress cases +
   explicit caveats (disclosed vs verified, indicative residual) + the standing disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after. The
output check re-derives the payment and every band as an independent tie-out, confirms both a rate-
and an income-stress scenario are present, screens for credit-decision / adverse-action /
qualification / directive-advice language, and requires the assumptions block and the standing
disclaimer. Fail closed on any miss.

## Human approval
`required`. A human underwriter must adjudicate before any credit decision, adverse-action notice,
customer commitment, filing, or write to the loan-origination system of record. No approval is needed
for the applicant's or officer's own read of the indicative estimate. The skill never records a
decision or sends an applicant-facing outcome.

## Failure handling
- **Missing net income / living expenses / obligations** → compute what the data supports; label
  DTI/residual **indicative/optimistic**; do not overstate affordability.
- **Ambiguous applicant/identity** → stop and confirm; never precheck against the wrong profile.
- **Conflicting disclosed vs document figures** → cite both; do not resolve silently.
- **Missing/omitted escrow on a mortgage** → warn that housing cost is understated; state the gap.
- **Stale config or rate** → record the `config_version` and `as_of`; a precheck is not a rate lock.
- **Tool timeout** → return the metrics computed so far with a clear "incomplete" flag; no retry
  assumption.

## Output contract
1. **Summary** — applicant (masked), loan terms, proposed monthly payment, indicative band.
2. **Metrics** — front-end / back-end DTI and residual income, each with the figures behind them.
3. **Assumptions** — loan terms, escrow, residual basis (net vs gross), and the `config_version`.
4. **Stress scenarios** — rate-up and income-down cases with per-scenario metrics and band.
5. **Caveats** — disclosed vs verified data; indicative residual when net income is absent.
6. **Machine-readable** — metrics + assumptions + stress cases + `precheck_id` for downstream reuse.
7. **Standing disclaimer** — "Indicative affordability estimate only; not a credit decision,
   approval, denial, or adverse-action determination. Any lending decision requires human
   underwriting."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask applicant/account numbers (last 4). Minimize applicant data in output to what
supports the estimate. Fair-lending: inputs are income, expenses, debt, and product terms only — no
protected-class attributes or proxies. Retain the precheck + inputs summary + `config_version` per
records policy; log the read and any request for external delivery or a system write (each needs
human approval). Never exfiltrate applicant data.

## Gotchas
- **An estimate is not a decision.** "Within typical guidelines" is not an approval and "Outside
  typical guidelines" is not a denial — only a human underwriter, on verified data, decides.
- **Disclosed ≠ verified.** The precheck runs on what the applicant states; do not present it as a
  qualification. Income/asset verification is a separate, human-owned step.
- **Residual needs net income.** Without `net_monthly`, residual uses gross and overstates capacity;
  the warning and the assumptions block flag this.
- **Escrow matters.** A mortgage payment excluding taxes/insurance/HOA understates the true housing
  cost and flatters the DTI — always include escrow when known.
- **Thresholds are versioned, not personal.** Bands come from the approved config; never tune them to
  make a given applicant "fit".
- **No steering language.** Present affordability neutrally; do not encourage or discourage borrowing.
