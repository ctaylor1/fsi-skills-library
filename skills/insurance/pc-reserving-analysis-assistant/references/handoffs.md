# P&C reserve analysis handoffs

Inputs are native cumulative triangles plus valuation/basis/unit metadata, a source reference,
and a versioned method/assumption set. A claim, treaty or monitor ID alone is not acceptable.
Every receiver validates its own input schema; retain upstream partial states and unresolved issues.

| Request | Owner and required boundary |
| --- | --- |
| Individual claim file evidence and completeness | `claim-file-quality-reviewer`; supply its native claim input |
| Individual claim reserve adequacy or financial evaluation | `claim-financial-evaluation-assistant`; paid/case/future scenario input and authorized claims review, without selecting a booked reserve |
| Existing catastrophe event/feed monitoring | `catastrophe-exposure-monitor`; supply native event/exposure input |
| Policy/location/peril accumulation | `insurance-exposure-aggregation-analyzer`; supplied identity, currency and inventory scope |
| Supplied joint annual event-loss statistics | `catastrophe-scenario-analyzer`; compatible event/year/probability and loss basis; no summing marginal PMLs |
| Hazard/vulnerability model generation or independent catastrophe model validation | Qualified catastrophe modeling specialist |
| Explain one treaty | `reinsurance-contract-reviewer`; supplied wording and supported illustration assumptions |
| Ceded premium/claim statements, notices or recoverable reconciliation | `reinsurance-contract-administration-reviewer`; supply native treaty, statement and ledger records; ceded reserve methodology and cession allocation remain specialist gaps |
| Independent actuarial reserve/model validation | Qualified independent actuary; financial asset valuation tools are not substitutes |
| Management/board packaging | `management-reporting-packager`; construct native input, retain draft and signoff status |
| Insurance subledger/GL close review | `insurance-financial-close-reviewer`; native ledger scope and signed movements; no authority to select/book is transferred |
| General close orchestration | `month-end-close-orchestrator`; construct native input and retain draft status |

The qualified actuary reviews methods, selects the carried reserve and assesses adequacy.
Finance acts only under separately granted authorization. Needs-data and anomaly-flagged
segments remain blocked from packageable indications. Reusing a content-bound artifact prevents
unnoticed source drift but is not evidence of professional acceptance or source authenticity.
