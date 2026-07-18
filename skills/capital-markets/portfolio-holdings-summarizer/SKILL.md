---
name: portfolio-holdings-summarizer
description: >-
  Summarize a portfolio's holdings into a clear, source-linked overview — positions,
  weights, asset-class and sector mix, top holdings, income, and notable concentrations —
  from authoritative account/position data. Use when a retail investor or associate asks
  "what's in this portfolio", "summarize my holdings", "what are my biggest positions",
  or wants a plain-language snapshot of an account statement or position file. This skill
  is informational only: it does not give investment advice, recommend buys/sells, assess
  suitability, or judge whether the portfolio is "good" — route those to the appropriate
  analysis or advice-boundary skill.
license: MIT
compatibility: Amazon Quick Desktop; requires portfolio-accounting/custody or position-file access, market/reference-data, and document-intelligence MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Capital Markets"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R1"
  aws-fsi-archetype: "Explain & summarize"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 1 — stabilize existing"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-no-changes"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Capital Markets / brokerage operations"
  aws-fsi-primary-user: "Retail investor"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Portfolio Holdings Summarizer

## Purpose and outcome
Produce a faithful, plain-language summary of what a portfolio holds so the user can
understand its composition at a glance. A successful output lets the reader see their
positions, how the portfolio is allocated, its largest holdings and concentrations, and
income characteristics — every number traceable to a source line — **without** any
recommendation or judgment about what to do next.

## Use when
- "Summarize my holdings", "what's in this account", "what do I own".
- "What are my top 10 positions", "how am I allocated across asset classes/sectors".
- The user attaches a brokerage statement, position export, or custody file and wants a
  readable overview.
- An associate needs a clean holdings snapshot to attach to a review packet (delivery to a
  client requires human review — see Human approval).

## Do not use
- The user wants advice, a recommendation, or a buy/sell/rebalance suggestion → this is
  out of scope; do not answer it here.
- The user asks whether the portfolio is suitable, well-diversified, or risky in a
  personalized sense → route to `portfolio-risk-diversification-check` (educational,
  non-advice) and, for suitability, to `suitability-reg-bi-reviewer`.
- The user wants performance/attribution over time → `performance-attribution-builder`.
- The user wants to place or stage trades → not supported here (see `portfolio-rebalancing-assistant`, R4).

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). In short: this skill is often the
**upstream** snapshot for `portfolio-risk-diversification-check`, `client-review-preparer`,
and `portfolio-proposal-comparator`. It hands off the normalized holdings table + a durable
`snapshot_id`; it never performs the downstream analysis itself.

## Inputs and prerequisites
- Authoritative holdings for **one account/portfolio at a time**: instrument identifier
  (CUSIP/ISIN/ticker), description, quantity, price, market value, currency, asset class,
  and as-of date. See the input schema in [scripts/validate_input.py](scripts/validate_input.py).
- The **as-of date** and pricing source for every position. Reject a mixed-as-of file
  unless the user confirms a single reporting date.
- Read permission to the position source; market/reference data for classification when
  the file lacks asset-class/sector fields.

## Source hierarchy
Rank sources and cite every figure. See [references/source-map.md](references/source-map.md).
1. Books-and-records custody/portfolio-accounting position of record (highest).
2. Official brokerage statement for the stated period.
3. Reference/market data for classification and prices where the file is silent.
Never substitute a user assertion for the position of record; if they conflict, surface
the conflict and cite both.

## Workflow
1. **Identify scope** — confirm the single account and as-of date. If multiple accounts or
   dates are present, ask which one (do not silently merge).
2. **Normalize** — map each line to the holdings schema; resolve identifiers; attach the
   source citation (system + statement page/line) to each position.
3. **Compute the summary (deterministic)** — totals, per-position weight, asset-class and
   sector mix, top-N holdings, cash, and portfolio income yield where income data exists.
   These are descriptive arithmetic only; run
   [scripts/validate_output.py](scripts/validate_output.py) to confirm weights sum to 100%
   (± rounding) and every figure ties to a cited source.
4. **Write the summary** — lead with composition; state the as-of date and currency; list
   top holdings and any concentration ≥ the configured threshold (default 10% single
   issuer) as a neutral observation, not a warning to act on.
5. **Surface gaps** — unpriced lines, unclassified instruments, stale prices, or
   unresolved identifiers are listed explicitly rather than guessed.

## Validation loop
Run `validate_input` before summarizing and `validate_output` after. If weights don't tie,
a figure lacks a citation, or the output contains advice/recommendation language, **fix or
fail closed** — do not deliver an untied or advice-tainted summary.

## Human approval
None required for the user's own informational read. **Human review is required before the
summary is delivered externally** (e.g., an associate sending it to a client) or attached
to a system of record — `aws-fsi-human-approval: external-delivery`.

## Failure handling
- **Missing/stale prices or as-of date** → summarize what is priced, list the rest as
  "not valued", state staleness; never invent prices.
- **Ambiguous identity** (identifier not resolvable) → list the position as-is, flag
  "unresolved instrument", exclude from classification totals with a note.
- **Multiple accounts/dates** → stop and ask; do not merge.
- **Source conflict** → present both figures with citations; do not pick a winner.
- **Tool timeout / permission denial** → report partial results and the exact gap; no retry
  assumption.

## Output contract
1. **Header** — account label (masked), as-of date, base currency, total market value.
2. **Allocation** — asset-class and sector weights (table), cash %.
3. **Top holdings** — top-N by market value with weight and citation.
4. **Concentrations & notes** — issuer/sector concentrations above threshold (neutral),
   plus a **Data gaps** list.
5. **Machine-readable** — the normalized holdings table and computed metrics, tagged with a
   durable `snapshot_id` for downstream skills.
6. **Standing disclaimer** — "Informational summary only; not investment advice or a
   recommendation."
Every figure carries a source citation. See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask account numbers (show last 4). Do not transmit holdings outside the
approved environment. Retain the snapshot and its citations per records policy; log the
read and any external-delivery approval. See [references/controls.md](references/controls.md).

## Gotchas
- **Weights must tie to 100%** after rounding; a rounding remainder line is fine, a
  silent gap is not.
- **Multi-currency**: convert only with a cited FX rate and as-of; otherwise report per
  currency and label it.
- **Cash and money-market sweep** are holdings — include them, don't drop them.
- **Options/short positions** can have negative market value/notional; don't take absolute
  values silently when computing weights.
- **"Summarize" is not "assess"**: describing a 40% single-stock position is in scope;
  calling it "too risky" or "overweight" is advice and is out of scope.
