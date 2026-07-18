---
name: credit-memo-drafter
description: >-
  Draft commercial credit memoranda from approved financial spreads, borrower statements and
  tax returns, collateral, covenants, risk ratings, and credit-policy requirements: compute
  DSCR, leverage, and LTV with spread tie-outs, document policy exceptions with mitigants, and
  assemble citation-linked, template-conformant memos for underwriter adjudication. Use when a
  commercial credit analyst or relationship manager needs to turn an approved credit package
  into a review-ready memo, refresh repayment/collateral analysis, or surface policy exceptions
  and covenants with traceable evidence. HARD BOUNDARY: decision-support only — this skill
  NEVER approves, declines, prices, books, funds, or files a facility, NEVER grants or waives a
  policy exception or covenant, and NEVER writes a system of record; every credit decision and
  exception disposition requires a human underwriter / credit officer.
license: MIT
compatibility: Amazon Quick Desktop; requires loan-origination, approved financial-spread, document-intelligence, credit-policy, covenant/collateral, risk-rating, CRM, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Banking"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Banking product & credit operations"
  aws-fsi-primary-user: "Commercial credit analyst / relationship manager"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Credit Memo Drafter

## Purpose and outcome
Turn an **approved** commercial credit package into a **review-ready draft credit
memorandum**. From the approved financial spread, borrower financials/tax returns,
collateral, covenants, risk rating, and credit-policy requirements, the skill computes the
repayment and coverage metrics (DSCR, leverage, LTV), ties the recomputed ratios back to the
spread, checks policy coverage and covenant headroom, documents exceptions with their
mitigants, and assembles a template-conformant memo where **every figure carries a citation**.
The outcome is a decision-support artifact an underwriter can adjudicate — never a credit
decision, approval, booking, or filing.

## Use when
- "Draft a credit memo for this borrower from the approved spread and package."
- "Assemble the repayment and collateral analysis into our credit-memo template."
- "Refresh the DSCR / leverage / LTV and covenant section of this memo with citations."
- "Document the policy exceptions and mitigants for underwriter review."

## Do not use
- To **make, price, or communicate a credit decision** (approve/decline/adverse action),
  **book/fund** a facility, or **file** anything — refuse; these require a human decision.
- To **grant or waive** a policy exception or covenant — the memo *documents* exceptions and
  mitigants; disposition stays with the approver.
- To **spread** raw financial statements/tax returns → `financial-spreading-assistant`.
- To **certify package completeness** for underwriting/closing → `loan-package-completeness-checker`.
- To **monitor covenants** over the life of the loan → `covenant-compliance-monitor`.
- For **retail affordability** or consumer adverse-action decisions → out of scope.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream, the approved spread comes from
`financial-spreading-assistant`, statement analysis from `bank-statement-analyzer`, forecasts
from `cashflow-forecaster`, and the assembled package from `credit-application-packager`.
Downstream, `loan-package-completeness-checker` certifies the package and
`covenant-compliance-monitor` tracks covenants after booking; portfolio effects go to
`credit-risk-portfolio-analyzer`. The **credit decision itself** is a human underwriter /
credit-officer / credit-committee action — there is no skill for it. This skill emits a
durable `memo_id` draft; it does not re-spread, certify, decide, or book.

## Inputs and prerequisites
- A credit-memo request bundle: borrower identity, requested facilities, the **approved**
  financial spread (with `spread_provider`), collateral with appraisals and advance rates,
  covenants (from the credit agreement), risk rating, applicable policy requirements,
  exceptions with mitigants, and source evidence. Schema:
  [scripts/validate_input.py](scripts/validate_input.py) and
  [references/domain-rules.md](references/domain-rules.md).
- Read access to loan origination, approved spreads, document intelligence, credit policy,
  covenant/collateral records, risk rating, and CRM. Figures must come from cited sources;
  the skill does not originate financial data.

## Source hierarchy
See [references/source-map.md](references/source-map.md). Credit policy is authoritative for
requirements and thresholds; the credit agreement for covenants; the approved spread for
financials; appraisals for collateral values; the risk-rating system for the grade. Cite
every item as `{system}:{ref}@{date/version}`. Policy and template versions are **versioned
contracts** recorded on the memo.

