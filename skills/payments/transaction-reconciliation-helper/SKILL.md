---
name: transaction-reconciliation-helper
description: >-
  Reconcile transaction-level records across gateway, processor/acquirer, bank, ledger, and
  merchant systems: match by transaction reference, classify mismatches into a documented
  break taxonomy, preserve source lineage, tie ledger totals to the cash position of record,
  and draft PROPOSED correcting entries. Use when a merchant or reconciliation analyst asks
  to "reconcile these transactions", "why doesn't the bank match our ledger", "classify
  these breaks", or wants tie-outs and proposed adjustments across payment records.
  Settlement-file and cash-ledger breaks route to settlement-break-reconciler. This skill
  matches records, classifies breaks with evidence, and proposes entries only; it NEVER
  posts, books, or finalizes a journal, closes a break, writes a system of record, or
  resolves settlement-file breaks — approval and posting remain human.
license: MIT
compatibility: Amazon Quick Desktop; requires gateway/processor/acquirer, bank, ledger/ERP, merchant-order, and approved-calculation MCP integrations (all read-only), plus a versioned reconciliation config.
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Reconcile & validate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 1 - stabilize existing"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Merchant / reconciliation analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Transaction Reconciliation Helper

## Purpose and outcome
Given transaction-level records from multiple payment systems (gateway, processor/acquirer,
bank, ledger, merchant order), match them by transaction reference, classify every mismatch
into a documented **break taxonomy** with source lineage, compute **tie-out** totals against
the cash position of record, and draft **proposed** correcting entries. A successful output
lets a reconciliation analyst see exactly which transactions broke, why, what the residual
is, and what entries *would* resolve it — while the posting, approval, and any settlement-file
break stay with the human and the dedicated workflows.

## Use when
- "Reconcile our gateway/processor/bank/ledger records for this period."
- "Why doesn't the bank deposit match what our ledger recorded for this transaction?"
- "Classify these breaks and propose correcting entries."
- An analyst needs a consistent, cited reconciliation with tie-out totals to attach to a
  close or an exception queue.

## Do not use
- The user wants entries **posted, booked, or finalized**, a break **closed**, or the ledger
  **written** → out of scope. Produce proposed entries and route to a human + the ledger
  system. This skill never posts.
- The break is a **settlement-file / cash-ledger** break (acquirer/processor settlement file
  vs bank cash, fees, reserves) → `settlement-break-reconciler`.
- The break traces to a **payment exception / ISO 20022 case** (rejected/returned/held) →
  `payment-exception-investigator`; a message-parsing/field question →
  `iso-20022-message-interpreter`.
