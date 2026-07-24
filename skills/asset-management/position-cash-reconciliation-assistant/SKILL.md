---
name: position-cash-reconciliation-assistant
description: >-
  Reconcile a fund's internal positions and cash to independent custodian, prime-broker,
  administrator, and counterparty records: match records by reconciliation key, classify every
  disagreement into a fixed break taxonomy (quantity_break, cash_break, missing_internal,
  missing_external, pending_settlement, duplicate), retain cited matching lineage, tie each
  reconciliation line out (residual zero), and draft PROPOSED-ONLY reconciling items. Use when a
  fund operations analyst asks to "reconcile positions/cash to the custodian or prime broker",
  "why don't our holdings tie to the administrator", "classify the position and cash breaks", or
  "what reconciling items should I raise" for a daily or period reconciliation. This skill
  classifies and evidences breaks and PROPOSES reconciling items only; it NEVER repairs a record,
  adjusts a book, moves an asset, books a trade, or transfers cash, and never decides which side is
  correct. Order/trade breaks route to trade-break-resolver; applying any change is a human action.
license: MIT
compatibility: Amazon Quick Desktop; requires accounting/IBOR (books of record), custodian, prime-broker, fund-administrator, counterparty, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Reconcile & validate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Fund operations analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Position & Cash Reconciliation Assistant

## Purpose and outcome
Given a fund's **internal** positions and cash (books of record / IBOR / accounting) and the
**external** records that independently confirm them — custodian, prime broker, fund
administrator, or counterparty — deterministically **match** the two sides per reconciliation line,
**classify** every disagreement into a fixed break taxonomy with **lineage** to the source rows,
**tie each line out** (the classified breaks fully explain the internal-vs-external difference), and
draft **PROPOSED** reconciling items. A successful output lets a fund operations analyst see exactly
why positions or cash do not tie, hand documented reconciling items forward, and give a reviewer a
set of proposed items to validate and action — the repair itself stays a human/authorized action in
the book of record.

## Use when
- "Reconcile our positions and cash for CUST-A to the custodian for 6/30."
- "Why don't our holdings tie to the prime broker / administrator? Classify the breaks."
- "What reconciling items should I raise for these position and cash differences?"
- A daily or period fund-ops reconciliation needs a consistent, cited, reproducible break list.

## Do not use
- You want the break **repaired**, the book **adjusted**, an asset/position/cash **moved**, or a
  trade **booked** → out of scope. Propose only; an authorized human/system actions the change in
  the book of record (see [references/handoffs.md](references/handoffs.md)).
- The break is an **order/trade discrepancy** to be worked to resolution and repaired →
  `trade-break-resolver` (Capital Markets). This skill routes such breaks; it does not resolve them.
- The disagreement is a **price / rating / index / instrument-attribute** difference between data
  sources → `investment-vendor-feed-reconciler`; a **stale/disputed/outlier price** needing a
  valuation packet → `valuation-exception-packet`. This skill never selects or values a price.
- The work is a full **NAV strike / fund-accounting tie-out** across prices, accruals, income,
  expenses, and shares → `nav-preparation-tie-out`. This skill feeds it; it does not strike NAV.
- You want **personalized investment advice** or a buy/sell/rebalance recommendation → out of scope
  for every skill in this library.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a reconciliation with a
durable `reconciliation_id`, a classified break list, lineage, and proposed-only reconciling items,
then stops. `nav-preparation-tie-out` may consume its `reconciliation_id` as one tie-out input;
order/trade breaks route to `trade-break-resolver`; price/data breaks route to
`investment-vendor-feed-reconciler` / `valuation-exception-packet`. It never repairs, never moves an
asset, and never approves its own reconciling items.

## Inputs and prerequisites
- `entity`, `as_of` (reconciliation date), `config_version`, `base_currency`.
- **Internal records** (books) and **external records** (custodian/prime-broker/administrator/
  counterparty), each row with `record_id`, `match_key`, `account`, `source_system`, `record_type`
  (`position` | `cash`), `quantity` (positions) or `amount` + `currency` (cash), `date`,
  `settle_date`, `source_ref`. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the books of record and each external source; approved reconciliation `config`
  (tolerances, materiality, pending-settlement window, fx rates) — see
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The internal book and each external
record are **two independent positions of record**; a break is a disagreement between them. The
external custodian/prime-broker/administrator/counterparty record is the **independent
confirmation**, so a proposed item is framed as bringing the internal book to agree to it — but the
skill **does not decide which side is correct** and never overwrites either. Cite every break to its
internal and/or external source rows.

## Workflow
1. **Scope & validate** — confirm `entity`/`as_of`/`base_currency`; load both sides per account and
   source; run [scripts/validate_input.py](scripts/validate_input.py). Fail closed on structural
   gaps (missing keys, bad `record_type`, non-numeric values, unknown `source_system`).
