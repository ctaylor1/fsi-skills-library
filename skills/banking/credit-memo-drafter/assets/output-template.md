# Commercial Credit Memorandum — Controlled Template

Draft-only deliverable. Every figure must trace to a cited source; no section may assert a
credit decision, approval, booking, funding, filing, or covenant/exception waiver. The memo
is decision-support for a human underwriter and credit officer.

- **Memo ID:** `{memo_id}`
- **Policy version:** `{policy_version}`  ·  **Template version:** `{template_version}`
- **Disposition:** `draft-for-underwriter-review` (the only disposition this skill emits)

## Required sections

Each section below is mandatory and must carry at least one source citation
(`{system}:{ref}@{date/version}`). These keys are enforced by `scripts/validate_output.py`
(`REQUIRED_SECTIONS`).

1. **Borrower overview** (`borrower_overview`) — obligor identity (masked), entity type,
   industry; cite loan-origination / financial-statement sources.
2. **Facility summary** (`facility_summary`) — each requested facility (type, amount, tenor,
   purpose) and total exposure; cite the origination record per facility.
3. **Financial analysis** (`financial_analysis`) — approved spread, EBITDA, total debt,
   leverage vs. policy cap, and spread tie-out status; cite the approved spread.
4. **Repayment analysis** (`repayment_analysis`) — CFADS, total debt service, DSCR vs. the
   policy floor; cite the approved spread.
5. **Collateral analysis** (`collateral_analysis`) — collateral items, appraised and lendable
   (advance-adjusted) values, LTV, and advance coverage; cite each appraisal.
6. **Risk rating** (`risk_rating`) — approved risk grade and model; cite the rating record. If
   no approved grade is provided, mark `needs-data` (an unsupported assertion, not a guess).
7. **Covenants** (`covenants`) — each covenant, threshold, tested metric, headroom, and any
   breach-at-inception; cite the credit agreement clause.
8. **Policy exceptions** (`policy_exceptions`) — each policy exception with its documented
   mitigant; cite the policy reference. Exceptions are *documented*, never *granted* here.
9. **Recommendation** (`recommendation`) — advisory observations for the underwriter (e.g.,
   DSCR below floor, leverage above cap, covenant breach). Presents evidence and a
   recommendation for review **only**; states that the credit decision and booking remain
   with the human approvers.

## Required control blocks

- **`computed_metrics`** — DSCR, leverage, LTV, exposure, lendable collateral (deterministic).
- **`spread_tie_out`** — status `tie` required; recomputed ratios must reconcile to the spread.
- **`policy_coverage`** — applicable vs. addressed requirements and any gaps.
- **`exceptions_with_mitigants`** — every exception paired with its mitigant.
- **`unsupported_assertions`** — MUST be empty; any unsupported claim is listed here and fails
  validation rather than being presented as fact.
- **`approvals`** — the required approver roles (Underwriter, Credit Officer, and Credit
  Committee for large credits), each `status: pending`. The draft never self-grants approval.
- **`standing_note`** — the fixed draft-only disclosure.

## Standing note (verbatim)

> Draft credit memorandum for human underwriting adjudication only. No credit decision has
> been made; no facility has been approved, declined, booked, funded, or disbursed; and
> nothing has been filed or written to a system of record.
