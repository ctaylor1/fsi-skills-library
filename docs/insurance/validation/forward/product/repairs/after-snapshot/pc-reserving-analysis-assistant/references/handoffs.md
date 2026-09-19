# P&C reserve analysis handoffs

Inputs are native cumulative triangles plus valuation/basis/unit metadata, a source reference,
and a versioned method/assumption set. A claim, treaty or monitor ID alone is not acceptable.
Every receiver validates its own input schema; retain upstream partial states and unresolved issues.

| Request | Owner and required boundary |
| --- | --- |
| Individual claim file evidence and completeness | `claim-file-quality-reviewer`; supply its native claim input |
| Individual claim reserve adequacy or financial evaluation | Qualified claims specialist; capability unavailable in this release |
| Existing catastrophe event/feed monitoring | `catastrophe-exposure-monitor`; supply native event/exposure input |
| New PML/accumulation modeling or catastrophe model validation | Specialist capability unavailable; obtain qualified model analysis |
| Explain one treaty | `reinsurance-contract-reviewer`; supplied wording and supported illustration assumptions |
| Ceded reserve mechanics, cession allocation or recoverable administration | Specialist capability unavailable; treaty interpretation does not perform these jobs |
| Independent actuarial reserve/model validation | Qualified independent actuary; financial asset valuation tools are not substitutes |
| Management/board packaging | `management-reporting-packager`; construct native input, retain draft and signoff status |
| Close preparation | `month-end-close-orchestrator`; construct native input; no authority to select/book is transferred |

The qualified actuary reviews methods, selects the carried reserve and assesses adequacy.
Finance acts only under separately granted authorization. Needs-data and anomaly-flagged
segments remain blocked from packageable indications. Reusing a content-bound artifact prevents
unnoticed source drift but is not evidence of professional acceptance or source authenticity.
