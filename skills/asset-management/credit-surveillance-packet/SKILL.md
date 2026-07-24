---
name: credit-surveillance-packet
description: >-
  Assemble a draft credit surveillance packet for a single issuer under ongoing credit review:
  gather and tie out leverage (gross/net debt-to-EBITDA), coverage (interest coverage, a
  fixed-charge proxy), liquidity (cash + undrawn revolver and near-term maturity coverage), the
  maturity wall, current-vs-prior credit spreads, reported agency ratings and outlook, and
  covenant-change flags — each item cited to an approved source, with period-over-period change
  tracking. Use when a credit research analyst asks to build, refresh, or tie out an issuer
  surveillance packet or credit update from filings, market data, and rating-agency inputs.
  HARD BOUNDARY: draft-only — it never assigns or derives a credit rating (it reports agency
  ratings only), never forms, alters, or restates an investment thesis, and never recommends or
  changes a position or trade. It flags that a covenant changed but hands off covenant-term
  extraction and interpretation to credit-terms-covenant-extractor; it gives no investment advice.
license: MIT
compatibility: Amazon Quick Desktop; requires filings/document-intelligence, credit-agreement (controlled documents), rating-agency, market-data, deterministic-computation (credit spreading), reference-data/security-master, and controlled-template MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Credit research analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Credit Surveillance Packet

## Purpose and outcome
Assemble a **draft** credit surveillance packet for a single issuer under ongoing review from
approved inputs — filings, the credit agreement, rating-agency reports, and market data. The
outcome is a controlled, fully-cited packet that **computes and ties out** the core credit
metrics (leverage, coverage, liquidity), lays out the maturity wall, tracks the credit spread
and reported ratings against the prior period, and **flags** covenant changes for handoff. The
deliverable is a surveillance artifact for human review; the rating, the thesis, and the
position stay with the humans who own them.

## Use when
- "Build the credit surveillance packet for [issuer]: leverage, coverage, liquidity, maturity
  wall, spreads, ratings, and covenant changes with citations."
- "Refresh the issuer packet and tie net leverage and interest coverage out to the 10-Q, with
  the change vs last quarter."
- "Summarize the maturity wall and near-term liquidity coverage for this credit."
- "Pull the current spread and the reported agency rating/outlook vs prior, with sources."

## Do not use
- **Assigning or deriving a credit rating** ("rate this issuer B+") → refuse; ratings are
  reported from the agency source only. `rating_action` stays `reported-only`.
- **Forming, changing, or restating the investment thesis** → refuse; the analyst/PM owns the
  thesis. `thesis_action` stays `unchanged`. Ongoing thesis tracking → `investment-thesis-monitor`.
- **Recommending or changing a position/trade** ("should we buy/add/trim") → refuse; a human
  PM/desk decides and it is a prohibited action. `position_action` stays `none`.
- **Extracting covenant terms or determining compliance/headroom** → `credit-terms-covenant-extractor`
  for terms; a human for any compliance determination. This skill flags only *that* a covenant changed.
- **Personalized investment advice** → refuse.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream skills ingest and reconcile the
raw feeds; this skill gathers and ties them into a packet keyed by `issuer_id` + `as_of`. The
mandated downstream handoff is `credit-terms-covenant-extractor` for covenant-term detail; the
rating, thesis, and position are **human** handoffs. Duplicate execution is prevented by scope:
surveillance never extracts covenant terms, monitors the thesis, or decides a rating/position.

## Inputs and prerequisites
- A surveillance build request: `issuer` metadata (with `as_of` and `prior_as_of`); `sources[]`
  with type + approval flags; `financials` (EBITDA, gross debt, cash, interest expense, capex,
  undrawn revolver, and any analyst/vendor-stated ratios to tie out); optional `prior_financials`
  for change tracking; `maturities[]`; `spreads` (current/prior, **approved market** source);
  `ratings[]` (agency + outlook + prior, **approved rating-agency** source); `covenants[]`
  (change flags); `approvals`. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to filings, the credit agreement, rating-agency reports, market data, the
  deterministic spreading service, reference data, and the versioned template/metric config.
- **Data-quality minimums:** non-zero EBITDA and interest expense; every material claim carries a
  `source_id`; market/rating sources must be **approved**.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **filing** is the system of record
for the raw financials — ratios tie out to it and are never restated looser. The **credit
agreement** is authoritative for the maturity schedule and for which covenant items changed.
Ratings always cite the **rating-agency** source (never an internal derivation). Cite every
figure and claim `{system}:{ref}@{as-of/version}`; when sources conflict, cite all and surface it.

