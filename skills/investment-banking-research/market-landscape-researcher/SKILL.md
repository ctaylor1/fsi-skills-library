---
name: market-landscape-researcher
description: >-
  Map an industry, sector, or investment theme end to end across eight dimensions — value
  chain, competitive landscape and concentration, customer/demand segments, regulation,
  technology shifts, unit economics, M&A and capital-markets activity, and strategic
  implications — with every finding tied to a cited, dated source and reproducible
  concentration (HHI/CR4), evidence-coverage, and completeness scorecards. Use when a banking
  or research analyst or strategist asks to "map the landscape", "research this
  industry/sector/theme", "who are the players and how concentrated is the market", or needs a
  source-linked landscape brief to seed a pitch, coverage note, comps set, or market-sizing
  model. HARD BOUNDARY: it researches and synthesizes cited evidence only — it NEVER issues
  investment advice, a buy/sell/hold recommendation, an analyst rating or price target, a
  personalized investment/legal/tax opinion, or a valuation conclusion, and it requires human
  review before external delivery.
license: MIT
compatibility: Amazon Quick Desktop; requires approved-source-retrieval (filings/research/deal data), document-intelligence, entity-resolution, CRM/data-room, and controlled-content MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Investment Banking & Research"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Domain workflow"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Investment Banking / Research"
  aws-fsi-primary-user: "Banking / research analyst or strategist"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Market Landscape Researcher

## Purpose and outcome
Given an industry, sector, or theme, produce a **source-linked landscape brief** that maps the
market across **eight dimensions** — value chain, competitors, customers, regulation,
technology, economics, transactions, and strategic implications — and attaches three
reproducible scorecards: **concentration** (CR4/CR8 and HHI over the named set),
**evidence coverage**, and **dimension completeness**. A successful output gives an analyst or
strategist a defensible, cited map of the market that seeds a pitch, coverage note, comps set,
or sizing model — while every conclusion, valuation, and investment call stays with a human.

## Use when
- "Map the landscape / competitive landscape for `<industry / sector / theme>`."
- "Research this industry — who are the players, how concentrated is it, what's the picture?"
- "Where does value sit in the value chain, and how is regulation/technology reshaping it?"
- An analyst needs a consistent, cited landscape section to feed a pitch, coverage, or model.

## Do not use
- The user wants **investment advice, a buy/sell/hold call, an analyst rating, or a price
  target** → out of scope; route to a **licensed research/investment professional** (see
  [references/handoffs.md](references/handoffs.md)). This skill never advises or rates.
- **Market sizing to a number** (TAM/SAM/SOM with methods/ranges) → `market-sizing-builder`.
- **Valuation / forecasting** → the modeling skills (this skill hands them context only).
- **A single-company profile** → `company-profile-builder`; **comparable-company multiples** →
  `comps-analysis-builder`; **an initiating-coverage thesis on one name** →
  `coverage-initiation-researcher`; **the client deck** → `investment-banking-pitch-builder`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a durable
`landscape_id` brief; downstream sizing/profile/comps/coverage/pitch skills consume it rather
than re-researching the sector. It must not size, model, value, or make a call.

## Inputs and prerequisites
- The **theme/industry**, **geography**, and **as-of date**; the configured `config_version`.
- A **source list** (`sources[]`) with tier (1 filings/stats → 4 unverified) and dates, and a
  **named competitor share table** (`competitors[]`) reconciled to sources.
- **Findings** organized under the eight dimensions, each with a `source_id`. Schema and
  field rules: [scripts/validate_input.py](scripts/validate_input.py) and
  [references/source-map.md](references/source-map.md).
