---
name: fixed-income-pricing-reviewer
description: >-
  Review submitted fixed-income marks against independent prices, comparable spreads, prior
  marks, liquidity adjustments, and the assigned fair-value level; explain each pricing-exception
  check that flagged, attach source-linked evidence, and produce a review-ready pack with a
  suggested review priority. Use when a trading supervisor, valuation-control, or compliance
  analyst asks "is this bond mark reasonable", "why is this price flagged", "review these marks
  for pricing exceptions", "check this spread vs comparables", or needs cited evidence for an
  IPV / price-challenge queue. This skill evidences and prioritizes pricing exceptions only; it
  NEVER approves, overrides, restates, or books a mark, signs off IPV/price verification, issues
  a valuation determination, or declares a mismark — those remain human/authorized-system actions.
license: MIT
compatibility: Amazon Quick Desktop; requires OMS/EMS, market & reference data, independent-pricing/IPV, document-intelligence, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Capital Markets"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Capital Markets operations & compliance"
  aws-fsi-primary-user: "Trading supervisor / valuation or compliance analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Fixed-Income Pricing Reviewer

## Purpose and outcome
Given a set of submitted fixed-income marks and the market/reference context behind them,
compute a set of **explainable pricing-exception checks** (mark vs independent price, spread
vs comparables, unexplained day-over-day move, price staleness, liquidity-adjustment
plausibility, fair-value-level consistency, and comparable-support depth), explain in plain
language why each flagged, attach cited evidence to each, and produce a review-ready pack with
a **suggested review priority** per instrument and overall. A successful output lets a
valuation-control or supervisory reviewer see exactly which marks warrant challenge and why —
the price challenge, any override, the IPV sign-off, and the booked mark all remain human.

## Use when
- "Is this bond mark reasonable / why is this price flagged?"
- "Review today's marks for pricing exceptions and give me the evidence."
- "Check this instrument's spread against its comparables."
- "Which of these illiquid marks look stale or off-market?"
- A reviewer needs a consistent, cited pricing-exception write-up for an IPV or
  price-challenge queue.

## Do not use
- The user wants a **valuation determination**, a **price approval/override**, an **IPV
  sign-off**, a booked/restated mark, or a declared "mismark" → out of scope. Provide cited
  exceptions and route to the human valuation-control / IPV function or the pricing committee.
- Broader **valuation methodology / hierarchy / independent-price-verification governance**
  review (methods, model inputs, uncertainty, overrides) → `valuation-reviewer`.
- The pricing **model or curve methodology** itself needs independent validation →
  `model-validation-assistant`.
- The concern is **market-risk limits / VaR / stress impact**, not mark correctness →
  `market-risk-limit-monitor`.
- Plain-English **explanation of a trade confirmation** with no exception question →
  `trade-confirmation-explainer`.
- The mark pattern suggests possible **manipulation or misconduct** (e.g., marking to hit a
  P&L target) → triage/investigate via `surveillance-alert-triager` →
  `market-surveillance-alert-investigator`; if it concerns trader **communications**, route to
  `communications-compliance-reviewer`. This skill does not adjudicate conduct.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a pricing-review pack
with a durable `review_id`; downstream valuation, model-validation, and surveillance work
consumes it. It must not duplicate their determination, sign-off, or disposition steps.

## Inputs and prerequisites
- The **focal instruments** under review (`focal_instrument_ids`) and the marks file with, per
  instrument: submitted price, prior price, independent price (and its prior), quoted bid/ask,
  applied liquidity adjustment, yield and benchmark yield, comparables (spreads), assigned
  fair-value level, input observability, and source timestamps. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to OMS/EMS marks, independent-pricing/IPV, and market & reference data; the
  approved, versioned thresholds/config (see [references/domain-rules.md](references/domain-rules.md)).
- The instrument identity confirmed (ISIN/CUSIP, masked in output). Do not review the wrong line.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The independent/IPV price is the
challenge reference; comparables and the benchmark curve corroborate; the submitted mark is the
subject under review, never the authority for its own correctness. Cite every flagged check to
a specific instrument/source row and the as-of date.

