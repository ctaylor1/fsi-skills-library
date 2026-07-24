---
name: nav-preparation-tie-out
description: >-
  Reconcile a fund's NAV components — positions, prices, accruals, income, expenses, shares
  outstanding, and cash — between the fund accounting book of record and the independent
  custodian, administrator, and approved pricing sources: match records per component,
  classify every disagreement into a fixed break taxonomy (quantity, price, cash, accrual,
  income, expense, shares, missing-record, timing), preserve lineage, tie the breaks out to
  explain each control total, and draft PROPOSED-only resolutions. Use when a fund accountant
  asks to "tie out the NAV", "reconcile the book to the custodian and administrator for the
  valuation date", "classify the NAV breaks", or "produce the tie-out/break packet". HARD
  BOUNDARY: never strikes, finalizes, or certifies a NAV, never chooses or overrides a price,
  and never posts an accounting entry; price disagreements route to valuation-exception-packet
  and every resolution requires fund-accountant review.
license: MIT
compatibility: Amazon Quick Desktop; requires fund-accounting/ABOR, custodian, administrator/transfer-agent, and approved-pricing MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Reconcile & validate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Fund accountant"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# NAV Preparation Tie-Out

## Purpose and outcome
Given a fund's NAV inputs for a valuation date — positions, prices, accruals, income,
expenses, shares outstanding, and cash — from the **book of record (ABOR)** and the
independent **custodian**, **administrator/transfer agent**, and **approved pricing source**,
deterministically **match** each component to its verifier, **classify** every disagreement
into a fixed break taxonomy with **lineage** to the source rows, **tie the breaks out** so
they fully explain each control total, and draft **PROPOSED-only** resolutions. A successful
output lets a fund accountant see exactly why the book does not agree to the custodian and
administrator, hand documented breaks forward, and give a reviewer a routed, evidenced packet
to act on — the NAV strike, any price selection, and any posting stay human/authorized.

## Use when
- "Tie out the NAV for LOTUS-CORE-FUND class INST as of 2026-06-30."
- "Reconcile the book to the custodian and administrator for the valuation date and classify
  the breaks."
- "Why doesn't the book agree to the custodian on positions/cash, or to the administrator on
  income/expenses/shares?"
- "Produce the tie-out / break packet for NAV preparation (daily or period)."

## Do not use
- You want the **NAV struck / finalized / certified**, or a **price chosen** → out of scope
  (hard boundary). Price disagreements go to `valuation-exception-packet`; the NAV strike is a
  fund accountant / valuation-committee action.
- You want a break **posted / booked** to the accounting system → out of scope. Propose only;
  an authorized fund accountant posts (see [references/handoffs.md](references/handoffs.md)).
- The task is a **position/cash-only** reconciliation to custodian/prime broker, not a full
  NAV tie-out → `position-cash-reconciliation-assistant`.
- The disagreement is an internal-vs-vendor **reference-data / rating / attribute** difference
  → `investment-vendor-feed-reconciler`.
- A break is really a **feed data-quality** issue (stale, duplicate, broken mapping) →
  `investment-data-quality-exception-detector`.
- A quantity break traces to an **unmatched order/trade** → `trade-break-resolver`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a tie-out with a durable
`tie_out_id`, a classified break list, lineage, and proposed resolutions, then stops.
`month-end-close-orchestrator` may call it as a close task; `holdings-transaction-normalizer`
may feed it canonical inputs; downstream skills consume its `tie_out_id` rather than recomputing
the match. It never strikes NAV, chooses a price, posts, or approves its own resolutions.

## Inputs and prerequisites
- `fund`, `share_class` (optional), `as_of` (valuation date), `base_currency`, `config_version`.
- **`lines[]`**, each with `line_id`, `component` (position, price, cash, accrual, income,
  expense, shares), `key`, `source` (book, custodian, administrator, pricing), signed `value`,
  `currency`, `as_of`, `source_ref`, `description`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to ABOR, custodian, administrator, and the approved pricing source; approved
  tie-out `config` (tolerances, materiality, date cutoff, component→verifier map) — see
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The book of record and each verifier
are **independent positions of record**; a break is a disagreement between them. The skill
classifies and evidences the break — it does not decide which side is right, select a price, or
overwrite either. Cite every break to its book and/or verifier source rows.

## Workflow
1. **Scope & validate** — confirm `fund`/`share_class`/`as_of`; load the book and verifier
   lines for each component; run [scripts/validate_input.py](scripts/validate_input.py). Fail
   closed on structural gaps.