- Read access to approved-source retrieval, document intelligence, entity resolution, and
  (for internal drafts) CRM / data room. Versioned thresholds: [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Regulatory filings and official
statistics rank highest, then licensed research/deal data, then reputable press; company
marketing is lead-only and never the sole support for a load-bearing figure. Cite every finding
`{publisher}:{source_id}@{date}`; where sources disagree, cite both and state the range.

## Workflow
1. **Scope** — confirm the theme, geography, and `as_of`; agree the eight dimensions are in
   scope; load sources and the competitor share table; run
   [scripts/validate_input.py](scripts/validate_input.py) (fails closed on structure; warns on
   uncited findings, stale/tier-4 sources, and a large unattributed tail).
2. **Gather & attribute** — collect findings per dimension from the highest available tier;
   attach a `source_id` to each; reconcile competitor shares to their sources.
3. **Compute scorecards (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to resolve citations
   and compute concentration (CR4/CR8, HHI, market-structure band), evidence coverage, and
   dimension completeness.
4. **Synthesize** — write the plain-language brief per dimension, each finding cited; describe
   the concentration band **factually** (structure, not attractiveness); state ranges where
   sources disagree.
5. **Limitations & disclaimer** — add the limitations/uncertainty section and the standing
   research disclaimer; wall off any MNPI/client-confidential context from an external version.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check confirms: all eight dimensions present with cited findings; concentration
ties out to a deterministic recompute; **no investment-advice/rating/price-target language**;
the standing disclaimer is present; and a limitations section exists. Fail closed on any miss.

## Human approval
`external-delivery`: banker/analyst review required before the brief is sent to a client, added
to a pitch/coverage deliverable, or written to a system of record. No approval is needed for
the analyst's own internal read. The skill takes no action and makes no call.

## Failure handling
- **Missing dimension** → fail closed; do not deliver a partial map as complete.
- **Uncited / tier-4-only load-bearing figure** → flag and require a higher-tier source or drop
  the figure; never present it as established.
- **Conflicting sources** → cite both and report the range; do not silently pick one.
- **Stale sources** (older than `staleness_days`) → list them; refresh before external delivery.
- **Ambiguous entity** (name/ticker collision) → stop and resolve; never conflate two firms.
- **Tool timeout** → return the dimensions gathered so far with an explicit "incomplete" flag.

## Output contract
1. **Header** — theme, geography, `as_of`, `config_version`, `landscape_id`.
2. **Concentration** — CR4/CR8, HHI, market-structure band, named-share sum, unattributed tail.
3. **Eight dimensions** — per dimension, cited findings (`{publisher}:{source_id}@{date}`).
4. **Scorecards** — evidence coverage (cited %, sources by tier, stale list) and completeness.
5. **Limitations / uncertainty** — ranges, unattributed tail, stale/low-tier sources, as-of.
6. **Machine-readable** — the calculate core + `landscape_id` for downstream skills.
7. **Standing disclaimer** — "Market research for informational purposes only; not investment
   advice, a recommendation, or an offer to buy or sell any security."
See [references/controls.md](references/controls.md).

## Privacy and records
Highly Confidential (MNPI / client-confidential). Keep non-public deal context in the internal
draft only; wall it off from any externally delivered brief and label internal-only material.
Minimize client identifiers to what the analysis requires. Retain the brief + citations +
`config_version` per records policy; log the read and any external-delivery approval. Never
exfiltrate MNPI or client data.

## Gotchas
- **A map is not a call.** Concentration bands and coverage stats describe **structure and
  evidence**, never attractiveness — do not let them drift into a buy/sell view.
- **Do not fabricate an "Other" firm.** Concentration is computed over named firms; the
  unattributed tail is reported separately, not folded into a synthetic competitor.
- **HHI bands are antitrust descriptors**, not a competition-law opinion and not an investment
  view; keep the standard 1500/2500 thresholds from the versioned config.
- **Share estimates ≠ reported figures.** Label estimates, prefer tier-1 filings for
  load-bearing numbers, and state the range when trackers disagree.
- **MNPI discipline.** A landscape drawn partly from a live deal's data room is internal-only
  until the control room clears it — never let non-public context reach an external brief.
