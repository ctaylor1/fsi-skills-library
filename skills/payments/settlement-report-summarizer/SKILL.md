---
name: settlement-report-summarizer
description: >-
  Summarize a merchant settlement or payout report into a clear, source-linked overview —
  gross card sales, refunds, chargebacks, interchange/scheme/processor fees, adjustments,
  reserves, and the net amount funded — with a gross-to-net tie-out and per-card-brand
  breakdown, from an authoritative processor/acquirer settlement report or ISO 20022
  camt.053/camt.054 statement. Use when a merchant, SMB owner, or payment-ops associate asks
  "summarize this settlement", "explain my payout", "what were my fees this period", "why is
  my deposit lower than my sales", or attaches a settlement/funding statement and wants a
  plain-language snapshot. Informational only: it does not give fee-optimization, financial,
  or tax advice, does not tell you to switch or renegotiate with a processor, does not
  reconcile figures against your books or bank, and makes no determination that the
  settlement is correct — route those to the reconciliation, exception, or fee-analysis skills.
license: MIT
compatibility: Amazon Quick Desktop; requires processor/acquirer/gateway settlement, bank/ISO-20022 statement, card-network fee-schedule, and document-intelligence MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R1"
  aws-fsi-archetype: "Explain & summarize"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 1 - stabilize existing"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-no-changes"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Merchant / SMB"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Settlement Report Summarizer

## Purpose and outcome
Produce a faithful, plain-language summary of a single merchant settlement (payout) so the
reader understands how gross card sales became the net amount deposited. A successful output
shows gross sales, every deduction (refunds, chargebacks, interchange/scheme/processor fees,
adjustments, reserves), the net funded amount and funding date, and a per-card-brand split —
with a **gross-to-net tie-out** and every figure traceable to a cited source line — **without**
any advice, fee judgment, or claim that the settlement has been reconciled or verified.

## Use when
- "Summarize this settlement", "explain my payout/deposit", "break down this statement".
- "What were my fees this period", "how much went to interchange vs. the processor".
- "Why is my deposit lower than my sales" (explain the deductions descriptively).
- The user attaches a processor/acquirer settlement report, funding advice, or an ISO 20022
  `camt.053`/`camt.054` statement and wants a readable overview.
- A payment-ops associate needs a clean settlement snapshot to attach to a review packet
  (delivery to the merchant requires human review — see Human approval).

## Do not use
- The user wants to know if fees are competitive, high, or reducible, or whether to switch or
  renegotiate with a processor → `merchant-fee-optimizer` (do not answer it here).
- The user wants the settlement matched to their own ledger/bank, or asks whether it
  "reconciles" / where the break is → `settlement-break-reconciler` or
  `transaction-reconciliation-helper`.
- The user wants a specific exception, missing funding, or reserve hold investigated →
  `payment-exception-investigator`.
- The user wants to know why specific payments failed → `payment-failure-diagnoser`.
- The user wants a `camt`/`pacs` message or field decoded → `iso-20022-message-interpreter`.
- The user wants to contest a chargeback shown on the settlement → `chargeback-dispute-packager`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). In short: this skill is often the
**upstream** snapshot for `settlement-break-reconciler`, `merchant-fee-optimizer`, and
`payment-exception-investigator`. It hands off the normalized category table + a durable
`snapshot_id`; it never performs the downstream reconciliation, optimization, or investigation.

## Inputs and prerequisites
- One authoritative settlement report for **one settlement/payout at a time**: `report_id`,
  merchant id (masked), settlement date, settlement currency, and line items with category,
  amounts, currency, and a source citation. See the input schema in
  [scripts/validate_input.py](scripts/validate_input.py).
- The **settlement/as-of date** and, where available, the **funding date** and expected net.
  Reject a file that mixes multiple settlement batches or funding dates unless the user
  confirms a single settlement.
- Read permission to the settlement source; card-network fee schedules for classifying fee
  lines when the report does not label them.

## Source hierarchy
Rank sources and cite every figure. See [references/source-map.md](references/source-map.md).
1. Processor/acquirer/gateway **settlement report** for the period (payout of record — highest).
2. **ISO 20022 bank statement** (`camt.053/054`) or funding advice confirming the net credit.
3. **Card-network/scheme fee schedules** for classifying interchange vs. scheme vs. processor.
4. Merchant-provided export/PDF of the same report — only when 1-2 are unavailable; label as
   unverified.
Never substitute a merchant assertion for the settlement of record; if they conflict, surface
the conflict and cite both.

