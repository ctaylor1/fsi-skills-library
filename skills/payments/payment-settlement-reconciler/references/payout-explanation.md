# Report-only payout explanation

This mode replaces the former standalone payout-summary entrypoint. It runs without bank
or ledger records and remains useful when the report does not tie to a declared payout.

Input: mode=explain-payout, report_id, merchant_id (masked), as_of_date, config_version, lines,
and explicit legal_entity_id/account_id/currency/settlement_cycle. Lines may override these
scope fields; groups never combine distinct scopes. Each line needs line_id, category,
description, source.system/ref, and one of net_amount, gross_amount or fee_amount. An unvalued
line is accepted as a gap. Optional funding has expected_net, source_ref, funding_date and
explicit/inherited partition context. A funding advice describes an expected amount, not
verified receipt of cash.

## Normalization

Category amounts are signed credits/deductions. Supported categories: gross_sales, refunds,
chargebacks, interchange_fees, scheme_fees, processor_fees, other_fees, fees, adjustments,
reserve_held, reserve_released, cash_advance, other and net_settlement. Retain unknown labels
with a warning. Prefer the explicit signed net_amount, otherwise derive a fee deduction from
negative absolute fee_amount or use signed gross_amount. Record the selected basis.

net_settlement lines are reported-net controls; never add them to component amounts.
Duplicate line IDs or source-system/source-row references quarantine their values across the
entire supplied report, including differing currencies and cycles. A renamed line cannot
reuse an existing source row as another contribution. Multiple net controls remain ambiguous.
Positive deduction lines and conflicting fee/net values are surfaced as source issues. A gross-sales
line with differing gross and net values requires separate component normalization; its contribution
remains unknown instead of labeling a net amount as gross sales.

Known component amounts sum to known_line_subtotal. calculated_net is null if any component
is unvalued or ambiguous. Do not call a subtotal a complete net figure. Explicit zeros count;
absence of fee or gross-sales evidence is not evidence of zero fees or zero sales.

Compare calculated, reported and declared funding amounts only within the same partition.
A mismatch is a discrepancy in the result, not invalid input/output. Missing pairs are not
evaluable. No FX conversion or account/cycle aggregation is performed.

## Metrics and language

Report total fee magnitudes and effective_fee_rate_pct = total fees / gross sales * 100 only
when inputs support them. The ratio is rounded to six decimal places, not a competitiveness
judgment. Route price advice to merchant-payment-cost-analyzer. Do not certify settlement correctness,
funding receipt or ledger reconciliation. The structured output is factual; added freeform
claims outside the deterministic contract fail validation.

## Migrated examples

- settlement_example.json retains the original 100000 sales, 2850 fees, 90500 known subtotal
  and unvalued pending adjustment. The calculated full net correctly remains unknown.
- payout_mismatch_example.json removes that unvalued line and declares funding of 90000.
  Output calculates 90500 and preserves a -500 difference without bank or ledger inputs.
- summary_with_advice.json remains a deliberately invalid output fixture.
