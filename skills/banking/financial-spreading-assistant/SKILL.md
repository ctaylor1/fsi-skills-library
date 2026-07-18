---
name: financial-spreading-assistant
description: >-
  Extract and spread borrower financial statements and tax returns into an approved bank
  template: classify each line item to a standard taxonomy, compute leverage, liquidity,
  coverage, and profitability ratios plus an operating cash-flow proxy, reconcile subtotals
  and statement tie-outs against the borrower's reported totals, and flag ambiguous mappings
  with source citations. Use when a commercial credit analyst or spreading team says "spread
  these financials", "normalize this balance sheet and income statement", "calculate the
  ratios / DSCR", or needs a source-linked, reproducible spread for a credit file. HARD
  BOUNDARY: this skill spreads and calculates only — it NEVER makes or implies a credit
  decision, credit rating, or eligibility determination, NEVER approves, declines, or
  recommends a facility, NEVER gives investment or tax advice, and NEVER writes a system of
  record; line items it cannot confidently classify are escalated to a human, not guessed.
license: MIT
compatibility: Amazon Quick Desktop; requires document-intelligence/OCR, approved spreading-template & taxonomy, deterministic-calculation, and loan-origination MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Banking"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Model & calculate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Banking product & credit operations"
  aws-fsi-primary-user: "Commercial credit analyst / spreading team"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Financial Spreading Assistant

## Purpose and outcome
Given a borrower's financial statements and/or tax returns and an approved spreading template,
produce a **deterministic, source-linked spread**: every raw line item classified to a standard
taxonomy, aggregated into balance-sheet and income-statement subtotals per period, with standard
**credit ratios** (leverage, liquidity, coverage, profitability), an **operating cash-flow
proxy**, an **as-reported vs. normalized** (analyst add-back) view, and **tie-outs** that
reconcile the spread to the borrower's own reported totals. A successful output is a spread a
credit officer can rely on to underwrite — figures tie, every mapping and adjustment is cited,
and anything the model could not confidently classify is flagged for a human. The spread is an
analytical artifact; the credit decision remains human.

## Use when
- "Spread these borrower financials / statements / tax returns into our template."
- "Normalize this balance sheet and income statement to our line-item taxonomy."
- "Calculate the leverage, current ratio, DSCR, and margins from these statements."
- "Build a two-year spread with the ratios and the year-over-year trend, cited to source."
- A spreading team needs a consistent, reproducible spread with statement tie-outs for a
  credit file.

