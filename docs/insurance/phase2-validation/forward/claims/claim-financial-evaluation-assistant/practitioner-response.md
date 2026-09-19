# CLM-WATER-731 — internal draft financial scenarios

The repair scenario produces a projected gross claim total of **$62,696.50**, with **$4,500.00** expected recovery shown separately and a resulting net scenario total of **$58,196.50**. The contested scenario's recovery remains unknown, so its net total cannot be calculated. No scenario or reserve has been selected.

Prepared for the fictional insurer's adjuster/claims finance reviewer; US-NY commercial property; review date 18 September 2026, ledger valued 17 September; synthetic review profile version 1. LEDGER is gross direct USD. ESTIMATE's future amounts are additional unpaid costs replacing the current outstanding estimate for comparison, not costs added on top of that estimate.

| Component | Current paid | Current outstanding | Reported incurred |
|---|---:|---:|---:|
| Indemnity | $18,450.75 | $41,800.00 | $60,250.75 |
| Expense | $2,175.25 | $6,400.00 | $8,575.25 |

| Scenario measure | REPAIR | CONTESTED |
|---|---:|---:|
| Additional unpaid indemnity | $36,920.50 | $52,600.00 |
| Additional unpaid expense | $5,150.00 | $11,200.00 |
| Projected gross total indemnity | $55,371.25 | $71,050.75* |
| Projected gross total expense | $7,325.25 | $13,375.25* |
| Difference from outstanding indemnity | −$4,879.50 | +$10,800.00* |
| Difference from outstanding expense | −$1,250.00 | +$4,800.00* |
| Separately expected recovery | $4,500.00 | Unknown |
| Net scenario total | $58,196.50 | Unknown |

*CONTESTED gross totals and differences are independent calculations from known raw amounts. The native helper suppresses all derived fields in that scenario because recovery is unknown, and labels it `not_evaluable`. The independent gross figures do not cure that missing recovery evidence. They are shown separately to make the known financial comparison useful; no recovery has been treated as zero.

REPAIR assumes acceptance of the repair scope and expenses outside indemnity scope. CONTESTED assumes expert-supported concealed damage and further expert/legal costs. Paid amounts are added once; existing outstanding amounts are used only to calculate changes. Independent arithmetic agrees with every native REPAIR and current-position result.

The overall output is `needs-data` with partial completeness/evaluability. The adjuster should obtain the recovery assessment, review coverage/damage scope and applicable expense/limit treatment, then submit reviewed scenarios to the authorized financial reviewer. Changes shown are comparisons, not instructions to release or increase reserves. Human professional review remains pending; no booking, settlement or payment occurred.

Sources: synthetic LEDGER, ESTIMATE and REVIEW-PROFILE, version 1, retained in `raw_sources/`.
