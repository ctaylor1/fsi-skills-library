# Field-repair planning rules

The fixed package catalog is `offline-field-repair-v1`:

| Confirmed defect | Permissible proposed fields |
|---|---|
| `invalid_beneficiary_detail` | beneficiary BIC, account, name, address |
| `missing_remittance_info` | remittance information |
| `missing_purpose_code` | purpose code |

Machine field keys are listed in `scripts/validate_input.py`. The supplied policy must further authorize the exact field, exception type, entity, rail, currency, amount and role. There is no default currency or universal monetary authority limit.

Only a held/rejected original instruction can enter this planner. Exact old value must match the snapshot and the new value must differ. The screening scope must match the complete proposed instruction. A settled or unknown-state instruction is not eligible for local repair planning.

The plan consists of a proposed field correction and possible resubmission, with current-state verification required before any external action. `expected_status` is `proposal_only`; no ledger deltas or successful resubmission are asserted.

Release of screening holds, returns, refunds, cancellations, and recall responses are not field repair. Such requests require the appropriate authorized servicing workflow. No action is universally reversible; a recall/compensation may fail.
