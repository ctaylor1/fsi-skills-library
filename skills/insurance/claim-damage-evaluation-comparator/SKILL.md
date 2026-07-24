---
name: claim-damage-evaluation-comparator
description: >-
  Compare damage-supporting documents on a claim — repair estimates, medical bills, wage
  records, valuations, and invoices — and deterministically surface duplicate (double-counted)
  line items, unsupported items, and price/amount differences for the same item across
  documents, with cited evidence, for a claims analyst to review. Use when a claims analyst
  asks to "compare these estimates", "check for double-counted items", "which line items are
  unsupported", or "reconcile the repair estimate against the invoice". HARD BOUNDARY: R3
  decision-support only — it NEVER sets, values, or recommends damages, reserve, or settlement
  amount, never determines coverage or liability, and never approves payment; every finding is
  evidence a licensed adjuster must adjudicate. Routes fault/liability mapping to
  liability-evidence-matrix-builder.
license: MIT
compatibility: Amazon Quick Desktop; requires claims document/line-item records and reference-data MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Insurance underwriting & claims"
  aws-fsi-primary-user: "Claims analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Claim Damage Evaluation Comparator

## Purpose and outcome
Given the damage-supporting documents on a claim and their line items, deterministically surface
duplicates (the same item counted across documents), unsupported items (no supporting document),
and amount differences (the same item priced differently across estimates), each with cited
evidence and a suggested review disposition. A successful output lets a claims analyst review —
the damages, reserve, and settlement remain the licensed adjuster's determination.

## Use when
- "Compare these estimates/bills", "check for double-counted line items".
- "Which line items are unsupported", "reconcile the repair estimate against the invoice".
- A reviewer needs a consistent, cited line-item comparison.

## Do not use
- The user wants you to **set or recommend damages, reserve, or settlement value** → out of
  scope; the adjuster decides.
- The question is **fault/liability** → route to `liability-evidence-matrix-builder`.
- The claim needs a **settlement-authority packet** → `claim-settlement-authority-packet`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Emits a comparison packet with a durable
`comparison_id`; it does not value the claim.

## Inputs and prerequisites
- The **claim** (id, type), the **documents** (id, type, source_ref), and the **line_items**
  (item_id, doc_id, category, description, amount, supported_by). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Comparison config (rounding, categories requiring support). See
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The claims document record is the
system of record. Cite every finding to the specific line items and documents.

## Workflow
1. **Validate input** — run `validate_input`; confirm documents and line items with amounts.
2. **Compute checks (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): normalize
   descriptions, group by (category, description), and flag duplicates, differences, and
   unsupported items.
3. **Assemble findings** — per finding: type, items, documents, amounts, citation.
4. **Suggest disposition** — `clean` or `items-for-review` (a triage suggestion, not a valuation).
5. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py) for
   citation coverage, the no-valuation screen, and disclaimer.

## Validation loop
`validate_input` before, `validate_output` after. If a finding lacks item citations, or the text
contains damages/reserve/settlement-setting language, **fix or fail closed**.

## Human approval
`required`: no damages, reserve, settlement, coverage, or liability determination without a
licensed adjuster. The skill only evidences line-item findings.

## Failure handling
- **Missing amounts** → flag the item as not-evaluable; do not impute a price.
- **Ambiguous descriptions** → group only on exact normalized match; report near-matches as data
  gaps, never merge on a guess.
- **A difference is not fraud** → report the price difference factually; the adjuster interprets.
- **Stale/conflicting source** → cite both; escalate. **Tool timeout** → partial + incomplete flag.

## Output contract
1. **Summary** — claim (masked), document count, counts by finding type, suggested disposition.
2. **Findings** — per finding: type (duplicate|difference|unsupported), items, documents,
   amounts, citation.
3. **Data gaps / not-evaluable items.**
4. **Machine-readable** — findings + `comparison_id`.
5. **Standing disclaimer** — "Line-item comparison evidence only; not a damages, reserve, or
   settlement determination and not a coverage or liability decision. No amount has been set or
   approved."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII (including medical). Mask claimant identifiers. Retain findings + citations. Log
read + external-delivery approval. Never exfiltrate claim/medical data.

## Gotchas
- **A duplicate flag is a review prompt, not a denial.** The same item may legitimately appear on
  two documents; the adjuster decides.
- **Differences** across estimates are expected (competing quotes); report the spread, do not pick
  a "right" number.
- **Unsupported** means no linked document, not "invalid" — report the missing support factually.
- **Never net, sum, or "recommend" a damages figure** — evidence only.