## Workflow
1. **Validate input** — run `validate_input`; fail closed on structural gaps, warn where a
   missing figure forces `needs-data` (never guess a figure to complete a section).
2. **Compute metrics (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): DSCR, leverage,
   LTV, exposure, and lendable collateral, all from cited inputs.
3. **Tie out the spread** — recompute DSCR/leverage from spread primitives and reconcile to
   the ratios the approved spread reported; a break makes the financial section unsupported.
4. **Check policy coverage & covenants** — map each applicable policy requirement to a section
   or an exception-with-mitigant; compute covenant headroom and flag breach-at-inception.
5. **Assemble the draft** — fill the required template sections
   ([assets/output-template.md](assets/output-template.md)), attach citations, list any
   `unsupported_assertions`, and record the **required (pending)** approver roles.
6. **Never decide** — no approval, decline, pricing, booking, funding, filing, or exception
   waiver. The recommendation is advisory for the underwriter.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output screen enforces: draft disposition only; every required section present and
cited; `unsupported_assertions` empty; spread tie-out reconciled; approvals recorded and still
pending (no self-grant); and **no decision/closure/filing/booking/waiver language**. Fail
closed on any miss and surface the gap.

## Human approval
`required`. This skill produces evidence and a recommendation only. Every regulated action —
the credit decision, pricing, exception/covenant disposition, booking, funding, and any
system-of-record write — is reserved for the human underwriter, credit officer, or credit
committee. The memo records those roles as **pending** approvals; it never grants them.

## Failure handling
- **Missing/invalid figure** (e.g., no risk grade, no appraisal) → mark the section
  `needs-data` and list it in `unsupported_assertions`; do not fabricate a value.
- **Spread tie-out break** → financial section is unsupported; stop and surface the diff for
  re-spreading, do not present the unreconciled ratio as fact.
- **Uncovered policy requirement / exception without mitigant** → record as a coverage gap;
  the memo cannot mark it addressed.
- **Covenant breach-at-inception** → document it for the underwriter; never waive it.
- **Ambiguous borrower/facility identity** → stop; request resolution rather than guessing.
- **Tool timeout / partial data** → return a partial draft with an explicit incomplete flag;
  assume no automatic retry or step-up authorization.

## Output contract
1. **Draft memo** — `memo_id`, policy/template versions, `disposition:
   draft-for-underwriter-review`, and the required sections (each cited).
2. **Control blocks** — `computed_metrics`, `spread_tie_out`, `policy_coverage`,
   `exceptions_with_mitigants`, `unsupported_assertions` (empty when clean), `approvals`
   (pending), and the fixed `standing_note`.
3. **Machine-readable** — the full draft object keyed by `memo_id` for the underwriter's
   workflow.
4. **Standing note** — "Draft credit memorandum for human underwriting adjudication only. No
   credit decision has been made; no facility has been approved, declined, booked, funded, or
   disbursed; and nothing has been filed or written to a system of record."
See [references/controls.md](references/controls.md).

## Privacy and records
**Highly Confidential — customer NPI/PII.** Minimize and mask borrower identifiers to what the
memo requires; keep tax-return and financial-statement detail to the figures cited. Retain the
draft, its citations, and the policy/template versions per the bank's credit-file
recordkeeping. Log every source read and every draft with the analyst identity. The draft is
internal work product until an authorized human releases it.

## Gotchas
- **Draft ≠ decision.** A complete, well-cited memo is still only decision-support; the
  approval, pricing, and booking are the underwriter's.
- **Exceptions are documented, not granted.** Pair every exception with a mitigant; never
  "waive" a policy or covenant in the memo text.
- **Tie-outs are load-bearing.** If recomputed DSCR/leverage do not reconcile to the approved
  spread, the number is not yet supportable — route back to spreading, don't paper over it.
- **No guessed figures.** A missing risk grade or appraisal is `needs-data`, not an estimate.
- **Policy and template are versioned.** Record the versions so the memo is reproducible and
  reviewable; a threshold change is a config change, not analyst judgment.
- **Citations everywhere.** Every material figure ties to a source; unsupported assertions
  fail the output screen by design.