## Do not use
- The user wants a **credit decision, rating, or eligibility call** ("do we approve?", "is the
  borrower creditworthy?", "what limit?") → out of scope; produce the spread and route the
  decision to a credit officer.
- The user wants the **credit write-up / memo** drafted from the spread → `credit-memo-drafter`.
- The user wants **covenant compliance** tested against the ratios → `covenant-compliance-monitor`.
- The user wants a **forward cash-flow forecast / projection** rather than a historical spread →
  `cashflow-forecaster`.
- General "**explain / summarize** this bank statement" with no spreading → `bank-statement-analyzer`.
- Corporate-entity **GL/financials normalization** outside a lending context → `financials-normalizer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a spread with a durable
`spread_id`; downstream memo, covenant, packaging, and pre-check skills consume it. It must not
cross into a credit decision, a memo, or a system-of-record write — those belong to the human
and the downstream skills.

## Inputs and prerequisites
- **Borrower identifier** and the **source documents** (financial statements, tax returns, or
  their extracted line items), plus the **approved template & taxonomy version** and a
  **classification-map version**.
- **Line items** per period, each with `period`, `statement` (`balance_sheet` | `income_statement`),
  `raw_label`, a proposed taxonomy `code` (optional), `amount`, and a `source_ref` citation.
- **Reported anchors** — the borrower's own reported totals (`total_assets`, `total_liabilities`,
  `total_equity`, `net_income`) per period, so the spread can tie out against them.
- **Adjustments** (optional) — analyst add-backs, each with `code`, `amount`, `direction`,
  a `reason`, a `provenance`, and a `citation`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to document-intelligence, the template/taxonomy, and loan-origination; the
  versioned spreading config (see [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The borrower's audited/prepared
statements and filed tax returns are the position of record; the approved template and
classification map govern how raw labels become standard lines; document intelligence supplies
extracted values with page citations. Every classified line cites its source; a raw label the
map does not resolve is **escalated, not guessed**. Where the tax return and the financial
statement disagree, cite both and flag for the analyst.

## Workflow
1. **Scope & validate** — confirm the borrower, periods, template, and classification-map
   versions; load line items and reported anchors; run `validate_input`. Heed ambiguous-mapping
   and thin-input warnings.
2. **Classify & spread (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to resolve each line's
   taxonomy code, aggregate components into subtotals per statement and period, and route any
   unresolved line to `ambiguous_mappings`.
3. **Compute ratios & cash flow** — leverage, liquidity, coverage, and profitability ratios by
   their documented formulas, plus an operating cash-flow proxy (needs a prior period for the
   working-capital change).
4. **Normalize (as-reported vs. adjusted)** — apply the documented add-backs to produce the
   normalized income-statement view; each adjustment stays in the register with its provenance
   and citation.
5. **Tie out** — balance sheet balances (`assets == liabilities + equity`); each computed
   subtotal reconciles to the reported anchor; computed net income ties to reported net income.
6. **Write the spread** — the template with per-period components, subtotals, ratios, cash flow,
   the as-reported/normalized pair, the trend, the adjustments register, and any flagged mappings.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check re-derives (does not trust) the tie-outs: every period balances and reconciles
to reported totals; net income ties; the normalized view differs from as-reported **only** by the
documented adjustments (no phantom add-back); every adjustment carries provenance and a citation;
if any mapping is ambiguous then `requires_human_mapping` is true and each has a citation;
`spread_id` and the template/classification-map versions are recorded; no credit-decision or
investment-advice language; the standing disclaimer is present. Fail closed on any miss.

## Human approval
`external-delivery`: human (credit-officer) approval is required before the spread is written to
the credit file / system of record or sent to the borrower. No approval is needed for the
analyst's own read. The skill produces a **draft artifact only** and never writes a system of
record.

## Failure handling
- **Ambiguous mapping** (raw label not in the map, no valid code) → route to `ambiguous_mappings`
  with the citation, set `requires_human_mapping`, and do not silently bucket or guess.
- **Tie-out failure** (assets ≠ liabilities + equity, or computed ≠ reported) → surface the gap
  for correction; never plug the difference to force a balance.
- **Ambiguous borrower/period identity** → stop and confirm; never spread the wrong entity.
- **Single period supplied** → report cash flow and trends as not evaluable; do not fabricate a
  prior period.
- **Missing reported anchor** → compute the internal balance check but flag that the reported
  reconciliation cannot be performed.
- **Stale / conflicting sources** (statement vs. tax return) → cite both; do not resolve silently.
- **Tool timeout** → return the periods spread so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — borrower (masked id), periods, whether every statement ties out, and whether any
   mapping needs human resolution.
2. **Spread** — per period and statement: classified components, subtotals, and the reported-total
   tie-outs.
3. **Ratios** — leverage, liquidity, coverage, and profitability per period (a ratio with a
   zero/near-zero denominator is reported as not computed, not as zero).
4. **Cash flow** — the operating cash-flow proxy and its working-capital components, or a
   not-evaluable reason.
5. **As-reported vs. normalized** — the adjustments register (each with provenance + citation) and
   the normalized income-statement view.
6. **Trend** — period-over-period growth for revenue, EBITDA, and net income.
7. **Flagged mappings** — ambiguous items with citations and `requires_human_mapping`.
8. **Machine-readable** — the spread core + `spread_id` + versions for downstream skills.
9. **Standing disclaimer** — the spread is analytical support, not a credit decision or advice.
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII (borrower financials, tax data). Mask account/tax identifiers to the last 4.
Minimize customer data in the output to what the spread needs. Retain the spread + citations +
template/classification-map/config versions per records policy; log the read and any
external-delivery approval. Never exfiltrate borrower data.

## Gotchas
- **A spread is not an underwrite.** Healthy ratios are not approval; strained ratios are not
  denial. State the figures and route the decision — never call the borrower creditworthy or
  recommend a facility.
- **Tie-outs are load-bearing.** If the classified components do not equal the reported totals,
  the extraction or classification is wrong — surface it; a spread that does not tie is not done.
- **Never guess an ambiguous line.** A "due from related party" or an unlabeled reserve that the
  map does not resolve goes to the human, with its citation — misclassifying it silently distorts
  every ratio built on it.
- **Adjustment provenance is required.** As-reported and normalized are distinct views; a
  normalized figure may differ from as-reported **only** by a documented, cited add-back — no
  phantom normalizations.
- **Add-backs are pre-tax by default.** The normalized view holds taxes as reported unless a tax
  effect is separately documented; say so rather than implying a post-tax normalization.
- **Do not tune the taxonomy to a borrower.** The classification map and ratio formulas are
  versioned config, not per-deal judgments; changing them changes every comparable spread.
- **Statement vs. tax return.** They are prepared on different bases; do not silently blend them —
  spread the requested basis and cite it.