2. **Match & classify (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to group by `match_key`,
   pair internal vs external rows, and classify each disagreement into the break taxonomy
   (`quantity_break`, `cash_break`, `missing_internal`, `missing_external`, `pending_settlement`,
   `duplicate`). Each break carries a native `break_amount`, a base-currency `base_impact` (cash), a
   `material` flag, and lineage citations.
3. **Route trade breaks** — a break flagged as an order/trade discrepancy is tagged
   `routing.route_to: trade-break-resolver` and carries **no** proposed item; resolving/repairing a
   trade break is out of scope here.
4. **Tie out (per line)** — confirm the classified breaks fully explain each line's internal-vs-
   external difference (`residual == 0`). If a line does not tie, surface the residual; never plug it.
5. **Propose reconciling items (PROPOSED only)** — for each adjusting break, draft a reconciling
   item whose `adjustment_amount` offsets the `break_amount`; `pending_settlement` items are
   documented reconciling items with **no** proposed item. Every item is `status: "PROPOSED"`.
6. **Write the pack** — plain-language summary + per-line tie-out + classified breaks with lineage +
   proposed items + routed breaks + the standing no-repair/no-move disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after. The
output check confirms per-line tie-outs (residual zero; corrected internal agrees to external after
proposed items, leaving only documented pending/routed items), the break taxonomy and lineage,
idempotency of the `reconciliation_id`, proposed-only reconciling items (`status: "PROPOSED"`, each
offsetting its break; order/trade breaks routed, never adjusted), the **R2 prohibited-action/advice
screen** (no record-repair, asset-movement, posting, or investment-advice language), and the
disclaimer. Fail closed on any miss.

## Human approval
`external-delivery`: human review required before the reconciliation or any proposed reconciling
item is delivered externally or written to a system of record. **Applying a reconciling item —
adjusting a book, moving an asset or cash, booking a trade — is always a separate, authorized
human/system action** performed in the book of record under segregation of duties, never by this
skill.

## Failure handling
- **Line doesn't tie** (residual ≠ 0) → report the residual and the unmatched items; do not
  fabricate a plug or force a tie.
- **Missing `match_key`** → items cannot be matched; report them as unmatched and flag the
  data-quality gap rather than guessing a pairing.
- **Ambiguous account/entity or wrong `as_of`** → stop and confirm; never reconcile the wrong
  account or date.
- **Missing fx rate for a cash currency** → surface the cash break but mark base-currency
  materiality not evaluable; do not invent a rate.
- **Stale / conflicting sources** → cite both the internal and external rows; do not silently pick
  a winner or decide which side is correct.
- **Tool timeout** → return the matches/breaks computed so far with a clear "incomplete" flag; no
  assumed retry.

## Output contract
1. **Summary** — entity, `as_of`, base currency, reconciliation-line count, break counts by type,
   material-break count, documented-pending count, routed count, `reconciliation_id`.
2. **Tie-out** — per line (`match_key`): `internal_total`, `external_total`, `difference`,
   `breaks_total`, `residual` (must be 0), `corrected_internal_total`, `ties_out`; plus
   `all_ties_out`.
3. **Breaks** — per break: `type`, `match_key`, `record_type`, `break_amount`, `base_impact`
   (cash), `material`, lineage citations, and either a proposed reconciling item, a documented
   pending-settlement note, or a `routing` to `trade-break-resolver`.
4. **Proposed items** — `PROPOSED` reconciling items (never applied), each offsetting its break.
5. **Machine-readable** — the full reconciliation JSON + `reconciliation_id` + `input_fingerprint`
   for downstream skills and reproducibility.
6. **Standing disclaimer** — "Reconciliation and proposed reconciling items only; no record has been
   repaired or adjusted and no asset, position, or cash has been moved. Breaks and proposed items
   require human review and authorized action in the book of record."
See [references/controls.md](references/controls.md).

## Privacy and records
Highly Confidential (MNPI / client-confidential). Position and cash detail can reveal fund strategy
and holdings; minimize to what evidences a break and restrict access on a need-to-know basis. Retain
the reconciliation, breaks, lineage, proposed items, and `config_version` per records policy; log
the read and any external-delivery approval. Do not compile holdings across funds beyond the
reconciliation scope.

## Gotchas
- **Propose, never repair.** A reconciling item is a proposal; the skill has no repair, adjust, or
  move operation. The disclaimer and `status: "PROPOSED"` are load-bearing controls, not decoration.
- **Pending settlements are documented, not adjusted.** Proposing an adjustment for an unsettled
  trade double-counts it after settlement — the engine deliberately emits no item for them and marks
  them expected-to-clear.
- **Trade breaks route out.** A quantity difference caused by an order/trade discrepancy is routed
  to `trade-break-resolver` with no proposed item; this skill does not resolve or book trades.
- **Don't decide which side is right.** The internal book and the external record are two positions
  of record; the skill evidences the disagreement for a human and never overwrites either.
- **Don't value positions.** Position materiality is assessed in units; converting a quantity break
  to money requires a price — that is `valuation-exception-packet`'s job, not this skill's.
- **Config is a versioned contract.** Tolerances, materiality, the pending-settlement window, and fx
  rates come from `config`, never tuned per-reconciliation to make a break disappear.
