---
name: financials-normalizer
description: >-
  Convert inconsistent corporate, issuer, or deal financial statements into standardized,
  model-ready data: map source line items to a standard chart-of-accounts taxonomy, roll them
  up, apply documented normalization adjustments, preserve cell-level provenance, and tie the
  result back to the source subtotals and the balance-sheet identity. Use when a finance,
  banking, or research analyst says "normalize these financials", "map this 10-K / issuer /
  deal statement to our standard template", "standardize these line items for the model", or
  needs a reproducible, source-linked normalized dataset for a downstream model or report.
  This skill maps, adjusts-with-rationale, and tie-out-checks only; it NEVER opines that the
  statements are GAAP/IFRS-compliant or materially correct, issues an accounting, audit, or
  investment judgment or recommendation, restates or posts figures to any system of record, or
  produces borrower credit spreading into bank templates; those are human/authorized-system
  actions or separate workflows.
license: MIT
compatibility: Amazon Quick Desktop; requires document-intelligence (statement/schedule extraction), entity-resolution, controlled chart-of-accounts/mapping library, normalization-policy library, and versioned-config MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Finance & Operations"
  aws-fsi-skill-type: "Utility skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Domain workflow"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Confidential (financial records)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Finance & Controllership"
  aws-fsi-primary-user: "Finance / banking / research analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Financials Normalizer

## Purpose and outcome
Given a source financial-statement extract for an entity, issuer, or deal, run a **multi-step
normalization procedure**: map each source line item to a standard chart-of-accounts account,
roll the detail up per account and period, apply documented normalization adjustments (with
rationale and source), preserve provenance back to the source cell, and **tie the result out**
against the source's own subtotals and the balance-sheet identity. A successful output is a
reproducible, source-linked **model-ready dataset** with a suggested readiness band that lets
an analyst feed a downstream model or report — the accounting, audit, and investment judgment,
and any posting, remain human.

## Use when
- "Normalize these issuer / corporate / deal financials into our standard template."
- "Map this 10-K / audited statement / management-account line items to our chart of accounts."
- "Standardize these figures for the DCF / three-statement / comps model and tie them out."
- "Roll these schedules up to standard accounts and keep the provenance."
- An analyst needs a consistent, cited, reproducible normalized dataset to hand to a model.

## Do not use
- The task is **borrower credit spreading** into a bank credit template (credit-analysis
  intent) → `financial-spreading-assistant`.
- You need to **build the model itself** (three-statement / DCF / LBO / merger / comps) →
  `three-statement-model-builder`, `dcf-modeler`, `lbo-model-builder`, `merger-model-builder`,
  or `comps-analysis-builder`.
- The figures **don't tie to the ledger/subledger** (a reconciliation break, not a
  source-to-model normalization) → `gl-reconciler`.
- You want an **analysis of earnings quality / results** → `earnings-results-analyzer`; a
  valuation built on these inputs reviewed → `valuation-reviewer`.
- Any **accounting, audit, investment, or credit opinion** on the entity → out of scope; route
  to a licensed specialist / the authorized human.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a normalized dataset
with a durable `normalization_id`; downstream model/report/audit skills consume it. It must not
duplicate their model-building, spreading, reconciliation, or posting steps.

## Inputs and prerequisites
- **Entity/issuer/deal identifier** and the **`as_of`** date, plus the `source_document`.
- **Source line items** — each with `line_id`, `raw_label`, `statement`
  (`income_statement`/`balance_sheet`/`cash_flow`), `period`, `value`, and a `source_ref` to
  the source cell. Subtotal lines carry `is_subtotal: true` and either `components` (line_ids
  they sum) or an identity `role` (`total_assets`/`total_liabilities`/`total_equity`).
