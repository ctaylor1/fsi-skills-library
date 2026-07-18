---
name: earnings-results-analyzer
description: >-
  Produce a post-earnings beat/miss analysis for a covered company: compare reported results
  against consensus/estimates, classify each metric line (Beat / In-line / Miss), classify
  guidance changes (Raised / Maintained / Lowered / Withdrawn), surface factual transcript
  language changes, and assemble source-linked evidence and thesis-impact considerations for
  an analyst. Use when an equity-research or portfolio analyst asks "how did the print look
  versus consensus", "did they beat or miss", "what changed in guidance / on the call", or
  needs a cited earnings read after a company reports. This skill classifies the print
  factually and cites evidence; it NEVER issues an investment rating, a price target, or a
  buy/sell/hold recommendation, NEVER gives personalized investment advice, and NEVER
  publishes a note externally — those are human/licensed-analyst and supervisory actions.
license: MIT
compatibility: Amazon Quick Desktop; requires market/financial-data, filings/document-intelligence, research-corpus/estimates, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Investment Banking & Research"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Investment Banking / Research"
  aws-fsi-primary-user: "Equity-research analyst / portfolio analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Earnings Results Analyzer

## Purpose and outcome
Given a company's reported earnings and the corresponding estimates/consensus, compute an
**explainable beat/miss analysis**: classify each reported metric against its estimate,
classify each guidance change, surface the factual language changes on the call, attach
evidence to every finding, and produce a cited pack with a deterministic **overall result
classification** (Beat / In-line / Mixed / Miss / Undetermined) plus thesis-impact
considerations. A successful output lets an analyst understand exactly how the print
compared to expectations and what changed — the investment view, rating, and any published
note remain the human analyst's, under supervisory/compliance review.

## Use when
- "How did the quarter look versus consensus — beat or miss?"
- "What changed in guidance / on the earnings call this quarter?"
- "Give me a cited read of the print with the surprise on each line."
- An analyst needs a consistent, evidenced earnings write-up to attach to a model update or
  a coverage/marketing meeting.

## Do not use
- The user wants an **investment recommendation, rating, price target, or personalized
  advice** ("should I buy this?", "what's your rating/PT?") → out of scope and prohibited at
  this tier. Provide the factual analysis and route the view to the human analyst / portfolio
  manager (see below).
- The user wants to **publish a research note** or send the read to clients → external
  delivery requires human (supervisory-analyst / compliance) review; this skill drafts
  analysis, it does not distribute.
- **Build or refresh the model itself** (three-statement, DCF, comps, LBO) → route to the
  modeling skills in [references/handoffs.md](references/handoffs.md).
- **Trade, rebalance, or move money** on the read → out of scope entirely; route to the
  human and the appropriate authorized process.
- A general company explainer with no earnings-vs-estimates question → use a coverage/profile
  skill instead.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a cited analysis pack
with a durable `analysis_id`; downstream modeling, memo, and monitoring skills consume it.
It must not duplicate their model builds, nor cross into rating/recommendation territory,
which is a human/licensed-analyst decision.

## Inputs and prerequisites
- **Ticker / company** and the **reporting period** (e.g., "Q2 2026").
- **Reported metrics** with, per line: the reported actual, the comparison estimate/consensus,
  a unit, a `direction` (`higher_is_better` / `lower_is_better`), a `headline` flag for the
  metrics that define the print (revenue, EPS), and a source reference for both the actual and
  the estimate. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- **Guidance items** (optional): prior and new ranges (or a `withdrawn` flag) with a source
  reference, to classify the guidance direction.
- **Transcript language changes** (optional): topic, prior language, current language, and a
  source reference, to surface factual commentary changes.
