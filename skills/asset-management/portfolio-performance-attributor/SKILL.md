---
name: portfolio-performance-attributor
description: Legacy single-period Brinson; explicit multiplicative currency, parallel
  duration/convexity, supplied factor and chronological linking methods, retained
  residuals and engine-result challenge. Draft-only; use explicit extension and detached
  source validation.
license: MIT
compatibility: Python 3.10+ standard-library offline supplied-record review. Production
  market data, engines, model registries and approval services require separately
  provisioned institution-approved integrations.
metadata:
  aws-fsi-category: Asset Management
  aws-fsi-skill-type: Artifact-creation skills
  aws-fsi-risk-tier: R2
  aws-fsi-archetype: Draft & package
  aws-fsi-agent-pattern: Interactive production copilot
  aws-fsi-delivery-wave: Wave 2 - analytical production
  aws-fsi-action-mode: Draft-only; no system-of-record change
  aws-fsi-scheduled-agent: 'no'
  aws-fsi-baseline-status: existing-updated
  aws-fsi-human-approval: external-delivery
  aws-fsi-data-classification: Highly Confidential (MNPI / client-confidential)
  aws-fsi-jurisdictions: US (default); configure additional jurisdiction packs per
    deployment
  aws-fsi-owner: Asset Management investment & product
  aws-fsi-primary-user: Performance analyst / portfolio manager
  aws-fsi-version: 0.3.0
  aws-fsi-recertification-date: '2027-09-20'
---

# Performance Attribution Builder

## Purpose and outcome
Turn a portfolio, its benchmark, and a segmented set of period returns into ONE **source-linked
performance-attribution draft**. For a single closed period the skill decomposes the active return
(`portfolio return - benchmark return`) into **allocation**, **selection**, **interaction**, and
**currency** effects per segment using arithmetic Brinson-Fachler, rolls the effects up by currency,
reconciles the bottom-up portfolio and benchmark returns to the **official book-of-record returns**,
runs deterministic QA tie-outs, documents the methodology and versions, and lists open items — every
asserted figure carries a citation and every attributed segment ties out. The outcome is an
attribution a human can review and route: a rendered analysis from
[assets/output-template.md](assets/output-template.md) plus a machine-readable manifest. The skill
**decomposes and cites** realized return; it does not advise, make a performance claim, conclude, or
deliver.

## Use when
- "Build / refresh the performance attribution for this portfolio vs its benchmark for the period."
- "What drove active return — allocation vs selection vs currency?"
- "Decompose the excess return by sector and by currency, with citations."
- "Reconcile the attribution to the official portfolio and benchmark returns and show the residual."
- "QA this attribution — do the effects tie out to active return and to the book of record?"

## Do not use
- **Investment advice, a recommendation, or a suitability view** on what to buy/sell/reweight →
  refuse; that is the portfolio manager's / licensed advisor's decision.
- **Forward-looking or guaranteed-performance claims**, or **GIPS-compliance** assertions → refuse;
  attribution is ex-post, and GIPS compliance is a firm-wide claim; independent verification is recommended, not required.
- **Estimating a risk model or unsupported linking convention** → the quant / performance-measurement team. Supplied factor and chronological linking reviews use the explicit specialist extension below.
- **Writing the performance commentary** → `investment-commentary-builder`; **fact sheet** →
  `fund-fact-sheet-builder`; **IC pack** → `investment-committee-memo-builder`; **client review
  pack** → `client-review-preparer`.