## Workflow
1. **Identify scope** — confirm the single settlement (`report_id`) and its as-of/funding
   dates. If multiple batches or funding dates are present, ask which one (do not silently
   merge).
2. **Normalize** — map each line to the category taxonomy in
   [references/domain-rules.md](references/domain-rules.md) (signed-amount convention);
   classify fee lines as interchange/scheme/processor/other; attach the source citation
   (system + report section/line) to each line.
3. **Compute the summary (deterministic)** — gross sales, each deduction category, net
   settlement, total fees, effective fee rate, and the per-card-brand split. These are
   descriptive arithmetic only; run [scripts/validate_output.py](scripts/validate_output.py)
   to confirm the gross-to-net tie-out, funding match, fee totals, and brand split, and that
   every figure carries a citation.
4. **Write the summary** — lead with gross → net; state the settlement date, funding date, and
   currency; present fees and reserves as neutral facts (amounts and shares), never as
   high/low/excessive or improvable.
5. **Surface gaps** — unvalued/pending lines, unclassified fees, currency mismatches, or a
   funding amount that does not match the computed net are listed explicitly rather than
   guessed or "reconciled".

## Validation loop
Run `validate_input` before summarizing and `validate_output` after. If the gross-to-net
tie-out fails, a figure lacks a citation, or the output contains advice/optimization or
settlement-determination language, **fix or fail closed** — do not deliver an untied or
advice/determination-tainted summary.

## Human approval
None required for the merchant's own informational read. **Human review is required before the
summary is delivered externally** (e.g., an associate sending it to the merchant or a
counterparty) or attached to a system of record — `aws-fsi-human-approval: external-delivery`.

## Failure handling
- **Unvalued/pending lines** → summarize what is valued, list the rest under Data gaps as "not
  valued", exclude from the tie-out; never invent an amount.
- **Unclassified fee** → label it `other_fees` and note it; do not force it into a bucket.
- **Funding mismatch** (computed net ≠ funding advice) → state both with citations as a data
  gap; do **not** declare it reconciled or a break — route to `settlement-break-reconciler`.
- **Multiple settlements/dates in one file** → stop and ask; do not merge.
- **Source conflict** (report vs. bank statement vs. merchant assertion) → present all with
  citations; do not pick a winner.
- **Tool timeout / permission denial** → report partial results and the exact gap; no retry
  assumption.

## Output contract
1. **Header** — merchant label (masked), `report_id`, settlement date, funding date, currency.
2. **Gross → net waterfall** — gross sales, refunds, chargebacks, fees (interchange/scheme/
   processor), adjustments, reserves, and net settlement (table), each cited.
3. **Fees & brand split** — total fees, effective fee rate (neutral ratio), and
   `by_card_brand` shares.
4. **Notes** — funding amount vs. computed net, plus a **Data gaps** list.
5. **Machine-readable** — the normalized category table and computed metrics, tagged with a
   durable `snapshot_id` for downstream skills.
6. **Standing disclaimer** — "Informational summary only; not financial, tax, or
   fee-optimization advice, and not a settlement reconciliation, dispute assessment, or
   confirmation that the settlement is correct."
Every figure carries a source citation. See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII and cardholder data. Never emit a full PAN; limit card data to brand and at
most last 4. Mask merchant and bank account numbers (show last 4). Do not transmit settlement
data outside the approved environment. Retain the snapshot and its citations per records
policy; log the read and any external-delivery approval. See
[references/controls.md](references/controls.md).

## Gotchas
- **Gross-to-net must tie out**; a stated funding amount that does not equal the computed net
  is a **data gap to surface**, not a discrepancy to resolve or reconcile here.
- **"Explain" is not "assess"**: stating a 2.85% effective fee rate is in scope; calling it
  "high", "competitive", or "worth renegotiating" is advice and is out of scope.
- **"Summarize" is not "reconcile"**: do not claim the payout matches the merchant's ledger or
  bank, or that there are "no discrepancies" — that is a control decision for another skill.
- **Fees are signed deductions**: interchange/scheme/processor and reserves reduce the payout;
  keep the sign convention and don't take absolute values when computing the tie-out.
- **Reserves** (held vs. released) are neutral lines — report the amount; do not opine on the
  reserve level.
- **Funding date ≠ period end**: the value date the money lands is separate from the settlement
  period; state both.
- **Multi-currency**: convert only with a cited FX rate and as-of; otherwise report per
  currency and label it.