## Workflow
1. **Validate & normalize** — run `validate_input`; on missing/unapproved inputs stop at
   `needs-data` and name the producing skill/human. Do not draft on a malformed request.
2. **Compute & tie out (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): compute gross/net
   leverage, interest coverage, the fixed-charge proxy, total liquidity, and near-term maturity
   coverage; reconcile to any stated values; block on a tie-out break.
3. **Track change vs prior** — compute leverage/coverage deltas, spread widening/tightening, and
   reported rating/outlook changes; surface deterioration as **disclosure** flags, never as a view.
4. **Report ratings, never assign** — report agency rating + outlook (and prior); set no internal
   rating and express no opinion on the level.
5. **Flag covenant changes** — list which covenant items changed and route term detail to
   `credit-terms-covenant-extractor`; do not interpret compliance or headroom.
6. **Assemble the packet** — populate the nine required template sections
   ([assets/output-template.md](assets/output-template.md)) from cited inputs only, with a
   traceability appendix, a change log, and an approvals block. Leave the action fields neutral.
7. **Validate output** — run `validate_output`; fail closed on any miss.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output gate is **independent** (it re-derives findings from the packet record): template
fidelity (all nine sections), no unsupported/unapproved claims, metric tie-outs, neutral action
fields (`rating_action == reported-only`, `position_action == none`, `thesis_action == unchanged`),
recorded `preparer`+`reviewer` approvals, no prohibited language, and the standing draft-only
note. Correct and re-run until clean or stop at `needs-data`.

## Human approval
`external-delivery`. A human must review the draft and **record** the preparer and reviewer
sign-offs before the packet is delivered to a PM/desk/committee or written to a system of record.
The rating, thesis, and position are set by humans, never by this skill. This skill gathers,
computes, and packages — it never assigns, decides, delivers, or files. See
[references/controls.md](references/controls.md).

## Failure handling
- **Missing / unapproved input** → `needs-data`; list exactly what is missing and the producing
  skill/human; never invent a figure, spread, or rating to fill the gap.
- **Tie-out break** → block; surface the stated-vs-recomputed discrepancy rather than restating.
- **Undefined ratio** (EBITDA or interest expense is 0) → block at input; do not divide by zero.
- **Conflicting sources** → cite all and surface in the evidence section; do not silently pick one.
- **Covenant change with no term source** → flag the change and route to the extractor; do not
  guess the terms or compliance.
- **Tool timeout** → return the partial draft with an explicit incomplete flag; assume no retry
  and no step-up authorization.

## Output contract
1. **Draft packet** — the nine required sections, each cited to its source(s).
2. **Metrics + change log** — computed ratios/liquidity and period-over-period deltas.
3. **Tie-out results** — machine-readable, with any break flagged.
4. **Covenant-change flags** — changed items with the `credit-terms-covenant-extractor` handoff.
5. **Traceability appendix** — claim → citation → as-of/version → approved.
6. **Approvals block** — `preparer`/`reviewer` status; action fields neutral
   (`rating_action: reported-only`, `position_action: none`, `thesis_action: unchanged`).
7. **needs-data list** — anything blocking a clean draft.
8. **Standing note** — "Draft credit surveillance packet for human review. It reports agency
   ratings but assigns none, forms or changes no investment thesis, recommends no position or
   trade, and has not been circulated, sent, or submitted."

## Privacy and records
**Highly Confidential (MNPI / client-confidential).** Issuer research frequently touches MNPI:
restrict to the entitled research team, honor information-barrier / wall-crossing controls, and
never disclose surveillance findings outside the entitled group. Retain the draft, traceability
appendix, citations, and template/metric-config versions with the issuer record; log every source
read and draft generation with the preparer identity for audit and recertification.

## Gotchas
- **Report ≠ assign.** The packet reports the agency rating and any change; it never sets an
  internal rating or opines on the level. `rating_action` staying `reported-only` is the control.
- **Surface ≠ recommend.** Rising leverage, compressing coverage, and a widening spread are
  **disclosed**; the packet never turns them into a buy/sell/thesis view.
- **Tie out, don't restate.** If a stated ratio and the computation disagree, the computation
  governs — fix the packet or disclose the adjustment with a citation.
- **Flag the covenant, hand off the terms.** Naming *that* a covenant changed is in scope;
  extracting terms or judging compliance is `credit-terms-covenant-extractor` and a human.
- **Approved ≠ present.** A market/rating source that exists but is not marked approved is treated
  as unapproved and its claims are blocked.
- **No selling language.** Guarantees, "risk-free", and trade calls fail the output screen; present
  balanced, cited evidence for the analyst instead.