- Read access to filings/press-release, transcript, and estimates sources; approved
  tolerances/config (see [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **filed release/8-K/10-Q** is
the position of record for reported actuals and guidance; the **transcript** is the source
for management commentary; the **estimates/consensus** provider supplies the comparison
baseline; the **prior model/note** supplies prior guidance and thesis context. Cite every
finding's evidence to a source reference; never substitute a media summary for the filing.

## Workflow
1. **Scope & validate** — confirm the ticker, period, and estimate source; load the reported
   metrics, guidance, and transcript changes; validate with `validate_input`. Fail closed on
   structural errors; note which lines are not evaluable (no estimate).
2. **Classify the print (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute the
   per-metric surprise and Beat / In-line / Miss classification (with `lower_is_better`
   inversion), classify each guidance item, and surface transcript language changes. Each
   finding returns its evidence and citation. Classifications are **explainable**, not an
   opaque score.
3. **Assemble evidence** — for each finding, attach the specific actual/estimate/guidance
   references it rests on.
4. **Map the overall result** — map the headline metric classifications (with the headline
   guidance cut) to an overall result band per the configured, documented mapping. This is a
   factual description of the print, explicitly **not** a rating or a call.
5. **Write the pack** — plain-language read per finding + the evidence + the overall result +
   thesis-impact considerations that invite the analyst to weigh quality-of-beat, guidance vs.
   expectations, and driver durability before forming any (human) view.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every evaluable metric finding cites both its actual and
estimate; every evaluable guidance finding is cited; the overall result maps deterministically
from the findings; no rating/price-target/recommendation/advice language is present; the
standing disclaimer is included; and thesis considerations are present when findings exist.
Fail closed on any miss.

## Human approval
`external-delivery`: human review (analyst plus supervisory-analyst / compliance where the
firm requires it) is required before the analysis is delivered to a client, published as a
note, or written to a system of record. No approval is needed for the analyst's own read. The
skill never issues a rating, sets a target, publishes, or trades.

## Failure handling
- **No estimate for a metric** → report the line as `not_evaluable`; do not invent a beat/miss.
- **No headline metric flagged** → overall result is `Undetermined`; say so rather than guess.
- **Guidance without a new range** (and not marked withdrawn) → direction not evaluable; report
  the reported range factually without a Raised/Lowered label.
- **Transcript change without a prior baseline** → surface as a new disclosure, not a "change".
- **Stale/conflicting sources** (filing vs. transcript vs. estimate) → cite both; do not resolve
  silently.
- **Ambiguous ticker/period** → stop and confirm; never analyze the wrong company or quarter.
- **Tool timeout** → return the findings computed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — ticker/company, period, estimate source, count of beats/misses on headline
   metrics, and the overall result band.
2. **Metric findings** — per line: metric, actual, estimate, unit, surprise %, classification,
   and the cited actual + estimate evidence.
3. **Guidance findings** — per item: prior vs. new midpoint, direction classification, and the
   cited evidence.
4. **Transcript observations** — factual language changes and new disclosures, cited; not scored.
5. **Not-evaluable** — lines/guidance/transcript items that could not be classified, with why.
6. **Thesis considerations** — factual angles to weigh (quality-of-beat, guidance vs.
   expectations, driver durability); prompts for the human analyst, not a recommendation.
7. **Machine-readable** — findings + evidence + `analysis_id` for downstream skills.
8. **Standing disclaimer** — "Factual earnings analysis and cited evidence only; not investment
   advice, a rating, or a price target. No recommendation to buy, sell, or hold has been made."
See [references/controls.md](references/controls.md).

## Privacy and records
Treat draft estimates, pre-publication views, and any non-public detail as **Highly
Confidential (MNPI / client-confidential)**. Do not incorporate material non-public
information from outside the approved sources, and observe the firm's information-barrier and
quiet-period rules. Retain the analysis + citations + config version per records policy; log
the read and any external-delivery approval. Never exfiltrate draft research or client data.

## Gotchas
- **A classification is not a call.** A "Beat" or an "Elevated"-looking print justifies
  *analysis*, never a rating, price target, or recommendation — those are human, supervised
  decisions.
- **Headline vs. detail metrics**: the overall result is driven by the metrics flagged
  `headline` (revenue, EPS). Mis-flagging turns a detail line into the whole story; confirm the
  headline set against the config.
- **Direction sense matters**: expenses, net debt, and churn are `lower_is_better` — a figure
  *below* estimate is a beat. The engine inverts these; feeding the wrong direction flips the read.
- **Guidance beats the print**: a headline guidance cut prevents a clean "Beat" even when the
  quarter beat — markets trade the forward number. The mapping encodes this.
- **Quality of the beat**: one-offs (tax, FX, non-recurring items) and lower opex can drive a
  headline beat; the thesis considerations exist so the analyst weighs durability.
- **Estimate provenance**: consensus, in-house, and whisper numbers differ — record which
  estimate source the surprise is measured against; do not mix them silently.
- **MNPI / quiet period**: never fold in non-public inputs or breach information barriers to
  "improve" the read.