- **Mapping** — `(source_label, statement) → std_account` with optional `normal_sign`.
- Optional **adjustments** — reclass / non-recurring / normalization entries with `amount`,
  `rationale`, `source_ref`, and `approver`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to document-intelligence, the mapping and normalization-policy libraries, entity
  resolution, and the versioned **config** (see [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **source statement is the
position of record**; normalization never overrides a reported figure. The mapping library,
normalization policy, and config are versioned contracts. Cite every mapped account's
provenance and every finding's evidence to a source row; when extracts conflict, cite both and
raise the break — never resolve silently.

## Workflow
1. **Scope & validate** — confirm the entity and `as_of`; load the extract, mapping, and
   config; run `validate_input`. Note which tie-outs are evaluable (subtotals with components;
   the three identity anchors).
2. **Map & roll up (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to map each detail
   line to a standard account, roll it up per account and period, and record provenance
   (`line_id`s). Unmapped detail is reported under `unmapped`, never dropped.
3. **Apply documented adjustments** — attach reclass / non-recurring / normalization
   adjustments to their standard accounts, each carrying rationale + source + provenance.
4. **Tie out** — reconcile each reported subtotal to the sum of its declared components and
   check the balance-sheet identity (assets = liabilities + equity) within tolerance. Each
   check returns a finding with its evidence and citations; checks without data are reported
   `not_evaluable`.
5. **Suggest readiness** — map the fired-finding profile to a readiness band (Model-ready /
   Needs mapping review / Hold - tie-out break) per the documented mapping. This is a triage
   suggestion for a human, explicitly **not** an accounting/audit sign-off.
6. **Write the pack** — plain-language mapping + adjustments + tie-outs, the review
   considerations, the not-evaluable checks, and the machine-readable normalized dataset.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every fired finding has evidence + citation, no accounting /
audit / investment judgment, recommendation, restatement, or posting language is present, the
readiness band maps deterministically from the findings, the standing disclaimer is present,
and review considerations are included. Fail closed on any miss.

## Human approval
`external-delivery`: human review required before the normalized dataset is delivered to a
downstream model/report, an audit file, or any system of record. No approval is needed for the
analyst's own read. The skill never restates, posts, judges, or approves.

## Failure handling
- **Missing mapping** (source labels not in the mapping pack) → report them under `unmapped`
  and fire `unmapped_line_item`; never guess a standard account or silently drop the line.
- **Ambiguous entity/period** → stop and confirm; never normalize the wrong entity or mix
  periods.
- **Missing identity anchors / components** → run only the tie-outs the data supports; report
  the rest as `not_evaluable`.
- **Stale/conflicting extracts** → cite both; do not resolve silently or override the reported
  figure.
- **Tool timeout** → return the accounts mapped so far with a clear "incomplete" flag; page
  long statement sets as resumable stages.

## Output contract
1. **Summary** — entity, `as_of`, framework/currency, counts (accounts mapped, unmapped,
   findings), suggested readiness band.
2. **Normalized accounts** — per standard account: mapped value, adjustments applied,
   normalized value, and the source `line_id` provenance.
3. **Tie-outs** — reported vs computed subtotal and the identity check, with diffs.
4. **Findings** — per fired finding: check name, plain-language reason, severity, evidence
   rows (cited), and the threshold/context it breached.
5. **Review considerations** — explicit benign explanations (capture completeness, rounding,
   approved delegation, immaterial line) so the reviewer weighs both sides.
6. **Not-evaluable checks** — with the reason each could not run.
7. **Machine-readable** — normalized dataset + findings + `normalization_id` for downstream
   skills.
8. **Standing disclaimer** — "Normalization output only; not an accounting, audit, or
   investment judgment, and not a system-of-record posting. Source figures are mapped and tied
   out, not restated or re-booked; a human reviewer must accept the normalized mapping before
   use."
See [references/controls.md](references/controls.md).

## Privacy and records
Confidential financial records; may include issuer- or deal-confidential, pre-release
financials (MNPI risk). Minimize data in the output to what evidences the mapping and findings;
respect information-barrier / need-to-know controls. Retain the normalization + provenance +
citations + `config_version` per records policy; log the read and any external-delivery
approval. Never exfiltrate issuer/deal data.

## Gotchas
- **A readiness band is not a decision.** Fired findings justify a *review readiness*, never an
  accounting/audit sign-off, an investment recommendation, or a posting.
- **The source figure is the record.** Normalization maps and ties out; it never overrides a
  reported number. A normalized value must trace to its source cell via provenance.
- **Subtotals are controls, not detail.** Never roll a subtotal into a standard account — that
  double-counts. Use subtotals only for tie-outs.
- **Tie-out breaks describe the data, not intent.** Flag a subtotal or identity break
  factually; never assert "management inflated assets" — that is an investigation conclusion.
- **Adjustments need evidence.** A reclass or non-recurring add-back without a rationale and
  source is a finding, not a silent correction; a material one needs an approver.
- **Do not tune thresholds to an extract**: tolerances come from the approved, versioned
  config, not from what would make this statement tie.