- **Portfolio positioning/exposure analysis** → `portfolio-exposure-analyzer`; **holdings
  summary** → `portfolio-holdings-summarizer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Building the attribution is deliberately
separated from writing the narrative, from assembling a client/committee deliverable, and from the
methodology sign-off and compliance/marketing review (distinct controls, accountability, and
reliance). This skill emits a durable `attribution_id` + cited manifest and hands off to
`investment-commentary-builder`, `fund-fact-sheet-builder`, `investment-committee-memo-builder`, and
`client-review-preparer`; it must not perform their work, advise, or deliver.

## Inputs and prerequisites
- The intake bundle: `model` (arithmetic Brinson-Fachler), `attribution_id`, `period{from,to}`,
  `portfolio_id`, `benchmark_id`, `base_currency`, versioned `config` (reconciliation / weight /
  official tolerances), optional `official_returns{portfolio,benchmark}`, `required_approvals`,
  recorded `approvals`, and the `segments` — each with `segment`, `currency`, `weight_port`,
  `weight_bench`, `local_return_port`, `local_return_bench`, `currency_return`, and `source_ref`.
  Schema and required fields: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the performance/risk system (book of record), PMS/accounting (weights,
  classification), and market/index data (benchmark segment returns, FX). No figure is fabricated:
  a segment missing a return becomes `needs-data` and its weight is unattributed.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The performance/risk system is the system
of record for realized returns (the attribution reconciles to its official figures); PMS/accounting
is the authority on weights and classification; market/index data on benchmark segment returns and
FX. Cite every asserted figure as `{system}:{ref}@{date}`. The `model`, tolerances, and template are
**versioned contracts**.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm the model is supported and structure is
   sound; surface data gaps (segments missing returns, weights not summing to ~1.0, non-base
   currency with no currency return, no official returns) as warnings/open items.
2. **Build the attribution (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): compute the Brinson-
   Fachler allocation/selection/interaction effects and the currency effect per segment, the effect
   totals, and the currency roll-up. Rules: [references/domain-rules.md](references/domain-rules.md).
3. **Reconcile** — tie the effects to the active return, reconcile the bottom-up portfolio and
   benchmark returns to the official book-of-record returns within tolerance, and check weight
   coverage; every break is an open item, never silently accepted.
4. **Render the analysis** — populate [assets/output-template.md](assets/output-template.md) from the
   manifest; every segment row carries its citation and ties out.
5. **Compile open items** — everything not clean (missing returns, currency-return-zero,
   unreconciled effects, official-return breaks, weight-sum issues, outstanding approvals) becomes an
   explicit open item. Do not silently drop, infer, or steer.
6. **Mark draft & hand off** — set `build_status: draft-attribution`, record that human approval is
   required before delivery, and route to the downstream drafting skills. Never advise, claim
   performance, conclude, or send.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after. The
output check enforces: all required template sections present; every segment row cited and every
attributed segment tied out (`allocation + selection + interaction + currency == total`); the effect
totals sum to the attributed active return and `active_return == portfolio_return - benchmark_return`
(no unsupported claims); approvals recorded with role/date/citation and delivery approval flagged; no
recommendation/advice, forward-looking/guaranteed-performance, GIPS-compliance, unsubstantiated-
marketing, or send/deliver language; `build_status` is `draft-attribution`; standing note present.
Fail closed on any miss.

## Human approval
`external-delivery`. This skill produces a **draft** attribution for internal review. A human must
review and approve before it is used externally, in marketing/advertising (SEC Marketing Rule), in a
client report, or treated as a system-of-record change. The methodology sign-off, the
compliance/marketing review, and external delivery are separate, human-owned steps — this skill
neither performs nor pre-empts them.

## Failure handling
- **Missing segment return** → segment `needs-data`; its weight is unattributed; missing-return open
  item; never fabricated.
- **Non-base currency with `currency_return` 0** → open item to confirm hedged or supply the period
  currency return; never assumed.
- **Effects do not tie to active return** → report the residual and raise an `unreconciled-effects`
  open item; do not present a decomposition that does not reconcile.
- **Bottom-up return != official book of record** → `official-return-break` open item with the
  residual; reconcile before use.
- **Weights do not sum to ~1.0** → weight-sum open item to confirm cash/residual treatment or
  benchmark coverage.
- **Unsupported model** → fail closed. The no-extension engine implements arithmetic Brinson-Fachler; select the explicit specialist extension for documented supplied-factor/linking methods. Other models require the quant team.
- **Unresolvable data / tool timeout** → return the partial attribution with an explicit incomplete
  flag and the open-items list; no retry assumption.

## Output contract
See [references/controls.md](references/controls.md) and
[assets/output-template.md](assets/output-template.md).
1. **Rendered analysis** — the template sections (attribution summary, portfolio/benchmark, segment
   attribution, effect totals, currency attribution, reconciliation, methodology, QA checks, open
   items, approvals, source index) populated with cited content.
2. **Machine-readable manifest** — `attribution_id`, per-segment effects with citations, effect
   totals, currency roll-up, reconciliation (effects tie-out + official book-of-record + weight
   coverage), methodology + versions, QA checks, approvals (recorded/outstanding), open items, source
   index, `build_status` (`draft-attribution`), and `human_approval_required_before_delivery: true`.
3. **Open-items list** — every missing/currency/unreconciled/break/weight/outstanding item with a
   required human action.
4. **Standing note** — "Draft performance-attribution analysis for human review only. It is not
   investment advice and not a recommendation; it makes no forward-looking or guaranteed-performance
   claim and asserts no GIPS compliance; the effects are an ex-post decomposition of realized return,
   and this draft has not been reviewed, approved, or delivered."

## Privacy and records
**Highly Confidential — MNPI / client-confidential.** Holdings, weights, and returns can be client-
or composite-confidential and potentially price-sensitive; enforce need-to-know and mask approver and
internal identifiers in output. Retain the attribution manifest, citations, and config/template
versions per the firm's performance-recordkeeping and (where applicable) GIPS/marketing
recordkeeping policy; log the analyst identity on every read and build. Data stays within the
deployment's residency boundary.

## Gotchas
- **Attribution != advice or a forecast.** The effects explain what *did* happen to realized return;
  they are not a recommendation and say nothing about future returns. Any "will outperform" /
  "guaranteed" / "buy" language is prohibited.
- **Overweight/underweight is a fact, not a rating.** "The portfolio was overweight EU equities" is a
  factual description of positioning; "we should overweight EU equities" is advice and is refused.
- **The effects must reconcile.** Allocation + selection + interaction + currency must equal the
  active return, and the bottom-up return must tie to the official book of record; an unreconciled
  decomposition is an open item, not a result.
- **A missing return is not a zero.** A segment without a return is `needs-data` and its weight is
  unattributed — never fill it with an assumed return to make the table complete.
- **GIPS compliance is not ours to claim.** GIPS compliance is a firm-wide, independently verified
  presentation claim; this skill never asserts it.
- **Explicit method selection.** The original engine uses single-period arithmetic Brinson-Fachler. The specialist extension adds only its documented supplied-factor and chronological linking conventions; it does not estimate a risk model.
- **Versioned contracts.** Record `config_version`, the model, tolerances, and template version on
  the manifest so the attribution is reproducible and reviewable.

## Phase 1 executable boundary

Read [the bounded offline contract](references/phase1-contract.md) before running the scripts or relying on a handoff. It states required input evidence, unavailable cases and source-bound validation. Enterprise connectors and review queues described above are deployment interfaces, not implemented integrations.

## Phase 1 support boundary

Single-period arithmetic Brinson-style supplied-return analysis; additive FX approximation

This package performs only its documented local supplied-input operations. Live source access, authenticated permissions, production engines and professional acceptance are separate deployment requirements. Generated resources are pinned in `references/package-manifest.json`; maintain the canonical shared source. Legacy identifiers resolve through the repository migration registry.

## Phase 4 specialist extension

Select `extension: specialist-attribution` explicitly for the bounded specialist method. Read [the Phase 4 contract](references/phase4-method.md), then use the existing input/calculation/output commands with a detached original input. The earlier schema remains available when `extension` is omitted. Unknown extensions fail. Use [the specialist review template](assets/phase4-template.md) and retain every residual, source gap and unsupported method. Source-linked calculations do not establish professional acceptance or execution authority.