- The mismatch is really a **merchant chargeback/refund** to package →
  `chargeback-dispute-packager`. A **settlement report summary** → `settlement-report-summarizer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a reconciliation with a
durable `recon_id`; routed settlement breaks leave **without** a proposed ledger entry so the
settlement workflow owns them (no double-posting). Downstream skills reuse the `recon_id`
lineage rather than re-matching.

## Inputs and prerequisites
- The **record set** to reconcile: rows from each source, each with `record_id`, `txn_ref`,
  `source`, `level` (transaction|settlement), `date`, `amount`, `currency`, `status`, and a
  `source_ref`. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- `as_of`, `config_version`, and the reconciliation **config** (tolerances, expected sources,
  cash ranking) — see [references/domain-rules.md](references/domain-rules.md).
- Read access to the payment systems and ledger (all read-only).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **bank** is the position of
record for cash actually moved; the **processor/acquirer** is authoritative for capture and
fees; the **ledger** is the internal book being tied out — never the cash position of record.
Cite every break and routed break to its source rows.

## Workflow
1. **Scope & validate** — confirm the period and record set; run `validate_input` (flags
   duplicate ids, single-source refs, missing currency/ledger).
2. **Match & classify (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): group by `txn_ref`,
   match across expected sources, classify each mismatch into the break taxonomy, and attach
   evidence + citations. Settlement-level groups are **routed** to `settlement-break-reconciler`.
3. **Tie out** — compute per-source totals, pick the cash position of record, and compute
   `residual_before`, `net_proposed`, and `residual_after` per the documented tie-out identity.
4. **Propose entries** — for each transaction-level break, draft a `status: "proposed"`
   ledger adjustment or an *investigate* action. Never post; every entry `requires_approval`.
5. **Write the pack** — matched summary + breaks (with lineage) + routed breaks + tie-out +
   proposed entries + explicit residual and the standing disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every break has a taxonomy `break_type` and cited lineage;
the tie-out recomputes deterministically (`residual_after == residual_before − net_proposed`);
routed settlement breaks carry no proposed entry; every proposed entry is `status: "proposed"`
with **no posting/finalization language**; and the standing disclaimer is present. Fail closed
on any miss.

## Human approval
`external-delivery`: human review and approval required before the pack or any proposed entry
is delivered externally or written to the ledger / system of record. No approval is needed for
the analyst's own read. The skill never posts, books, finalizes, or closes.

## Failure handling
- **Single-source `txn_ref`** → classify `unmatched`; do not assume a missing counterpart
  exists.
- **Missing cash source within the in-transit window** → flag as possible timing/in-transit;
  propose *investigate*, not an adjustment.
- **Missing currency / mixed currencies** → `currency_mismatch`; resolve FX basis first, do
  not net across currencies.
- **Ambiguous or duplicate `record_id`** → stop and surface; never silently de-duplicate.
- **Non-zero `residual_after`** → report it plainly as unresolved; never tune tolerance to
  force a tie-out.
- **Tool timeout** → return the matches/breaks computed so far with an "incomplete" flag; page
  long periods as resumable stages.

## Output contract
1. **Summary** — `recon_id`, period, counts (groups, matched, breaks, routed).
2. **Matched** — tied transactions with sources and citation.
3. **Breaks** — per break: `break_type`, plain-language reason, present/missing sources,
   per-source amounts, cited evidence rows, and the **proposed** entry.
4. **Routed breaks** — settlement-file/cash-ledger breaks with `route_to`
   `settlement-break-reconciler` and evidence (no proposed entry).
5. **Tie-out** — source totals, cash position of record, `residual_before`, `net_proposed`,
   `residual_after`, `tied_out`.
6. **Proposed entries** — `status: "proposed"`, `ledger_delta`, `requires_approval`.
7. **Machine-readable core** + `recon_id` for downstream skills.
8. **Standing disclaimer** — "Proposed entries only; not posted to any system of record.
   Human approval and posting required."
See [references/controls.md](references/controls.md).

## Privacy and records
Highly Confidential (customer NPI/PII; cardholder data). Mask PAN/account numbers to last 4;
never emit full card numbers. Minimize record fields to what evidences a break. Retain the
reconciliation + citations + `config_version` per records policy; log the read and any
external-delivery approval. Never exfiltrate cardholder or customer data.

## Gotchas
- **A proposed entry is not a posting.** Everything this skill emits is a draft for a human;
  it never writes the ledger or declares a reconciliation "final".
- **Ledger is not the cash truth.** Tie the ledger *to* the bank (cash position of record),
  not the reverse; treating the ledger as authoritative hides real cash breaks.
- **In-transit ≠ break.** Bank cash posts 1–2 days after capture; a missing bank row inside
  `intransit_days` is a timing reconciling item, not a confirmed break.
- **Fees and FX explain differences.** A net difference matching a documented processor fee or
  an FX conversion is a reconciling item — attribute it, don't over-adjust.
- **Route settlement breaks; don't resolve them.** A settlement-file/cash-ledger break gets
  handed to `settlement-break-reconciler` with no proposed entry — otherwise two workflows
  post the same correction.
- **Don't tune tolerance to tie out.** Tolerances come from the versioned config; a residual
  that won't close is information, not a nuisance to suppress.
