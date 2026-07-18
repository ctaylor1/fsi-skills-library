---
name: settlement-break-reconciler
description: >-
  Reconcile network, acquirer, and processor settlement files to bank cash, fees, reserves,
  and the internal ledger/subledger; match records, tie out gross/fee/reserve/net/cash,
  classify breaks with a documented taxonomy, quantify impact, preserve lineage, and draft
  proposed corrections. Use when a settlement or finance-operations user asks to reconcile
  settlement files to cash and the ledger, explain why an acquirer's net does not match the
  cash received, classify and quantify settlement breaks, or prepare correcting entries for
  review. HARD BOUNDARY: it proposes corrections only — it NEVER posts a journal, writes a
  system of record, executes a payment repair, or marks a break reconciled/cleared; posting
  and disposition are human/authorized-system actions that require approval.
license: MIT
compatibility: Amazon Quick Desktop; requires network/acquirer/processor settlement-file, bank-cash, internal-ledger, fee/reserve-schedule, entity-resolution, and deterministic-reconciliation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Reconcile & validate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Settlement operations / finance operations"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Settlement Break Reconciler

## Purpose and outcome
Given a settlement period's source files — network/scheme, acquirer/processor, bank cash,
the fee/reserve schedule, and the internal ledger — **match** the records, **tie out** gross,
fees, reserve, net, and cash, **classify** every discrepancy into a documented break
taxonomy, **quantify** its impact, **preserve lineage** (source citations), and **draft
proposed corrections**. A successful output lets a settlement/finance operations reviewer see
exactly which batches broke, by how much, why, and what correcting entry is proposed — while
every correction remains a **proposal for human approval**, never a posting.

## Use when
- "Reconcile the Visa/Mastercard settlement files to our bank cash and ledger for this period."
- "Why doesn't the acquirer's net settlement match the cash we received?"
- "Classify and quantify the settlement breaks and propose correcting entries for review."
- A reviewer needs a consistent, cited break pack with tie-out totals to attach to the close.

## Do not use
- The user wants the correcting journals **posted**, a system of record **written**, or a
  break **marked reconciled/cleared** → out of scope. Deliver the proposed corrections and
  route posting/sign-off to an authorized human or the gated close process.
- **Transaction-level** processor/gateway/merchant reconciliation (not file/period cash
  tie-out) → `transaction-reconciliation-helper`.
- **GL-balance-to-subledger** reconciliation → `gl-reconciler`.
- **Executing a repair / resubmitting** a held or rejected payment → `payment-repair-assistant`
  (R4, approval-gated).
- Deep **exception investigation** (chronology, parties, ISO 20022 camt) → `payment-exception-investigator`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a break pack with a
durable `reconciliation_id`; upstream summarizer/diagnoser skills feed it, and downstream
investigation, repair, GL, and close skills consume its breaks and proposed corrections. It
must not duplicate their investigation, posting, or closure steps.

## Inputs and prerequisites
- A **settlement period** (`period.start`/`period.end`) and the source files for it.
- **Sources** — `network[]`, `processor[]`, `bank_cash[]`, `ledger[]`, each record carrying a
  `match_key`, currency, dated amount(s), and a `source_ref` for citation. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- **Fee/reserve schedule** (versioned) and **tolerance config** (versioned). Missing schedule
  → fee/reserve tie-outs are reported not-evaluable, not silently skipped.
