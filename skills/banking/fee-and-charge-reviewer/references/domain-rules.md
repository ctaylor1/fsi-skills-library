# Domain Rules — fee-and-charge-reviewer

How posted fees are categorized and compared against **disclosed terms**, and how the
comparison maps to a **review outcome**. Disclosed amounts, caps, and waiver conditions are
configuration sourced from the account's fee schedule / product terms (versioned, owned by
the deposit/loan product team) — not hard-coded judgments, and never inferred from what a
fee "should" be. The firm's fee-disclosure standard (e.g., deposit account disclosures under
Reg DD/TISA, remittance/loan disclosures where applicable) is the orienting framework, but
this skill **compares against the disclosed schedule text**; it does not adjudicate whether a
disclosure or fee complies with any law or regulation.

## Fee categories (examples)

Overdraft (OD), returned-item / NSF, monthly maintenance, out-of-network ATM, outgoing wire,
foreign-transaction, minimum-balance, paper-statement, stop-payment, late-payment, account
research. Categories come from the disclosed term the fee maps to; a posted fee with no
matching term is `not_in_schedule`.

## Comparison status taxonomy

| Status | Assigned when | Evidence attached |
| ------ | ------------- | ----------------- |
| `matches_disclosed` | Posted amount ≤ disclosed amount + tolerance, within caps, no waiver met | Posted row + disclosed term |
| `exceeds_disclosed` | Posted amount > disclosed amount + `amount_tolerance` | Posted row + disclosed term (amount delta) |
| `frequency_cap_exceeded` | Count of the fee_code exceeds the disclosed `cap_per_day` or `cap_per_period` | The over-cap row(s) + disclosed cap |
| `waiver_condition_may_apply` | A disclosed `waiver_condition` for the fee is present in `account_context.waivers_met` | Posted row + disclosed term + met condition(s) |
| `not_in_schedule` | Posted fee has no matching disclosed term | Posted row only (no disclosed term exists) |

Statuses are assigned with a fixed **precedence**: `not_in_schedule` → `frequency_cap_exceeded`
→ `exceeds_disclosed` → `waiver_condition_may_apply` → `matches_disclosed`. Each posted fee
gets exactly one status. `exceeds_disclosed`, `frequency_cap_exceeded`, and `not_in_schedule`
are **discrepancies**; `waiver_condition_may_apply` is a **question**.

## Review-outcome mapping (deterministic, documented)

| Outcome | Rule |
| ------- | ---- |
| **discrepancies_found** | Any finding has a discrepancy status |
| **questions_to_raise** | No discrepancies, but ≥ 1 `waiver_condition_may_apply` |
| **no_discrepancies** | Every finding is `matches_disclosed` |

The outcome is a **triage signal for a human reviewer**. It is not a determination that a fee
was improper, unauthorized, or unlawful, and it never triggers a refund, credit, or reversal.
`total_flagged_for_review` sums the discrepancy deltas (overcharge amount, over-cap amount,
undisclosed amount) and is labeled "for review" — it is **not** an amount owed or approved.

## Hard boundaries (fail closed)

- Never state or imply a fee **violates** a law, regulation, or the disclosure (e.g., "this
  violates Reg DD", "unlawful fee", "illegal", "non-compliant") — describe the comparison
  factually and attribute any conclusion to the human reviewer.
- Never **decide or promise** a refund, credit, adjustment, or reversal ("we will refund",
  "the bank owes", "entitled to a refund", "reverse the fee", "issue a credit").
- Never take or record a fee **action** (reverse/waive/credit) — those are authorized-system
  actions taken by a human after review.
- Never give **legal advice** ("you should sue", "grounds for a lawsuit", "file a lawsuit").
- Never infer the disclosed amount, cap, or waiver — use only the provided fee schedule /
  product terms and the recorded `config_version`.

## Neutral questions & remediation-request drafting

For each flagged finding, draft a **neutral question** that asks servicing to confirm the
applicable schedule version or whether a waiver applied. The `remediation_request_draft` is a
**request for review**, explicitly not an assertion that any charge was improper, and is a
draft a human must review before any external delivery.
