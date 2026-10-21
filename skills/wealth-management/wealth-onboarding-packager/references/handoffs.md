# Handoffs and domain boundaries

| Adjacent skill / human | Trigger | Handoff artifact |
| --- | --- | --- |
| `customer-onboarding-document-checker` | Bank-product document completeness work | Product scope and policy-required document evidence |
| `customer-due-diligence-reviewer` | Applicable KYC/CDD evidence review is needed | Engagement/capacity, identity evidence and policy requirement |
| `sanctions-match-investigator` | Screening outcome is missing, pending or escalated | Attributed screening reference; specialist and human decide |
| `beneficial-ownership-analyzer` | Entity ownership/authority evidence requires specialist analysis | Entity registration, ownership records and source IDs |
| `enhanced-due-diligence-assessor` | Authorized specialist requests enhanced evidence | Scope, owner request and existing cited records |
| `investment-recommendation-evidence-reviewer` | An investment recommendation needs separate evidence review | Client profile and actual recommendation, outside onboarding acceptance |
| `senior-investor-protection-screener` | Safeguarding concerns arise | Minimized context and structured human observations |
| Authorized onboarding/custodian operator | Human decides acceptance/opening | artifact_id, full input hash, applicability, sources and unresolved gaps |

This package assembles evidence and owns no specialist approval or account-opening decision.
It does not duplicate bank-document checks or KYC/sanctions analysis. External review outcomes
return as sourced input records; they are not inferred from another skill's reassuring prose.
Human approval and governed systems handle acceptance, opening, activation, transfers and any
client delivery. No handoff implies automatic execution or permission to disclose restricted data.
