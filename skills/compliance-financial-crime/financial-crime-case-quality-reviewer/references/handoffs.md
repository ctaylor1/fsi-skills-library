# Handoffs

| Adjacent skill | Trigger and owner boundary |
|---|---|
| `financial-crime-case-investigator` | Receive a case workpaper after validating the investigator-native output against its detached original; findings return to the investigation owner for correction. QA cannot reopen/close or adjudicate it. |
| `compliance-control-testing-assistant` | Statutory testing or formal testing mandate needs that separately accepted testing method and owner; QA counts do not create independence or assurance. |
| `compliance-remediation-evidence-reviewer` | Accepted quality findings and source-bound corrective evidence go to the remediation owner; a proposed correction does not establish closure. |
| `suspicious-activity-report-drafter` | Refer reporting-material quality issues only after authorized human reportability review; this QA output makes no filing decision. SAR evidence keeps authorized_fiu restrictions. |
| `model-validation-assistant` | Model/system validation questions belong to the model owner and independent validator; case tool-output consistency is not model validation. |
| `audit-evidence-packager` | Audit mandate/evidence packaging remains audit-owned; QA does not issue opinions or infer audit acceptance. |

The native-only producer artifact is financial_crime_case_quality_review. No receiver is assumed
to consume its schema. A separately reviewed adapter must map exact case IDs, upstream versions,
context, criterion IDs/versions, source claims, dates, issues and confidentiality/recipient limits.
Retain producer result and detached input references. Validate both producer reconstruction and
receiver intake. Unknown aliases, changed object/audience/context/cutoff or unresolved issues
withhold transfer; no automatic invocation or live transmission is implemented.