- Read access to the settlement, cash, ledger, and schedule sources (see
  [references/source-map.md](references/source-map.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Bank cash is authoritative for cash
received; the network file for gross cleared; the processor file is the working breakdown; the
schedule sets expected fees/reserves; the internal ledger is what was booked. Cite every break
to the specific source rows; when sources conflict, cite both and classify the break.

## Workflow
1. **Scope & validate** — confirm the period and load the four sources + schedule; run
   `validate_input`. Fail closed on structural problems; note data-quality gaps that limit
   which tie-outs are evaluable.
2. **Match & tie out (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to match records by
   `match_key` and tie out gross, fee, reserve, net calc, cash, and ledger per matched group,
   plus portfolio-level tie-out totals.
3. **Classify breaks** — every discrepancy outside tolerance is classified into the taxonomy
   (see [references/domain-rules.md](references/domain-rules.md)) with a signed impact and
   cited evidence. Settlements within the cash-lag window with no cash yet are **timing
   reconciling items**, not missing-cash breaks.
4. **Propose corrections** — each break yields one proposed correction (a journal, a
   dispute/adjust query, or an investigation item) with a deterministic `correction_id`,
   `status: "proposed"`, and `requires_approval: true`. Nothing is posted.
5. **Write the pack** — tie-out summary, classified breaks with evidence, reconciling items,
   proposed corrections, and the standing draft-only disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms tie-outs are present and numeric, every break_type is in the
taxonomy, every break and correction is cited (lineage), identifiers are unique and stable
(idempotency), reported impact ties to the sum of break impacts, **corrections are proposed
only** (no posted/booked/executed status, no posting language), and the disclaimer is present.
Fail closed on any miss.

## Human approval
`external-delivery`: human approval required before the break pack or proposed corrections are
delivered to the settlement/GL team or the close process, or written to any system of record.
No approval is needed for the reviewer's own read. The skill never posts, repairs, or closes.

## Failure handling
- **Missing source / empty file** → tie-outs requiring it are reported not-evaluable; do not
  assume a zero or fabricate the missing side.
- **No fee schedule for a scheme** → fee/reserve variance for those keys is not-evaluable;
  presence and cash/ledger tie-outs still run.
- **Ambiguous match key** → do not force a match; classify presence breaks and surface the
  ambiguity for the reviewer.
- **Currency conflict on a matched group** → raise `CURRENCY_MISMATCH`; do not net across
  currencies.
- **Stale/conflicting sources** → cite both; never silently pick one.
- **Tool timeout** → return the keys reconciled so far with a clear "incomplete" flag; page
  long periods as resumable stages.

## Output contract
1. **Summary** — period, keys examined, break count by type, total break impact, clean flag.
2. **Tie-out** — per-source totals (network gross, processor gross/fees/reserve/net, bank
   cash, ledger net) and the bank-vs-processor and ledger-vs-processor differences.
3. **Breaks** — per break: `break_id`, `match_key`, `break_type`, plain-language reason,
   signed `impact`, and cited evidence rows.
4. **Reconciling items** — timing/in-transit items (with `in_transit_amount`), excluded from
   break impact and from corrections.
5. **Proposed corrections** — per break: `correction_id`, `break_ref`, type, proposed entry
   (where applicable), `status: "proposed"`, `requires_approval: true`, evidence.
6. **Machine-readable** — the full reconciliation JSON with `reconciliation_id` for downstream
   skills.
7. **Standing disclaimer** — "Reconciliation and proposed corrections only; no journal has
   been posted and no system of record has been changed. Every proposed correction requires
   human review and approval before posting."
See [references/controls.md](references/controls.md).

## Privacy and records
Highly Confidential (customer NPI/PII; cardholder data), PCI DSS scope. Never emit a PAN; work
from scheme + masked funding references only. Minimize data to what evidences a break. Retain
the reconciliation + citations + config version per records policy; log the read and any
external-delivery approval. Never exfiltrate cardholder or customer data.

## Gotchas
- **A break is not a posting.** Proposed corrections justify *review and approval*, never an
  autonomous journal or a "reconciled" state change.
- **Timing vs. missing cash.** Funds not yet due (within the cash-settlement lag) are
  in-transit reconciling items — raising them as `MISSING_IN_BANK` creates false breaks and
  overstates impact.
- **Baseline of tie-out is the file, not the ledger.** Test cash against the *bank* record and
  gross against the *network* file; do not substitute the processor's or ledger's own figures.
- **Fee math uses the schedule, not the invoice.** Expected fee = gross × scheduled `rate_bps`
  from the versioned schedule; a processor's stated fee that differs is the variance.
- **Idempotency matters.** `correction_id` derives from the break identity, so re-running the
  same period never spawns duplicate proposed corrections — do not regenerate fresh IDs.
- **Do not net across breaks.** Report each break with its own signed impact; a net-zero
  portfolio can still hide offsetting breaks that each need a correction.