2. **Match & classify (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to pair book vs the
   configured verifier per component, and classify each disagreement into the break taxonomy
   (`quantity_break`, `price_break`, `cash_break`, `accrual_break`, `income_break`,
   `expense_break`, `shares_break`, `missing_record`, `timing_difference`). Each break carries
   a signed `impact`, a `material` flag, and lineage citations.
3. **Tie out** — confirm the classified breaks fully explain every `(component, currency)`
   control total (`difference == breaks_impact_sum`) and the overall `residual == 0`. If a
   control total does not tie, surface the residual; never plug it.
4. **Propose resolutions (PROPOSED only)** — for each break draft a resolution: `price_break`
   **routes to `valuation-exception-packet`** (never choose a price); other value/missing
   breaks propose an adjustment to investigate (never posted); `timing_difference` items are
   documented reconciling items with **no** resolution. Every resolution has
   `chooses_value`/`strikes_nav`/`posts_entry` all false.
5. **Write the packet** — plain-language summary + tie-out (control totals + residual) +
   classified breaks with lineage + proposed resolutions + the standing no-strike/no-price/
   no-post disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check confirms tie-outs (each control total ties, residual zero, break impacts
recomputed from the list), the break taxonomy and lineage, idempotency of the `tie_out_id`,
proposed-only resolutions (status `PROPOSED`; no NAV strike, no price chosen, no posting; price
breaks routed), and the disclaimer. Fail closed on any miss.

## Human approval
`required` (R3): a fund accountant must review before the tie-out or any proposed resolution is
delivered externally or acted on. **Striking the NAV, selecting a price, and posting an entry
are always separate, authorized human/system actions** performed under segregation of duties —
never by this skill.

## Failure handling
- **Breaks don't tie** (residual ≠ 0) → report the residual and the unmatched items; do not
  fabricate a plug or force a tie.
- **Missing verifier side for a component** → book values cannot be tied out; report them and
  flag the data-quality gap rather than assuming agreement.
- **Ambiguous fund/class or wrong valuation date** → stop and confirm; never tie out the wrong
  book.
- **Stale / conflicting sources** → cite both the book and verifier rows; do not silently pick
  a winner or a price.
- **Tool timeout** → return the matches/breaks computed so far with a clear "incomplete" flag;
  no assumed retry.

## Output contract
1. **Summary** — fund, share class, `as_of`, break counts by type, material-break count,
   `tie_out_id`.
2. **Tie-out** — per `(component, currency)` control total: `book_total`, `verifier_total`,
   `difference`, `breaks_impact_sum`, `ties_out`; overall `residual` (must be 0) and status.
3. **Breaks** — per break: `type`, `component`, `key`, `impact`, `material`, lineage citations,
   and either a proposed resolution or a documented-reconciling-item note (timing).
4. **Proposed resolutions** — `PROPOSED` only; price breaks routed to
   `valuation-exception-packet`; `chooses_value`/`strikes_nav`/`posts_entry` all false.
5. **Machine-readable** — the full tie-out JSON + `tie_out_id` + `input_fingerprint` for
   downstream skills and reproducibility.
6. **Standing disclaimer** — "Tie-out and break packet only; NAV has not been struck, no price
   has been selected, and no accounting entry has been posted. All resolutions are PROPOSED and
   require fund-accountant review and authorized action in the systems of record."
See [references/controls.md](references/controls.md).

## Privacy and records
Highly Confidential (MNPI / client-confidential) fund holdings and NAV inputs. No retail
customer NPI is required; minimize counterparty detail to what evidences a break. Retain the
tie-out, breaks, lineage, proposed resolutions, and `config_version` per records policy; log
the read and any external-delivery approval.

## Gotchas
- **Tie out, never strike.** The skill has no NAV-strike, price-select, or posting operation.
  The disclaimer and the `PROPOSED` / false-flag fields are load-bearing controls, not
  decoration.
- **Price breaks route — they are never priced here.** A price disagreement is evidence for
  `valuation-exception-packet`; choosing the "right" price is a valuation control action.
- **Timing differences are documented, not repaired.** Proposing an adjustment for an in-transit
  cash/settlement item double-counts it next cycle — the engine emits no resolution for them.
- **Don't force a tie.** If a control total doesn't tie, the residual is the finding. A plug
  hides the real break.
- **Sign discipline.** `impact` is `book − verifier`; a sign error breaks the tie-out — trust
  the deterministic engine over hand math.
- **Config is a versioned contract.** Tolerances, materiality, cutoff, and the component→verifier
  map come from `config`, never tuned per tie-out to make a break disappear.
- **Independent positions of record.** The skill never decides the book or a verifier is
  "correct"; it evidences the disagreement for a human.