## Workflow
1. **Scope & confirm** — confirm the focal instruments and the as-of date; load marks and
   context; validate with `validate_input`. Heed evaluability warnings (a check with missing
   inputs is reported `not_evaluable`, never silently passed).
2. **Compute checks (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute the
   configured checks per focal instrument. Each check returns a flagged/not-flagged result, a
   plain-language reason, and the evidence rows behind it. Checks are **explainable**, not a
   black-box pricing score.
3. **Assemble evidence** — for each flagged check attach the specific prices/spreads/dates and
   the reference it deviates from, with citations.
4. **Suggest priority** — map each instrument's flagged-check set to a priority band
   (Informational / Review / Elevated) per the configured, documented mapping, and take the
   overall band as the highest across focal instruments. This is a triage suggestion for a
   human, explicitly **not** a valuation determination or price approval.
5. **Write the pack** — plain-language explanation per flagged check + the evidence + the
   suggested priority + explicit benign explanations and not-evaluable checks to consider.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every flagged check has evidence + citation, the per-instrument
and overall priority map deterministically from the flagged sets, no
determination/approval/mark-action language is present, the standing disclaimer is included, and
benign-explanation prompts are present when any check flagged. Fail closed on any miss.

## Human approval
`external-delivery`: human review required before the pack is sent onward or written to a case /
system of record (IPV queue, price-challenge log). No approval is needed for the reviewer's own
read. The skill never approves, overrides, restates, or books a mark, and never signs off IPV.

## Failure handling
- **Missing independent price / comparables / prior mark** → mark the affected checks
  `not_evaluable`; do not infer a reference or overstate an exception.
- **Ambiguous instrument identity** → stop and confirm; never review the wrong line.
- **Stale vs. missing timestamps** → distinguish a stale *vendor feed* from a stale *trader
  mark*; cite the timestamps rather than concluding which is stale.
- **Conflicting sources** (two vendors, vendor vs broker quote) → cite both; do not resolve
  silently or pick a "winner".
- **Tool timeout / large book** → return the instruments reviewed so far with a clear
  "incomplete" flag; page the book into resumable stages.

## Output contract
1. **Summary** — as-of date, focal instrument count, overall suggested priority band.
2. **Per instrument** — instrument (masked identifier), each flagged check with its
   plain-language reason, evidence rows (cited), the reference it deviates from, and the
   instrument's suggested priority.
3. **Consider (benign explanations)** — explicit alternatives (issuer news, curve shift not yet
   in comparables, approved liquidity/model reserve, stale vendor feed) so the reviewer weighs
   both sides before challenging.
4. **Not-evaluable checks / data gaps** — which checks could not run and why.
5. **Machine-readable** — checks + evidence + `review_id` for downstream skills.
6. **Standing disclaimer** — "Pricing-review evidence only; not a valuation determination or
   price approval. No mark has been changed, approved, or booked."
See [references/controls.md](references/controls.md).

## Privacy and records
Marks, positions, and counterparty context are **Highly Confidential**; treat any embedded
account/holder identifiers as NPI/PII and mask instrument identifiers to the last 4. Minimize
data in the output to what evidences a flagged check. Retain the review + citations + config
version per records policy; log the read and any external-delivery approval. Never exfiltrate
marks or positions.

## Gotchas
- **A flagged check is not a mismark.** Flagged checks justify *review priority* and a human
  challenge, never a conclusion that the mark is wrong, right, or "fair value".
- **Independent ≠ correct.** The independent/vendor price can itself be stale or thin; a
  deviation is a prompt to investigate, not proof the trader mark is off. Cite timestamps.
- **Illiquid lines legitimately diverge.** Wide bid-ask and documented liquidity/model reserves
  can explain a level; the benign-explanation prompts exist for this reason.
- **Fair-value level is about input observability, not price size.** The level-consistency check
  compares the assigned level to documented input observability, not to how large the mark is.
- **Do not tune thresholds to a desk or trader.** Thresholds come from the approved, versioned
  config, not from guessing what is "normal" for this book.
- **Describe patterns factually.** Never assert intent (e.g., "marking to hit P&L"); that is a
  conduct determination for surveillance and a human, not for this skill.
